"""
procesar_cenapred.py
====================
Procesa el CRUDO de CENAPRED (base de impacto socioeconómico a nivel evento) hacia
DOS estructuras consolidadas — porque la calibración de este proyecto y la calibración
de funciones de impacto en CLIMADA requieren estructuras DISTINTAS:

  A) PANEL (este proyecto, λ y severidad):  consolidados/impacto_estado_anio_peril.csv
     Grano: (entidad, anio, peril_canonico) con daños totales, defunciones, etc.
     Solo eventos de UN estado; los multi-estado NO se reparten (principio del
     proyecto: sin certeza no se fabrica estructura espacial) y van a
     consolidados/impacto_multiestado.csv para reconciliación nacional.

  B) EVENTOS (calibración CLIMADA):         consolidados/eventos_cenapred_climada.csv
     Grano: EVENTO, con la lista de estados afectados (separados por '|'), fechas,
     nombre del fenómeno (emparejable con IBTrACS NAME/SID) y daño observado TOTAL.
     Los multi-estado se conservan como UN registro: la calibración compara el daño
     modelado SUMADO sobre esos estados contra el observado (análogo estado-evento
     del esquema país-evento de Eberenz et al. 2021 con EM-DAT).

Limpieza aplicada (decisiones documentadas en fuentes/cenapred.md):
  - números con separador de miles (p. ej. "126,954") -> float
  - entidades canonicalizadas con limpieza_cnsf.clasificar_entidad (mismo estándar CNSF)
  - eventos GEO (sismo/volcán) marcados fuera de alcance climático (se conservan con bandera)
  - subtipos sin mapeo -> '__SIN_MAPEO__' (revisión manual, nunca asignación silenciosa)
  - montos en millones de pesos CORRIENTES (deflactar aparte, igual que CNSF)

El encabezado real del CSV se valida contra un mapa de conceptos; si algo no
empata, el script FALLA RUIDOSAMENTE con un reporte de columnas (no procesa a ciegas).
"""

from __future__ import annotations
import logging
import re
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

# limpieza_cnsf vive en la raíz del repo o junto a src/
sys.path.extend([".", "..", str(Path(__file__).resolve().parent.parent)])
try:
    from limpieza_cnsf import clasificar_entidad, CAT_ESTADO # type: ignore
except ImportError:  # fallback mínimo para no romper si se corre aislado
    def clasificar_entidad(x):  # type: ignore
        return ("estado", str(x).strip())
    CAT_ESTADO = "estado"

DIR_BASE = Path("datos/datos_CENAPRED")
DIR_CRUDOS = DIR_BASE / "crudos"
DIR_CONS = DIR_BASE / "consolidados"
ARCHIVO_CSV = DIR_CRUDOS / "BASE_IMPACTO_SOCIOECONOMICO_DESASTRES_2000_2015.csv"
ARCHIVO_LOG = DIR_BASE / "_log_cenapred.log"

log = logging.getLogger("procesar_cenapred")


def configurar_log():
    DIR_BASE.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler(ARCHIVO_LOG, encoding="utf-8"),
                  logging.StreamHandler(sys.stdout)])


# ----------------------------------------------------------------------------- #
# 1. Mapa de conceptos -> candidatos de encabezado (se valida contra el crudo)
# ----------------------------------------------------------------------------- #
def _norm(s: str) -> str:
    s = str(s).strip().lower()
    s = "".join(c for c in unicodedata.normalize("NFD", s)
                if unicodedata.category(c) != "Mn")
    return " ".join(s.split())


