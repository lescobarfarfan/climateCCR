# Calibración de funciones de impacto subnacionales para México en CLIMADA

**Rama:** calibración de funciones de daño ad-hoc (estatal) — fenómenos hidrometeorológicos
**Estado:** diseño aprobado, pre-implementación
**Última actualización:** 2026-06-11

---

## 1. Objetivo y motivación

Las funciones de impacto incluidas en CLIMADA agrupan a México dentro de la región
"Latinoamérica y el Caribe", perdiendo heterogeneidad subnacional relevante para la
evaluación de riesgos focalizados. Eberenz, Lüthi y Bresch (2021) demuestran que usar
una sola función de impacto calibrada para EE.UU. a nivel global sesga el daño simulado
hasta por un factor de 36 en algunas regiones, y proponen calibración regional de la
función de Emanuel (2011) contra daños reportados (EM-DAT, nivel país-evento).

**Este proyecto lleva esa lógica un nivel más abajo:** funciones de impacto por entidad
federativa, calibradas contra microdatos de pérdidas CNSF (aseguradas) y CENAPRED
(totales), aprovechando que CLIMADA permite asignar una función de impacto distinta a
cada punto de exposición vía la columna `impf_*` del `GeoDataFrame` de `Exposures`.

**Alcance de perils (fase 1):**
- Viento ciclónico (`TropCyclone`)
- Marejada ciclónica (`TCSurgeBathtub`, climada-petals)
- Lluvia ciclónica (`TCRain`, climada-petals)
- Inundación fluvial independiente (`RiverFlood`, climada-petals)

Fuera de alcance (documentado en §9): inundación pluvial/urbana.

---

## 2. Decisiones de diseño (con justificación)

