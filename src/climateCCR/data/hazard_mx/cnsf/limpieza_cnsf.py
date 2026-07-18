"""
limpieza_cnsf.py
=================
Normalización y limpieza de VALORES para la consolidación CNSF.
Codifica las decisiones documentadas en `referencias_riesgo_catastrofico.md` (>= v0.6).

Se aplica DESPUÉS de la consolidación de cada ramo (sobre el DataFrame ya unido por años),
antes de construir el panel de calibración. Es el análogo, a nivel de VALORES, del dict
`CORRECCIONES_CANONICAS` que ya corrige encabezados en el consolidador.

Principios (ver documento):
- Entidades: remapear typos obvios; EXCLUIR extranjero y no localizado para calibrar; nunca
  repartir ni asignar sin certeza (sesga la atribución espacial).
- Pérdida: usar MONTO PAGADO (no MONTO DEL SINIESTRO, contable y con negativos).
- Frecuencia: NÚMERO DE SINIESTROS.
- Vacío = NA, no 0 (columnas introducidas tarde, p. ej. reaseguro/devengada acumulada >= 2021).
- Texto: canonicalizar (casefold + sin acentos + sinónimos) antes de agrupar.
"""

from __future__ import annotations

import unicodedata

try:
    import numpy as np
    import pandas as pd
except ImportError:  # las funciones núcleo (clasificar_entidad) no requieren pandas
    pd = None
    np = None


# --------------------------------------------------------------------------- #
# 0. Utilidad base de normalización de texto
# --------------------------------------------------------------------------- #
def norm_txt(s) -> str:
    """minúsculas, sin acentos, espacios colapsados. Para COMPARAR, no para mostrar."""
    if s is None:
        return ""
    s = str(s).strip().lower()
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    return " ".join(s.split())


# --------------------------------------------------------------------------- #
# 1. ENTIDADES
# --------------------------------------------------------------------------- #
# 32 entidades federativas en su forma canónica (para mostrar).
ENTIDADES_32 = [
    "Aguascalientes",
    "Baja California",
    "Baja California Sur",
    "Campeche",
    "Chiapas",
    "Chihuahua",
    "Ciudad de México",
    "Coahuila",
    "Colima",
    "Durango",
    "Estado de México",
    "Guanajuato",
    "Guerrero",
    "Hidalgo",
    "Jalisco",
    "Michoacán",
    "Morelos",
    "Nayarit",
    "Nuevo León",
    "Oaxaca",
    "Puebla",
    "Querétaro",
    "Quintana Roo",
    "San Luis Potosí",
    "Sinaloa",
    "Sonora",
    "Tabasco",
    "Tamaulipas",
    "Tlaxcala",
    "Veracruz",
    "Yucatán",
    "Zacatecas",
]
_ENTIDADES_32_NORM = {norm_txt(e): e for e in ENTIDADES_32}

# Variantes/typos OBVIOS -> canónico. Se aplican automáticamente.
# (claves en forma normalizada con norm_txt)
CORRECCIONES_ENTIDAD = {
    "quitana roo": "Quintana Roo",  # typo confirmado
    "chichuahua": "Chihuahua",  # typo confirmado (CENAPRED)
    "distrito federal": "Ciudad de México",  # DF -> CDMX
    "mexico": "Estado de México",  # 'México' (estado) -> Estado de México
    "edo de mexico": "Estado de México",
    "edo. de mexico": "Estado de México",
    # formas oficiales largas (por si aparecen)
    "coahuila de zaragoza": "Coahuila",
    "michoacan de ocampo": "Michoacán",
    "veracruz de ignacio de la llave": "Veracruz",
    "queretaro de arteaga": "Querétaro",
}

# Fuera del dominio espacial mexicano -> EXCLUIR (no repartir).
ENTIDADES_EXTRANJERAS = {
    "extranjero",
    "no aplica (exportacion)",
}

# Mexicana sin localizar -> EXCLUIR de calibración, conservar como "No Disponible".
# (NU se colapsa aquí por decisión documentada: sin certeza del estado.)
ENTIDADES_NO_LOCALIZADAS = {
    "nu",
    "no disponible",
    "varios estados",  # CENAPRED: evento nacional/difuso, sin asignar (no repartir)
    "todo el pais",
    "nacional",
    "no localizado",
    "no especificado",
    "sin entidad",
    "",
}

# Categorías
CAT_ESTADO = "estado"
CAT_EXTRANJERO = "extranjero"
CAT_NO_LOCALIZADO = "no_localizado"
CAT_DESCONOCIDO = "desconocido"  # no clasificado: requiere revisión MANUAL (no se asigna)


