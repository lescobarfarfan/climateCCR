"""
config_sequia.py
=================
Constantes y parámetros del pipeline de atribución de sequía (ERA5 -> SPI/SPEI ->
agregación estatal -> validación).

Todas las decisiones de modelación quedan centralizadas aquí para que sean
explícitas, versionables y trazables. Cualquier cambio de supuesto se documenta
en README_sequia.md (sección "Bitácora de decisiones").

Referencias clave (ver README_sequia.md para la lista completa):
  - McKee et al. (1993)             -> definición del SPI.
  - WMO (2012), WMO-No. 1090        -> guía operativa del SPI; recomienda Gamma.
  - Vicente-Serrano et al. (2010)   -> definición del SPEI; log-logística por L-momentos.
  - Beguería et al. (2014)          -> revisión de distribuciones y PET para SPEI.
  - Thom (1958)                     -> estimador de máxima verosimilitud para Gamma.
  - C3S / ERA5-Drought (2025)       -> producto oficial de referencia/validación.
"""

# --------------------------------------------------------------------------- #
# Dominio espacial: recorte de México (bounding box).
# Se recorta en la descarga para reducir drásticamente el tamaño de los .nc.
# Límites holgados para cubrir todo el territorio + islas + margen de celda.
# Orden CDS (area): [Norte, Oeste, Sur, Este].
# --------------------------------------------------------------------------- #
BBOX_MEXICO = {
    "norte": 33.5,
    "oeste": -118.5,
    "sur": 14.0,
    "este": -86.0,
}
BBOX_CDS_AREA = [BBOX_MEXICO["norte"], BBOX_MEXICO["oeste"],
                 BBOX_MEXICO["sur"], BBOX_MEXICO["este"]]

# --------------------------------------------------------------------------- #
# Escalas de acumulación (en meses).
# Set base: cubre sequía agrícola (3-6), hidrológica anual (12) y plurianual (24).
# Escalas opcionales (1, 48) se habilitan con la bandera --escalas-extra.
# --------------------------------------------------------------------------- #
ESCALAS_BASE = [3, 6, 12, 24]
ESCALAS_EXTRA = [1, 48]

# --------------------------------------------------------------------------- #
# Periodos de referencia (calibración de la distribución).
# El registro de SALIDA cubre todo el rango descargado; estos periodos solo
# definen sobre qué años se ajusta la distribución que define "lo normal".
#   - 1991-2020: normal climatológica vigente de la OMM; igual al producto
#                oficial ERA5-Drought (permite comparabilidad y validación).
#   - 1961-1990: normal "pre-aceleración" usada como base de cambio climático;
#                contra ella las sequías recientes (2011-2012, 2020-2021) se ven
#                más anómalas, exponiendo la señal de calentamiento.
# CAVEAT: 1961-1978 cae en la back-extension de ERA5 (pre-satelital), de menor
#         confiabilidad. Documentado en README_sequia.md.
# --------------------------------------------------------------------------- #
PERIODOS_REFERENCIA = {
    "1991-2020": (1991, 2020),
    "1961-1990": (1961, 1990),
}

# --------------------------------------------------------------------------- #
# Variables ERA5 (CDS: "reanalysis-era5-single-levels-monthly-means").
# Se descargan los miembros del ensemble (10 realizaciones del EDA).
#   - total_precipitation        : P  (m/mes en medias mensuales de tasas).
#   - potential_evaporation      : PET (m, signo ERA5; se normaliza en cálculo).
# Se usa la PET propia de ERA5 para mantener consistencia metodológica con el
# producto oficial ERA5-Drought (no se recalcula PET por Thornthwaite).
# --------------------------------------------------------------------------- #
CDS_DATASET_CRUDO = "reanalysis-era5-single-levels-monthly-means"
CDS_PRODUCT_TYPE_CRUDO = "monthly_averaged_ensemble_members"  # 10 miembros (EDA)
VARIABLES_ERA5 = ["total_precipitation", "potential_evaporation"]

# Producto oficial ERA5-Drought (solo como BENCHMARK de validación del caso 1991-2020).
CDS_DATASET_OFICIAL = "derived-drought-historical-monthly"
CDS_VERSION_OFICIAL = "1_0"
CDS_DOI_OFICIAL = "10.24381/9bea5e16"
# product_type del ensemble en el producto oficial = "ensemble_members" (10 realizaciones
# del EDA). Confirmado en la guía de usuario de ECMWF (Ejemplo 4). NO usar "ensemble".
CDS_PRODUCT_TYPE_OFICIAL = "ensemble_members"
CDS_DATASET_TYPE_OFICIAL = "consolidated_dataset"  # va 2-3 meses detrás de tiempo real

# --------------------------------------------------------------------------- #
# Decisiones de distribución (modelación). Configurables y documentadas.
#   - SPI : Gamma de 2 parámetros (Thom 1958), con corrección de ceros (mezcla).
#           WMO (2012) y Stagge et al. (2015) recomiendan Gamma.
#   - SPEI: log-logística de 3 parámetros por L-momentos (Vicente-Serrano 2010).
#           NOTA: ERA5-Drought usa "logística generalizada"; la diferencia frente
#           al producto oficial se cuantifica en el módulo de validación.
# Límite de saturación del índice (estándar en productos operativos).
# --------------------------------------------------------------------------- #
DIST_SPI = "gamma"
DIST_SPEI = "loglogistica"
LIMITE_INDICE = 3.09  # equivale a ~P=0.999; evita infinitos en las colas

# --------------------------------------------------------------------------- #
# Año inicial por defecto del registro de salida.
# 1960 permite cubrir el periodo de referencia 1961-1990 con un año de margen.
# --------------------------------------------------------------------------- #
ANIO_INICIAL_DEFECTO = 1960

# --------------------------------------------------------------------------- #
# Agregación estatal.
#   - CRS_EQUIAREA: proyección de área igual para pesos exactos por intersección.
#   - INEGI Marco Geoestadístico es la fuente AUTORITATIVA de los polígonos
#     estatales (32 entidades). La ruta se pasa por bandera --shp-estados.
# --------------------------------------------------------------------------- #
CRS_EQUIAREA = "EPSG:6933"  # World Cylindrical Equal Area (preserva área)
CRS_GEOGRAFICO = "EPSG:4326"
CLAVE_ESTADO = "CVE_ENT"    # campo de clave estatal en el Marco Geoestadístico INEGI

# Nombres de directorios (espejo de la convención CNSF).
DIR_SEQUIA = "datos/datos_sequia"
DIR_CRUDOS = "datos/datos_sequia/crudos"
DIR_CONSOLIDADOS = "datos/datos_sequia/consolidados"
ARCHIVO_PROCEDENCIA = "_procedencia.json"
ARCHIVO_LOG = "scraper_sequia.log"   # bitácora persistente (append) por ejecución
