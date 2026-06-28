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
    import pandas as pd
    import numpy as np
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
    s = "".join(c for c in unicodedata.normalize("NFD", s)
                if unicodedata.category(c) != "Mn")
    return " ".join(s.split())


# --------------------------------------------------------------------------- #
# 1. ENTIDADES
# --------------------------------------------------------------------------- #
# 32 entidades federativas en su forma canónica (para mostrar).
ENTIDADES_32 = [
    "Aguascalientes", "Baja California", "Baja California Sur", "Campeche",
    "Chiapas", "Chihuahua", "Ciudad de México", "Coahuila", "Colima", "Durango",
    "Estado de México", "Guanajuato", "Guerrero", "Hidalgo", "Jalisco",
    "Michoacán", "Morelos", "Nayarit", "Nuevo León", "Oaxaca", "Puebla",
    "Querétaro", "Quintana Roo", "San Luis Potosí", "Sinaloa", "Sonora",
    "Tabasco", "Tamaulipas", "Tlaxcala", "Veracruz", "Yucatán", "Zacatecas",
]
_ENTIDADES_32_NORM = {norm_txt(e): e for e in ENTIDADES_32}

# Variantes/typos OBVIOS -> canónico. Se aplican automáticamente.
# (claves en forma normalizada con norm_txt)
CORRECCIONES_ENTIDAD = {
    "quitana roo": "Quintana Roo",                 # typo confirmado
    "chichuahua": "Chihuahua",                     # typo confirmado (CENAPRED)
    "distrito federal": "Ciudad de México",        # DF -> CDMX
    "mexico": "Estado de México",                  # 'México' (estado) -> Estado de México
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
    "varios estados",      # CENAPRED: evento nacional/difuso, sin asignar (no repartir)
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
COL_PERDIDA = "MONTO PAGADO"          # usar como pérdida (limpio, sin negativos)
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
    return (d.groupby([col_anio, "entidad_cat"]).size()
              .unstack(fill_value=0).sort_index())


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
        print(f"[limpieza_cnsf] AVISO: {len(desconocidos)} filas con ENTIDAD "
              f"no clasificada (revisar, no se asignan): {etiquetas}")
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
            print(f"[limpieza_cnsf] NOTA: '{COL_PERDIDA_PROHIBIDA}' tiene {neg} valores "
                  f"negativos (movimiento contable de reservas). Usar '{COL_PERDIDA}' como pérdida.")
    return df


# --------------------------------------------------------------------------- #
# 5. Pipeline de conveniencia
# --------------------------------------------------------------------------- #
def limpiar_ramo(df, col_entidad="ENTIDAD", col_anio="anio",
                 columnas_monetarias=None, path_mapa_perils=None,
                 col_causa=None, ramo=None, solo_clima=True):
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
            lambda v: mapear_peril(ramo, v, mapa, solo_clima=solo_clima))
    return filtrar_para_calibracion(df, col_entidad=col_entidad)


if __name__ == "__main__":
    # mini auto-prueba de la clasificación de entidades
    pruebas = ["Quitana Roo", "Quintana Roo", "QUINTANA ROO", "Extranjero",
               "No aplica (exportación)", "NU", "No Disponible", "Distrito Federal",
               "México", "Coahuila de Zaragoza", "Marte"]
    for p in pruebas:
        print(f"{p!r:35} -> {clasificar_entidad(p)}")
