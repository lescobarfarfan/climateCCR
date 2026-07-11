# Pipeline de sequía (Tier 1) — ERA5 → SPI/SPEI → agregación estatal

Documentación del módulo de obtención y procesamiento de datos de **sequía** para la tesis de atribución de riesgo financiero al cambio climático en México. Sigue las mismas convenciones que la documentación de CENAPRED y CNSF: verificación de fuentes, trazabilidad de decisiones, reproducibilidad y control de versiones.

---

## 1. Propósito y contexto

La sequía es uno de los peligros del Tier 1 cuya intensidad debe medirse con un índice **continuo, multiescalar y reproducible** que sirva como covariable de intensidad para la calibración de modelos estocásticos y, aguas abajo, para el pricing de instrumentos paramétricos. Este pipeline produce ese índice a partir del reanálisis ERA5 y lo agrega a nivel estatal para empatar con la microdata CNSF.

El **Monitor de Sequía en México (MSM)** de CONAGUA/SMN se trata como capa de **validación** independiente (producto categórico oficial, ligado a declaratorias), no como insumo de calibración. Ver §3.1.

---

## 2. Fuentes de datos

| Fuente | Uso | Acceso | Referencia |
|---|---|---|---|
| **ERA5 monthly means** (C3S/ECMWF) — `total_precipitation`, `potential_evaporation`, miembros del ensemble | **Insumo crudo** para cálculo propio de SPI/SPEI | CDS API (`reanalysis-era5-single-levels-monthly-means`) | Hersbach et al. (2020) |
| **ERA5-Drought** (C3S) — SPI y SPEI oficiales, 0.25°, base 1991-2020 | **Benchmark de validación** del cálculo propio | CDS (`derived-drought-historical-monthly`, v1_0, DOI 10.24381/9bea5e16) | C3S (2025); Scientific Data (2025) |
| **Marco Geoestadístico Nacional** (INEGI) — 32 entidades | Polígonos para agregación estatal | Descarga INEGI (manual) | INEGI (vigente) |
| **Monitor de Sequía en México (MSM)** — categorías D0–D4, quincenal | Validación / cruce con declaratorias | Shapefiles **por solicitud** al SMN; Excel municipal público desde 2003 | SMN-CONAGUA / NADM |

> **Nota de entorno.** El CDS (`cds.climate.copernicus.eu`) y `conagua.gob.mx` no son
> alcanzables desde el sandbox de desarrollo (igual que `cnsf.gob.mx`). Las descargas se
> ejecutan y validan en la máquina del usuario. El cálculo, la agregación y la validación
> corren sin red sobre los `.nc` ya descargados.

---

## 3. Decisiones de modelación

### 3.1 Elección de índice: SPEI primario, SPI robustez, MSM validación

- **SPEI** (Vicente-Serrano et al. 2010) es el índice **primario**. Incorpora el balance hídrico climático *D = P − ETP*, capturando el efecto de la demanda evaporativa —que es **el canal por el que el calentamiento intensifica la sequía**—, justo lo que se quiere atribuir. En México la señal de secamiento está en el balance hídrico, no en la lluvia: la temperatura nacional subió ~0.71 °C (1951-2017) sin tendencia clara en precipitación, pero el balance P−ETP muestra una estación seca mucho más seca (Cruz-Reyes/scielo 2021; estudios locales con Mann-Kendall confirman tendencia en temperatura, no en lluvia).
- **SPI** (McKee et al. 1993; estándar OMM) se calcula **en paralelo** como índice de robustez/comparabilidad. Solo usa precipitación, por lo que es ciego a la temperatura.
- **MSM** (SMN/CONAGUA, parte del NADM): producto **categórico de consenso** (D0–D4), semi-subjetivo, ideal como verdad-terreno oficial y para empatar con **declaratorias**, pero **no** apto como covariable continua de calibración.

### 3.2 Dos periodos de referencia (Opción II: cálculo propio)

El índice se estandariza contra un periodo de referencia que define "lo normal". El registro de **salida** cubre todo el rango descargado (incluye 2011-2012, 2020-2021); el periodo de referencia solo cambia **respecto a qué** se mide la anomalía.

- **1991-2020** — normal climatológica vigente de la OMM; idéntica al producto oficial, habilita comparabilidad y validación.
- **1961-1990** — normal "pre-aceleración", base estándar de cambio climático para México. Contra esta base más fría las sequías recientes se ven **más anómalas**, exponiendo la señal de calentamiento (verificado en pruebas internas: la sequía de 2012 pasa de SPEI-12 ≈ −2.2 con base 1991-2020 a ≈ −2.5 con base 1961-1990).