def clasificar_entidad(raw) -> tuple[str, str]:
    """
    Clasifica una etiqueta de ENTIDAD.
    Devuelve (categoria, valor_canonico).
      - (CAT_ESTADO, '<estado>')         -> usar en calibración
      - (CAT_EXTRANJERO, 'Extranjero')   -> excluir (fuera de México)
      - (CAT_NO_LOCALIZADO, 'No Disponible') -> excluir (sin certeza)
      - (CAT_DESCONOCIDO, '<raw>')       -> NO asignar; revisar a mano
    """
    n = norm_txt(raw)
    if n in ENTIDADES_EXTRANJERAS:
        return CAT_EXTRANJERO, "Extranjero"
    if n in ENTIDADES_NO_LOCALIZADAS:
        return CAT_NO_LOCALIZADO, "No Disponible"
    if n in CORRECCIONES_ENTIDAD:
        return CAT_ESTADO, CORRECCIONES_ENTIDAD[n]
    if n in _ENTIDADES_32_NORM:
        return CAT_ESTADO, _ENTIDADES_32_NORM[n]
    # No reconocida: NO se asigna a ningún estado (evita sesgo). Se marca para revisión.
    return CAT_DESCONOCIDO, str(raw).strip()


# --------------------------------------------------------------------------- #
# 2. Constantes de variables de pérdida / frecuencia
# --------------------------------------------------------------------------- #
# Nombres canónicos por ramo pueden variar; estos son los recomendados.
COL_PERDIDA = "MONTO PAGADO"  # usar como pérdida (limpio, sin negativos)
COL_FRECUENCIA = "NÚMERO DE SINIESTROS"
# NO usar como pérdida: es movimiento contable de reservas (puede ser negativo).
COL_PERDIDA_PROHIBIDA = "MONTO DEL SINIESTRO"

# Columnas introducidas tarde -> antes de su año de inicio deben ser NA (no 0).
# (hidro; ajustar si otros ramos lo replican)
COLUMNAS_TARDIAS = {
    "PRIMA DEVENGADA ACUMULADA": 2021,
    "MONTO DE REASEGURO": 2021,
    "MONTO RECUPERADO DE TERCEROS": 2021,
}


# --------------------------------------------------------------------------- #
# 3. Canonicalización de campos de texto específicos
# --------------------------------------------------------------------------- #
def normalizar_primera_linea_de_mar(raw) -> str:
    """Colapsa las ~9 variantes a 3 categorías: '<500 m' / '>500 m' / 'No disponible'."""
    n = norm_txt(raw)
    if n.startswith("menos de 500"):
        return "<500 m"
    if n.startswith("mas de 500") or n.startswith("más de 500"):
        return ">500 m"
    return "No disponible"


