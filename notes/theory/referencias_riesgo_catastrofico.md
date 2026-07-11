# Referencias y fuentes para vincular fenómenos naturales (climáticos) con pérdidas económico-financieras

**Proyecto:** Riesgo financiero de fenómenos naturales (insumo para *MSc Thesis* — atribución de incremento de riesgo al cambio climático)
**Insumo central:** bases consolidadas del scraper de la CNSF (ramos *agrícola y animales*, *riesgos hidrometeorológicos*, *incendio*, *automóviles* [individual y flotilla]). Nivel **estatal**, resolución temporal **anual**.
**Fecha:** 2026-06-11 · **Versión:** 0.18

> **Estándar del proyecto.** Referencias **[web]** (consultada con URL) o **[canónico]** (obra estándar; confirmar edición/DOI). Registrar en el log del repo toda decisión derivada y versionar con git. Los mapeos peril↔fuente viven en dos CSV acompañantes: `mapa_perils_seguros_a_canonico.csv` y `mapa_canonico_a_fuentes.csv`.

> **Alcance de peligros.** Por el enfoque de **atribución al cambio climático** se **excluyen los peligros geofísicos** (sismo, erupción, tsunami). Foco: ciclón tropical, marejada, inundación, lluvia intensa, granizo, viento severo/tornado, deslizamiento por lluvia, sequía, calor extremo, helada/frío, nevada y rayo.

---

## 1. Marco conceptual y restricciones de diseño

Dos descomposiciones ordenan el uso de los datos:
1. **Triángulo del riesgo:** $\text{Riesgo} = \text{Peligro} \times \text{Exposición} \times \text{Vulnerabilidad}$ + módulo financiero (AAL, PML, curva de excedencia).
2. **Frecuencia–severidad (riesgo colectivo):** $S = \sum_{i=1}^{N} X_i$. $S(t)$ es un **Poisson compuesto** (Lévy de saltos puros); con intensidad dependiente del peligro se llega a los **procesos de Cox / Poisson doblemente estocásticos** — el puente al cálculo estocástico.

**Restricciones confirmadas con los datos:**
- **Grano:** $\text{estado} \times \text{peril} \times \text{año}$. Sin mes. → panel estatal anual (~32 estados × ~17 años); la dimensión espacial compensa la temporal. Intensidad $\lambda_{\text{año}}(\text{estado}) = f(\text{covariables de peligro anuales})$.
- **Exposición peril-agnóstica:** ninguna hoja de exposición (`emisión`, `suma asegurada`, `unidades expuestas`) trae la causa/tipo de evento; sólo `siniestros` la trae. Por tanto **tasa de un peril = pérdida de ese peril ÷ exposición total del estrato**, y el grano máximo de normalización es la **intersección de llaves** entre siniestros y la hoja de exposición.
- **Dos preocupaciones distintas:** la **subestimación por baja penetración** es de *nivel* (sólo se ve lo asegurado; se cierra con CENAPRED); la **atribución del peril** es de *resolución* y la resuelve el campo de causa/tipo de evento de la CNSF.

---

## 2. Referencias por bloque temático

### A. Fundamentos actuariales (frecuencia–severidad)
- **Klugman, Panjer & Willmot — *Loss Models: From Data to Decisions* (Wiley).** *[canónico]*
- **Mikosch — *Non-Life Insurance Mathematics* (Springer).** *[canónico]*
- **Panjer (1981), *ASTIN Bulletin*** — recursión para la distribución agregada. *[canónico]*

### B. Severidad, colas pesadas y EVT
- **Embrechts, Klüppelberg & Mikosch (1997), *Modelling Extremal Events* (Springer).** *[canónico]*
- **McNeil (1997), *ASTIN Bulletin* 27:117–137** — POT + GPD en catástrofe natural. *[web]* https://www.researchgate.net/publication/2314750
- **Coles (2001), *Statistical Modeling of Extreme Values* (Springer)** — GEV/GPD, niveles de retorno. *[canónico]*
- **McNeil, Frey & Embrechts (2005/2015), *Quantitative Risk Management* (Princeton)** — VaR/ES, cópulas. *[canónico]*

### C. Modelos de catástrofe (industria/regulatorio)
- **NAIC, *Catastrophe Modeling Primer* (2025).** *[web]* https://content.naic.org/sites/default/files/committees-pending-action-cat-mod-primer.pdf
- **Insurance Information Institute.** *[web]* https://www.iii.org/article/catastrophe-modeling-vital-tool-risk-management-box
- **Oasis Loss Modelling Framework (open source).** *[web]* https://en.wikipedia.org/wiki/Catastrophe_modeling

### D. Procesos estocásticos y valuación (puente con cálculo estocástico)
- **Proceso de Cox / Poisson doblemente estocástico** (intensidad estocástica para *clustering*). *[web]* https://www.sciencedirect.com/science/article/abs/pii/S016766870200152X
- **Baryshnikov et al. (2001); Burnecki (2005)** — cat bonds con Poisson compuesto no homogéneo y cola pesada. *[web]* https://www.sciencedirect.com/science/article/abs/pii/S0167668713000024
- **Jump-diffusion / ILS** (Vaugirard; Cox, Fairchild & Pedersen 2004; Jaimungal & Wang 2006). *[web]* https://www.sciencedirect.com/science/article/abs/pii/S0264999315001893
- **Cont & Tankov (2004), *Financial Modelling with Jump Processes* (Chapman & Hall/CRC).** *[canónico]*
- **Cummins (2008), *RMIR*** — cat bonds / ILS. *[canónico]*

### E. Transmisión clima → economía/finanzas
- **NGFS — riesgo físico y escenarios (Fase V, 2024).** *[web]* https://www.ngfs.net/en/press-release/ngfs-publishes-latest-long-term-climate-macro-financial-scenarios-climate-risks-assessment