> **Por qué cálculo propio (Opción II).** El producto oficial ERA5-Drought está
> estandarizado a 1991-2020 **fijo**, y un índice ya estandarizado **no** se puede
> re-estandarizar a otra base (la transformación es no lineal a través de la distribución
> ajustada). Para comparar dos periodos de forma metodológicamente limpia hay que
> recalcular **ambos** con el mismo código desde las acumulaciones crudas. El producto
> oficial se usa solo como benchmark de validación del caso 1991-2020 (§7).

> **Caveat (documentado).** 1961-1978 cae en la *back-extension* de ERA5 (pre-satelital),
> de menor confiabilidad. Alternativa más conservadora disponible: 1971-2000.

### 3.3 Escalas de acumulación

Cada escala n-meses mide un tipo de sequía distinto y se asocia a sistemas/pérdidas distintos: **3–6 meses** → agrícola (ciclo de cultivo); **12 meses** → hidrológica anual (presas, año-agua); **24 meses** → plurianual (mega-sequías como 2011-2012). La escala operativa para cada ramo CNSF se elige **empíricamente por correlación** con las pérdidas.

- Set base: **{3, 6, 12, 24}**. Escalas opcionales {1, 48} con `--escalas-extra`.

### 3.4 Distribuciones (estandarización)

- **SPI**: Gamma de 2 parámetros, estimador de Thom (1958), con corrección de ceros (mezcla *q + (1−q)·Gamma*). Recomendada por WMO (2012) y Stagge et al. (2015).
- **SPEI**: log-logística de 3 parámetros por **L-momentos** (Vicente-Serrano et al. 2010; Beguería et al. 2014). *Diferencia conocida*: ERA5-Drought usa logística generalizada; la brecha frente al producto oficial se **cuantifica** en la validación (§7).
- Ajuste **por mes calendario** (elimina estacionalidad); índice saturado a ±3.09.

### 3.5 Ensemble e incertidumbre

Se usan los **10 miembros del ensemble de ERA5 (EDA)**. Esto representa incertidumbre del **reanálisis/observacional**, *no* dispersión multi-modelo de cambio climático. La estimación central es la **media** sobre miembros; la **desviación estándar** entre miembros se reporta como banda de incertidumbre (útil para pricing).

### 3.6 Agregación espacial: estatal, ponderada por área

Unidad de análisis: **estado** (32 entidades), porque la mayoría de las fuentes no llega a detalle municipal; los crudos quedan en `.nc`, así que la capa municipal puede aplicarse después sobre los mismos datos. La agregación es **media ponderada por área de intersección** celda-estado en proyección de área igual (EPSG:6933), con **fallback** a la celda con dato más cercana. Esto evita que entidades pequeñas (p. ej. CDMX, ~2 celdas a 0.25°) desaparezcan del panel —el artefacto de discretización observado en el panel de viento IBTrACS a 0.5°—. Verificado en pruebas: la entidad chica recibe siempre valor finito.

**Rendimiento (por qué no se requiere `exactextract` ni GeoTIFF).** La intersección geométrica (geopandas) se calcula **una sola vez** —la malla es fija para todos los años, escalas, índices, miembros y periodos— en ~0.6 s para ~10,300 celdas × 32 estados. Esos pesos se guardan como **matriz dispersa** `W` (n_estados × n_celdas) y la agregación de toda la serie temporal se hace con **un solo producto matriz** (BLAS, sin geometría por paso de tiempo): ~4 s para 16 campos × 768 meses × (media + sd), frente a ~300 s de un bucle por paso. Una librería de zonal-stats por raster (exactextract, rasterstats) sería más lenta aquí y exigiría convertir a GeoTIFF en cada paso. El verdadero cuello de botella del pipeline NO es la agregación sino el **ajuste de índices** (§7), que es numérico, no espacial; ahí es donde conviene optimizar (vectorización por celda / numba).

### 3.7 Unidades

ERA5 entrega `tp`/`pev` en metros y `pev ≤ 0` (convención descendente). El pipeline convierte a **mm/mes** y toma |pev| como demanda positiva, registrando los rangos en log para revisión manual (verification-first). **Verificar en la máquina** que las magnitudes sean físicamente razonables antes de confiar en los índices.

---

## 4. Estructura de directorios