def cargar_mapa_perils(path_csv: str) -> dict:
    """
    Carga `mapa_perils_seguros_a_canonico.csv` ->
    dict[(ramo, norm(valor_crudo))] = (peril_canonico, en_alcance_climatico).
    """
    import csv

    mapa = {}
    with open(path_csv, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            clave = (row["ramo"], norm_txt(row["valor_crudo"]))
            mapa[clave] = (row["peril_canonico"], row["en_alcance_climatico"])
    return mapa


def mapear_peril(ramo: str, valor_crudo, mapa: dict, solo_clima: bool = True):
    """
    Devuelve el peril canónico para un valor crudo de causa/tipo de evento.
    Si solo_clima=True, devuelve None cuando en_alcance_climatico == 'no'.
    Devuelve '__SIN_MAPEO__' si la combinación (ramo, valor) no está en el mapa
    (señal de deriva/categoría nueva que hay que revisar).
    """
    res = mapa.get((ramo, norm_txt(valor_crudo)))
    if res is None:
        return "__SIN_MAPEO__"
    peril, alcance = res
    if solo_clima and norm_txt(alcance) == "no":
        return None
    return peril


# --------------------------------------------------------------------------- #
# 4. Funciones a nivel DataFrame (requieren pandas)
# --------------------------------------------------------------------------- #
def anexar_clasificacion_entidad(df, col_entidad="ENTIDAD"):
    """Añade columnas 'entidad_cat' y 'entidad_canon' sin borrar nada."""
    cats = df[col_entidad].map(lambda x: clasificar_entidad(x))
    df = df.copy()
    df["entidad_cat"] = cats.map(lambda t: t[0])
    df["entidad_canon"] = cats.map(lambda t: t[1])
    return df


def reporte_entidades(df, col_entidad="ENTIDAD", col_anio="anio"):
    """Auditoría: conteo de filas por categoría y año. Útil para verificar antes de filtrar."""
    d = anexar_clasificacion_entidad(df, col_entidad)
    return d.groupby([col_anio, "entidad_cat"]).size().unstack(fill_value=0).sort_index()


def filtrar_para_calibracion(df, col_entidad="ENTIDAD"):
    """
    Devuelve (df_estados, df_no_asignado):
      - df_estados: SOLO entidades-estado (con 'entidad_canon' normalizada). Para calibrar.
      - df_no_asignado: extranjero + no localizado + desconocido. Para reconciliación
        nacional y trazabilidad (NO entra al panel por estado).
    Los 'desconocido' se reportan por separado: revisarlos antes de descartarlos.
    """
    d = anexar_clasificacion_entidad(df, col_entidad)
    df_estados = d[d["entidad_cat"] == CAT_ESTADO].copy()
    df_no_asignado = d[d["entidad_cat"] != CAT_ESTADO].copy()
    desconocidos = df_no_asignado[df_no_asignado["entidad_cat"] == CAT_DESCONOCIDO]
    if len(desconocidos):
        etiquetas = sorted(desconocidos[col_entidad].astype(str).unique())
        print(
            f"[limpieza_cnsf] AVISO: {len(desconocidos)} filas con ENTIDAD "
            f"no clasificada (revisar, no se asignan): {etiquetas}"
        )
    return df_estados, df_no_asignado


def vacio_a_na(df, columnas=None, columnas_tardias=COLUMNAS_TARDIAS, col_anio="anio"):
    """
    Convierte cadenas vacías/espacios a NaN en las columnas indicadas, y fuerza NaN
    (no 0) en columnas introducidas tarde para los años previos a su año de inicio.
    """
    df = df.copy()
    cols = columnas if columnas is not None else df.columns
    for c in cols:
        if c in df.columns and df[c].dtype == object:
            df[c] = df[c].replace(r"^\s*$", np.nan, regex=True)
    for c, anio_inicio in columnas_tardias.items():
        if c in df.columns and col_anio in df.columns:
            df.loc[df[col_anio] < anio_inicio, c] = np.nan
    return df


def validar_variable_perdida(df):
    """Advierte si se intenta usar MONTO DEL SINIESTRO (negativos = movimiento de reservas)."""
    if COL_PERDIDA_PROHIBIDA in df.columns:
        neg = (pd.to_numeric(df[COL_PERDIDA_PROHIBIDA], errors="coerce") < 0).sum()
        if neg:
            print(
                f"[limpieza_cnsf] NOTA: '{COL_PERDIDA_PROHIBIDA}' tiene {neg} valores "
                f"negativos (movimiento contable de reservas). Usar '{COL_PERDIDA}' como pérdida."
            )
    return df


# --------------------------------------------------------------------------- #
# 5. Pipeline de conveniencia
# --------------------------------------------------------------------------- #
def limpiar_ramo(
    df,
    col_entidad="ENTIDAD",
    col_anio="anio",
    columnas_monetarias=None,
    path_mapa_perils=None,
    col_causa=None,
    ramo=None,
    solo_clima=True,
):
    """
    Pipeline mínimo: vacío->NA, clasificación de entidad, (opcional) mapeo de peril.
    Devuelve (df_estados, df_no_asignado). No normaliza MONEDA (requiere tipo de cambio Banxico;
    ver nota en el documento) — hacerlo aparte antes de sumar montos.
    """
    df = vacio_a_na(df, columnas=columnas_monetarias, col_anio=col_anio)
    df = validar_variable_perdida(df)
    if path_mapa_perils and col_causa and ramo:
        mapa = cargar_mapa_perils(path_mapa_perils)
        df = df.copy()
        df["peril_canonico"] = df[col_causa].map(
            lambda v: mapear_peril(ramo, v, mapa, solo_clima=solo_clima)
        )
    return filtrar_para_calibracion(df, col_entidad=col_entidad)


# --------------------------------------------------------------------------- #
# 6. Correcciones de magnitud — ramo agrícola (documento §4, recuadro agrícola)
# --------------------------------------------------------------------------- #
# Dos errores de magnitud documentados en el consolidado agrícola (evidencia en el
# documento y en impactcal-mx `scraps/cnsf_agricola_dq/`):
#   (a) superficies ×1000 (clúster 2015, ecos 2010-2024): superficie asegurada/siniestrada
#       imposible (> territorio estatal) con montos intactos; ÷1000 devuelve el valor
#       implícito MXN/ha al rango del propio historial de la celda.
#   (b) SUMA ASEGURADA ≈×FIX (sistémico 2022-2024): superficies y prima intactas, suma
#       inflada por ~el tipo de cambio del año (doble conversión MXN→"USD"→MXN en la
#       entrega SESA); la tasa de prima colapsa a <0.5% vs 2.7-7.5% de mediana histórica.
# Las correcciones son NO destructivas: se aplican sobre una copia, cada renglón tocado
# queda marcado (`dq_correccion`, `dq_valor_original`) y se devuelve una auditoría.

COL_SUP_ASEGURADA = "SUPERFICIE ASEGURADA\n(HECTÁREAS)"
COL_SUP_SINIESTRADA = "SUPERFICIE SINIESTRADA\n(HECTÁREAS)"
COL_SUMA_ASEGURADA = "SUMA ASEGURADA"
COL_PRIMA_EMITIDA = "PRIMA EMITIDA"

# FIX promedio del periodo (Banxico, Informe Anual — compilación 2024, cuadro "Tipos de
# cambio representativos"): años con la firma "suma inflada" confirmada. Aproximación
# documentada: el factor real por renglón depende de la fecha de emisión intra-año.
FIX_PROMEDIO_ANUAL = {2022: 20.1274, 2023: 17.7587, 2024: 18.3049}

BANDA_VALOR_MXN_HA = (1_000, 200_000)  # valor asegurado implícito plausible (MXN/ha)
UMBRAL_MONTO_SIN_MXN_HA = 50  # monto/ha siniestrada mínimo plausible
UMBRAL_FIRMA_MXN_HA = 200_000  # arriba de esto + tasa colapsada = firma ×FIX
UMBRAL_TASA_PRIMA_PCT = 0.5  # tasa de prima bajo la cual la suma no es creíble
FACTOR_HISTORIA = 5  # prima<=0: exigir >=5x la mediana histórica propia


def _mascara_agricola_nacional(df):
    col_tipo = "TIPO SEGURO" if "TIPO SEGURO" in df.columns else "TIPO DE SEGURO"
    return (df[col_tipo].map(norm_txt) == "agricola") & (df["MONEDA"].map(norm_txt) == "nacional")


def _marcar(df, mascara, columna, factor, etiqueta, auditoria):
    """Divide `columna` entre `factor` en las filas de `mascara`; registra la auditoría."""
    if mascara.any():
        df[columna] = df[columna].astype(float)  # la división ÷FIX no cabe en int64
    for idx in df.index[mascara]:
        original = df.at[idx, columna]
        df.at[idx, columna] = original / factor
        df.at[idx, "dq_correccion"] = etiqueta
        df.at[idx, "dq_valor_original"] = original
        auditoria.append(
            {
                "fila_csv": idx,
                "anio": df.at[idx, "anio"],
                "entidad": df.at[idx, "ENTIDAD"],
                "cultivo": df.at[idx, "CULTIVO"],
                "campo": columna.splitlines()[0],
                "valor_original": original,
                "valor_corregido": df.at[idx, columna],
                "regla": etiqueta,
                "factor": factor,
            }
        )


def corregir_magnitudes_agricola_emision(df):
    """
    Correcciones (a) superficie ÷1000 y (b) suma ÷FIX en la hoja de emisión agrícola.
    Devuelve (df_corregido, auditoria: DataFrame). No toca renglones pecuarios ni en
    moneda extranjera. Renglones con firma débil (prima<=0 sin historial propio que
    los contradiga) NO se corrigen: quedan para revisión manual.
    """
    df, auditoria = df.copy(), []
    df["dq_correccion"], df["dq_valor_original"] = "", np.nan
    base = _mascara_agricola_nacional(df)
    sup, suma, prima = df[COL_SUP_ASEGURADA], df[COL_SUMA_ASEGURADA], df[COL_PRIMA_EMITIDA]

    # (a) superficie ×1000: valor implícito <100 MXN/ha que ÷1000 regresa a banda plausible
    v = suma / sup.where(sup > 0)
    div1000 = (
        base
        & (sup >= 1000)
        & (v > 0)
        & (v < BANDA_VALOR_MXN_HA[0] / 10)
        & (v * 1000 >= BANDA_VALOR_MXN_HA[0])
        & (v * 1000 <= BANDA_VALOR_MXN_HA[1])
    )
    _marcar(df, div1000, COL_SUP_ASEGURADA, 1000, "superficie_div1000", auditoria)

    # (b) suma ×FIX (2022+): firma = MXN/ha > 200k con tasa de prima colapsada
    sup, suma = df[COL_SUP_ASEGURADA], df[COL_SUMA_ASEGURADA]  # sup ya corregida en (a)
    mxn_ha = suma / sup.where(sup >= 10)
    tasa = 100 * prima / suma.where(suma > 0)
    firma = base & df["anio"].isin(FIX_PROMEDIO_ANUAL) & (mxn_ha > UMBRAL_FIRMA_MXN_HA)
    fix_a = firma & (prima > 0) & (tasa < UMBRAL_TASA_PRIMA_PCT)
    # prima<=0: sin tasa que delate; exigir >=FACTOR_HISTORIA x la mediana pre-2022 propia
    hist = df[base & (df["anio"] < min(FIX_PROMEDIO_ANUAL)) & (sup >= 10) & (suma > 0)]
    mediana_hist = (
        (hist[COL_SUMA_ASEGURADA] / hist[COL_SUP_ASEGURADA])
        .groupby([hist["ENTIDAD"].map(norm_txt), hist["CULTIVO"].map(norm_txt)])
        .median()
    )
    llaves = pd.MultiIndex.from_arrays([df["ENTIDAD"].map(norm_txt), df["CULTIVO"].map(norm_txt)])
    mh = pd.Series(mediana_hist.reindex(llaves).to_numpy(), index=df.index)
    fix_b = (
        firma
        & (prima <= 0)
        & mh.notna()
        & (mh < UMBRAL_FIRMA_MXN_HA)
        & (mxn_ha >= FACTOR_HISTORIA * mh)
    )
    assert not (div1000 & (fix_a | fix_b)).any(), "una fila no puede llevar ambas correcciones"
    for anio, factor in FIX_PROMEDIO_ANUAL.items():
        _marcar(
            df,
            (fix_a | fix_b) & (df["anio"] == anio),
            COL_SUMA_ASEGURADA,
            factor,
            "suma_div_fix",
            auditoria,
        )

    debil = (firma & (prima <= 0) & ~fix_b).sum()
    if debil:
        print(
            f"[limpieza_cnsf] AVISO: {debil} renglones de emisión con firma ×FIX débil "
            f"(prima<=0, sin historial que la confirme) NO corregidos; revisar a mano."
        )
    return df, pd.DataFrame(auditoria)


def corregir_magnitudes_agricola_siniestros(df, emision_corregida=None):
    """
    Corrección (a) superficie siniestrada ÷1000 en la hoja de siniestros agrícola. Dos vías:
      - monto por hectárea siniestrada >0 y <50 MXN/ha (imposiblemente bajo);
      - monto 0 (sin ratio que delate) pero superficie >10x la asegurada corregida de la
        misma celda año×entidad×cultivo — requiere pasar `emision_corregida`.
    Devuelve (df_corregido, auditoria: DataFrame).
    """
    df, auditoria = df.copy(), []
    df["dq_correccion"], df["dq_valor_original"] = "", np.nan
    base = _mascara_agricola_nacional(df)
    sup = df[COL_SUP_SINIESTRADA]
    monto = df[["MONTO DEL SINIESTRO OCURRIDO", "MONTO PAGADO"]].max(axis=1)
    v = monto / sup.where(sup > 0)
    div1000 = base & (sup >= 1000) & (v > 0) & (v < UMBRAL_MONTO_SIN_MXN_HA)
    if emision_corregida is not None:
        em = emision_corregida
        em_ag = em[em["TIPO SEGURO"].map(norm_txt) == "agricola"]
        aseg = em_ag.groupby(
            [em_ag["anio"], em_ag["ENTIDAD"].map(norm_txt), em_ag["CULTIVO"].map(norm_txt)]
        )[COL_SUP_ASEGURADA].sum()
        llave = pd.MultiIndex.from_arrays(
            [df["anio"], df["ENTIDAD"].map(norm_txt), df["CULTIVO"].map(norm_txt)]
        )
        aseg_celda = pd.Series(aseg.reindex(llave).to_numpy(), index=df.index)
        div1000 |= (
            base & (sup >= 1000) & (monto <= 0) & aseg_celda.notna() & (sup > 10 * aseg_celda)
        )
    _marcar(df, div1000, COL_SUP_SINIESTRADA, 1000, "superficie_div1000", auditoria)
    return df, pd.DataFrame(auditoria)


if __name__ == "__main__":
    # mini auto-prueba de la clasificación de entidades
    pruebas = [
        "Quitana Roo",
        "Quintana Roo",
        "QUINTANA ROO",
        "Extranjero",
        "No aplica (exportación)",
        "NU",
        "No Disponible",
        "Distrito Federal",
        "México",
        "Coahuila de Zaragoza",
        "Marte",
    ]
    for p in pruebas:
        print(f"{p!r:35} -> {clasificar_entidad(p)}")