# concepto -> lista de nombres candidatos (normalizados) en el CSV crudo.
# CONFIRMADO contra el encabezado real de la descarga (corrida del usuario):
# ['Fecha de Inicio', 'Fecha de Fin', 'Año', 'Mes', 'Clasificacion del fenomeno',
#  'Tipo de fenomeno', 'Clave del Estado', 'Estado', 'Municipios Afectados',
#  'Descripcion general de los daños', 'Defunciones', 'Poblacion afectada ',
#  'Viviendas dañadas', 'Escuelas', 'Hospitales ',
#  'Area de cultivo dañada / pastizales (h)', 'Caminos afectados           (Km)',
#  'Total de daños                    (Millones de pesos)',
#  'Total daños (Millones de dolares)', 'Tipo de declaratoria',
#  'Sustancia involucrada', 'Fuente', 'Observaciones', 'Documentado']
# (la normalización colapsa espacios internos/finales y quita acentos)
# OJO: 'Clasificacion del fenomeno' es el NIVEL 1 (Geológico/Hidrometeorológico/...)
#      y 'Tipo de fenomeno' es el SUBTIPO (Ciclón tropical, Lluvias, Sequía, ...).
CONCEPTOS = {
    "fecha_inicio":       ["fecha de inicio", "fecha", "fecha del evento"],
    "fecha_fin":          ["fecha de fin", "fecha fin"],
    "anio":               ["ano", "año", "anio", "year"],
    "mes":                ["mes"],
    "tipo":               ["clasificacion del fenomeno", "clasificacion"],
    "subtipo":            ["tipo de fenomeno", "subtipo", "subtipo de fenomeno"],
    "clave_estado":       ["clave del estado", "clave", "cve ent", "cve_ent"],
    "estado":             ["estado", "entidad", "entidad federativa", "estados"],
    "municipio":          ["municipios afectados", "municipio", "municipios"],
    "descripcion":        ["descripcion general de los danos", "descripcion",
                           "descripcion del evento"],
    "defunciones":        ["defunciones", "muertos", "decesos"],
    "pob_afectada":       ["poblacion afectada", "personas afectadas", "afectados"],
    "viviendas":          ["viviendas danadas", "viviendas"],
    "escuelas":           ["escuelas", "escuelas danadas"],
    "hospitales":         ["hospitales", "unidades medicas"],
    "ha_cultivo":         ["area de cultivo danada / pastizales (h)",
                           "area de cultivo", "hectareas", "superficie danada"],
    "km_carretera":       ["caminos afectados (km)", "carreteras", "caminos"],
    "danio_mdp":          ["total de danos (millones de pesos)", "danos totales",
                           "monto de danos", "total de danos", "costo total"],
    "danio_mdd":          ["total danos (millones de dolares)",
                           "danos millones de dolares", "millones de dolares"],
    "tipo_declaratoria":  ["tipo de declaratoria", "declaratoria emitida"],
    "sustancia":          ["sustancia involucrada"],
    "fuente":             ["fuente", "fuentes"],
    "observaciones":      ["observaciones"],
    "documentado":        ["documentado"],
}
REQUERIDOS = ["anio", "tipo", "subtipo", "estado", "danio_mdp"]


def mapear_columnas(df: pd.DataFrame) -> dict:
    """Empata conceptos con encabezados reales. Falla ruidosamente si falta un requerido."""
    nmap = {_norm(c): c for c in df.columns}
    res, faltan = {}, []
    for concepto, candidatos in CONCEPTOS.items():
        col = next((nmap[c] for c in candidatos if c in nmap), None)
        if col is None and concepto in REQUERIDOS:
            faltan.append(concepto)
        if col is not None:
            res[concepto] = col
    if faltan:
        log.error("REPORTE DE COLUMNAS — encabezados del crudo: %s", list(df.columns))
        raise RuntimeError(
            f"Conceptos requeridos sin columna en el crudo: {faltan}. "
            "Actualizar CONCEPTOS en procesar_cenapred.py con el encabezado real "
            "(ver reporte en el log). NO se procesa a ciegas.")
    log.info("mapa de columnas: %s", res)
    return res


