"""
procesar_ibtracs.py
===================
Procesa los CRUDOS de IBTrACS hacia dos salidas consolidadas:

  datos/datos_IBTrACS/consolidados/
      ciclones_mexico_puntos.csv          <- puntos de trayectoria que afectaron México
      covariables_ciclon_estado_anio.csv  <- PANEL estado x año para calibrar lambda

Decisiones/supuestos (documentados en fuentes/ibtracs.md):
- Cuencas: Pacífico Este (EP) + Atlántico Norte (NA); se concatenan y se deduplican por
  (SID, ISO_TIME) porque una tormenta puede aparecer en ambos subconjuntos si cruza de cuenca.
- "Afectó directamente a México": un punto de trayectoria se atribuye a un estado si cae
  dentro del polígono estatal o dentro de un BUFFER (default 100 km) que aproxima la huella
  de viento/marejada costa afuera/adentro. Una tormenta "afectó a México" si tiene >=1 punto
  atribuido a algún estado.
- Naturaleza: se conservan sistemas tropicales/subtropicales (NATURE in {'TS','SS'}).
- Viento: WMO_WIND (nudos); si falta, USA_WIND. Presión: WMO_PRES (mb).
- ACE: solo puntos sinópticos (00/06/12/18 UTC) con viento >= 34 kt.
- Categoría Saffir-Simpson derivada del viento (transparente, no se usa el código USA_SSHS).

Dependencias: pandas; geopandas + shapely SOLO para la atribución espacial.
Shapefile de estados: Marco Geoestadístico de INEGI (recomendado) o GADM/Natural Earth.
Se pasa la ruta como parámetro (no se descarga aquí para no acoplar fuentes).
"""

from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

DIR_CRUDOS = Path("datos/datos_IBTrACS/crudos")
DIR_CONS = Path("datos/datos_IBTrACS/consolidados")
ARCHIVOS_CRUDOS = ["ibtracs.EP.list.v04r01.csv", "ibtracs.NA.list.v04r01.csv"]

# Columnas mínimas que usamos (IBTrACS trae ~170).
COLS = ["SID", "SEASON", "BASIN", "NAME", "ISO_TIME", "NATURE",
        "LAT", "LON", "WMO_WIND", "WMO_PRES", "USA_WIND", "USA_PRES",
        "DIST2LAND", "LANDFALL"]