| # | Decisión | Justificación / referencia |
|---|----------|---------------------------|
| D1 | Dos rutas de calibración: (A) pérdidas aseguradas CNSF vs exposición asegurada; (B) pérdidas totales CENAPRED vs exposición LitPop. La ruta B funge como análisis de sensibilidad de la ruta A. | La baja penetración del seguro en México hace que la ruta asegurada no represente vulnerabilidad económica total. Dos targets *independientes* (no uno escalado del otro) fortalecen la sensibilidad. Consistencia interna pérdidas↔exposición en cada ruta. |
| D2 | Hazard autocontenido en CLIMADA (campos de viento de `TropCyclone`, no el pipeline propio IBTrACS/Holland). | Una función de impacto calibrada con un modelo de viento no es transferible a otro: `v_half` absorbe los sesgos del hazard de calibración. La aplicación downstream ocurre en CLIMADA → calibrar en CLIMADA. |
| D3 | Unidad de calibración: **año × estado** (no evento × estado). | CNSF reporta por año-estado-ramo; asignar pérdidas anuales a tormentas individuales introduce ambigüedad cuando múltiples ciclones afectan el mismo estado el mismo año. Eberenz et al. (2021) agregan de forma análoga ante solapamientos en EM-DAT. |
| D4 | Periodo de análisis: **2000–presente**. | Acotado por el lado de pérdidas (serie CENAPRED "Impacto Socioeconómico de los Desastres en México" inicia ~2000). El hazard IBTrACS es confiable hacia atrás hasta ~1980 (era satelital, cuenca EP), pero no se inventan pérdidas hacia atrás. |
| D5 | Deflactación a pesos constantes con **INPC (INEGI)**, año base = último año completo del panel. | Serie doméstica de pérdidas en MXN → deflactor doméstico oficial y público. Deflactores del PIB (Banco Mundial/FMI) son para comparación internacional. Conversión a USD (FIX promedio anual, Banxico) solo para comparar magnitudes con literatura, nunca dentro de la calibración. |
| D6 | Forma funcional viento→daño: sigmoide de Emanuel (2011) vía `ImpfTropCyclone.from_emanuel_usa`, con `v_thresh = 25.7` m/s y `scale = 1` **fijos**; único parámetro libre: `v_half` por estado. | El nombre del constructor refleja los *defaults* de la calibración original de EE.UU.; la forma funcional es general. Eberenz et al. (2021) fijan `v_thresh = 25.7` m/s (valor de Emanuel 2011) y `scale = 1` por identificabilidad: liberar dos parámetros de forma con pérdidas agregadas produce valles planos en la superficie de costo. Sensibilidad opcional: `v_thresh ∈ {20, 25.7, 30}`. |
| D7 | Curvas de inundación/marejada: forma profundidad-daño del **JRC** (Huizinga et al. 2017, región Norteamérica, sector residencial como base) con un **escalar multiplicativo del MDD por estado** como único parámetro libre. | Mantiene la forma anclada al estándar de literatura; un parámetro por estado, simétrico al esquema de `v_half`. Sobre transferibilidad de curvas entre regiones: Wagenaar et al. (2018). |
| D8 | Timestep de interpolación de trayectorias: **1 h por defecto**, sujeto a test de convergencia (§4.1). Idéntico en calibración y en toda aplicación downstream. | Eberenz et al. (2021) interpolan a pasos horarios; tutoriales de CLIMADA usan 0.5–1 h. Principio rector: el sesgo de timestep se absorbe en `v_half` durante la calibración, por lo que la **consistencia** calibración↔aplicación domina sobre la "precisión" absoluta. Observación pendiente de explicar: en pruebas previas, timesteps más finos produjeron pérdidas menores — se investiga vía test de convergencia, no se elige el timestep por el resultado que produce. |
| D9 | Escasez de eventos por estado → **modelo jerárquico bayesiano** (partial pooling) en lugar de pooling duro por grupos. Implementación externa a CLIMADA (PyMC, con réplica opcional en Stan), con CLIMADA como forward model vía superficie precomputada (§5). | Conserva el detalle estatal solicitado. Estados sin costa / con pocos ciclones se contraen hacia la media regional/nacional con interpretación física directa. El `BayesianOptimizer` de `climada.util.calibrate` es optimización bayesiana (búsqueda GP, devuelve punto óptimo), **no** inferencia bayesiana — no produce posteriores. |
| D10 | Combinación multi-peril ciclónico a nivel **celda** con regla de unión de fracciones de daño (§6); calibración **conjunta** contra la pérdida total observada. | Evita doble conteo por construcción y respeta la cota física (daño ≤ valor del activo). Lógica análoga a la metodología de combinación viento-inundación de HAZUS (FEMA). La suma directa de impactos agregados sobreestima sistemáticamente en celdas costeras donde coinciden los tres sub-perils. |
| D11 | Desagregación espacial de sumas aseguradas estatales (CNSF) a malla: proporcional a LitPop dentro de cada estado. | CNSF da agregados estatales; CLIMADA requiere puntos. LitPop (luces nocturnas × PIB) es proxy razonable de localización de activos asegurados. Supuesto documentado, evaluable en sensibilidad. |
| D12 | Artefacto canónico de salida: **tabla de parámetros versionada** (CSV/JSON) + script reconstructor determinista del `ImpactFuncSet`. Nunca objetos serializados (pickle) como fuente de verdad. | Robustez entre versiones de CLIMADA; consumo limpio desde el proyecto paralelo; git-friendly. |
| D13 | Crosswalk de perils CNSF para ciclones con penetración tierra adentro: recoger pérdidas tanto de categorías "ciclón" como "inundación/hidro" en estados del cono de lluvia. | Pérdidas por remanentes ciclónicos en estados interiores (p.ej. CDMX) se registran en CNSF bajo perils de inundación, no de ciclón. Regla de asignación documentada en el crosswalk (§3.1). |

---

## 3. Datos: inventario y forma requerida

### 3.1 Target de calibración (pérdidas observadas)

**Forma:** DataFrame año × estado (filas = años, columnas = claves INEGI de 2 dígitos),
una tabla por ruta (A: asegurada; B: total) y por familia de peril (ciclónico
agregado; inundación fluvial). El módulo `climada.util.calibrate` espera filas =
eventos y columnas = regiones; con D3, "evento" = año.

| Insumo | Fuente | Estado |
|--------|--------|--------|
| Pérdidas aseguradas por año-estado-peril | CNSF (pipeline propio: `scraper_cnsf.py` → `limpieza_cnsf.py`) | Disponible |
| Sumas aseguradas por año-estado | CNSF (mismo pipeline) | Disponible |
| Pérdidas totales por año-estado-fenómeno | CENAPRED, "Impacto Socioeconómico de los Desastres en México" | **Pendiente: scraper CENAPRED** |
| INPC mensual/anual | INEGI / Banxico (SIE) | Por descargar (pinear con `_procedencia.json`) |
| Crosswalk año-estado ↔ tormentas IBTrACS | Construcción propia | **Siguiente entregable** |