# ----------------------------------------------------------------------------- #
# 2. Catálogo de perils CENAPRED -> canónico (CÓDIGOS REALES del crudo, del log
#    de la corrida del usuario, + palabras completas por robustez)
# ----------------------------------------------------------------------------- #
# subtipo (normalizado) -> (peril_canonico, en_alcance_climatico)
PERILS_CENAPRED = {
    # --- HIDRO (clima = sí) ---
    "ct": ("Ciclón tropical", "si"), "ciclon tropical": ("Ciclón tropical", "si"),
    "huracan": ("Ciclón tropical", "si"),
    "lluv": ("Daños por lluvia", "si"), "lluvias": ("Daños por lluvia", "si"),
    "inun": ("Inundación", "si"), "inund": ("Inundación", "si"),
    "inundacion": ("Inundación", "si"),
    "seq": ("Sequía", "si"), "sequia": ("Sequía", "si"),
    "helada": ("Helada", "si"), "heladas": ("Helada", "si"),
    "bt": ("Baja temperatura", "si"),       # bajas temperaturas / frente frío
    "gran": ("Granizo", "si"), "granizo": ("Granizo", "si"), "granizada": ("Granizo", "si"),
    "nev": ("Nevada", "si"), "nevada": ("Nevada", "si"), "nevadas": ("Nevada", "si"),
    "torn": ("Vientos/Tornado", "si"), "tornado": ("Vientos/Tornado", "si"),
    "fv": ("Vientos/Tornado", "si"),        # fuertes vientos
    "vientos": ("Vientos/Tornado", "si"), "viento": ("Vientos/Tornado", "si"),
    "ts": ("Tormenta severa", "si"),        # [confirmar etiqueta exacta vs descripciones]
    "te": ("Tormenta eléctrica", "si"),     # [confirmar etiqueta exacta vs descripciones]
    "mt": ("Marejada", "si"),               # marea de tormenta [confirmar]
    "mf": ("Marejada", "si"),               # mar de fondo
    "marejada": ("Marejada", "si"),
    "ola de calor": ("Onda cálida", "si"), "onda calida": ("Onda cálida", "si"),
    "oc": ("Onda cálida", "si"),
    # --- GEO: deslizamiento es clima=sí (detonado por lluvia); resto no ---
    "desliz": ("Deslizamiento", "si"), "deslizamiento": ("Deslizamiento", "si"),
    "sismo": ("Sismo", "no"), "sis": ("Sismo", "no"),
    "volc": ("Actividad volcánica", "no"), "volcan": ("Actividad volcánica", "no"),
    "tsu": ("Tsunami", "no"), "tsunami": ("Tsunami", "no"), "maremoto": ("Tsunami", "no"),
    # --- QUIM: incendio forestal es clima=sí; resto no ---
    "if": ("Incendio forestal", "si"), "incf": ("Incendio forestal", "si"),
    "incendio forestal": ("Incendio forestal", "si"),
    "iu": ("Incendio urbano", "no"),
    "fug": ("Fuga química", "no"),
    "expl": ("Explosión", "no"),
    "derme": ("Derrame químico", "no"),
    "intox": ("Intoxicación", "no"),
    "flam": ("Material inflamable", "no"),
    # --- SOCIO ---
    "atrans": ("Accidente de transporte", "no"),
    "atrab": ("Accidente de trabajo", "no"),
    "derrs": ("Derrumbe (estructural)", "no"),
    # --- SAN ---
    "epi": ("Epidemia", "no"), "plag": ("Plaga", "no"), "tox": ("Toxicidad", "no"),
}

# Clasificaciones (nivel 1) cuyo contenido NO es climático: si el subtipo no está
# en el dict, se mapea automáticamente a fuera-de-alcance con etiqueta genérica
# (silencioso a nivel debug) — el AVISO ruidoso se reserva para HIDRO/GEO
# desconocidos, que sí exigen revisión manual por ser potencialmente climáticos.
CLASIF_NO_CLIMA = {"quim": "Químico-tecnológico", "socio": "Socio-organizativo",
                   "san": "Sanitario-ecológico", "sani": "Sanitario-ecológico"}


def mapear_peril(subtipo, tipo) -> tuple[str, str]:
    s = _norm(subtipo)
    if s in PERILS_CENAPRED:
        return PERILS_CENAPRED[s]
    t = _norm(tipo)
    if t.startswith("geo"):
        return (str(subtipo).strip() or "GEO", "no")
    for pref, etiqueta in CLASIF_NO_CLIMA.items():
        if t.startswith(pref):
            log.debug("subtipo %r de clasificación no-climática %r -> fuera de alcance",
                      subtipo, tipo)
            return (f"{etiqueta} ({str(subtipo).strip()})", "no")
    log.warning("subtipo sin mapeo: %r (tipo=%r) -> __SIN_MAPEO__ (revisión manual; "
                "potencialmente climático)", subtipo, tipo)
    return ("__SIN_MAPEO__", "revisar")


# ----------------------------------------------------------------------------- #
# 3. Limpieza de valores
# ----------------------------------------------------------------------------- #
def a_numero(x):
    """'126,954' -> 126954.0 ; ''/None/'NA' -> NaN."""
    if x is None:
        return np.nan
    s = str(x).strip().replace(",", "")
    if s in ("", "NA", "N/A", "ND", "-", "nan"):
        return np.nan
    try:
        return float(s)
    except ValueError:
        return np.nan


RE_SEPARADOR_ENTIDADES = re.compile(r",|\b[yY]\b|\b[eE]\b(?=\s+[A-ZÁÉÍÓÚ])")