### F. Instrumentos en México
- **Banco Mundial / IBRD — cat bonds soberanos FONDEN (2006–2024).** *[web]* La tranche de ciclón es la pertinente; las *offering circulars* documentan la metodología de modelación. https://www.worldbank.org/en/news/press-release/2024/04/17/world-bank-issues-420-million-in-catastrophe-bonds-for-renewed-disaster-risk-protection-for-mexico

---

## 3. Taxonomía de perils confirmada por ramo (catálogos CNSF)

Valores reales extraídos de los catálogos (detalle y homogeneización en `mapa_perils_seguros_a_canonico.csv`).

- **Hidro `TIPO DE EVENTO`** (taxonomía limpia y estable 17 años). In-scope: *Ciclón tropical (Huracán), Marejada, Inundación por desbordamiento/lluvia, Daños por lluvia, Granizo, Vientos tempestuosos/Tornado, Avalancha de lodo/Deslizamientos, Helada, Nevada*. Fuera: *Tsunami/Golpe de mar* (sísmico), *Roturas de tuberías*, *Otro tipo de evento*. **Es el campo de peril más fuerte.**
- **Agro `CAUSA DEL SINIESTRO`** (rica para clima). In-scope: *Sequía, Onda cálida, Disminución en vegetación* (déficit hídrico/calor); *Heladas, Bajas temperaturas, Nieve* (frío); *Exceso de humedad, Inundación, Granizo, Huracán/Ciclón/Tornado/Vientos*. Fuera: *Terremoto/erupción* y las bióticas/operativas (plagas, enfermedades, accidente, etc.).
- **Incendio `CAUSA DEL SINIESTRO`** — **es fuego en propiedad, NO incendio forestal.** Única causa climática limpia: **`Rayo`**. El resto es no climático (explosión, corto circuito, cerillos, fricción…). **Decisión: incendio pasa a fuente secundaria; la señal de wildfire viene de CONAFOR/FIRMS/CONABIO, no de este ramo.**
- **Autos `Causa del siniestro_desc`** — sólo poblada **2016–2024** (9 años). In-scope: *Ciclón/huracán, Inundación, Granizo, Derrumbe/alud*; *Incendio/rayo/explosión* (compuesto, sólo fracción rayo). Señal corroborante de corto plazo, no base larga.

**Variables estructurales clave confirmadas:**
- **Agro régimen hídrico** vive en `TIPO DE CULTIVO` (mal nombrada): `Riego / Temporal / Medio riego / Humedad`. `Temporal` (secano) concentra la vulnerabilidad a sequía. El cultivo real está en `CULTIVO`; el ciclo en `CICLO DE CULTIVO` (Primavera-Verano / Otoño-Invierno / Perenne).
- **Agro `ESQUEMA DE ASEGURAMIENTO`** separa **catastrófico/paramétrico** (`Seguro agrícola catastrófico`, `Seguro de animales catastrófico`, `Índice de Vegetación Satelital`) de **comercial** (a la inversión, con ajuste al rendimiento/daños, garantía de producción…). **Los catastróficos/paramétricos se disparan por índice, no por peritaje: modelar por separado.**
- **Hidro `COBERTURA` NO es peril** sino tipo de cobertura: la base es *Riesgos Hidrometeorológicos* y el resto son consecuenciales/financieras (Gastos Extraordinarios, Pérdida de Utilidades, Remoción de Escombros…). Útil para aislar daño físico directo de pérdida consecuencial.
- **`PRIMERA LÍNEA DE MAR`** (hidro): exposición costera (storm surge); en el fondo son 2 categorías (`<500 m` / `>500 m`) bajo 9 variantes de redacción → normalizar.
- **Autos `Tipo de Perdida`**: *Total / Parcial* (+ variantes SIPAC). La pérdida total está topada al valor del vehículo → régimen de severidad distinto; estratificar.

---

## 4. Pros y contras de los datos CNSF y banderas de limpieza

**Ventajas:** fuente oficial pública; 2007/2008–2024; cobertura de mercado completa; **causa/tipo de evento** y **nivel estatal**; exposición (suma asegurada, unidades, superficie) y resultado (siniestros, prima) → frecuencias normalizadas, severidades medias y *loss ratios*. En agro, `SUPERFICIE SINIESTRADA`/`SUPERFICIE ASEGURADA` da una **tasa de daño físico en hectáreas** (más cercana al peligro que el monto).

**Limitaciones:** datos **agregados** (frecuencia + severidad media, no la **cola** → la cola se calibra con CENAPRED por evento); **resolución anual**; **solo asegurado** (subestima total); categorías compuestas/solapadas.