**Reglas del crosswalk (a detallar en su propio documento al implementarlo):**
1. Identificar, por año, las tormentas IBTrACS cuyo campo de viento modelado intersecta
   cada estado con intensidad > `v_thresh`.
2. Para estados del cono de lluvia (intensidad de `TCRain` > umbral, aun sin viento
   dañino), incluirlos en el conjunto afectado del año (D13).
3. La pérdida anual del estado se compara contra el impacto modelado **agregado sobre
   todas las tormentas del año** que afectan al estado — no se particiona la pérdida
   observada entre tormentas.
4. Años-estado sin tormenta modelada pero con pérdida observada > 0 (y viceversa) se
   flaggean para revisión manual antes de entrar al likelihood; la regla de
   inclusión/exclusión final se documenta.

### 3.2 Exposición

| Objeto | Construcción | Notas |
|--------|--------------|-------|
| `exp_total` | `LitPop.from_countries(['MEX'])` | Ruta B. Estándar de literatura (Eberenz et al. 2020, ESSD). |
| `exp_aseg_{año}` | Sumas aseguradas CNSF estatales del año, desagregadas ∝ LitPop intraestatal (D11) | Ruta A. Exposición específica del año → la normalización temporal viene gratis. |

Ambos `GeoDataFrame` requieren:
- `region_id` = clave INEGI del estado (spatial join contra Marco Geoestadístico — shapefile estatal ya disponible, pinear versión).
- `impf_TC`, `impf_TCSurgeBathtub`, `impf_TR`, `impf_RF` = clave del estado (la misma para los cuatro perils; el `ImpactFuncSet` distingue por tipo de hazard).

### 3.3 Hazard (congelado, una sola vez)

| Hazard | Construcción | Insumos |
|--------|--------------|---------|
| Viento | `TCTracks.from_ibtracs_netcdf(provider='usa', basin=...)` para EP y NA, filtro ≥ 2000 → `equal_timestep(1.0)` (D8) → `TropCyclone.from_tracks(tracks, centroids=...)` | IBTrACS v04r01 (ya pineado en el repo) |
| Marejada | `TCSurgeBathtub.from_tc_winds(tc, topo_path)` | DEM `.tif` ya disponible (documentar fuente/versión; referencia estándar: SRTM15+ V2.0, Tozer et al. 2019). Relación viento-marejada de Xu (2010) basada en SLOSH, con decaimiento tierra adentro. |
| Lluvia ciclónica | `TCRain.from_tracks(...)` (climada-petals, `haz_type='TR'`, intensidad en mm) | Mismas trayectorias. Modelos disponibles en petals: R-CLIPER (Tuleya et al. 2007) y TCR (Lu et al. 2018); decisión de modelo a documentar tras prueba (default: R-CLIPER, menor costo). |
| Inundación fluvial | `RiverFlood.from_nc(dph_path=..., frc_path=...)` | Archivos `.nc` de depth y fraction (ISIMIP/CaMa-Flood) ya disponibles (documentar simulación ISIMIP exacta, GCM/GHM forzante, en `_procedencia.json`). Resolución temporal: máximo anual → consistente con D3. |

**Requisito crítico:** los cuatro hazards comparten los **mismos centroides** (los de la
exposición). Sin esto, la combinación multi-peril a nivel celda (§6) es imposible.

**Persistencia:** cada hazard se guarda en HDF5 (`haz.write_hdf5()`) con
`_procedencia.json` (versión CLIMADA, versión IBTrACS, sha256, fecha, parámetros de
generación incluyendo timestep). La calibración corre **solo** contra hazards
congelados; nunca se regeneran al vuelo.

### 3.4 Test de convergencia de timestep (previo a congelar hazard — D8)

Protocolo:
1. Seleccionar 3–4 eventos mayores con buena cobertura de pérdidas (candidatos: Wilma
   2005, Odile 2014, Patricia 2015, Willa 2018).
2. Generar `TropCyclone` con timestep ∈ {0.25, 0.5, 1, 3} h sobre la malla definitiva
   de centroides.
3. Comparar: (a) swath de intensidad máxima por celda, (b) pérdida modelada agregada
   por estado con una función de impacto fija de referencia (Eberenz NA).
4. Documentar la curva de convergencia y la interacción timestep × resolución de
   centroides (relevante para entidades pequeñas — cf. artefacto CDMX del pipeline
   propio).