def separar_estados(celda) -> list[str]:
    """'Chiapas, Michoacan y Nuevo Leon' / 'Morelos y Sonora' -> canónicos.
    Separa por coma Y por conjunción 'y'/'e' (visto en corrida real: 'Morelos y
    Sonora', 'Tabasco y Veracruz'). Lo no-estado se omite del panel con aviso
    ('Varios estados'/'Todo el pais' ya clasifican como no_localizado)."""
    if celda is None or str(celda).strip() == "":
        return []
    canonicos = []
    for parte in RE_SEPARADOR_ENTIDADES.split(str(celda)):
        if parte is None or not parte.strip():
            continue
        cat, canon = clasificar_entidad(parte)
        if cat == CAT_ESTADO:
            canonicos.append(canon)
        elif cat == "desconocido":
            log.warning("entidad no-estado en CENAPRED: %r (cat=%s) — se omite del panel",
                        parte.strip(), cat)
    # dedup conservando orden
    vistos, res = set(), []
    for c in canonicos:
        if c not in vistos:
            vistos.add(c)
            res.append(c)
    return res


SENTINELAS_FECHA = {"sd", "s/d", "nd", "n/d", "na", "n/a", "-", "", "nan"}


def limpiar_fecha(serie: pd.Series) -> pd.Series:
    """Convierte sentinelas ('SD' = sin dato, visto en el crudo real) a NA antes de
    parsear, para que el parseo no truene ni meta ruido; lo demás d-m-aa dayfirst."""
    s = serie.astype(str).str.strip()
    s = s.mask(s.str.lower().isin(SENTINELAS_FECHA))
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)  # formatos mixtos -> dateutil
        return pd.to_datetime(s, dayfirst=True, errors="coerce")


# El CSV NO trae columna de nombre del evento: para ciclones/tormentas el nombre
# viene dentro de 'Observaciones' (p. ej. "Ciclon Carlotta. El Huracan decrecio
# sus vientos hasta el 24-Jun"). Se extrae la PRIMERA mención tipo+Nombre propio.
RE_NOMBRE_CICLON = re.compile(
    r"\b([Cc]icl[oó]n|[Hh]urac[aá]n|[Tt]ormenta\s+[Tt]ropical|[Dd]epresi[oó]n\s+[Tt]ropical)"
    r"\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:-[A-Z]\w*)?)")


def extraer_nombre_evento(observaciones) -> str:
    """Devuelve p. ej. 'Ciclón Carlotta' desde Observaciones, o '' si no hay nombre.
    El patrón exige Nombre propio capitalizado, así evita falsos positivos como
    'el huracan decrecio' o el genérico 'ciclón tropical'."""
    if observaciones is None:
        return ""
    m = RE_NOMBRE_CICLON.search(str(observaciones))
    if not m:
        return ""
    tipo = _norm(m.group(1))
    tipo = {"ciclon": "Ciclón", "huracan": "Huracán",
            "tormenta tropical": "Tormenta tropical",
            "depresion tropical": "Depresión tropical"}.get(tipo, m.group(1))
    return f"{tipo} {m.group(2)}"


def leer_crudo(path_csv: Path) -> pd.DataFrame:
    """Lee el CSV intentando utf-8 estricto y cayendo a latin1 CON AVISO (el crudo
    real es latin1; un fallback silencioso con errors='replace' produciría mojibake
    mudo en acentos/ñ — error confirmado en la corrida del usuario)."""
    try:
        df = pd.read_csv(path_csv, encoding="utf-8", low_memory=False)
        log.info("crudo leído como utf-8")
        return df
    except UnicodeDecodeError:
        df = pd.read_csv(path_csv, encoding="latin1", low_memory=False)
        log.info("crudo leído como latin1 (utf-8 falló — codificación del archivo real)")
        return df