```
proyecto/
├── src/
│   ├── config_sequia.py        # constantes y decisiones de modelación
│   ├── indices_sequia.py       # SPI (Gamma/Thom) y SPEI (log-logística/L-momentos)
│   ├── agregacion_sequia.py    # malla -> estatal (ponderado por área + fallback)
│   ├── validacion_sequia.py    # comparación propio vs ERA5-Drought oficial
│   ├── scraper_sequia.py       # orquestador + descarga CDS + procedencia (CLI)
│   ├── requirements_sequia.txt
│   └── README_sequia.md        # este documento
└── datos/datos_sequia/
    ├── scraper_sequia.log      # bitácora persistente (append) de cada ejecución
    ├── crudos/                 # .nc ERA5 recortados a México + benchmark oficial
    │   └── _procedencia.json   # URL/dataset/request/version/DOI/sha256/bytes/fecha
    └── consolidados/           # spi{n}_ref{periodo}.nc, spei..., panel estatal, validación
```

> **Bitácora `scraper_sequia.log`.** Cada ejecución escribe (en modo *append*) un
> encabezado de sesión con fecha/modo/parámetros y todos los mensajes —incluidos los de
> `cdsapi`/`ecmwf` durante las descargas— para llevar control de qué pasó en cada corrida
> (mismo patrón que el scraper de CENAPRED).

---

## 5. Requisitos e instalación

```bash
pip install -r requirements_sequia.txt
```

Configurar credenciales del CDS en `~/.cdsapirc` (ver `https://cds.climate.copernicus.eu/how-to-api`):

```
url: https://cds.climate.copernicus.eu/api
key: <UID>:<APIKEY>
```

Aceptar los términos de licencia del dataset en el portal del CDS la primera vez.

---

## 6. Uso del scraper

Modos (encadenables con `--modo todo`):

| Modo | Acción |
|---|---|
| `verificar` | **Pre-vuelo:** revisa la config del CDS y **compara los archivos en disco contra `_procedencia.json`** (sha256 + bytes, sin red), reportando por archivo: `OK` / `CAMBIADO` / `SIN_PROCEDENCIA` / `FALTA`, y qué pediría `descargar`. Mismo patrón que el `verificar` de CENAPRED. Primer paso recomendado. *No confundir con `validar`.* |
| `descargar` | Baja crudos ERA5 (P, PET, ensemble) + benchmark oficial. **Salta solo los archivos verificados e íntegros** vs procedencia (estilo `sync` de CENAPRED); re-baja lo faltante, cambiado o parcial. `--forzar` re-baja todo. Registra procedencia. |
| `recuperar` | Descarga **un solo** resultado del CDS por su `--request-id` (un job ya enviado, p. ej. uno que quedó "accepted" y se cortó). Con `--objetivo {crudo_era5\|benchmark_spi\|benchmark_spei}` lo deja con **nombre canónico y procedencia completa** que el pipeline reconoce. No re-envía el request. |
| `registrar` | **Adopta** en la procedencia un archivo que ya está en disco y completo, bajo su `--objetivo` canónico, **sin red**. Para cuando un archivo se recuperó/renombró a mano y quedó `SIN_PROCEDENCIA`. |
| `calcular` | Calcula SPI y SPEI propios, por escala y periodo de referencia → `consolidados/*.nc` |
| `agregar` | Agrega a estatal (ponderado por área) → `panel_sequia_estatal.csv`/`.parquet` |
| `validar` | **QA posterior:** compara el cálculo propio (1991-2020) vs ERA5-Drought oficial → `reporte_validacion.json` |
| `todo` | Ejecuta la cadena completa (`descargar` → `calcular` → `agregar` → `validar`) |

> **`verificar` vs `validar`.** `verificar` es el chequeo *previo* (configuración + lista de
> descargas, barato, sin red de datos). `validar` es el control de calidad *posterior* que
> compara el índice propio contra el producto oficial (requiere haber descargado y calculado).

Banderas principales:

| Bandera | Defecto | Descripción |
|---|---|---|
| `--anio-inicial` / `--anio-final` | 1960 / año previo | Rango del registro de salida |
| `--indices` | `spi spei` | Índices a calcular |
| `--escalas` | `3 6 12 24` | Escalas de acumulación (meses) |
| `--escalas-extra` | — | Añade {1, 48} al set base |
| `--forzar` | — | Re-descarga aunque el archivo ya exista (por defecto `descargar` omite lo existente) |
| `--periodos-referencia` | `1991-2020 1961-1990` | Periodos de calibración |
| `--shp-estados` | — | Ruta al Marco Geoestadístico INEGI (requerido en `agregar`) |
| `--request-id` | — | ID de un job del CDS ya enviado (modos `recuperar`/`registrar`) |
| `--objetivo` | — | Objetivo canónico `crudo_era5\|benchmark_spi\|benchmark_spei` para `recuperar`/`registrar` (fija nombre y procedencia correctos; **recomendado**) |
| `--destino` | — | Ruta libre de salida para `recuperar` (solo si NO usas `--objetivo`; un nombre no canónico no será reconocido por `verificar`/`descargar`) |