5. Congelar el timestep en el valor donde la pérdida agregada converge (default
   esperado: 1 h). **El criterio es convergencia, nunca la magnitud del resultado.**

---

## 4. Forma funcional y parámetros

### 4.1 Viento (Emanuel 2011)

Fracción de daño en función del viento sostenido `V`:

```
v_n   = max(V − V_thresh, 0) / (V_half − V_thresh)
f(V)  = v_n³ / (1 + v_n³)
```

- `V_thresh = 25.7 m/s` (fijo; Emanuel 2011, mantenido por Eberenz et al. 2021).
- `scale = 1` (fijo).
- `V_half,s` = parámetro libre, uno por estado `s` (jerárquico, §5).

Constructor: `ImpfTropCyclone.from_emanuel_usa(impf_id=s, v_thresh=25.7, v_half=...)`.

### 4.2 Marejada e inundación (JRC profundidad-daño)

Curva base: `ImpfRiverFlood.from_jrc_region_sector('NorthAmerica', 'residential')`
(Huizinga et al. 2017). Parámetro libre por estado: escalar multiplicativo `κ_s` sobre
el MDD (recortado a [0, 1] tras escalar):

```
MDD_s(d) = min(κ_s · MDD_JRC(d), 1)
```

La misma curva base aplica a marejada (`TCSurgeBathtub`, intensidad en m) y a
inundación fluvial (`RF`), con escalares separados `κ_s^surge` y `κ_s^RF` (mecanismos
de daño distintos: agua salada + oleaje vs agua dulce).

### 4.3 Lluvia ciclónica

No existe función estándar precipitación→daño en CLIMADA core. Opciones, en orden de
preferencia:
1. **Sigmoide tipo Emanuel sobre precipitación acumulada** con umbral `P_thresh` fijo
   (calibración exploratoria nacional para fijarlo, p.ej. percentil de eventos sin
   pérdida) y `P_half,s` libre — simetría total con el esquema de viento.
2. Lineal-a-trozos con un escalar libre.

La decisión se toma con datos en mano (identificabilidad, §6) y se documenta. Si la
componente de lluvia resulta no identificable, se colapsa al modelo nulo (§6,
viento-como-proxy) y se reporta.

---

## 5. Modelo jerárquico bayesiano

### 5.1 Por qué no basta `climada.util.calibrate`

`climada.util.calibrate` (Input + `BayesianOptimizer`/`ScipyMinimizeOptimizer`, costos
MSE/MSLE ponderados) entrega **puntos óptimos** por minimización. Se usará para:
- calibración nacional de referencia (modelo nulo),
- diagnósticos (`OutputEvaluator`: espacio de parámetros, robustez del costo),
- verificación cruzada de los modos posteriores.

El partial pooling estatal requiere inferencia completa → PyMC (réplica opcional Stan).

### 5.2 Superficie precomputada (surrogate exacto)

Para hazard y exposición **fijos**, la pérdida modelada del estado `s` en el año `t` es
una función monótona y suave de los parámetros de su función de impacto. Se precomputa
con CLIMADA:

```
L_st(v_half)  sobre malla v_half ∈ {30, 32, ..., 120} m/s        (viento)
L_st(κ)       sobre malla κ ∈ {0.1, 0.2, ..., 3.0}               (surge, RF, lluvia)
```

Dentro del sampler, el likelihood **interpola** estas curvas (interpolación monótona,
PCHIP) — nunca llama a CLIMADA. Exportación: tensores `(estado, año, malla_parámetro)`
en parquet/NetCDF, con procedencia. Esto hace el modelo barato, exacto a efectos
prácticos y completamente reproducible.

Para la calibración conjunta multi-peril (§6), la combinación de unión no es separable
por peril a nivel agregado; la superficie se precomputa entonces a nivel de
**fracciones por celda** o, más práctico, sobre una malla conjunta gruesa
`(v_half, κ_surge, κ_rain)` por estado-año, refinada localmente tras una corrida
exploratoria. Decisión de implementación a documentar al construir los scripts.

### 5.3 Especificación

Sea `g(s)` el grupo regional del estado `s` (Pacífico Sur, Pacífico Norte/Península BC,
Golfo, Península de Yucatán, Interior — agrupación a justificar por climatología de
trayectorias):