**Banderas de limpieza (antes de extraer):**
- **Variable de pérdida — usar `MONTO PAGADO`, NO `MONTO DEL SINIESTRO` (ver recuadro abajo).** Para frecuencia, `NÚMERO DE SINIESTROS`. Nombre inconsistente del monto ocurrido en agro (`OCOURRIDO`/`COURRIDO`/`OCURRIDO`/``) — homologar. Distintos nombres por ramo.
- **Dos hojas de emisión:** agro (`Emision` 2018–24 + `Emisión` 2008–17) e incendio (`Emisión` 2007 con 14 cols) → concatenar con cuidado.
- **Ventana real:** siniestros 2008–2024 (incendio agrega 2007); **autos con causa sólo 2016–2024**.
- **Quiebres de registro 2015 y 2021 (RESUELTOS — sólo granularidad, no cobertura).** En hidro, 2015 tiene ~½ de filas y 2021 ~2× respecto a vecinos, pero los **valores** (suma asegurada, prima, número de ubicaciones, número de siniestros, valores totales) son **continuos** en ambos casos (2015 al 100–129% del promedio vecino; 2021/2020 al 100–110%). Es decir, los archivos sólo cambiaron la **desagregación de filas** (y, en 2021, añadieron columnas), no la información. Implicación: trabaja en **valores y tasas por exposición**, nunca en conteo crudo de filas; así la serie 2008–2024 es homogénea.
- **Vacío = NA, no 0.** Donde el consolidador rellenó columnas faltantes con vacío (p. ej. `PRIMA DEVENGADA ACUMULADA` antes de 2021; `MONTO DE REASEGURO` y `MONTO RECUPERADO DE TERCEROS` antes de 2021), trátalo como **faltante**, no como cero, o sesgarás promedios/sumas. Corolario: la **pérdida neta de reaseguro sólo es reconstruible desde 2021**; para la serie larga se trabaja en bruto.
- **`MONEDA`** en agro/hidro/incendio (hay USD → normalizar a MXN real); **autos sin `MONEDA`** → confirmar que todo es MXN.
- **`TIPO PRIMER RIESGO`:** en primer riesgo la suma asegurada ≠ valor total expuesto → usar `SUMA ASEGURADA EXPUESTA` / `VALORES TOTALES` como denominador y tratar aparte.
- **Exposición de autos:** `unidades_expuestas` **no trae `ENTIDAD`** → usar `Número de Vehículos`/`Suma Asegurada` de `emisión` como denominador estatal.
- **Normalización de texto:** deriva de ortografía/mayúsculas (incendio `CAUSA`, hidro `PRIMERA LÍNEA DE MAR`, autos menor) → canonicalizar (casefold + acentos + sinónimos). `GIRO` de incendio: 838 valores libres → agrupar en sectores si se usa.
- **`ENTIDAD` — normalizar y clasificar las etiquetas no-estado (ver recuadro abajo).** En hidro aparecen `Quitana Roo` (typo de Quintana Roo), `Extranjero`, `No aplica (exportación)`, `NU` y `No Disponible`/`No disponible`. La diferencia de conteo entre años (p. ej. 34 entidades en 2020 vs 32 en 2021) viene de estas etiquetas, no de estados faltantes.

> ### ⚠️ Punto fino: valores negativos en `MONTO DEL SINIESTRO` → usar `MONTO PAGADO`
> **Qué pasa.** En la hoja de siniestros, `MONTO DEL SINIESTRO` (ocurrido) **no es la pérdida bruta limpia, sino el *movimiento contable* de la estimación/reservas del periodo**. Por eso aparece con **valores negativos** por estado y con totales anuales erráticos: cuando se reestiman a la baja los siniestros de un año catastrófico, el año siguiente sale negativo.
>
> **Evidencia (hidro, total nacional):** `MONTO DEL SINIESTRO` = 18,085 M (2014) → **255 M (2015, 2%)** → 2,951 M (2016), con negativos por estado (Aguascalientes 2015 = −184 M; Baja California Sur 2015 = −491 M). En contraste, `MONTO PAGADO` = 6,552 M (2014) → 11,060 M (2015) → 5,325 M (2016): **siempre positivo y del mismo orden**. El caso de libro: BCS 2014 = 6,250 siniestros y 11,800 M corresponde al **huracán Odile** (sep-2014); el −491 M de BCS 2015 es el ajuste de cola de esos mismos siniestros.
>
> **Regla.** Para severidad/pérdida usar **`MONTO PAGADO`** (resuelve el problema de los negativos) y para frecuencia **`NÚMERO DE SINIESTROS`** (limpio). **No** usar `MONTO DEL SINIESTRO` como pérdida anual.
>
> **Matiz que `MONTO PAGADO` NO resuelve por sí solo (temporalidad).** El pagado es **caja del año calendario**, y un evento catastrófico **derrama pagos en varios años** (Odile se paga en 2014 *y* 2015). Por tanto, para atribuir pérdida a un evento/peril no basta leer el pagado de un solo año: hay que **acumular la pérdida del evento sobre su ventana de desarrollo** (p. ej. la temporada + el año siguiente) o atribuirla al evento dominante. Para el modelo agregado de panel, el pagado por año calendario es aceptable siempre que los años catastróficos se traten con esta salvedad de desarrollo plurianual.

> ### Manejo de entidades fuera de los 32 estados (¿quitar o repartir?)
> Las etiquetas no-estado son de **tres tipos** y se tratan distinto — no es un "quitar vs. repartir" único:
> 1. **Typo de estado real** (`Quitana Roo` → Quintana Roo): **remapear** al estado correcto. Es la más pesada (226 siniestros / 45 M en 2014) y lleva información espacial real; quitarla o repartirla sería tirar datos.
> 2. **Fuera de México** (`Extranjero`, `No aplica (exportación)`): **excluir** — están fuera del dominio espacial/peligro mexicano; repartirlas inyectaría pérdida que no ocurrió en México.
> 3. **Mexicana sin localizar** (`NU`, `No Disponible`/`No disponible`): aquí vive la duda. Tras corregir el typo, el residuo es **diminuto** (≤1.1% del número de siniestros y <0.7% del monto pagado en cualquier año; 0% en 2021).
>
> **Recomendación: NO repartir.** Para lo no localizado, **quitar y documentar** (mantener una línea "no asignado" en la reconciliación nacional, pero fuera de las tasas por estado). El reparto proporcional es **peor** para atribución porque (a) **fabrica** estructura espacial que no está en los datos, (b) puede **embarrar** una pérdida concentrada sobre los 32 estados, y (c) la ganancia es <1%, sin justificar el riesgo del supuesto. El reparto sólo se consideraría si el residuo fuera **material** (>~5%) y se necesitara cuadrar el total nacional; aun así, se asignaría por **exposición localizada** (suma asegurada por estado-año), nunca a partes iguales ni por pérdida, y siempre como caso de **sensibilidad**.
>
> **Flujo:** normalizar `ENTIDAD` (remapear typos como `Quitana Roo`) → excluir lo extranjero → quitar-y-documentar lo no localizado → usar **sólo lo localizado** para `λ(estado)` y severidad, conservando el total nacional con su línea "no asignado" para el puente asegurado→económico. **`NU` confirmado como no localizado** (se conserva como `No Disponible`, sin asignar a estado). Todo esto está **codificado e integrado a la consolidación** en `limpieza_cnsf.py` (clasificación de entidad, vacío→NA, mapeo de perils, validación de variable de pérdida); las etiquetas no reconocidas se marcan como `desconocido` para revisión manual en vez de asignarse.