Ejemplos:

**Ejemplo 1 — Pre-vuelo (primer paso): verificar configuración y listar descargas.** No baja nada; confirma que `~/.cdsapirc` y `cdsapi` están bien, e imprime el plan exacto de descarga (datasets, variables, años, área) y qué archivos están pendientes o ya existen. Es lo primero que conviene correr, especialmente la primera vez.

```bash
python scraper_sequia.py --modo verificar
# acotar el rango de años a verificar:
python scraper_sequia.py --modo verificar --anio-inicial 1960 --anio-final 2023
```

**Ejemplo 2 — Solo descargar los crudos (+ benchmark oficial).** Primera vez: correr antes el Ejemplo 1 (`verificar`), porque aún no existe `_procedencia.json` ni logs; así confirmas la config y revisas el plan antes de bajar GB de datos. El rango de años y las escalas (para el benchmark oficial) se pasan como banderas.

```bash
# 1) pre-vuelo (si es la primera vez)
python scraper_sequia.py --modo verificar --anio-inicial 1960 --anio-final 2023
# 2) descarga propiamente dicha
python scraper_sequia.py --modo descargar --anio-inicial 1960 --anio-final 2023 --escalas 3 6 12 24
```

`descargar` deja los `.nc` recortados a México en `datos/datos_sequia/crudos/` y escribe `_procedencia.json` (request CDS + versión + DOI + sha256 + bytes + fecha) por cada archivo. Es **idempotente y verificado por integridad**: omite los archivos cuyo `sha256`/`bytes` coinciden con `_procedencia.json` (salvo `--forzar`), y **re-baja los faltantes, cambiados o parciales** (una descarga interrumpida no deja registro de procedencia, así que se detecta y se vuelve a bajar). Esto permite *reanudar* sin repetir lo ya descargado **y** sin arrastrar archivos corruptos. Corre `verificar` antes para ver el estado de cada archivo sin red.

**Ejemplo 2b — Recuperar un job que quedó pendiente, por su `request_id`.** Si una descarga quedó en estado *accepted/running* y tuviste que cortarla, el job sigue vivo en el servidor del CDS. Toma el `Request ID is …` impreso en consola (también queda en `scraper_sequia.log`) y bájalo —solo ese— sin re-enviar el request. **Usa `--objetivo`** (no `--destino` libre): así cae con el nombre canónico y la procedencia completa que `verificar`/`descargar` reconocen. (La caché del CDS retiene el resultado ~día y medio; recupéralo dentro de ~un día.)

```bash
python scraper_sequia.py --modo recuperar \
    --objetivo benchmark_spei \
    --request-id f112b1f7-77e8-496d-9f88-6a56a57ae26d
```

**Ejemplo 2c — Adoptar un archivo ya descargado pero `SIN_PROCEDENCIA`.** Si un archivo se recuperó con nombre libre y lo renombraste a mano (o por cualquier razón existe completo en disco pero sin registro), `verificar` lo marcará `SIN_PROCEDENCIA` y `descargar` lo volvería a bajar. Adóptalo (calcula su sha256/bytes y escribe el registro), sin red, dándole su nombre canónico primero:

```bash
# 1) asegúrate de que el archivo tenga el nombre canónico esperado:
#    datos/datos_sequia/crudos/era5drought_spi_oficial.nc
# 2) adóptalo en la procedencia:
python scraper_sequia.py --modo registrar --objetivo benchmark_spi
# ahora 'verificar' lo marca OK y 'descargar' ya no lo re-baja.
```

Alternativa a recuperar: volver a correr `--modo descargar` reengancha al mismo job vía la deduplicación de requests idénticos del CDS (cache hit) si el resultado sigue en caché.

**Ejemplo 3 — Solo calcular índices y agregar a estatal (descarga ya hecha).** Condicional a que los crudos ya estén descargados. Calcula SPI/SPEI propios para ambas bases, agrega a nivel estatal y corre el QA contra el oficial. *(Atención: `calcular` es el paso más costoso en cómputo.)*