```
Hiperpriors:
  μ_g ~ Normal(log μ₀, σ₀²)            μ₀ anclado al V_half regional NA de
                                        Eberenz et al. (2021) — prior, no dato
  τ   ~ HalfNormal(σ_τ)

Nivel estatal (partial pooling):
  log V_half,s ~ Normal(μ_g(s), τ²)
  log κ_s      ~ Normal(0, σ_κ²)        (centrado en κ=1, la curva JRC tal cual)

Likelihood (pérdidas en log — equivale al espíritu de MSLE/RMSF; las pérdidas
abarcan órdenes de magnitud):
  log L_obs,st ~ Normal(log L_mod,st(θ_s), σ_obs²)
```

Tratamiento de ceros y censura (años-estado afectados con pérdida observada 0, o
pérdidas por debajo de deducibles en la ruta asegurada): hurdle/censura por la
izquierda — decisión fina a tomar con los datos, documentada.

### 5.4 Validación

1. **Leave-one-year-out** sobre los años con eventos mayores (re-ajuste excluyendo el
   año; error predictivo out-of-sample).
2. **Benchmark externo:** posterior nacional/regional vs `V_half` NA de Eberenz et al.
   (2021). El resultado central de la tesis es cuantificar la heterogeneidad estatal
   que el promedio regional esconde.
3. **Ruta A vs Ruta B:** comparación de rankings estatales de vulnerabilidad entre
   target asegurado y total — sensibilidad principal.
4. **Modelo nulo:** esquema Eberenz puro (solo viento contra pérdida total, `v_half`
   absorbiendo implícitamente marejada y lluvia). Si la descomposición de tres
   sub-perils no mejora la validación out-of-sample, se reporta — eso también es un
   resultado.
5. Diagnósticos MCMC estándar (R-hat, ESS, divergencias) vía ArviZ; correlaciones
   posteriores entre familias de parámetros como diagnóstico de identificabilidad (§6).

---

## 6. Agregación multi-peril sin doble conteo

**Problema:** las pérdidas observadas por año-estado son totales del fenómeno, no vienen
separadas por sub-peril (viento / marejada / lluvia). Calibrar cada sub-peril por
separado contra el total triplica el conteo; calibrar conjuntamente deja la *partición*
débilmente identificada.

**Diseño:**

1. **Combinación a nivel celda** (requiere centroides compartidos, §3.3). Con
   fracciones de daño por celda-evento `f_viento`, `f_surge`, `f_lluvia` (de
   `imp_mat / valor expuesto`):

   ```
   f_total = 1 − (1 − f_viento)(1 − f_surge)(1 − f_lluvia)
   ```

   Regla de unión de daños (lógica de la combinación viento-inundación de HAZUS,
   FEMA): el daño combinado nunca excede el valor del activo, y un activo dañado al
   60% por viento solo puede perder el 40% restante por agua. La suma directa de
   impactos agregados sobreestima sistemáticamente en la costa, exactamente donde
   están las pérdidas grandes. Supuesto implícito: independencia condicional de los
   mecanismos de daño dado el evento — documentado como supuesto, con la alternativa
   conservadora `f_total = max(f_i)` como cota inferior en sensibilidad.

2. **Un solo likelihood contra el total observado**, con los tres bloques de
   parámetros dentro: cero doble conteo por construcción.

3. **Identificación de la partición**, por dos vías:
   - *Priors asimétricos:* las curvas de agua quedan ancladas a JRC (solo escala,
     centrada en 1); el parámetro verdaderamente libre es `v_half`.
   - *Firma física de los eventos:* el panel contiene ciclones de viento extremo y
     poca lluvia, y ciclones débiles en viento pero catastróficos en agua. Esa
     variación entre eventos separa los parámetros. Se reporta la correlación
     posterior entre bloques como diagnóstico; si la partición no identifica, se
     colapsa al modelo nulo y se reporta.

---

## 7. Flujo de inundación fluvial independiente

1. Hazard `RiverFlood.from_nc()` con los `.nc` de depth/fraction disponibles
   (ISIMIP/CaMa-Flood; máximo anual → unidad año-estado nativa, consistente con D3).
2. Target: pérdidas CNSF de perils de inundación por año-estado (excluyendo los
   años-estado ya atribuidos a lluvia ciclónica vía crosswalk D13 — regla de
   partición del target a documentar: la pérdida hidro de un año-estado se asigna a
   "ciclónica" si hay tormenta en el cono de lluvia, a "fluvial independiente" en caso
   contrario; los casos mixtos se flaggean) + CENAPRED para la ruta B.
