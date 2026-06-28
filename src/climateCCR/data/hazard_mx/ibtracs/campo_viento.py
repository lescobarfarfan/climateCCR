"""
campo_viento.py
===============
Campo de viento de ciclón tropical SIN necesidad de CLIMADA: implementa el modelo
paramétrico de Holland (1980) directo desde las ecuaciones (solo numpy + geopandas).
Opcionalmente puede delegar en CLIMADA si está instalado (--backend climada).

Se usa desde procesar_ibtracs.py con la bandera --campo-viento. Parámetros:
  --paso-temporal-min : interpola la traza a este paso (p. ej. 60, 30, 15 min)
  --granularidad-malla: malla regular en grados (p. ej. 0.5 -> 0.5°x0.5°)
  --backend           : 'holland' (propio) | 'climada'

Referencias (ver fuentes/ibtracs.md §9 y §11):
  - Holland, G. J. (1980), Mon. Wea. Rev. 108, 1212-1218  (perfil paramétrico).
  - Holland (2008), Mon. Wea. Rev. 136, 3432-3445  (parámetro B revisado) [confirmar DOI].
  - Geiger, Frieler & Bresch (2018), ESSD 10, 185-194  (umbrales 34/64/96 kt).
  - Factor gradiente->superficie ~0.9: convención (p. ej. Powell et al. 2003) [confirmar].
  - Rmax cuando falta: estimación empírica documentada (placeholder a calibrar).
"""
from __future__ import annotations
import numpy as np
import pandas as pd

# Constantes físicas
RHO = 1.15          # densidad del aire (kg/m^3)
OMEGA = 7.292e-5    # velocidad angular de la Tierra (rad/s)
KT_A_MS = 0.514444  # nudos -> m/s
NMI_A_KM = 1.852    # millas náuticas -> km
RED_SUP = 0.90      # factor de reducción gradiente -> superficie (10 m)
PENV_HPA = 1010.0   # presión ambiental por defecto (hPa)
R_TIERRA_KM = 6371.0
UMBRALES_KT = (34, 64, 96)  # TCE-DAT (Geiger et al. 2018)


def _haversine_km(lat0, lon0, lat, lon):
    """Distancia great-circle (km) de un punto (lat0,lon0) a arrays lat/lon."""
    lat0r, lon0r = np.radians(lat0), np.radians(lon0)
    latr, lonr = np.radians(lat), np.radians(lon)
    d = (np.sin((latr - lat0r) / 2) ** 2
         + np.cos(lat0r) * np.cos(latr) * np.sin((lonr - lon0r) / 2) ** 2)
    return 2 * R_TIERRA_KM * np.arcsin(np.sqrt(d))


def parametro_holland_B(vmax_ms, dp_pa):
    """B de Holland (1980): B = rho*e*Vmax^2 / dp. Acotado a [1.0, 2.5]."""
    if vmax_ms is None or dp_pa is None or dp_pa <= 0 or np.isnan(vmax_ms):
        return 1.3  # default razonable si faltan datos
    B = RHO * np.e * vmax_ms ** 2 / dp_pa
    return float(np.clip(B, 1.0, 2.5))


def estimar_rmax_km(vmax_kt, lat_deg):
    """
    Rmax (km) cuando IBTrACS no lo trae. PLACEHOLDER documentado a calibrar:
    decrece con la intensidad y crece con la latitud. NO usar como verdad;
    preferir USA_RMW si existe. Forma simple y transparente.
    """
    if vmax_kt is None or np.isnan(vmax_kt):
        return 50.0
    rmax = 50.0 * np.exp(-0.005 * (vmax_kt - 34)) + 0.5 * abs(lat_deg)
    return float(np.clip(rmax, 15.0, 150.0))


def viento_holland_kt(r_km, rmax_km, vmax_kt, lat_deg=None, pc_hpa=None,
                      penv_hpa=PENV_HPA, B=None):
    """
    Viento sostenido en superficie (nudos) a distancia r_km del centro, perfil de
    Holland (1980) ANCLADO a Vmax: pica en Vmax en r=Rmax y decae con la distancia.
    El Vmax de best-track ya es viento de superficie (10 m) => NO se re-reduce.
    B se deriva de Vmax y del déficit de presión si hay presión; si no, default 1.3.
    r_km puede ser array. (Versión sin término de Coriolis; refinamiento documentado.)
    """
    if vmax_kt is None or (isinstance(vmax_kt, float) and np.isnan(vmax_kt)) or vmax_kt <= 0:
        return np.zeros_like(np.asarray(r_km, float))
    vmax_ms = vmax_kt * KT_A_MS
    if B is None:
        if pc_hpa is not None and not (isinstance(pc_hpa, float) and np.isnan(pc_hpa)):
            dp_pa = max((penv_hpa - pc_hpa) * 100.0, 1.0)
            B = float(np.clip(RHO * np.e * vmax_ms ** 2 / dp_pa, 1.0, 2.5))
        else:
            B = 1.3
    r_m = np.maximum(np.asarray(r_km, float) * 1000.0, 1.0)
    rmax_m = max(rmax_km * 1000.0, 1.0)
    term = (rmax_m / r_m) ** B
    shape = np.sqrt(term * np.exp(1.0 - term))  # perfil normalizado: =1 en r=Rmax
    return vmax_ms * shape / KT_A_MS            # superficie (kt)