```bash
# calcular + agregar + validar, sin volver a descargar:
python scraper_sequia.py --modo calcular --escalas 3 6 12 24 --periodos-referencia 1991-2020 1961-1990
python scraper_sequia.py --modo agregar  --shp-estados datos/inegi/estados.shp
python scraper_sequia.py --modo validar  --escalas 3 6 12 24

# si los índices YA están calculados y solo quieres re-agregar (barato):
python scraper_sequia.py --modo agregar --shp-estados datos/inegi/estados.shp
```

**Pipeline completo (todo) — descarga + cálculo + agregación + validación en una corrida:**

```bash
python scraper_sequia.py --modo todo --shp-estados datos/inegi/estados.shp
# con escalas opcionales {1, 48} añadidas al set base:
python scraper_sequia.py --modo todo --escalas-extra --shp-estados datos/inegi/estados.shp
```

---

## 7. Procedimiento de cálculo (resumen reproducible)

1. **Acumulación.** Suma móvil de n meses sobre P (para SPI) o sobre el balance *D = P − ETP* (para SPEI). Los primeros n−1 meses quedan indefinidos (NaN).
2. **Ajuste por mes calendario.** Para cada uno de los 12 meses, se ajusta la distribución (Gamma o log-logística) **solo** sobre los años del periodo de referencia.
3. **Transformación.** Toda la serie se mapea con la CDF ajustada a la normal estándar: *índice = Φ⁻¹(F(x))*, saturado a ±3.09.
4. **Por miembro del ensemble**, luego media (central) y sd (incertidumbre).

### Validación contra el producto oficial

El módulo compara, por índice y escala, el cálculo propio con base **1991-2020** contra ERA5-Drought oficial (misma base), reportando **correlación, sesgo y RMSE**. Criterio orientativo de reproducción satisfactoria: *corr ≥ 0.95* y *|sesgo| ≤ 0.1*. Solo si el caso 1991-2020 reproduce al oficial se confía en los números de 1961-1990 (que no existen como producto oficial). Una brecha grande motivaría revisar la elección de distribución (log-logística vs logística generalizada).

---

## 8. Limitaciones y caveats

- **Back-extension ERA5 (pre-1979):** menor confiabilidad; afecta parte de la base 1961-1990. Documentar al reportar tendencias; considerar 1971-2000 como sensibilidad.
- **PET de ERA5:** se usa la PET propia de ERA5 (consistencia con el producto oficial); su definición tiene particularidades. La validación es el control de que la elección es adecuada.
- **Distribución SPEI:** log-logística (propio) vs logística generalizada (oficial); la diferencia se cuantifica, no se asume nula.
- **Resolución 0.25°:** mejora frente a 0.5° (IBTrACS) pero sigue siendo gruesa para entidades muy pequeñas; la ponderación por área + fallback lo mitiga, no lo elimina.
- **MSM:** los shapefiles requieren solicitud al SMN; el Excel municipal cambió de criterio de asignación de categoría en 2016 (antes: ≥40% de superficie; después: intensidad máxima observada) — relevante al construir series largas de validación.
- **Recencia del benchmark oficial:** el `consolidated_dataset` de ERA5-Drought va 2-3 meses detrás de tiempo real, así que el pipeline **topa los años del benchmark** a `año_actual−1` (pedir el año en curso da `400 invalid request`). Esto no afecta a los crudos ERA5 ni al cálculo; solo a la ventana de validación, que de todos modos se ancla en 1991-2020.
- **Robustez de descarga:** un fallo del benchmark es **no crítico** y no aborta la corrida (los crudos, que son lo que necesita `calcular`, ya quedaron); `validar` simplemente omite lo que falte. Los errores `4xx`/"invalid request" **no se reintentan** (son de cliente).

---

## 9. Referencias