---

## 5. Fuentes de datos complementarias (URLs y acceso)

Catálogos discutidos para complementar la información de seguros. Mapeo peril→fuente en `mapa_canonico_a_fuentes.csv`.

### 5.1 Peligro (ocurrencia + localización + intensidad)
- **IBTrACS (NOAA/NCEI)** — ciclones tropicales: posición, viento máx, presión mín, radios; punto/traza, **3 h**, cuencas Pacífico Este y Atlántico. Acceso: **descarga directa CSV/netCDF, sin scraper**. https://www.ncei.noaa.gov/products/international-best-track-archive
- **HURDAT2 (NOAA/NHC)** — best track Atlántico/Pacífico, 6 h. Acceso: **archivo de texto, descarga directa**. https://www.nhc.noaa.gov/data/
- **SMN-CONAGUA** — reseñas de ciclones, avisos. Acceso: **web → scraper o manual**. https://smn.conagua.gob.mx/
- **Monitor de Sequía de México (SMN-CONAGUA)** — D0–D4, SPI, conteo municipal; municipal/polígono; **quincenal** (mensual <2014). Acceso: **shapefile/CSV por fecha (scraper útil para batch)**. https://smn.conagua.gob.mx/es/climatologia/monitor-de-sequia/monitor-de-sequia-en-mexico
- **SIH CONAGUA** — precipitación/hidrometría por estación, SPI/SDI. Acceso: **descarga CSV (scraper útil)**. https://sih.conagua.gob.mx/
- **Atlas Nacional de Riesgos (CENAPRED)** — peligro inundación/deslizamiento, índices municipales. Acceso: **geoportal/WMS (GIS)**. http://www.atlasnacionalderiesgos.gob.mx/
- **ERA5 (Copernicus CDS)** — reanálisis (precipitación, viento, temperatura) gridded. Acceso: **API `cdsapi` / Google Earth Engine**. https://cds.climate.copernicus.eu/
- **CHIRPS (UCSB)** — precipitación satelital gridded. Acceso: **descarga directa / GEE**. https://www.chc.ucsb.edu/data/chirps
- **NASA FIRMS** — fuego activo: **usar MODIS** (1 km, 2000+, cubre toda la ventana) como base; VIIRS 375 m (S-NPP 2012+, NOAA-20 2018+) sólo como cotejo, **sin empalmar series**; preferir agregación por **FRP** sobre conteo. Acceso: **API (MAP_KEY gratis) / GEE / descarga de archivo (registro gratis)**. El CSV anual por país NO sirve para el panel (pierde el estado) → agregar puntos a estado por *spatial join*. https://firms.modaps.eosdis.nasa.gov/
- **CONAFOR / SNIF** — número de incendios forestales y superficie afectada por estado (histórico **1970–2023**). Acceso: **descarga directa, libre**. https://snif.cnf.gob.mx/
- **CONABIO – Alerta Temprana de Incendios** — puntos de calor MODIS/VIIRS + áreas quemadas para México. Acceso: **portal/descarga, libre**. https://incendios.conabio.gob.mx/

### 5.2 Impacto (ocurrencia + localización + pérdida)
- **CENAPRED – Impacto socioeconómico** — daño económico total por evento, estatal/municipal, costo de reposición (metodología CEPAL); **anual**, 2000–presente. Acceso: **PDF → extracción/scraper**. Cierra la brecha asegurado→total. https://www.cenapred.gob.mx/
- **DesInventar Sentinel (UNDRR)** — pérdidas municipales por evento (incluye pequeños/recurrentes), ~1,159 eventos MX. Acceso: **export por UI (CSV/Excel) → scraper/manual**. https://www.desinventar.org/
- **EM-DAT (CRED)** — daño país/evento, con umbrales. Acceso: **cuenta gratuita, descarga xlsx (sin API abierta)**. https://public.emdat.be/
- **Declaratorias de Emergencia/Desastre (CNPC/CENAPRED)** — municipios declarados por evento, **fechado**, 2000–2023, con tipo de fenómeno (clasificación del Atlas Nacional de Riesgos). El registro dado más fino de "qué municipio, qué evento, qué fecha". Acceso: **datos abiertos CSV (CKAN)**. https://www.datos.gob.mx/busca/dataset/declaratorias-sobre-emergencia-desastre-y-contingencia-climatologica

### 5.3 Contexto (no extraíble como dato; citable)
- **NGFS** — escenarios y canales de transmisión (PDF). https://www.ngfs.net/
- **Swiss Re *sigma*** — reportes anuales de catástrofes (PDF, contexto; el servicio de datos es de pago). https://www.swissre.com/institute/research/sigma-research.html
- **World Bank — cat bonds México** — *offering circulars* (metodología de trigger; manual). https://www.worldbank.org/
- *Descartados como fuente de datos:* Munich Re NatCatSERVICE y Swiss Re sigma explorer (de pago/corporativo); Dartmouth Flood Observatory (dashboard sin API ni histórico claro). Alternativa de inundación satelital: Global Flood Database (Tellman et al. 2021, vía GEE; cobertura ~hasta 2018, verificar).

