# Fuente de datos: IBTrACS (ciclones tropicales) — Tier 1

**Peril canónico:** Ciclón tropical (y, vía marejada, exposición costera).
**Rol:** peligro (hazard) — provee las covariables de intensidad para `λ(estado, año)`.
**Estado:** scripts construidos; descarga real pendiente de correr en la máquina del usuario.
**Documento principal:** ver `referencias_riesgo_catastrofico.md` (§5.4 prioriza esta fuente como Tier 1 #1).

---

## 1. Qué es y por qué es Tier 1

IBTrACS (*International Best Track Archive for Climate Stewardship*) es el archivo global de *best tracks* de ciclones tropicales de la NOAA/NCEI, avalado por la OMM. Es el insumo de peligro **estándar** en la literatura de *cat modeling* y valuación de cat bonds, y el ciclón tropical es el peril con mayores pérdidas aseguradas catastróficas en México (ramos hidro y autos). Por eso es la primera fuente a integrar.

México está expuesto por **dos cuencas**: Pacífico Este (`EP`) y Atlántico Norte (`NA`); se usan ambos subconjuntos.

## 2. Fuente, versión y cita

- **Versión fijada:** `v04r01` (Versión 4.01). Fijar la versión es parte de la reproducibilidad.
- **CSV (acceso):** `https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/v04r01/access/csv/`
  - `ibtracs.EP.list.v04r01.csv` (Pacífico Este)
  - `ibtracs.NA.list.v04r01.csv` (Atlántico Norte)
- **Documentación de columnas:** `.../v04r01/doc/IBTrACS_v04r01_column_documentation.pdf`
- **DOI del dataset:** `10.25921/82ty-9e16`
- **Cita:** Knapp, K. R., M. C. Kruk, D. H. Levinson, H. J. Diamond y C. J. Neumann (2010). *The International Best Track Archive for Climate Stewardship (IBTrACS): Unifying tropical cyclone best track data.* BAMS 91, 363–376.
- **Acceso:** descarga directa HTTP (sin API key, sin scraper). Actualizado ~3 veces por semana; al fijar versión + fecha + sha256 la corrida es reproducible.

## 3. Almacenamiento robusto y procedencia

Se conserva el **crudo intacto** para poder reproducir todo desde cero:

```
datos/datos_IBTrACS/
  crudos/                              # NUNCA se modifica
    ibtracs.EP.list.v04r01.csv
    ibtracs.NA.list.v04r01.csv
    _procedencia.json                  # URL, versión, fecha UTC, sha256, bytes
  consolidados/
    ciclones_mexico_puntos.csv         # puntos de trayectoria que afectaron México
    covariables_ciclon_estado_anio.csv # PANEL estado x año -> alimenta λ
```

`_procedencia.json` (lo genera `descarga_ibtracs.py`) registra para cada archivo la URL, el `sha256` y el tamaño, más versión, DOI, cita y fecha de descarga. Así cualquiera puede verificar que el crudo no cambió y re-derivar los consolidados.

## 4. Scripts

- **`src/descarga_ibtracs.py`** — baja los CSV de EP y NA a `crudos/`, idempotente (no rebaja si ya existen, salvo `--force`), y escribe `_procedencia.json` con checksums. Solo stdlib (`urllib`).
- **`src/procesar_ibtracs.py`** — lee crudos → filtra a México → atribuye a estados → calcula covariables. Funciones:
  - `leer_crudo` / `cargar_crudos`: lee saltando la **fila de unidades** (índice 1), coacciona numéricos, parsea `ISO_TIME`, concatena EP+NA y **deduplica por `(SID, ISO_TIME)`** (una tormenta que cruza de cuenca aparece en ambos subconjuntos).
  - `preparar`: viento en nudos, categoría Saffir-Simpson, marca de punto sinóptico, filtro de naturaleza.
  - `atribuir_estados`: *spatial join* con buffer (geopandas).
  - `covariables_estado_anio`: agrega el panel del baseline (buffer).
  - **Campo de viento opcional** (bandera `--campo-viento`): ver §9.
- **`src/campo_viento.py`** — modelo paramétrico de Holland (1980) **sin CLIMADA** (solo numpy + geopandas): `viento_holland_kt`, `parametro_holland_B`, `estimar_rmax_km`, `interpolar_traza`, `construir_malla`, `footprint_tormenta`, `covariables_campo_viento`; `disponible_climada()` para el backend opcional.

## 5. Supuestos de procesamiento (cada uno con su referencia)

1. **Cuencas EP + NA**, deduplicadas por `(SID, ISO_TIME)`. *Base:* IBTrACS define los subconjuntos por cuenca como "todas las tormentas con ≥1 posición en esa cuenca", de modo que una que cruza aparece en ambos (Knapp et al., 2010).
2. **"Afectó directamente a México" y el buffer de 100 km.** Un punto se atribuye a un estado si cae **dentro del polígono o dentro de un buffer** (default **100 km**). **Honestidad sobre el valor:** 100 km **no proviene de un artículo específico**; es una **aproximación pragmática** al radio de los vientos con fuerza de tormenta tropical (≥34 kt), que es como la literatura define la huella de afectación. El enfoque **riguroso** es un **modelo paramétrico de campo de viento** (Holland, 1980), usado por los datasets de exposición a ciclón —TCE-DAT estima áreas expuestas a >34, 64 y 96 kt (Geiger, Frieler & Bresch, 2018)— y por la plataforma abierta **CLIMADA** (Aznar-Siguan & Bresch, 2019). Se eligió un **buffer fijo** como default robusto porque los **radios de viento históricos son muy inciertos** (Klotzbach et al., 2020), lo que hace poco fiable una huella variable en años antiguos. **Decisión:** tratar 100 km como **parámetro a calibrar/sensibilizar** (`--buffer-km`) y migrar a un campo de viento (TCE-DAT/CLIMADA) como refinamiento; el umbral de 34 kt para "afectación" sigue la convención de TCE-DAT.
3. **Naturaleza:** se conservan sistemas **tropicales y subtropicales** (`NATURE ∈ {TS, SS}`); se excluyen extratropicales/perturbaciones para no inflar la actividad. *Base:* la métrica ACE solo acumula mientras el sistema es de fuerza de tormenta tropical o mayor (Bell et al., 2000).
4. **Viento:** `WMO_WIND` (nudos) y, donde falte, `USA_WIND`; **presión:** `WMO_PRES` (mb); celdas vacías = NA. *Base:* documentación de columnas IBTrACS v04r01 (Knapp et al., 2010); los faltantes se almacenan como celdas en blanco.
5. **Categoría Saffir-Simpson** derivada del **viento** (transparente, reproducible), no del código `USA_SSHS`: <34 kt = depresión (−1); 34–63 = TT (0); 64–82 = 1; 83–95 = 2; 96–112 = 3; 113–136 = 4; ≥137 = 5. *Base:* escala de Simpson (1974).
6. **ACE** solo sobre puntos **sinópticos** (00/06/12/18 UTC) con viento ≥ 34 kt. *Base:* definición de ACE de Bell et al. (2000) — suma de cuadrados del viento sostenido a intervalos de 6 h mientras el sistema es ≥34 kt, dividida entre 10⁴.
7. **Año** = `SEASON`. La ventana de análisis se alinea con CNSF (2008–2024), aunque el panel puede generarse para todo el histórico como contexto.

## 6. Covariables para `λ(estado, año)` (panel de salida)

Por cada par **(entidad, año)** sobre los puntos atribuidos:

| Covariable | Definición | Referencia que respalda su uso |
|---|---|---|
| `n_ciclones` | nº de tormentas distintas (`SID`) con ≥1 punto atribuido | Bell et al. (2000) — la actividad integra frecuencia |
| `n_puntos` / `horas_exposicion` | nº de puntos atribuidos (×6 h) | Bell et al. (2000); Emanuel (2005) — ambos integran duración |
| `viento_max_kt` | viento sostenido máximo | Simpson (1974); Nordhaus (2010) — daño escala con potencia alta del viento |
| `pres_min_mb` | presión central mínima | **Klotzbach et al. (2020)** — MSLP es mejor predictor de daño normalizado que el viento |
| `cat_ss_max` | categoría Saffir-Simpson máxima | Simpson (1974); Pielke et al. (2008) |
| `ace` | Σ (v² / 10⁴) en puntos sinópticos con v≥34 kt | **Bell et al. (2000)** — definición de ACE |
| `pdi` | Σ v³ (v≥34 kt) | **Emanuel (2005)** — PDI; el daño potencial escala ~v³ |
| `n_landfalls` | nº de puntos con `LANDFALL == 0` | Pielke & Landsea (1998); Pielke et al. (2008) — daño normalizado por *landfall* |

El uso de estas como **covariables de la intensidad `λ`** se apoya en que ACE y PDI son las métricas estándar de actividad y destructividad (Bell et al., 2000; Emanuel, 2005), que `pdi` escala con el daño potencial (Emanuel, 2005) y que la presión mínima es el mejor predictor empírico de daño normalizado (Klotzbach et al., 2020). El proceso de Cox/doblemente estocástico que las consume está referenciado en §2.D del documento principal. `pdi` es la más ligada a daño; `n_ciclones`/`ace` capturan la carga de actividad anual (clave para el problema de **múltiples eventos por estado-año**, §7 del documento principal: una temporada con dos eventos severos se refleja en `ace`/`pdi` altos sin necesidad de repartir).

## 7. Dependencias y datos externos

- **Python:** `pandas`; `geopandas` + `shapely` solo para la atribución espacial (importados dentro de la función para no acoplar).
- **Capa de estados:** shapefile/geojson de las 32 entidades. **Recomendado:** Marco Geoestadístico de **INEGI** (oficial); alternativas: GADM, Natural Earth. Se pasa como parámetro `--estados`; no se descarga aquí para no acoplar fuentes. La columna de nombre de entidad se indica con `col_estado` (p. ej. `NOMGEO` en INEGI) y debe normalizarse con `limpieza_cnsf.clasificar_entidad` para empatar con la base CNSF.
- **CRS:** se reproyecta a EPSG:6372 (cónica conforme de Lambert para México) para que el buffer en km sea métricamente correcto.

## 8. Limitaciones / notas

- **Heterogeneidad histórica:** la calidad/observación de *best tracks* mejora con el tiempo (era satelital). Para tendencias de largo plazo, considerar esta heterogeneidad (igual que con sensores en FIRMS); para 2008–2024 es razonablemente homogénea.
- **Atribución por buffer fijo** sobreestima/subestima la huella real frente a un campo de viento; ver §9 para el análisis de costo/beneficio del refinamiento con campo de viento.
- **Un punto puede atribuirse a varios estados** (buffers solapados) — es intencional (un ciclón afecta varios estados); las covariables se calculan por estado independientemente.
- El sandbox de desarrollo bloquea `ncei.noaa.gov`; la descarga se valida en la máquina del usuario.

## 9. Refinamiento con campo de viento: ¿cuánto se gana? (costo vs. beneficio)

El buffer fijo (§5.2) asigna afectación de forma **binaria e isotrópica**: un estado "se afecta" si un punto de trayectoria cae a ≤100 km, sin importar el tamaño de la tormenta, la asimetría, la velocidad de avance ni el decaimiento radial del viento. Un campo de viento (Holland, 1980; CLIMADA, Aznar-Siguan & Bresch, 2019; TCE-DAT, Geiger et al., 2018) sustituye eso por el **viento modelado en cada ubicación**, lo que permite (a) usar la intensidad **local** experimentada en el estado y no el pico de la tormenta "cerca", (b) capturar el **tamaño** del sistema, y (c) **ponderar por exposición** integrando el viento sobre una malla de población/activos — la entrada teóricamente correcta a una función de daño.

**Principio clave: la ganancia está acotada por la resolución de la PÉRDIDA, no del peligro.** La pérdida CNSF es **anual, estatal y agregada**; el campo de viento aporta precisión sub-estatal, sub-diaria y ponderada por exposición que la respuesta **no puede resolver**. Por eso la ganancia es muy desigual:

| Componente | Ganancia esperada | Razón |
|---|---|---|
| **Frecuencia** (panel estado×año) | **Pequeña** | El grano anual/estatal lava la diferencia; un evento mayor marca el estado con ambos métodos. La mejora se limita a casos de borde (estados rozados) y al efecto del tamaño de la tormenta. |
| **Severidad** (magnitud) | **Moderada — la más valiosa** | La pérdida escala con potencia alta del viento *local* (Emanuel, 2005; Nordhaus, 2010); el buffer no distingue impacto directo de roce. La ponderación por exposición es el upgrade metodológico mayor. |
| **Valuación de trigger paramétrico** | **Grande / casi necesaria** | Reduce el **riesgo base** del trigger (disparo vs. pérdida real); es la aplicación donde el campo de viento sí justifica el costo completo. |

**Costo y cómo contenerlo.** El costo de CLIMADA escala con **densidad de malla × pasos de tiempo × nº de tormentas**; a granularidad fina es prohibitivo (experiencia del usuario). Mitigaciones que preservan la mejora útil para un panel estatal:
- Calcular el viento solo en un **puñado de puntos por estado** (centroide ponderado por población/exposición), no en una malla nacional densa.
- O malla **gruesa** (0.25–0.5°) agregada a estados.
- Restringir a tormentas que **afectaron México** (ya hecho) y a la ventana **2008–2024**.
- **Cachear** los campos por tormenta (son estáticos) para abaratar re-corridas.
- Reutilizar **TCE-DAT** precomputado (Geiger et al., 2018; extensión hasta 2020 disponible a solicitud) para el histórico, en vez de regenerar.

**Recomendación (camino intermedio, medible).** Mantener el buffer como **baseline** robusto y barato; añadir una capa **opcional** de campo de viento en centroides estatales ponderados por exposición que produzca `viento_local_max`, `viento_local_pond_exp` y ACE/PDI ponderados; y **comparar empíricamente** (validación cruzada) si cambian el ajuste de `λ`/severidad. Así "cuánto se gana" se responde con datos, no por afirmación: si no mejora la frecuencia (lo más probable), se reserva el campo de viento para severidad y para el trigger. Documentar la decisión y la métrica de comparación en el changelog del documento principal.

### 9.1 Implementación (bandera `--campo-viento`)

**¿Requiere CLIMADA? No.** El campo de viento se implementa en `src/campo_viento.py` con el perfil paramétrico de **Holland (1980)** directo desde las ecuaciones (solo `numpy` + `geopandas`, ya dependencias). CLIMADA es, en su núcleo, una implementación de estos mismos modelos paramétricos; por eso no es necesario instalar toda su pila. Se ofrece además `--backend climada` para quien ya lo tenga (refinamientos: Holland 2008, asimetría por traslación, decaimiento sobre tierra), pero el default `holland` es transparente y reproducible.

**Cómo se calcula (backend `holland`):**
1. `construir_malla` arma una malla regular de `granularidad_malla`° sobre el bbox de México y se queda con las celdas cuyo centro cae dentro de algún estado (sjoin), etiquetadas por entidad. **Estados pequeños sin centro de celda dentro** (p. ej. **Ciudad de México**, la entidad más chica, con malla 0.5°) reciben su **punto representativo interior** (`representative_point()`), garantizando ≥1 nodo por estado y un panel `estado×año` completo sin tener que refinar toda la malla nacional.
2. `interpolar_traza` remuestrea cada tormenta que afectó México al `paso_temporal_min` (interpolación lineal en tiempo de lat/lon/viento/presión).
3. `viento_holland_kt` calcula, en cada celda y para cada punto de traza, el viento sostenido en superficie (perfil de gradiente de Holland 1980; B de Holland; reducción gradiente→superficie ~0.9). `footprint_tormenta` toma el **máximo por celda** a lo largo de la vida de la tormenta.
4. `covariables_campo_viento` agrega por **(entidad, año)**: `viento_local_max_kt`, `viento_local_p95_kt`, `celdas_ge34/64/96kt` (extensión de exposición, umbrales de Geiger et al. 2018), `n_ciclones_local` y `pdi_local` (Σ sobre tormentas del máximo local³). Salida: `consolidados/covariables_ciclon_estado_anio_campoviento.csv`.

**Parámetros (como pediste):**
- `--campo-viento` — activa el cálculo (por defecto **no** se hace; el baseline es el buffer).
- `--paso-temporal-min` — paso de interpolación de la traza (p. ej. `60`, `30`, `15`). Más fino = más puntos = más costo.
- `--granularidad-malla` — resolución de la malla en grados (p. ej. `0.5` → 0.5°×0.5°). Más fina = más celdas = más costo.
- `--decaimiento-tierra` — aplica el decaimiento sobre tierra de **Kaplan & DeMaria (1995)** (ver §9.2).
- `--anio-inicial` — descarta tormentas anteriores a ese año (p. ej. `2005`); **reduce mucho** el nº de eventos a procesar (el costo del campo de viento escala con el nº de tormentas). Empata con la ventana del resto de fuentes.
- `--backend holland|climada`.

**Nota de modelo (anclaje a Vmax).** El perfil se **ancla a `Vmax`** (pica en `Vmax` en `Rmax` y decae con la distancia), en lugar de gobernarse por el déficit de presión. Esto corrige una sobreestimación interior: con presión vieja o `B` recortado, un perfil gobernado por presión se quedaba demasiado fuerte tierra adentro. Como el `Vmax` de best-track ya es viento de superficie, no se aplica reducción adicional. (Versión sin término de Coriolis ni asimetría por traslación; refinamientos documentados, presentes en el backend CLIMADA.)

### 9.2 Decaimiento sobre tierra — Kaplan & DeMaria (1995)

Con `--decaimiento-tierra`, el `Vmax` sobre tierra se decae según `V(t) = Vb + (R·V0 − Vb)·exp(−α·t)`, con `V0` = intensidad en *landfall*, `t` = horas desde *landfall*, y coeficientes de EE.UU. `R=0.9`, `Vb=26.7 kt`, `α=0.095 h⁻¹` (Kaplan & DeMaria, 1995). El *landfall* se detecta con `DIST2LAND ≤ 1 km`; al volver al mar se reinicia. Se usa `vmax_efectivo = min(Vmax_besttrack, V_KD)` — solo puede **reducir**, nunca inflar (evita doble conteo si el best-track ya viene debilitado). **Honestidad:** los coeficientes son de EE.UU.; para México no hay valores establecidos (parámetro a revisar). Para best-track histórico el decaimiento parcialmente solapa el debilitamiento ya observado, por eso se aplica como reducción conservadora; es más relevante aún para trazas sintéticas. El propio IWDM de K&D tiende a sobrestimar ~11 kt según sus autores, así que tómese como tempering, no como verdad.

**Costo.** ≈ `nº tormentas × nº puntos de traza (tras interpolar) × nº celdas`. Las palancas son `--paso-temporal-min`, `--granularidad-malla` y sobre todo `--anio-inicial` (recorta tormentas). El cálculo está vectorizado por celdas. Para un panel estatal, malla 0.25–0.5°, paso 60 min y `--anio-inicial 2005` suelen bastar; afinar solo si la comparación empírica (§9) lo justifica.

**Datos faltantes / supuestos del modelo (con su referencia):** `Rmax` se toma de `USA_RMW` si existe; si no, una **estimación empírica documentada** (placeholder a calibrar; los radios históricos son muy inciertos — Klotzbach et al. 2020). `B` se deriva de `Vmax`/Δp (Holland 1980). Decaimiento sobre tierra: Kaplan & DeMaria (1995). Umbrales de exposición 34/64/96 kt: Geiger et al. (2018). Asimetría por traslación: no en el default (refinamiento; sí en CLIMADA).

### 9.3 Evaluación empírica: buffer vs. campo de viento (Otis 2023)

Comparación sobre los datos reales procesados (huracán Otis, SID `2023294N09264`, y la temporada 2023):

- **Otis NO afecta estados lejanos.** Por evento (archivo de puntos), Otis tocó solo **Guerrero, Michoacán y Estado de México** (contiguos). Los estados lejanos que aparecen en el **panel anual 2023** (Quintana Roo, Yucatán, Tamaulipas, Nuevo León, Baja California…) son de **otras tormentas** de 2023 (Harold en el NE, Idalia en la península, Lidia/Norma en occidente, Hilary en Baja). El panel anual agrega todas las tormentas (correcto para `λ(estado, año)`); para atribución por evento se usa el archivo de puntos por `NAME`.
- **Defecto real del buffer (intensidad, no geografía):** asigna a cada estado la **intensidad de la tormenta en el punto de traza más cercano**, no el viento local. Otis → Michoacán/Edomex con **85 kt**; el campo de viento da ahí **~59–60 kt** locales con **0 celdas ≥64 kt**. El buffer confunde "el centro pasó a <100 km" con "aquí sopló esa intensidad".
- **El campo de viento NO tiene menos filas** (31 estados en 2023 vs. 19 del buffer): calcula un viento en cada estado. Lo que lo hace utilizable como panel limpio son las **columnas de umbral** (`celdas_ge34/64/96kt`), que permiten definir "afectado" por exposición real. El formato "panel" no distingue buffer de campo de viento (ambos tienen su panel `estado×año`); lo desordenado es el archivo de **puntos**.
- **Captura bien el golpe real:** Guerrero 2023 = **129 kt** local máx, 11 celdas ≥64 kt, 4 ≥96 kt (consistente con la catástrofe de Otis). La diferencia 129 vs. 145 (valor puntual) es **suavizado de malla** (0.5°≈55 km y un Otis muy compacto); una malla más fina en la zona de impacto lo recupera.
- **Caveat de interior (motiva §9.2):** sin decaimiento, valores interiores (p. ej. Zacatecas 60 kt de Lidia) quedaban sobreestimados; el anclaje a `Vmax` y `--decaimiento-tierra` (Kaplan & DeMaria 1995) los temperan.

**Recomendación operativa:** usar el panel de campo de viento **umbralizado** (`celdas_ge34kt ≥ 1` define "afectado"; `viento_local_max_kt`/`pdi_local`/`celdas_ge64kt` como covariables), con `--decaimiento-tierra` activado; conservar el buffer como chequeo de robustez; y recortar a 2008–2024 (vía `--anio-inicial`).

## 10. Reproducibilidad (resumen)

1. `python src/descarga_ibtracs.py` → crudos + `_procedencia.json` (versión v04r01 fija, checksums).
2. `python src/procesar_ibtracs.py --estados <ruta_INEGI> --buffer-km 100` → consolidados (baseline).
   - Opcional, campo de viento: `... --campo-viento --anio-inicial 2005 --paso-temporal-min 60 --granularidad-malla 0.5 --decaimiento-tierra --backend holland`
3. Versionar en git los scripts, este documento y `_procedencia.json` (no los crudos pesados; basta el manifiesto con sha256 para verificar). Registrar cualquier cambio de versión de IBTrACS o de buffer en el changelog del documento principal.

## 11. Referencias

Verificadas en web salvo donde se indica *[clásico — confirmar DOI]*.

- **Knapp, K. R., M. C. Kruk, D. H. Levinson, H. J. Diamond & C. J. Neumann (2010).** The International Best Track Archive for Climate Stewardship (IBTrACS): Unifying tropical cyclone best track data. *BAMS* 91, 363–376. (Dataset DOI 10.25921/82ty-9e16.) — fuente IBTrACS, estructura por cuenca, columnas.
- **Bell, G. D., et al. (2000).** Climate Assessment for 1999. *Bulletin of the American Meteorological Society* 81(6). — definición de **ACE** (Σ viento² a 6 h, ≥34 kt, /10⁴). *[clásico — confirmar volumen/páginas]*
- **Emanuel, K. (2005).** Increasing destructiveness of tropical cyclones over the past 30 years. *Nature* 436, 686–688. DOI 10.1038/nature03906. — **PDI** (Σ v³) como destructividad; el daño potencial escala ~v³.
- **Klotzbach, P. J., M. M. Bell, S. G. Bowen, E. J. Gibney, K. R. Knapp & C. J. Schreck (2020).** Surface Pressure a More Skillful Predictor of Normalized Hurricane Damage than Maximum Sustained Wind. *BAMS* 101(6), E830–E846. DOI 10.1175/BAMS-D-19-0062.1. — **MSLP** mejor predictor de daño que viento (r=0.77 vs 0.66); radios de viento muy inciertos.
- **Geiger, T., K. Frieler & D. N. Bresch (2018).** A global historical data set of tropical cyclone exposure (TCE-DAT). *Earth System Science Data* 10, 185–194. DOI 10.5194/essd-10-185-2018. — exposición a ciclón con campo de viento (umbrales 34/64/96 kt); base del enfoque de huella.
- **Aznar-Siguan, G. & D. N. Bresch (2019).** CLIMADA v1: a global weather and climate risk assessment platform. *Geoscientific Model Development* 12, 3085–3097. DOI 10.5194/gmd-12-3085-2019. — plataforma abierta de impacto con campo de viento (refinamiento del buffer).
- **Kaplan, J. & M. DeMaria (1995).** A simple empirical model for predicting the decay of tropical cyclone winds after landfall. *Journal of Applied Meteorology* 34, 2499–2512. — decaimiento sobre tierra (`--decaimiento-tierra`); coeficientes de EE.UU. R=0.9, Vb=26.7 kt, α=0.095 h⁻¹.
- **Holland, G. J. (1980).** An analytic model of the wind and pressure profiles in hurricanes. *Monthly Weather Review* 108, 1212–1218. — modelo paramétrico de campo de viento (default de `campo_viento.py`). *[clásico — confirmar DOI]*
- **Holland, G. J., J. I. Belanger & A. Fritz (2010/2008).** A revised model for radial profiles of hurricane winds. *Monthly Weather Review* 136, 3432–3445 / 138. — parámetro B revisado (backend CLIMADA). *[confirmar cita/DOI]*
- **Powell, M. D., et al. (2003).** Reduced drag coefficient for high wind speeds in tropical cyclones. *Nature* 422, 279–283. — base del factor de reducción gradiente→superficie. *[confirmar aplicación del 0.9]*
- **Knaff, J. A., et al. (2016).** estimación empírica del radio de viento máximo (`Rmax`) a partir de intensidad/latitud. — fallback de `Rmax` cuando falta `USA_RMW`. *[confirmar cita/DOI]*
- **Pielke, R. A. Jr., J. Gratz, C. W. Landsea, D. Collins, M. A. Saunders & R. Musulin (2008).** Normalized Hurricane Damage in the United States: 1900–2005. *Natural Hazards Review* 9(1), 29–42. — daño normalizado por intensidad/*landfall*. *[clásico — confirmar DOI]*
- **Pielke, R. A. Jr. & C. W. Landsea (1998).** Normalized hurricane damages in the United States: 1925–95. *Weather and Forecasting* 13, 621–631. — daño normalizado por *landfall*. *[clásico — confirmar DOI]*
- **Nordhaus, W. D. (2010).** The economics of hurricanes and implications of global warming. *Climate Change Economics* 1(1), 1–20. — el daño monetario escala con una potencia alta del viento. *[clásico — confirmar DOI]*
- **Simpson, R. H. (1974).** The hurricane disaster-potential scale. *Weatherwise* 27, 169–186. — escala Saffir-Simpson. *[clásico — confirmar DOI]*

## Related
[[HAZ_MOC]] · Home: [[_INDEX]]

#arm/haz #type/source