- McKee, T.B., Doesken, N.J., Kleist, J. (1993). *The relationship of drought frequency and duration to time scales.* 8th Conf. on Applied Climatology, AMS.
- WMO (2012). *Standardized Precipitation Index User Guide.* WMO-No. 1090.
- Vicente-Serrano, S.M., Beguería, S., López-Moreno, J.I. (2010). *A multiscalar drought index sensitive to global warming: the SPEI.* Journal of Climate, 23, 1696–1718.
- Beguería, S., Vicente-Serrano, S.M., Reig, F., Latorre, B. (2014). *SPEI revisited: parameter fitting, evapotranspiration models, tools, datasets and drought monitoring.* Int. J. Climatol., 34, 3001–3023.
- Thom, H.C.S. (1958). *A note on the gamma distribution.* Monthly Weather Review, 86, 117–122.
- Stagge, J.H., et al. (2015). *Candidate distributions for climatological drought indices (SPI and SPEI).* Int. J. Climatol., 35, 4027–4040.
- Hersbach, H., et al. (2020). *The ERA5 global reanalysis.* Q. J. R. Meteorol. Soc., 146, 1999–2049.
- C3S/ECMWF (2025). *Monthly drought indices from 1940 to present derived from ERA5 reanalysis (ERA5-Drought).* CDS `derived-drought-historical-monthly`, v1_0, DOI 10.24381/9bea5e16.
- Hosking, J.R.M., Wallis, J.R. (1997). *Regional Frequency Analysis: An Approach Based on L-Moments.* Cambridge Univ. Press.
- INEGI. *Marco Geoestadístico Nacional* (vigente).
- SMN-CONAGUA. *Monitor de Sequía en México (MSM)* / *Monitor de Sequía de América del Norte (NADM).*
- Contexto sequía México 2011-2012 y tendencias: Semarnat (2012); Cruz-Reyes et al. (scielo, 2021, "Seven decades of climate change across Mexico"); estudios SPEI por entidad (Zacatecas, Durango/Puebla, Estado de México/CDMX).

---

## 10. Bitácora de decisiones

| Fecha | Decisión | Justificación |
|---|---|---|
| (inicial) | Fuente primaria = ERA5-Drought; sin contraste SPEIbase; MSM como validación aparte | Consistencia con workstream ERA5; producto único con SPI+SPEI, versión fijable y DOI |
| (inicial) | SPEI primario, SPI robustez | SPEI captura demanda evaporativa = canal de atribución; SPI estándar OMM |
| (inicial) | **Opción II**: cálculo propio de ambas bases + validación contra oficial | Único modo metodológicamente limpio de comparar periodos de referencia |
| (inicial) | Periodos de referencia: 1991-2020 y **1961-1990** | Comparabilidad vs base fría que expone la señal de calentamiento |
| (inicial) | Escalas base {3,6,12,24}; {1,48} opcionales | Cubren agrícola/hidrológica/plurianual; escala operativa por correlación con pérdidas |
| (inicial) | SPI=Gamma/Thom; SPEI=log-logística/L-momentos | Estándares de la literatura; brecha vs oficial cuantificada |
| (inicial) | Solo ensemble (10 miembros); central=media, incertidumbre=sd | Bandas de incertidumbre para pricing |
| (inicial) | Agregación estatal ponderada por área + fallback | Evita desaparición de entidades pequeñas (CDMX) |
| 2026-06-13 | `product_type` del benchmark oficial corregido a `ensemble_members` (no `ensemble`) | `400 invalid request` en la primera descarga; confirmado en la guía ECMWF (Ejemplo 4) |
| 2026-06-13 | Años del benchmark topados a `año_actual−1`; descarga del benchmark no crítica; sin reintentos ante `4xx` | El `consolidated_dataset` va 2-3 meses detrás; los crudos no deben perderse por un fallo del benchmark |
| 2026-06-13 | Bitácora persistente `scraper_sequia.log` (append por ejecución) | Control de qué pasa en cada corrida, igual que CENAPRED |
| 2026-06-13 | Modo `recuperar` para bajar un job del CDS por `request_id` | Recuperar descargas que quedan "accepted"/pendientes sin re-enviar ni recalcular |
| 2026-06-14 | `descargar` idempotente: omite archivos existentes (salvo `--forzar`) | Evita re-bajar el crudo (~2 h en cola) y permite reanudar para llegar a los benchmarks pendientes |
| 2026-06-14 | `verificar` compara sha256/bytes vs `_procedencia.json`; `descargar` salta solo lo íntegro y re-baja faltante/cambiado/parcial | Alinear con la convención de CENAPRED (verificar vs almacenado); detectar descargas parciales que el salto por-existencia no atrapaba |
| 2026-06-14 | `recuperar --objetivo` (nombre canónico + procedencia completa) y nuevo modo `registrar` (adoptar archivo existente) | Recuperar con `--destino` libre dejaba nombres no canónicos que el pipeline no reconocía; renombrar a mano orfanaba la procedencia |

## Related
[[HAZ_MOC]] · Home: [[_INDEX]]

#arm/haz #type/pipeline