# --------------------------------------------------------------------------- #
# Decaimiento sobre tierra: Kaplan & DeMaria (1995)
# --------------------------------------------------------------------------- #
# Coeficientes de EE.UU. (Kaplan & DeMaria 1995). Para México no hay valores
# establecidos; se usan los de EE.UU. como mejor aproximación disponible (a revisar).
KD_R = 0.90       # factor de reducción al cruzar la costa
KD_VB = 26.7      # viento de fondo (kt)
KD_ALPHA = 0.095  # constante de decaimiento (1/h)


def decaimiento_kaplan_demaria(track, R=KD_R, Vb=KD_VB, alpha=KD_ALPHA,
                               umbral_tierra_km=1.0):
    """
    Aplica el decaimiento de Kaplan & DeMaria (1995) al Vmax sobre tierra:
        V(t) = Vb + (R*V0 - Vb) * exp(-alpha * t)
    donde V0 es el Vmax en landfall y t las horas desde landfall.
    Devuelve `track` con columna 'vmax_efectivo' = min(Vmax_besttrack, V_KD) sobre
    tierra (solo puede REDUCIR; evita sobreestimar interior y no infla si best-track
    ya viene debilitado), y = Vmax_besttrack sobre agua.
    Requiere DIST2LAND (km): tierra si DIST2LAND <= umbral_tierra_km.
    """
    d = track.sort_values("ISO_TIME").reset_index(drop=True).copy()
    vmax = pd.to_numeric(d.get("WMO_WIND"), errors="coerce")
    if "USA_WIND" in d.columns:
        vmax = vmax.fillna(pd.to_numeric(d["USA_WIND"], errors="coerce"))
    d["_vmax"] = vmax
    if "DIST2LAND" not in d.columns:
        d["vmax_efectivo"] = d["_vmax"]
        return d.drop(columns="_vmax")
    es_tierra = pd.to_numeric(d["DIST2LAND"], errors="coerce").fillna(9999) <= umbral_tierra_km

    vmax_ef = d["_vmax"].to_numpy(dtype=float).copy()
    landfall_t = None
    V0 = None
    for i in range(len(d)):
        if es_tierra.iloc[i]:
            if landfall_t is None:  # acaba de tocar tierra
                landfall_t = d["ISO_TIME"].iloc[i]
                V0 = vmax_ef[i - 1] if i > 0 and not np.isnan(vmax_ef[i - 1]) else d["_vmax"].iloc[i]
            if V0 is not None and not np.isnan(V0):
                t_h = (d["ISO_TIME"].iloc[i] - landfall_t).total_seconds() / 3600.0
                v_kd = Vb + (R * V0 - Vb) * np.exp(-alpha * t_h)
                bt = d["_vmax"].iloc[i]
                vmax_ef[i] = min(bt, v_kd) if not np.isnan(bt) else v_kd
        else:
            landfall_t, V0 = None, None  # de regreso sobre agua: reinicia
    d["vmax_efectivo"] = vmax_ef
    return d.drop(columns="_vmax")  # m/s -> superficie -> nudos


# --------------------------------------------------------------------------- #
# Interpolación temporal de la traza
# --------------------------------------------------------------------------- #
def interpolar_traza(df_storm, paso_min):
    """Remuestrea una tormenta (un SID) al paso temporal dado (interp. lineal en tiempo)."""
    d = df_storm.sort_values("ISO_TIME").set_index("ISO_TIME")
    cols = [c for c in ["LAT", "LON", "WMO_WIND", "USA_WIND", "WMO_PRES", "DIST2LAND"] if c in d.columns]
    d = d[cols].apply(pd.to_numeric, errors="coerce")
    d = d.resample(f"{int(paso_min)}min").interpolate(method="time").dropna(subset=["LAT", "LON"])
    return d.reset_index()