3. Función: curva JRC NorthAmerica residencial × `κ_s^RF` jerárquico (§4.2, §5).
4. Ruta de refinamiento (fase 2): módulo GloFAS de petals — caudales diarios del CDS
   (reanálisis desde 1979) traducidos a footprints vía periodos de retorno y mapas de
   amenaza JRC. Mejor resolución de eventos; mayor costo (cuenta CDS, volúmenes,
   distribución de extremos por pixel). Referencia de calibración fluvial del
   ecosistema CLIMADA/PIK: Sauer et al. (2021).

---

## 8. Reproducibilidad y exportación

**Artefacto canónico:** `parametros_impacto_estatal.csv` (versionado en git):

```
estado_cve | estado_nombre | peril | forma_funcional | v_thresh | param_libre |
post_media | post_mediana | ci90_inf | ci90_sup | n_anios_efectivos | ruta_target |
hash_insumos | version_climada | tag_git | fecha
```

Acompañado de:
- `construir_impfset.py`: reconstruye el `ImpactFuncSet` determinísticamente desde la
  tabla. El proyecto paralelo consume **la tabla**, nunca objetos serializados (D12).
- Hazards e impactos precomputados en HDF5 + `_procedencia.json` (patrón existente
  del repo: URL/origen, sha256, fecha, bytes, versiones).
- Superficies precomputadas `L_st(·)` en parquet/NetCDF con procedencia.
- Trazas posteriores completas en NetCDF (`arviz.to_netcdf`), una por corrida,
  nombradas con tag de git.
- `environment.yml` exportado y pineado (versión exacta de climada, climada-petals,
  PyMC).
- Log de decisiones por corrida: qué años-estado entraron al likelihood, qué versión
  del crosswalk, qué cambió vs la corrida anterior. La auditoría de "cómo cambian
  resultados con cada mejora" = comparación de trazas entre tags de git.

---

## 9. Limitaciones declaradas

1. **Inundación pluvial/urbana fuera de alcance (fase 1).** Ni ISIMIP ni GloFAS
   capturan inundación por colapso de drenaje urbano — mecanismo dominante en CDMX,
   Monterrey, Guadalajara. No existe hazard pluvial nacional off-the-shelf integrable
   a CLIMADA. Mitigación parcial: la componente `TCRain` captura lluvia *ciclónica*
   también en estados interiores. Trabajo futuro: piloto precipitación→daño para CDMX
   con CHIRPS/ERA5 (precedente en literatura econométrica de daños), que requeriría
   además resolución sub-estatal fina (conecta con el artefacto de discretización de
   CDMX del pipeline propio).
2. **Hazard de inundación modelado, no observado** (CaMa-Flood/GloFAS): la
   vulnerabilidad calibrada es condicional a un hazard con error propio.
3. **Ruta asegurada ≠ vulnerabilidad económica total** (penetración heterogénea,
   deducibles, demand surge). Por eso D1.
4. **Funciones casadas al hazard de CLIMADA** con el timestep congelado (D2, D8): no
   transferibles al pipeline propio IBTrACS/Holland sin recalibrar.
5. **Coeficientes y curvas de origen extranjero como priors** (Eberenz NA, JRC NA,
   Xu/SLOSH): el esquema jerárquico los trata como priors actualizables, no como
   verdad.

---

## 10. Secuencia de trabajo

1. **Crosswalk año-estado ↔ tormentas** (siguiente entregable; bloquea todo lo demás).
   Requiere previamente el scraper CENAPRED (en desarrollo en el flujo paralelo).
2. Test de convergencia de timestep (§3.4) → congelar hazards (§3.3).
3. Construcción de exposiciones (LitPop + desagregación CNSF).
4. Tablas target (deflactadas, dos rutas).
5. Calibración nacional de referencia con `climada.util.calibrate` (modelo nulo).
6. Superficies precomputadas → modelo jerárquico PyMC (viento solo).
7. Extensión multi-peril (calibración conjunta §6).
8. Inundación fluvial independiente (§7).
9. Validación completa (§5.4) y exportación canónica (§8).

---

## Referencias

- Aznar-Siguan, G. & Bresch, D. N. (2019). CLIMADA v1: a global weather and climate
  risk assessment platform. *Geoscientific Model Development*, 12, 3085–3097.
  doi:10.5194/gmd-12-3085-2019