### 5.4 Orden de obtención (priorizado por relevancia en la literatura + diseño)

Ordenado por el peso que la literatura de *cat modeling*, seguro paramétrico/agrícola y atribución clima-económica da a cada insumo, y por su valor para este diseño (panel estatal anual, perils climáticos, covariables de la intensidad $\lambda$, puente asegurado→económico).

**Tier 1 — indispensables (sin esto no hay atribución):**
1. **Ciclón tropical — IBTrACS / HURDAT2.** Peril con mayores pérdidas aseguradas catastróficas en México (hidro y autos) y centro de la literatura de cat modeling y valuación de cat bonds; el *best track* es el insumo de peligro estándar. Acceso fácil (descarga directa) → **empezar aquí**.
2. **Sequía — Monitor de Sequía de México + SPI (CONAGUA/SIH).** Peril dominante del ramo agrícola y el más claramente atribuible al clima; la literatura de seguro agrícola/paramétrico se construye sobre índices de sequía (SPI, NDVI), y los esquemas catastróficos agrícolas son literalmente *index-based*.
3. **CENAPRED — Impacto socioeconómico.** Puente asegurado→económico; imprescindible para el problema de penetración que enmarca la tesis; benchmark oficial de pérdida total (metodología CEPAL).

**Tier 2 — covariables y desambiguación:**
4. **ERA5 / Copernicus (reanálisis).** *Workhorse* de la literatura de funciones de daño climático (NGFS Fase V / Kotz et al. 2024); cubre los perils sin catálogo propio (lluvia/inundación, calor, helada, viento) con precipitación, viento y temperatura gridded. Acceso: API `cdsapi`.
5. **Declaratorias (CNPC/datos.gob.mx).** Etiquetado de evento fechado y municipal; desambiguador del problema de múltiples eventos por estado-año (§7) y cross-check. Datos abiertos.
6. **DesInventar Sentinel.** Pérdida municipal por evento, incluye lo pequeño/recurrente; complemento fino del lado de impacto.

**Tier 3 — complementos / contexto:**
7. **CONAGUA SIH (estaciones).** Precipitación puntual fina; complementa ERA5/CHIRPS donde la estación importa.
8. **CHIRPS.** Precipitación satelital gridded de respaldo (parcialmente redundante con ERA5/SIH/Monitor de Sequía).
9. **CONAFOR/SNIF + FIRMS-MODIS.** Incendio/rayo; prioridad baja porque el ramo incendio quedó degradado (sólo `Rayo`; no es wildfire), aunque FRP sirve como proxy de calor/sequía.
10. **EM-DAT.** País/eventos mayores; sobre todo contexto, ya cubierto mejor por CENAPRED/DesInventar a grano fino.
11. **Atlas Nacional de Riesgos.** Capas de peligro estáticas (susceptibilidad inundación/deslizamiento); útil para vulnerabilidad/exposición, no como covariable temporal.

### 5.5 Documentos por fuente (`fuentes/`)

Cada fuente integrada tiene su propio documento markdown con la descripción, las URLs/versión, el almacenamiento crudo + procedencia, los scripts de descarga/procesamiento, los supuestos y las covariables derivadas. Esto mantiene el proceso reproducible y desacoplado.