# --------------------------------------------------------------------------- #
# Malla sobre la capa de estados
# --------------------------------------------------------------------------- #
def construir_malla(ruta_estados, granularidad_deg, col_estado="NOMGEO"):
    """
    Malla regular (granularidad_deg x granularidad_deg) sobre el bbox de México,
    quedándose con las celdas cuyo centro cae dentro de algún estado.
    Devuelve DataFrame: lat, lon, entidad.
    """
    import geopandas as gpd
    from shapely.geometry import Point

    estados = gpd.read_file(ruta_estados).to_crs(4326)
    minx, miny, maxx, maxy = estados.total_bounds
    lons = np.arange(minx, maxx + granularidad_deg, granularidad_deg)
    lats = np.arange(miny, maxy + granularidad_deg, granularidad_deg)
    grid_lon, grid_lat = np.meshgrid(lons, lats)
    pts = gpd.GeoDataFrame(
        {"lat": grid_lat.ravel(), "lon": grid_lon.ravel()},
        geometry=[Point(x, y) for x, y in zip(grid_lon.ravel(), grid_lat.ravel())],
        crs=4326)
    est = estados[[col_estado, "geometry"]].rename(columns={col_estado: "entidad"})
    celdas = gpd.sjoin(pts, est, how="inner", predicate="within")
    out = pd.DataFrame(celdas[["lat", "lon", "entidad"]]).reset_index(drop=True)
    # Garantizar >=1 nodo por estado: estados pequeños sin centro de celda dentro
    # (p. ej. Ciudad de México con malla gruesa) reciben su punto representativo interior.
    presentes = set(out["entidad"].unique())
    faltantes = est[~est["entidad"].isin(presentes)].copy()
    if len(faltantes):
        rep = faltantes.copy()
        rep["geometry"] = rep.geometry.representative_point()  # garantizado dentro del polígono
        rep["lon"] = rep.geometry.x
        rep["lat"] = rep.geometry.y
        out = pd.concat([out, rep[["lat", "lon", "entidad"]]], ignore_index=True)
        print("[campo_viento] estados sin celda de malla (se añade punto representativo): "
              f"{sorted(faltantes['entidad'].tolist())}")
    return out.reset_index(drop=True)


# --------------------------------------------------------------------------- #
# Footprint por tormenta y covariables por estado-año
# --------------------------------------------------------------------------- #
def footprint_tormenta(track_interp, malla, rmax_col="USA_RMW"):
    """
    Viento máximo (kt) en cada celda a lo largo de la vida de la tormenta (footprint).
    Si existe 'vmax_efectivo' (decaimiento sobre tierra), se usa; si no, WMO/USA_WIND.
    Vectorizado por celdas; itera puntos de traza.
    """
    lat_c = malla["lat"].to_numpy()
    lon_c = malla["lon"].to_numpy()
    vmax_cell = np.zeros(len(malla))
    usar_ef = "vmax_efectivo" in track_interp.columns
    for _, p in track_interp.iterrows():
        vmax_kt = p.get("vmax_efectivo") if usar_ef else np.nan
        if pd.isna(vmax_kt):
            vmax_kt = p.get("WMO_WIND")
        if pd.isna(vmax_kt):
            vmax_kt = p.get("USA_WIND")
        if pd.isna(vmax_kt) or vmax_kt <= 0:
            continue
        pc = p.get("WMO_PRES")
        rmax_km = (p[rmax_col] * NMI_A_KM if rmax_col in track_interp.columns and pd.notna(p.get(rmax_col))
                   else estimar_rmax_km(vmax_kt, p["LAT"]))
        r = _haversine_km(p["LAT"], p["LON"], lat_c, lon_c)
        v = viento_holland_kt(r, rmax_km, vmax_kt, lat_deg=p["LAT"], pc_hpa=pc)
        vmax_cell = np.maximum(vmax_cell, v)
    return vmax_cell


def covariables_campo_viento(df_mex, malla, pesos_exposicion=None, decaimiento_tierra=False):
    """
    df_mex: puntos IBTrACS (interpolados) de tormentas que afectaron México.
    malla: celdas (lat, lon, entidad).
    decaimiento_tierra: si True, aplica Kaplan & DeMaria (1995) por tormenta.
    Devuelve panel (entidad, anio) con covariables de viento LOCAL.
    """
    registros = []
    for (sid, season), g in df_mex.groupby(["SID", "SEASON"]):
        g = g.sort_values("ISO_TIME").reset_index(drop=True)
        if decaimiento_tierra:
            g = decaimiento_kaplan_demaria(g)
        fp = footprint_tormenta(g, malla)
        tmp = malla.copy()
        tmp["v_kt"] = fp
        tmp["SID"] = sid
        tmp["anio"] = season
        registros.append(tmp)
    if not registros:
        return pd.DataFrame()
    todo = pd.concat(registros, ignore_index=True)

    def agg(g):
        out = {
            "viento_local_max_kt": g["v_kt"].max(),
            "viento_local_p95_kt": g["v_kt"].quantile(0.95),
            "n_ciclones_local": g["SID"].nunique(),
        }
        for u in UMBRALES_KT:
            out[f"celdas_ge{u}kt"] = int((g["v_kt"] >= u).sum())
        # PDI local: suma sobre tormentas del (máx local en el estado)^3
        pdi = g.groupby("SID")["v_kt"].max()
        out["pdi_local"] = float((pdi ** 3).sum())
        return pd.Series(out)

    panel = todo.groupby(["entidad", "anio"]).apply(agg).reset_index()
    return panel.sort_values(["entidad", "anio"]).reset_index(drop=True)


# --------------------------------------------------------------------------- #
# Backend CLIMADA opcional
# --------------------------------------------------------------------------- #
def disponible_climada() -> bool:
    try:
        import climada  # noqa: F401
        return True
    except ImportError:
        return False