- Eberenz, S., Stocker, D., Röösli, T. & Bresch, D. N. (2020). Asset exposure data for
  global physical risk assessment. *Earth System Science Data*, 12, 817–833.
  doi:10.5194/essd-12-817-2020
- Eberenz, S., Lüthi, S. & Bresch, D. N. (2021). Regional tropical cyclone impact
  functions for globally consistent risk assessments. *Natural Hazards and Earth
  System Sciences*, 21, 393–415. doi:10.5194/nhess-21-393-2021. Código:
  doi:10.5281/zenodo.4467858
- Emanuel, K. (2011). Global Warming Effects on U.S. Hurricane Damage. *Weather,
  Climate, and Society*, 3, 261–268. doi:10.1175/WCAS-D-11-00007.1
- FEMA. *Hazus Hurricane Model Technical Manual* (metodología de combinación de
  pérdidas viento-inundación). Verificar edición vigente al citar.
- Gelman, A. & Hill, J. (2007). *Data Analysis Using Regression and
  Multilevel/Hierarchical Models*. Cambridge University Press. (Fundamento de partial
  pooling.)
- Huizinga, J., De Moel, H. & Szewczyk, W. (2017). Global flood depth-damage
  functions: Methodology and the database with guidelines. EUR 28552 EN, Publications
  Office of the European Union. doi:10.2760/16510
- Kaplan, J. & DeMaria, M. (1995). A simple empirical model for predicting the decay
  of tropical cyclone winds after landfall. *Journal of Applied Meteorology*, 34,
  2499–2512. (Contexto del pipeline propio; no se usa en esta rama por D2.)
- Knapp, K. R., Kruk, M. C., Levinson, D. H., Diamond, H. J. & Neumann, C. J. (2010).
  The International Best Track Archive for Climate Stewardship (IBTrACS). *Bulletin of
  the American Meteorological Society*, 91, 363–376. doi:10.1175/2009BAMS2755.1
- Lu, P., Lin, N., Emanuel, K., Chavas, D. & Smith, J. (2018). Assessing hurricane
  rainfall mechanisms using a physics-based model. *Journal of the Atmospheric
  Sciences*, 75, 2337–2358. (Modelo TCR en climada-petals.)
- Sauer, I. J., Reese, R., Otto, C., Geiger, T., Willner, S. N., Guillod, B. P.,
  Bresch, D. N. & Frieler, K. (2021). Climate signals in river flood damages emerge
  under sound regional disaggregation. *Nature Communications*, 12, 2128.
  doi:10.1038/s41467-021-22153-9
- Tozer, B., Sandwell, D. T., Smith, W. H. F., Olson, C., Beale, J. R. & Wessel, P.
  (2019). Global bathymetry and topography at 15 arc sec: SRTM15+. *Earth and Space
  Science*, 6, 1847–1864. doi:10.1029/2019EA000658
- Tuleya, R. E., DeMaria, M. & Kuligowski, R. J. (2007). Evaluation of GFDL and simple
  statistical model rainfall forecasts for U.S. landfalling tropical storms. *Weather
  and Forecasting*, 22, 56–70. (R-CLIPER.)
- Wagenaar, D., Lüdtke, S., Schröter, K., Bouwer, L. M. & Kreibich, H. (2018).
  Regional and temporal transferability of multivariable flood damage models. *Water
  Resources Research* / *Risk Analysis* — verificar revista exacta al citar.
- Xu, L. (2010). A simple coastline storm surge model based on pre-run SLOSH outputs.
  (Relación viento-marejada usada por `TCSurgeBathtub`; citar vía documentación de
  climada-petals.)
- Documentación: CLIMADA v6 (`climada.util.calibrate`, `TropCyclone`), climada-petals
  v6 (`TCSurgeBathtub`, `TCRain`, `RiverFlood`, `ImpfRiverFlood`, módulo GloFAS).
  Pinear versiones exactas en `environment.yml` al implementar.

> **Nota de verificación pendiente:** dos referencias quedan marcadas con "verificar"
> (edición de Hazus; revista exacta de Wagenaar et al. 2018) y la cita de Sauer et al.
> (2021) debe confirmarse contra el DOI antes de usarse en el manuscrito de tesis —
> consistente con el estándar del proyecto de verificación estricta de fuentes.