- **`fuentes/ibtracs.md`** — Ciclón tropical (Tier 1 #1). Descarga `v04r01` (cuencas EP+NA) con procedencia y checksums; filtra a tormentas que afectaron México (buffer 100 km sobre estados INEGI); deriva covariables anuales por estado (`n_ciclones`, `viento_max_kt`, `pres_min_mb`, `cat_ss_max`, `ace`, `pdi`, `n_landfalls`). Scripts: `src/descarga_ibtracs.py`, `src/procesar_ibtracs.py`.
- **`fuentes/cenapred.md`** — Impacto socioeconómico (Tier 1 #3). Scraper con modos `sync/verificar/descargar`, log de control y procedencia; base abierta a nivel evento 2000–2015 (CSV) + resúmenes ejecutivos 2016+ (PDF, con descubrimiento de años nuevos). El procesador emite **DOS estructuras** porque la calibración de este proyecto y la de funciones de impacto CLIMADA tienen granos distintos: **A** panel `estado×año×peril` (penetración vs CNSF; multi-estado excluido y no repartido) y **B** tabla `evento×estados` (daño observado por evento, emparejable con IBTrACS por `nombre_evento`+año, para `climada.util.calibrate` al estilo Eberenz et al. 2021). Scripts: `src/descarga_cenapred.py`, `src/procesar_cenapred.py`.
- *(pendientes, mismo patrón):* `fuentes/monitor_sequia.md` (Tier 1 #2), luego ERA5, declaratorias, DesInventar…

---

## 6. Flujo de emparejamiento (ejemplo: huracán Otis, 2023)

Cuatro vías independientes que se corroboran y anclan la relación intensidad→pérdida:
1. **Peligro:** IBTrACS/HURDAT2 ubican a Otis (Pacífico Este, oct-2023, categoría 5) en Guerrero; SMN aporta la reseña.
2. **Impacto total:** CENAPRED 2023 cuantifica daños en Guerrero/Acapulco.
3. **Localización oficial:** declaratorias para Acapulco y Coyuca de Benítez (fechadas, municipales).
4. **Asegurado (CNSF):** la celda `(Guerrero, 2023)` salta en hidro/autos por causas climáticas.

La brecha CENAPRED–CNSF estima el factor de penetración asegurado→económico para ese peril/estado.

---

## 7. Múltiples eventos severos del mismo peril en un estado-año

Con resolución anual, dos eventos mayores del mismo peril en un estado caen en la misma celda. Opciones (de la recomendada a la de último recurso):
1. **(Por defecto) No separar:** la celda estado-año es la unidad; explica la pérdida anual con la **carga de peligro anual** (ACE estacional, conteo de ciclones, intensidad máxima de IBTrACS/HURDAT2). Sin supuesto de reparto, y es lo correcto para atribución climática.
2. **Reparto (si se necesita pérdida por evento):** peso por daño de CENAPRED por evento o por proxy peligro×exposición (campo de viento × valor; potencia del viento; ACE; municipios con declaratoria). Documentar regla + sensibilidad.
3. **Declaratorias como desambiguador espacial:** si los eventos golpean municipios distintos, reparten la pérdida estatal; si solapan, vuelve a (1).
4. **Robustez:** marcar esos estado-año y correr el análisis con y sin ellos.

**Doble conteo entre causas:** un mismo ciclón genera siniestros en *ciclón*, *inundación* y *deslizamiento* a la vez → **agregar las causas climáticas en un cubo hidrometeorológico** por estado-año antes de relacionarlas con el peligro.

---

## 8. Hoja de ruta metodológica (panel estatal anual, foco climático)

1. **Limpieza CNSF:** deflactar; **usar `MONTO PAGADO` como pérdida y `NÚMERO DE SINIESTROS` como frecuencia** (no `MONTO DEL SINIESTRO`, contable y con negativos — ver recuadro §4); tratar vacío como NA; **normalizar `ENTIDAD`** (remapear typos tipo `Quitana Roo`, excluir `Extranjero`/`No aplica (exportación)`, quitar-y-documentar lo no localizado — recuadro §4); homologar `MONEDA`; construir frecuencias por exposición y *loss ratios* por `estado × peril × año`; canonicalizar texto; agregar causas correlacionadas (§7).
2. **Mapeo de perils:** aplicar `mapa_perils_seguros_a_canonico.csv` para homogeneizar nombres entre ramos.
3. **Covariables de peligro:** agregar IBTrACS/HURDAT2, Monitor de Sequía, SIH/ERA5/CHIRPS a covariables anuales por estado (ACE, conteo, intensidad máx., SPI, déficit de lluvia).
4. **Frecuencia:** regresión de conteos (`NÚMERO DE SINIESTROS`) en panel (Poisson/NB con efectos de estado y año + covariables) → `λ_{año}(estado)`.
5. **Severidad:** cuerpo (lognormal/gamma) por celda sobre `MONTO PAGADO`, **acumulando los pagos de un evento sobre su ventana de desarrollo** en años catastróficos (§4); cola con CENAPRED por evento.
6. **Agregado:** modelo compuesto anual; Monte Carlo + recursión de Panjer.
7. **Puente asegurado→total:** factor de conversión vía CENAPRED por peril/estado.
8. **Aplicación financiera:** capital/ruina; valuación de trigger paramétrico tipo FONDEN bajo medida riesgo-neutral (el trigger vive sobre el catálogo de peligro fino; la resolución anual de CNSF sólo afecta la calibración de frecuencia).
9. **Atribución climática:** vincular tendencias en `λ`/severidad con covariables/escenarios (encuadre NGFS).
10. **Reproducibilidad:** versionar datos, código, supuestos; sensibilidad al umbral, a `λ(t)`, a la regla de reparto.

---

## 9. Lista breve para empezar
1. NAIC, *Catastrophe Modeling Primer* (2025). *[web]*
2. Klugman, Panjer & Willmot, *Loss Models*. *[canónico]*
3. McNeil (1997), *ASTIN Bulletin*. *[web]*
4. Burnecki (2005) / Baryshnikov et al. (2001). *[web]*
5. Cont & Tankov (2004). *[canónico]*
6. NGFS, riesgo físico (2024). *[web]*
7. CENAPRED, *Impacto socioeconómico*. *[web]*

---

## Archivos acompañantes
- **`mapa_perils_seguros_a_canonico.csv`** — homogeneización: valor crudo de cada ramo → peril canónico, con bandera de alcance climático y notas.
- **`mapa_canonico_a_fuentes.csv`** — peril canónico → fuentes externas (rol peligro/impacto, URL, variable clave, granularidad geográfica y temporal, modo de acceso).
- **`limpieza_cnsf.py`** — módulo de limpieza para la consolidación: clasificación/normalización de `ENTIDAD` (typos → estado; excluir extranjero y no localizado), vacío→NA (columnas tardías), validación de variable de pérdida, canonicalización de `PRIMERA LÍNEA DE MAR`, y mapeo de causa/tipo de evento → peril canónico vía el CSV de arriba.
- **`fuentes/ibtracs.md`** + **`src/descarga_ibtracs.py`**, **`src/procesar_ibtracs.py`**, **`src/campo_viento.py`** — fuente IBTrACS (ciclón tropical, Tier 1): descarga con procedencia, filtro a México, covariables `λ(estado, año)` y campo de viento opcional (Holland 1980, sin CLIMADA). Ver §5.5.
- **`fuentes/cenapred.md`** + **`src/descarga_cenapred.py`**, **`src/procesar_cenapred.py`** — fuente CENAPRED (impacto socioeconómico, Tier 1): scraper con sync/verificar/descargar, log y procedencia; salidas A (panel estado×año×peril) y B (eventos para calibración CLIMADA). Ver §5.5.

## Changelog
- **v0.18 (2026-06-11):** procesamiento CENAPRED robustecido con el log de la corrida real completa. (1) **Catálogo de códigos del crudo cerrado** (4,246 sin-mapeo → 1 regla): HIDRO `BT/TS/TE/FV/INUND/MT/MF/OC` mapeados a clima=sí; **`QUIM|IF` = 504 incendios forestales clima=sí** (trampa LGPC confirmada); fallback automático QUIM/SOCIO/SAN→fuera-de-alcance con etiqueta legible (silencioso), aviso ruidoso reservado a HIDRO/GEO desconocidos. (2) Separador de estados por coma y conjunción **"y"/"e"**; typo `Chichuahua`→Chihuahua; `Varios estados`/`Todo el pais`→no localizado. (3) Fechas `SD`→NA limpio. (4) Nombre de ciclón buscado en Observaciones **y Descripción** (`nombre_origen`); CT sin nombre contados para empalme por fechas+estados. (5) **Nuevo `catalogo_fenomenos_climaticos.csv`**: ocurrencia (evento×estado) con año/mes/fechas/peril/nombre/municipios y daño como total de evento etiquetado (no repartido). (6) Plantilla de captura de extensos alineada (mes, fecha_inicio/fin, municipios) para alimentar el mismo catálogo. Probado end-to-end con los casos reales del log.
- **v0.17 (2026-06-11):** `procesar_cenapred.py` reconstruido contra el **encabezado real del CSV** (24 columnas confirmadas por el usuario): dos fechas (inicio/fin → `duracion_dias`, texto crudo conservado para rangos textuales de sequías), `Clasificacion del fenomeno`=nivel 1 vs `Tipo de fenomeno`=subtipo (el mapeo de perils opera sobre el subtipo), **nombre del ciclón extraído de `Observaciones` por regex** (incl. depresiones numeradas "Once-E"; sin falsos positivos sobre menciones genéricas) para el empalme B↔IBTrACS, columnas `Sustancia involucrada`/`Documentado` conservadas en B, y lectura con **utf-8 estricto → fallback latin1 con aviso** (codificación real del archivo; se elimina el `errors="replace"` que ocultaba mojibake). Probado end-to-end con encabezado real y latin1.
- **v0.16 (2026-06-11):** versión final del scraper CENAPRED tras corrida real exitosa (CSV + extensos 2000–2021 descargados con procedencia; el descubrimiento del índice olmeca recuperó también los extensos 2000–2015). Cierre del inventario: **extenso 2023 = `517-IMPACTO_SOCIOECONOMICO_2023.PDF`** y extenso 2022 reapuntado a gob.mx (URLs verificadas por el usuario) → serie 2016–2023 completa, hueco solo 2024. Robustez nueva: **fallback automático entre dominios espejo** (gob.mx/unam.mx/olmeca; cada uno bloquea rutas distintas con 403), corte temprano de reintentos en errores definitivos (403/404/410), y registro de `url_efectiva` en `_procedencia.json`.
- **v0.15 (2026-06-11):** corrección de descarga CENAPRED tras corrida real del usuario (`CERTIFICATE_VERIFY_FAILED` en macOS): el script ahora usa **certifi** automáticamente si está instalado, da sugerencia accionable en el log, corta los reintentos en errores de certificado (reintentar no los resuelve), y añade la bandera explícita **`--inseguro`** para cadenas de certificados incompletas de servidores de gobierno — con advertencia prominente y compensación de integridad vía sha256 (`--modo verificar`). Nota de solución de problemas en `fuentes/cenapred.md` §7.
- **v0.14 (2026-06-11):** CENAPRED 2016+ resuelto. **Serie de documentos extensos 2016–2023 disponible** (hueco real: solo 2024; extenso 2023 confirmado por el usuario, URL por registrar — el `sync` lo descubrirá) (URLs verificadas por el usuario para 2016–2021, incl. `384-IMPACTO2016OEFINAL…` y `415-IMPACTO_SOCIOECONOMICO_2017`; 2022 del índice Apache de olmeca, que el modo `sync` ahora scrapea para descubrir años/extensos nuevos). Diagnóstico del problema de asignación: los totales estatales de los resúmenes **mezclan perils** (CDMX 2017 = sismo) y desde 2019 son **porcentajes con residuo "otros"** → solo el grano evento/fenómeno es utilizable; el sismo queda fuera vía `en_alcance_climatico`. **Decisión de extracción: captura manual estructurada** (no parser automático; diseños cambian por año y los errores silenciosos en montos son inaceptables): esquema fijo + procedencia por página + validación contra cifras de control (`plantillas/captura_extenso_PLANTILLA.csv`, `src/procesar_captura_extensos.py`, falla ruidosa >5%). Taxonomía de empate extensos↔CSV 2000–2015 documentada (clima por SUBTIPO: deslizamiento sí aunque GEO; incendio forestal sí aunque químico-tec; COVID fuera). Noticias descartadas como fuente de montos; validación cruzada con DesInventar/EM-DAT. Ver `fuentes/cenapred.md` §2 y §6bis.
- **v0.13 (2026-06-11):** fuente **CENAPRED** integrada (Tier 1 #3). `src/descarga_cenapred.py` (modos sync/verificar/descargar, log `_log_cenapred.log`, `_procedencia.json` con sha256, descubrimiento de PDFs anuales nuevos) y `src/procesar_cenapred.py` (validación de encabezados contra mapa de conceptos con falla ruidosa; números con miles; entidades vía `limpieza_cnsf`; perils CENAPRED→canónico con `__SIN_MAPEO__` a revisión). **Dos estructuras de salida** por diferencia de grano con la rama CLIMADA: A panel `estado×año×peril` (multi-estado NO repartido → `impacto_multiestado.csv`) y B `evento×estados` para `climada.util.calibrate` (multi-estado conservado como un registro; empalme con IBTrACS por `nombre_evento`+año). Nuevo `fuentes/cenapred.md` con URLs verificadas (CSV abierto 2000–2015; resúmenes ejecutivos 2016+), cifras de control 2022–2024 y supuestos referenciados (CEPAL DaLA; Eberenz et al. 2021).
- **v0.12 (2026-06-05):** `construir_malla` (campo de viento) ahora **garantiza ≥1 nodo por estado**: las entidades pequeñas sin centro de celda dentro (p. ej. **Ciudad de México** con malla 0.5°) reciben su punto representativo interior, completando el panel `estado×año` sin refinar toda la malla. Era artefacto de discretización, no error de medición ni de nombres.
- **v0.11 (2026-06-05):** campo de viento mejorado y evaluado. (1) Perfil de Holland **anclado a `Vmax`** (corrige sobreestimación interior por presión vieja/`B` recortado). (2) **Decaimiento sobre tierra de Kaplan & DeMaria (1995)** como bandera `--decaimiento-tierra` (R=0.9, Vb=26.7, α=0.095; `min` con best-track, solo reduce). (3) Bandera `--anio-inicial` (p. ej. 2005) que recorta tormentas y baja mucho el costo. (4) `fuentes/ibtracs.md` §9.2 (K&D) y §9.3 (**evaluación empírica Otis 2023**: el buffer sobreestima intensidad local —85 kt a Michoacán/Edomex vs ~60 kt del campo de viento—; Otis solo tocó 3 estados, los lejanos del panel 2023 son otras tormentas; recomendación de usar campo de viento umbralizado por `celdas_ge34kt`).
- **v0.10 (2026-06-05):** rutina de campo de viento (`src/campo_viento.py`, Holland 1980 sin CLIMADA; backend climada opcional) con banderas `--campo-viento`, `--paso-temporal-min`, `--granularidad-malla`, `--backend`.
- **v0.9 (2026-06-05):** `fuentes/ibtracs.md` §9 costo/beneficio del campo de viento.
- **v0.8 (2026-06-05):** cada supuesto/covariable de `fuentes/ibtracs.md` con referencia real; buffer 100 km como aproximación a calibrar; §10 referencias.
- **v0.7 (2026-06-05):** inicio del Tier 1 con **IBTrACS**; scripts de descarga/procesamiento; §5.5 documentos por fuente.
- **v0.6:** `NU`=no localizado; limpieza en `limpieza_cnsf.py`; §5.4 orden priorizado de fuentes.
- **v0.5:** continuidad de 2021 en siniestros; entidades no-estado (no repartir).
- **v0.4:** quiebres 2015/2021 = granularidad; regla `MONTO PAGADO`/`NÚMERO DE SINIESTROS`; vacío=NA.
- **v0.3:** taxonomía de perils; incendio→`Rayo`; riego/temporal; esquema catastrófico vs comercial; hidro `COBERTURA` no es peril; autos causa 2016+; capítulo de fuentes; CSV de mapeo.
- **v0.2:** exclusión de geofísicos; catálogos peligro/impacto; ejemplo Otis; múltiples eventos; nivel vs resolución.
- **v0.1:** versión inicial.
- **v0.9 (2026-06-05):** `fuentes/ibtracs.md` §9 nueva — **costo/beneficio de refinar con campo de viento** (CLIMADA/TCE-DAT/Holland): la ganancia está acotada por la resolución anual-estatal de la pérdida (pequeña para frecuencia, moderada para severidad, grande para valuación de trigger); mitigaciones de costo y recomendación de comparar empíricamente buffer vs. campo de viento.
- **v0.8 (2026-06-05):** `fuentes/ibtracs.md` ahora **respalda cada supuesto de procesamiento y cada covariable con una referencia real y validable** (ACE → Bell et al. 2000; PDI/v³ → Emanuel 2005; presión mínima como predictor de daño → Klotzbach et al. 2020; categoría → Simpson 1974; daño ~potencia del viento → Nordhaus 2010 / Pielke et al. 2008; *landfall* → Pielke & Landsea 1998). El **buffer de 100 km** se documenta explícitamente como aproximación pragmática (no citada) al radio de vientos ≥34 kt, con el campo de viento (Holland 1980; TCE-DAT, Geiger et al. 2018; CLIMADA, Aznar-Siguan & Bresch 2019) como refinamiento riguroso y parámetro a sensibilizar. Nueva §10 de referencias en el documento de fuente.
- **v0.7 (2026-06-05):** inicio del Tier 1 con **IBTrACS**; `fuentes/ibtracs.md` + scripts `src/descarga_ibtracs.py` y `src/procesar_ibtracs.py`; §5.5 documentos por fuente; patrón `datos/datos_IBTrACS/{crudos,consolidados}`.
- **v0.6:** `NU`=no localizado; limpieza codificada en `limpieza_cnsf.py`; §5.4 orden priorizado de fuentes.
- **v0.5:** continuidad de 2021 en siniestros; manejo de entidades no-estado (no repartir).
- **v0.4:** quiebres 2015/2021 resueltos como granularidad; regla `MONTO PAGADO`/`NÚMERO DE SINIESTROS`; vacío=NA.
- **v0.3:** taxonomía de perils; incendio→`Rayo`; riego/temporal; esquema catastrófico vs comercial; hidro `COBERTURA` no es peril; autos causa 2016+; capítulo de fuentes; CSV de mapeo.
- **v0.2:** exclusión de geofísicos; catálogos peligro/impacto; ejemplo Otis; múltiples eventos; nivel vs resolución.
- **v0.1:** versión inicial.

*Documento vivo. Pendientes: confirmar ediciones/DOIs de textos canónicos; tipo de cambio (Banxico) para normalizar `MONEDA`; localizar valor exacto que separa SIPAC en autos; cobertura del Global Flood Database. Registrar cambios en git.*

## Related
[[HAZ_MOC]] · Home: [[_INDEX]]

#arm/haz #type/theory