# ----------------------------------------------------------------------------- #
# 4. Procesamiento -> dos estructuras
# ----------------------------------------------------------------------------- #
def procesar(path_csv: Path = ARCHIVO_CSV, dir_cons: Path = DIR_CONS):
    dir_cons.mkdir(parents=True, exist_ok=True)
    df = leer_crudo(path_csv)
    log.info("crudo leído: %d filas, %d columnas", len(df), len(df.columns))
    cols = mapear_columnas(df)

    # ---- limpieza por evento ----
    ev = pd.DataFrame()
    ev["anio"] = pd.to_numeric(df[cols["anio"]], errors="coerce")
    ev["mes"] = pd.to_numeric(df[cols["mes"]], errors="coerce") if "mes" in cols else np.nan
    ev["tipo"] = df[cols["tipo"]].astype(str).str.strip()          # nivel 1 (clasificación)
    ev["subtipo"] = df[cols["subtipo"]].astype(str).str.strip()    # fenómeno
    perils = [mapear_peril(s, t) for s, t in zip(ev["subtipo"], ev["tipo"])]
    ev["peril_canonico"] = [p for p, _ in perils]
    ev["en_alcance_climatico"] = [a for _, a in perils]
    ev["estados_lista"] = df[cols["estado"]].map(separar_estados)
    ev["n_estados"] = ev["estados_lista"].map(len)
    ev["estados"] = ev["estados_lista"].map(lambda xs: "|".join(xs)) # type: ignore

    # fechas de inicio/fin (d-m-aa; 'SD' = sin dato -> NA) + duración; texto crudo conservado
    for c in ["fecha_inicio", "fecha_fin"]:
        if c in cols:
            ev[f"{c}_raw"] = df[cols[c]].astype(str).str.strip()
            ev[c] = limpiar_fecha(df[cols[c]])
        else:
            ev[f"{c}_raw"], ev[c] = "", pd.NaT
    ev["duracion_dias"] = (ev["fecha_fin"] - ev["fecha_inicio"]).dt.days
    n_fechas_malas = int(ev["fecha_inicio"].isna().sum())
    if n_fechas_malas:
        log.info("%d filas sin fecha de inicio parseable ('SD' o rango textual; queda "
                 "el texto crudo en fecha_inicio_raw)", n_fechas_malas)

    for concepto in ["defunciones", "pob_afectada", "viviendas", "escuelas",
                     "hospitales", "ha_cultivo", "km_carretera",
                     "danio_mdp", "danio_mdd"]:
        ev[concepto] = df[cols[concepto]].map(a_numero) if concepto in cols else np.nan
    for concepto in ["tipo_declaratoria", "fuente", "municipio", "descripcion",
                     "observaciones", "sustancia", "documentado"]:
        ev[concepto] = (df[cols[concepto]].astype(str).str.strip()
                        if concepto in cols else "")

    # nombre del evento: NO hay columna -> se busca en Observaciones y, si no,
    # en la Descripción (inconsistencia confirmada: no todos los CT lo traen).
    nom_obs = ev["observaciones"].map(extraer_nombre_evento)
    nom_desc = ev["descripcion"].map(extraer_nombre_evento)
    ev["nombre_evento"] = nom_obs.where(nom_obs != "", nom_desc)
    ev["nombre_origen"] = np.select(
        [nom_obs != "", nom_desc != ""], ["observaciones", "descripcion"], default="")
    es_ct = ev["peril_canonico"] == "Ciclón tropical"
    ct_sin_nombre = int((es_ct & (ev["nombre_evento"] == "")).sum())
    log.info("nombres de ciclón extraídos: %d (obs: %d, desc: %d). CT SIN nombre: %d "
             "-> empalmar con IBTrACS por fechas+estados",
             int((ev["nombre_evento"] != "").sum()), int((nom_obs != "").sum()),
             int(((nom_obs == "") & (nom_desc != "")).sum()), ct_sin_nombre)

    ev["evento_id"] = [f"CEN-{a}-{i:05d}" for i, a in
                       zip(range(1, len(ev) + 1), ev["anio"].fillna(0).astype(int))]

    sin_mapeo = (ev["peril_canonico"] == "__SIN_MAPEO__").sum()
    if sin_mapeo:
        log.warning("%d eventos con subtipo SIN MAPEO (revisar PERILS_CENAPRED); "
                    "valores: %s", sin_mapeo,
                    sorted(ev.loc[ev["peril_canonico"] == "__SIN_MAPEO__", "subtipo"].unique())[:15])
    sin_estado = (ev["n_estados"] == 0).sum()
    if sin_estado:
        log.warning("%d eventos sin estado canónico (quedan fuera del panel, "
                    "permanecen en eventos B)", sin_estado)

    # ---- ESTRUCTURA B: eventos (calibración CLIMADA) — TODOS los eventos ----
    cols_b = ["evento_id", "nombre_evento", "nombre_origen", "anio", "mes",
              "fecha_inicio", "fecha_fin", "fecha_inicio_raw", "fecha_fin_raw",
              "duracion_dias", "tipo", "subtipo", "peril_canonico",
              "en_alcance_climatico", "estados", "n_estados", "municipio",
              "danio_mdp", "danio_mdd", "defunciones", "pob_afectada",
              "tipo_declaratoria", "sustancia", "fuente", "descripcion",
              "observaciones", "documentado"]
    eventos_b = ev[cols_b].copy()
    salida_b = dir_cons / "eventos_cenapred_climada.csv"
    eventos_b.to_csv(salida_b, index=False)
    log.info("[B] eventos para calibración CLIMADA: %d filas -> %s",
             len(eventos_b), salida_b)

    # ---- ESTRUCTURA A: panel estado×año×peril — SOLO eventos de un estado ----
    un_estado = ev[ev["n_estados"] == 1].copy()
    un_estado["entidad"] = un_estado["estados_lista"].map(lambda xs: xs[0]) # type: ignore
    panel = (un_estado.groupby(["entidad", "anio", "peril_canonico",
                                "en_alcance_climatico"], dropna=False)
             .agg(n_eventos=("evento_id", "size"),
                  danio_mdp=("danio_mdp", "sum"),
                  danio_mdd=("danio_mdd", "sum"),
                  defunciones=("defunciones", "sum"),
                  pob_afectada=("pob_afectada", "sum"),
                  viviendas=("viviendas", "sum"))
             .reset_index()
             .sort_values(["entidad", "anio", "peril_canonico"]))
    salida_a = dir_cons / "impacto_estado_anio_peril.csv"
    panel.to_csv(salida_a, index=False)
    log.info("[A] panel estado×año×peril: %d filas -> %s", len(panel), salida_a)

    # ---- multi-estado: NO se reparte; reconciliación nacional ----
    multi = ev[ev["n_estados"] >= 2].copy()
    salida_m = dir_cons / "impacto_multiestado.csv"
    multi[cols_b].to_csv(salida_m, index=False)
    pct = 100 * multi["danio_mdp"].sum() / max(ev["danio_mdp"].sum(), 1e-9)
    log.info("[A'] eventos multi-estado (no repartidos): %d filas, %.1f%% del daño total "
             "-> %s", len(multi), pct, salida_m)

    # ---- CATÁLOGO de fenómenos climáticos por año/mes/estado (ocurrencia) ----
    # Una fila por (evento × estado afectado), SOLO clima. Es un catálogo de
    # OCURRENCIA del peligro: explotar por estado es legítimo para presencia;
    # el daño se conserva como TOTAL DEL EVENTO con bandera multi_estado
    # (no se reparte — principio del proyecto). Municipios como texto crudo
    # (mayoría 'Varios municipios'; pocos registros traen nombres específicos).
    clima = ev[ev["en_alcance_climatico"] == "si"].copy()
    filas_cat = []
    for _, e in clima.iterrows():
        for entidad in e["estados_lista"]:
            filas_cat.append({
                "evento_id": e["evento_id"], "anio": e["anio"], "mes": e["mes"],
                "fecha_inicio": e["fecha_inicio"], "fecha_fin": e["fecha_fin"],
                "duracion_dias": e["duracion_dias"],
                "peril_canonico": e["peril_canonico"], "subtipo": e["subtipo"],
                "nombre_evento": e["nombre_evento"], "entidad": entidad,
                "municipios": e["municipio"],
                "n_estados_evento": e["n_estados"],
                "multi_estado": e["n_estados"] >= 2,
                "danio_mdp_evento_total": e["danio_mdp"],
                "defunciones_evento_total": e["defunciones"],
                "fuente": e["fuente"],
            })
    catalogo = (pd.DataFrame(filas_cat)
                .sort_values(["anio", "mes", "entidad", "peril_canonico"])
                .reset_index(drop=True))
    salida_cat = dir_cons / "catalogo_fenomenos_climaticos.csv"
    catalogo.to_csv(salida_cat, index=False)
    log.info("[CAT] catálogo de fenómenos climáticos (evento×estado): %d filas, "
             "%d eventos, %d estados -> %s", len(catalogo),
             catalogo["evento_id"].nunique(), catalogo["entidad"].nunique(), salida_cat)

    return panel, eventos_b, multi, catalogo


if __name__ == "__main__":
    configurar_log()
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--crudo", default=str(ARCHIVO_CSV))
    a = p.parse_args()
    procesar(Path(a.crudo))