# --------------------------------------------------------------------------- #
# 1. Lectura del crudo (doble fila de encabezado: nombres + unidades)
# --------------------------------------------------------------------------- #
def leer_crudo(path: Path) -> pd.DataFrame:
    """Lee un CSV de IBTrACS saltando la fila de unidades (índice 1)."""
    df = pd.read_csv(path, skiprows=[1], low_memory=False, na_values=[" ", ""])
    cols = [c for c in COLS if c in df.columns]
    df = df[cols].copy()
    for c in ["LAT", "LON", "WMO_WIND", "WMO_PRES", "USA_WIND", "USA_PRES",
              "DIST2LAND", "LANDFALL"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df["ISO_TIME"] = pd.to_datetime(df["ISO_TIME"], errors="coerce")
    return df


def cargar_crudos(dir_crudos: Path = DIR_CRUDOS) -> pd.DataFrame:
    partes = [leer_crudo(dir_crudos / a) for a in ARCHIVOS_CRUDOS if (dir_crudos / a).exists()]
    if not partes:
        raise FileNotFoundError(f"No se encontraron crudos en {dir_crudos}. Corre descarga_ibtracs.py")
    df = pd.concat(partes, ignore_index=True)
    # dedupe: una tormenta que cruza de cuenca aparece en ambos subconjuntos
    df = df.drop_duplicates(subset=["SID", "ISO_TIME"]).reset_index(drop=True)
    return df


# --------------------------------------------------------------------------- #
# 2. Limpieza / variables derivadas
# --------------------------------------------------------------------------- #
def viento_kt(df: pd.DataFrame) -> pd.Series:
    """Viento sostenido en nudos: WMO_WIND y, donde falte, USA_WIND."""
    v = df["WMO_WIND"].copy()
    if "USA_WIND" in df.columns:
        v = v.fillna(df["USA_WIND"])
    return v


def categoria_ss(v_kt: float) -> float:
    """Saffir-Simpson a partir del viento sostenido (nudos). NaN si no hay viento."""
    if v_kt is None or (isinstance(v_kt, float) and np.isnan(v_kt)):
        return np.nan
    if v_kt < 34:   return -1   # depresión tropical
    if v_kt < 64:   return 0    # tormenta tropical
    if v_kt < 83:   return 1
    if v_kt < 96:   return 2
    if v_kt < 113:  return 3
    if v_kt < 137:  return 4
    return 5


def preparar(df: pd.DataFrame, naturalezas=("TS", "SS")) -> pd.DataFrame:
    df = df.copy()
    df["viento_kt"] = viento_kt(df)
    df["cat_ss"] = df["viento_kt"].map(categoria_ss)
    df["es_sinoptico"] = df["ISO_TIME"].dt.hour.isin([0, 6, 12, 18])
    if naturalezas:
        df = df[df["NATURE"].isin(naturalezas)].copy()
    return df


# --------------------------------------------------------------------------- #
# 3. Atribución espacial a estados (geopandas)
# --------------------------------------------------------------------------- #
def atribuir_estados(df: pd.DataFrame, ruta_estados: str,
                     buffer_km: float = 100.0, col_estado: str = "NOMGEO") -> pd.DataFrame:
    """
    Atribuye cada punto a un estado si cae dentro del polígono o de un buffer (km).
    `ruta_estados`: shapefile/geojson de entidades (INEGI Marco Geoestadístico, GADM...).
    `col_estado`: columna con el nombre de la entidad en esa capa.
    Devuelve df con columna 'entidad' (puntos sin estado dentro del buffer se descartan).
    """
    import geopandas as gpd
    from shapely.geometry import Point

    estados = gpd.read_file(ruta_estados).to_crs(6372)  # CRS métrico para México (Lambert ITRF92)
    estados["geometry"] = estados.geometry.buffer(buffer_km * 1000.0)
    estados = estados[[col_estado, "geometry"]].rename(columns={col_estado: "entidad"})

    pts = df.dropna(subset=["LAT", "LON"]).copy()
    gpts = gpd.GeoDataFrame(pts,
                            geometry=[Point(xy) for xy in zip(pts["LON"], pts["LAT"])],
                            crs=4326).to_crs(6372)
    unido = gpd.sjoin(gpts, estados, how="inner", predicate="within")
    return pd.DataFrame(unido.drop(columns="geometry"))


# --------------------------------------------------------------------------- #
# 4. Covariables estado x año (panel para lambda)  -- testable sin GIS
# --------------------------------------------------------------------------- #
def covariables_estado_anio(df_attrib: pd.DataFrame) -> pd.DataFrame:
    """
    Entra: puntos YA atribuidos a 'entidad' (con viento_kt, cat_ss, es_sinoptico,
    LANDFALL, WMO_PRES, SID, SEASON). Sale: panel (entidad, anio) con covariables.
    """
    d = df_attrib.copy()
    d["v"] = d["viento_kt"]
    d["ace_term"] = np.where(d["es_sinoptico"] & (d["v"] >= 34), d["v"] ** 2 / 1e4, 0.0)
    d["pdi_term"] = np.where(d["v"] >= 34, d["v"] ** 3, 0.0)
    d["es_landfall"] = (d["LANDFALL"] == 0)

    g = d.groupby(["entidad", "SEASON"])
    out = g.agg(
        n_ciclones=("SID", "nunique"),
        n_puntos=("SID", "size"),
        viento_max_kt=("v", "max"),
        pres_min_mb=("WMO_PRES", "min"),
        cat_ss_max=("cat_ss", "max"),
        ace=("ace_term", "sum"),
        pdi=("pdi_term", "sum"),
        n_landfalls=("es_landfall", "sum"),
    ).reset_index().rename(columns={"SEASON": "anio"})
    out["horas_exposicion"] = out["n_puntos"] * 6  # puntos sinópticos ~6 h
    return out.sort_values(["entidad", "anio"]).reset_index(drop=True)


# --------------------------------------------------------------------------- #
# 5. Orquestación
# --------------------------------------------------------------------------- #
def main(ruta_estados: str, buffer_km: float = 100.0, dir_cons: Path = DIR_CONS,
         campo_viento: bool = False, paso_temporal_min: int = 60,
         granularidad_malla: float = 0.5, backend: str = "holland",
         col_estado: str = "NOMGEO", anio_inicial: int = None, # type: ignore
         decaimiento_tierra: bool = False):
    dir_cons.mkdir(parents=True, exist_ok=True)
    df = preparar(cargar_crudos())
    if anio_inicial is not None:
        n0 = df["SID"].nunique()
        df = df[df["SEASON"] >= anio_inicial].copy()
        print(f"[procesar_ibtracs] año inicial {anio_inicial}: {df['SID'].nunique()} de {n0} ciclones")
    attrib = atribuir_estados(df, ruta_estados, buffer_km=buffer_km, col_estado=col_estado)
    attrib.to_csv(dir_cons / "ciclones_mexico_puntos.csv", index=False)
    panel = covariables_estado_anio(attrib)
    panel.to_csv(dir_cons / "covariables_ciclon_estado_anio.csv", index=False)
    print(f"[procesar_ibtracs] {attrib['SID'].nunique()} ciclones afectaron México; "
          f"panel buffer: {len(panel)} filas -> {dir_cons}")

    if campo_viento:
        import campo_viento as cv
        sids_mex = set(attrib["SID"].unique())
        df_mex = df[df["SID"].isin(sids_mex)].copy()
        if backend == "climada":
            if not cv.disponible_climada():
                raise RuntimeError("backend 'climada' pedido pero CLIMADA no está instalado. "
                                   "Usa --backend holland (no requiere CLIMADA).")
            raise NotImplementedError(
                "Backend CLIMADA: usar climada.hazard.TCTracks + Centroids + "
                "TropCyclone.from_tracks() con la malla de --granularidad-malla y "
                "track.equal_timestep(paso_temporal_min/60). Ver fuentes/ibtracs.md §9.")
        malla = cv.construir_malla(ruta_estados, granularidad_malla, col_estado=col_estado)
        partes = [cv.interpolar_traza(g, paso_temporal_min).assign(SID=sid, SEASON=g["SEASON"].iloc[0])
                  for sid, g in df_mex.groupby("SID")]
        df_interp = pd.concat(partes, ignore_index=True)
        panel_cv = cv.covariables_campo_viento(df_interp, malla, decaimiento_tierra=decaimiento_tierra)
        sufijo = "_decae" if decaimiento_tierra else ""
        salida_cv = dir_cons / f"covariables_ciclon_estado_anio_campoviento{sufijo}.csv"
        panel_cv.to_csv(salida_cv, index=False)
        print(f"[procesar_ibtracs] campo de viento ({backend}, malla {granularidad_malla}°, "
              f"paso {paso_temporal_min} min, decaimiento_tierra={decaimiento_tierra}): "
              f"{len(panel_cv)} filas -> {salida_cv}")
        return panel, panel_cv
    return panel


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--estados", required=True, help="ruta al shapefile/geojson de entidades (INEGI/GADM)")
    p.add_argument("--buffer-km", type=float, default=100.0)
    p.add_argument("--col-estado", default="NOMGEO", help="columna con el nombre de la entidad en la capa")
    p.add_argument("--anio-inicial", type=int, default=None,
                   help="descarta tormentas anteriores a este año (p. ej. 2005); reduce mucho el costo")
    p.add_argument("--campo-viento", action="store_true", help="además, generar campo de viento (Holland)")
    p.add_argument("--paso-temporal-min", type=int, default=60, help="paso de interpolación de la traza (min)")
    p.add_argument("--granularidad-malla", type=float, default=0.5, help="resolución de la malla en grados")
    p.add_argument("--decaimiento-tierra", action="store_true",
                   help="aplica decaimiento sobre tierra de Kaplan & DeMaria (1995) al campo de viento")
    p.add_argument("--backend", choices=["holland", "climada"], default="holland")
    a = p.parse_args()
    main(a.estados, buffer_km=a.buffer_km, campo_viento=a.campo_viento,
         paso_temporal_min=a.paso_temporal_min, granularidad_malla=a.granularidad_malla,
         backend=a.backend, col_estado=a.col_estado, anio_inicial=a.anio_inicial,
         decaimiento_tierra=a.decaimiento_tierra)
