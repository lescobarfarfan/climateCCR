# Pipeline CNSF — Bases del sector asegurador

Todo se orquesta desde `scraper_cnsf.py` mediante `--modo`. La consolidación
(`consolidar_cnsf.py`) puede correrse encadenada (modo `sync`) o por separado.

Fuente (SharePoint):
`.../InstitucionesSociedadesMutualistas/Paginas/DetalladaSeguros.aspx`

---

## Modos de ejecución (`--modo`)

| modo         | red | descarga          | consolida | uso                                   |
|--------------|-----|-------------------|-----------|---------------------------------------|
| `verificar`  | sí  | no (dry-run)      | no        | ver qué hay nuevo/cambiado            |
| `descargar`  | sí  | nuevo/cambiado    | no        | solo bajar datos                      |
| `consolidar` | no  | no                | sí        | solo consolidar lo ya descargado      |
| `sync` (def) | sí  | nuevo/cambiado    | sí*       | verificar + bajar + reconsolidar      |

\* en `sync` solo se reconsolidan las categorías que cambiaron; si nada cambió,
no se reconsolida.

```bash
# ¿Hay algo nuevo o modificado? (no baja nada)
python scraper_cnsf.py --modo verificar

# Solo descargar lo nuevo/cambiado
python scraper_cnsf.py --modo descargar --categorias agricola hidro incendio

# Solo consolidar lo que ya está en disco
python scraper_cnsf.py --modo consolidar

# Todo en uno (default): verificar + bajar + reconsolidar lo que cambió
python scraper_cnsf.py
```

`--categorias` acepta nombre o slug con coincidencia parcial
(`hidro` => `riesgos_hidrometeorologicos`). `--anios 2023 2024` filtra por año.
`--forzar` re-descarga aunque no haya cambios.

### Descargar y consolidar en una sola ejecución

Ya está cubierto por el modo `sync` (el default): descarga lo nuevo/cambiado y
luego reconsolida, todo en la misma corrida.

```bash
python scraper_cnsf.py                       # = descargar + consolidar
python scraper_cnsf.py --categorias agricola # acotado a una categoría
```

`--modo` recibe **un solo valor** a propósito: los modos no son combinables de
forma libre. `verificar` es un dry-run (no actúa), así que combinarlo con
`descargar` sería contradictorio; y la única combinación útil —descargar +
consolidar— ya es precisamente `sync`. Si en algún momento quieres las dos cosas
pero por separado (p. ej. revisar la descarga antes de consolidar), corre en dos
pasos: `--modo descargar` y luego `--modo consolidar`.

Matiz de `sync`: reconsolida **solo las categorías que cambiaron** en esa corrida
(si una categoría no tuvo cambios, su CSV consolidado ya está vigente y no se
reescribe). Para forzar la reconsolidación de todo, usa `--modo consolidar`
después, o `--forzar` en la descarga.

### Enfocar en algunas categorías

`--categorias` aplica a **todos** los modos (`verificar`, `descargar`, `sync`,
`consolidar`). Acepta el slug o parte del nombre (coincidencia parcial), así que
`--categorias agricola hidro` enfoca toda la corrida —descarga y, en `sync`,
también la reconsolidación— a ese subconjunto.

```bash
# Ver los nombres y slugs exactos disponibles (15 categorías)
python scraper_cnsf.py --listar-categorias

# Sync (bajar + consolidar) enfocado a tres categorías
python scraper_cnsf.py --categorias agricola hidrometeorologicos incendio
```

Categorías del portal (nombre → slug). Para `--categorias` basta un fragmento
inequívoco (p. ej. `hidro`, `terremoto`, `credito_vivienda`):

```
Vida                                         -> vida
Pensiones                                    -> pensiones
Accidentes y Enfermedades                    -> accidentes_y_enfermedades
Salud                                        -> salud
Responsabilidad Civil y Riegos Profesionales -> responsabilidad_civil_y_riegos_profesionales
Marítimo y Transportes                       -> maritimo_y_transportes
Incendio                                     -> incendio
Agrícola y Animales                          -> agricola_y_animales
Automóviles                                  -> automoviles
Crédito                                      -> credito
Crédito a la Vivienda                        -> credito_a_la_vivienda
Garantía Financiera                          -> garantia_financiera
Riesgos Hidrometereológicos                  -> riesgos_hidrometereologicos
Terremoto y Erupción Volcánica               -> terremoto_y_erupcion_volcanica
Diversos                                     -> diversos
```

(La lista se obtiene en vivo con `--listar-categorias`; aquí se incluye solo por
comodidad y puede cambiar si el portal agrega/renombra categorías.)

---

## Por qué NO hace falta POST ni `__VIEWSTATE`

El portal es SharePoint. El vínculo `javascript:__doPostBack(...)` de cada
categoría solo expande/ordena el grupo: **no trae datos**. El HTML del servidor
ya incluye los enlaces DIRECTOS y ESTÁTICOS a cada archivo por año, p. ej.:

```
.../InstitucionesSociedadesMutualistas/AyA Bases/2024 Agricola Bases.xlsx
.../InstitucionesSociedadesMutualistas/Riesgos Hidro Bases/2024 Hidro Bases.xlsx
```

Flujo: `GET` de la página `.aspx` -> extraer `<a>` a `.xls/.xlsx/.xlsm` ->
`GET` del binario. El "POST que baja un Excel" de DevTools es la descarga del
binario en sí; un `GET` directo al href hace lo mismo.

---

## Detección de cambios e integridad (SHA-256)

- **Estado persistente** en `<out_dir>/_estado.json` (acumulativo entre corridas):
  por archivo guarda `sha256`, `bytes`, tamaño reportado, `Last-Modified`/`ETag`
  y fecha.
- Para decidir si bajar **sin** descargar todo, se comparan señales baratas de red
  contra el estado previo: el tamaño del listado y, vía `HEAD`,
  `Content-Length`/`Last-Modified`/`ETag`. Tras descargar, el **SHA-256 confirma**
  si el contenido cambió de verdad (evita re-escribir por falsas alarmas).
- Si un archivo **cambió de contenido**, la versión previa se archiva en
  `<out_dir>/_versiones/<categoria>/<nombre>.<fecha>.<sha8>.<ext>` antes de
  reemplazarla (retención/auditoría). Desactivable con `--no-versionar`.

La corrida anual entonces: año nuevo => `nuevo`; archivo con SHA distinto =>
`cambiado` (con respaldo de la versión anterior); lo demás => `sin_cambio`.

---

## Salida

```
datos/cnsf/
  agricola_y_animales/2024 Agricola Bases.xlsx
  riesgos_hidrometeorologicos/2024 Hidro Bases.xlsx
  ...
  _estado.json                       # estado acumulativo (sha256, bytes, etag, ...)
  _versiones/<categoria>/...          # versiones previas de archivos que cambiaron
  cnsf_manifest_<fecha>.json          # por corrida: estado/motivo/sha256 por archivo
  cnsf_verificacion_<fecha>.json      # solo en modo verificar
datos_crudos/cnsf/<fecha>/
  agricola_y_animales.html            # snapshot del listado (auditoría)
datos/cnsf_consolidado/               # salida del consolidador (ver abajo)
```

### Instalación

```bash
pip install requests beautifulsoup4         # descarga (modos verificar/descargar/sync)
pip install pandas openpyxl xlrd            # consolidación (modos sync/consolidar)
```

---

## Consolidación — `consolidar_cnsf.py`

Une todos los años de **cada categoría** en CSV, **uno por hoja de datos**
(Emisión / Suma Asegurada / Siniestros). Es **por categoría**, no entre
categorías: aunque la hoja se llame igual, el esquema es incompatible
(Agrícola = cultivo/animal; Hidro e Incendio = ubicaciones/valores/giro).

**Por qué CSV y no un xlsx único:** "Suma Asegurada" de Hidro trae ~366 mil filas
POR AÑO; con 2-3 años se rebasa el límite de Excel (1,048,576 filas/hoja). CSV no
tiene ese límite y alimenta directo Power Query. `--xlsx-si-cabe` genera además
xlsx solo para hojas que sí caben.

### Salida (una carpeta por categoría, un CSV por hoja)

```
datos/cnsf_consolidado/
  agricola_y_animales/
    emision.csv
    siniestros.csv
    _reporte.json
  riesgos_hidrometeorologicos/
    emision.csv
    suma_asegurada.csv
    siniestros.csv
    _reporte.json
  reporte_consolidacion.json     # resumen global
```

Cada CSV antepone columnas de procedencia: `categoria`, `anio`, `archivo_origen`.

### Cambios de columnas en el tiempo (deriva)

- Esquema **canónico** = columnas del **año más reciente**, en su orden.
- Encabezados se emparejan por **clave normalizada** (sin acentos, sin saltos de
  línea, espacios colapsados, mayúsculas).
- **Las HOJAS también se agrupan por nombre normalizado**: "Emisión" (años viejos)
  y "Emision" (años recientes) se consolidan JUNTAS en un solo `emision.csv`.
  (Antes se trataban como hojas distintas que escribían el mismo archivo y una
  sobreescribía a la otra: pérdida de datos. Corregido.)
- Columna canónica ausente en un año viejo -> se **rellena vacía**.
- Columna solo en años viejos -> se **conserva al final** (default) y se reporta;
  `--estricto` la descarta.
- `--limpiar-encabezados` colapsa saltos de línea/espacios dobles en los nombres
  de columna del CSV (p. ej. `PRIMERA LÍNEA \nDE MAR` -> `PRIMERA LÍNEA DE MAR`).
  El emparejamiento entre años no depende de esto; solo limpia el encabezado.

### Verificación post-consolidación (sección `validaciones`)

Cada hoja del `_reporte.json` trae un bloque `validaciones` con `ok` y `avisos`:

- **reconciliación de filas** (suma por año == total),
- **columnas 100% vacías** (posible desalineación o error de lectura),
- **columnas sin encabezado**,
- **posibles_duplicados**: columnas histórico-only muy parecidas a una canónica
  (típico de un typo/renombre entre años). Se devuelven como
  `{variante, canonica, similitud}`, listas para volverse alias.
- **medidas_no_numericas**: columnas de medida (PRIMA/MONTO/SUMA/…) con valores no
  numéricos (p. ej. el texto "No disponible" que usa la CNSF como faltante).

En `reporte_consolidacion.json` cada categoría lista `hojas_a_revisar`.

### Alias por ámbito (`--aliases`)

Para fusionar variantes/typos de encabezado. El JSON puede ser plano (global) o
**por ámbito** (recomendado, porque la misma palabra puede ser canónica en una
hoja y variante en otra):

```json
{
  "agricola_y_animales/siniestros": {
    "MONTO DEL SINIESTRO OCURRIDO": "MONTO DEL SINIESTRO OCOURRIDO",
    "MONTO DEL SINIESTRO COURRIDO": "MONTO DEL SINIESTRO OCOURRIDO"
  },
  "incendio/siniestros": { "GIRO DE LA UBICACIÓN": "GIRO LA UBICACIÓN" }
}
```

Ámbitos: `"_global"`, `"<categoria>"`, o `"<categoria>/<hoja>"`. Ver
`aliases_cnsf.json` (incluye los typos detectados en agro/incendio/hidro).

Se puede correr solo: `python consolidar_cnsf.py --root datos/cnsf --out-dir datos/cnsf_consolidado --aliases aliases_cnsf.json`
o encadenado vía `--modo sync` / `--modo consolidar` del scraper (mismas banderas
`--estricto`, `--xlsx-si-cabe`, `--aliases`, `--limpiar-encabezados`, `--categorias`).

---

## Explorar la estructura de los xlsx — `explorar_xlsx_cnsf.py`

Análogo a la exploración de los `.mdb` de Automóviles, pero para los sectores en
Excel (Agrícola, Incendio, Hidro…). Es de **solo lectura** (no consolida) y da el
**contexto temporal** de las columnas, para decidir alias y entender los avisos
del consolidador. Lee solo unas filas por hoja (rápido).

```bash
python explorar_xlsx_cnsf.py --root datos/cnsf                  # todas
python explorar_xlsx_cnsf.py --root datos/cnsf --categorias hidro incendio
# -> reporte_estructura.json + resumen en consola
```

Por cada (categoría, hoja) reporta: columnas por año, **matriz de presencia** (en
qué años aparece cada columna), columnas **sin encabezado pero con datos**
(posición + valores de muestra, y **en qué año**), **encabezados duplicados**, y
**candidatos a alias** (columnas históricas parecidas ≥0.88 a una canónica). Estos
últimos se pasan tal cual a `aliases_cnsf.json` para que la consolidación las
empareje en vez de tratarlas como columnas distintas.

Flujo recomendado cuando la consolidación marca `REVISAR`:
1. corre `explorar_xlsx_cnsf.py` sobre la categoría,
2. mira `alias_candidatos` → agrega los reales a `aliases_cnsf.json` (con clave
   `<categoria>/<hoja>` si aplica),
3. mira `sin_encabezado_con_datos` → identifica qué es esa columna por su muestra
   y su año; si es real, dale nombre vía alias; si es basura, queda como
   `(sin encabezado)` y puedes ignorarla o filtrarla,
4. re-consolida.

> Nota: la lectura de hojas es **robusta ante encabezados duplicados** (p. ej.
> varias columnas en blanco): la selección es por posición y los nombres
> repetidos se hacen únicos (`MONTO`, `MONTO (2)`), evitando el error
> "truth value of a Series is ambiguous".

---

## Categorías en formato MDB (Automóviles)

Algunas categorías (p. ej. **Automóviles**) NO publican Excel: el enlace es un
`.zip` que adentro trae una base **Microsoft Access `.mdb`** (tablas grandes).
El pipeline ya las maneja de extremo a extremo:

- **Descarga (integrada):** el scraper reconoce `.zip`, calcula SHA-256, los
  registra en `_estado.json` y el manifest, detecta cambios y versiona —igual que
  los xlsx. Además **separa por subsector**: descarga a subcarpetas
  `automoviles/individual/` y `automoviles/flotilla/` según el nombre del archivo,
  para no mezclarlos.
- **Procesamiento (independiente):** `procesar_autos_cnsf.py` descomprime el
  `.zip`, lee el `.mdb` con mdbtools en streaming, resuelve los códigos contra sus
  catálogos (código + columnas `_desc`) y emite CSV por subsector y tabla. En
  `--modo sync`/`consolidar`, Automóviles se enruta automáticamente a este
  procesador (no al consolidador de xlsx).
- **El año se toma del nombre del `.zip`**: en 2008–2009 el `.mdb` extraído no
  trae el año en su nombre, pero el pipeline lo deriva del `.zip` y extrae cada
  año a una carpeta temporal aparte, así que no hay colisión.

Para **explorar** un `.mdb` a mano (lo que alimentó el diseño), Excel para **Mac**
no puede abrirlo con "Get Data > From Database" (falta el ODBC Driver Manager y el
driver de Access para Mac es de **pago**, Actual ODBC). La ruta libre y robusta es
**mdbtools** (CLI, hace streaming; los visores gratuitos truenan con archivos
grandes) — ver `explorar_mdb_cnsf.sh` y la guía `Guia_MDB_Automoviles_CNSF.md`:

```bash
brew install mdbtools          # macOS (o: sudo port install mdbtools)

mdb-tables -1 base.mdb         # lista las tablas (una por línea)
mdb-schema  base.mdb           # DDL: columnas y tipos
mdb-count   base.mdb Tabla     # número de filas

# Exportar una tabla a CSV:
mdb-export base.mdb Tabla > Tabla.csv

# Exportar TODAS las tablas a CSV:
for t in $(mdb-tables -1 base.mdb); do mdb-export base.mdb "$t" > "$t.csv"; done

# Si ves acentos rotos (archivos Access viejos / Jet3):
export MDB_JET3_CHARSET=cp1252
```

Visores con interfaz (alternativas): *MDB Tool* (gratis, pero inestable con
archivos grandes), *MDB ACCDB Viewer* (~USD 20, sin compras dentro de la app).

Como las tablas MDB son grandes, aplica la misma regla que en las hojas pesadas:
el consolidado va a **CSV**, no a xlsx.

---

## Retención de los Excel fuente (estándar de la industria)

**Conserva los Excel originales; no los borres.** Síguese el patrón estándar
(arquitectura *medallion*: crudo/bronce inmutable -> plata -> oro). La capa cruda
es el "sistema de registro": de ahí se reproduce todo lo derivado y es la única
base de auditoría. Los CSV consolidados son derivados/reproducibles; los Excel no.

Razón específica: los portales de gobierno revisan o retiran archivos históricos
sin aviso. Si la CNSF reemplaza un "2018 Bases.xlsx" y ya lo borraste, es
irrecuperable. El disco es trivial (todo el corpus ~pocos GB; Hidro ~30 MB/año).

Este pipeline ya implementa lo operativo de esa política:
- **Hash SHA-256 + tamaño por archivo** en `_estado.json` y en el manifest
  (integridad y deduplicación).
- **Versionado automático**: las versiones previas de archivos que cambian se
  guardan en `_versiones/` en vez de sobrescribirse.

Recomendación de ciclo de vida (sin borrar):
- *Caliente* (últimos ~3-5 años): disco local de trabajo.
- *Frío* (más viejos): comprimidos y/o en almacenamiento barato (disco externo,
  NAS, o S3 con regla de ciclo de vida a clase de archivo). Los `.xls` antiguos
  comprimen mucho; los `.xlsx` ya son ZIP, ahí el ahorro es menor.
- Mantén siempre caliente `_estado.json` y el manifest aunque archives binarios.
- Borrar: solo si hay una segunda copia verificada por hash en otra ubicación.

---

## Almacenamiento de largo plazo (capa consolidada)

La política de arriba cubre los **archivos fuente** (crudo inmutable). Esta sección
es para la **capa consolidada** (los CSV derivados), que es donde el espacio
empieza a importar: Automóviles solo, en Emisión, ronda los ~20 M+ de filas a lo
largo de los años.

**Punto de partida: comprime los CSV con gzip (`.csv.gz`).** Tanto
`consolidar_cnsf.py` como `procesar_autos_cnsf.py` aceptan `--comprimir gzip`
(también `bz2`, `xz`). Se eligió **gzip** como balance óptimo de
**compatibilidad / efectividad**: lo leen de forma transparente y en todos los
sistemas operativos pandas (`pd.read_csv("x.csv.gz")`), R (`readr::read_csv`,
`data.table::fread`), DuckDB y la línea de comandos, sin instalar nada extra.
Reduce típicamente el tamaño 5–10× en datos tabulares como estos.

**Cuidado con el tablero (Power Query en Excel para Mac).** Power Query en Mac es
muy limitado: solo conectores **Text/CSV** y **Excel**. No lee **Parquet** (eso es
de Power BI / vía ODBC), y un `.csv.gz` **no** se carga con un conector nativo:
hay que añadir un paso M manual (`Binary.Decompress(File.Contents(...),
Compression.GZip)` y luego `Csv.Document(...)`). Por eso, para lo que consuma el
tablero conviene **mantener CSV plano** (o generar al vuelo el subconjunto/agregado
que necesite) y dejar la compresión para el almacén y el análisis en Python/R.

**Para máxima compresión + tipos: Parquet (opcional).** Si el almacén analítico lo
consumes desde Python/R/DuckDB (no desde Excel), **Parquet** (con compresión
interna `zstd` o `snappy`) es la mejor opción de largo plazo: columnar, conserva
los tipos de dato, y suele comprimir bastante más que `.csv.gz`. Es portable entre
sistemas (pandas/pyarrow, R `arrow`, DuckDB). La pega: Excel/Power Query no lo lee
directo. Una estrategia práctica es **doble salida**: `.csv.gz` como formato
portable universal + un espejo `.parquet` para análisis pesado.

**Feather/Arrow IPC: NO para archivo.** Feather es excelente para intercambio
rápido entre Python y R en caliente, pero el propio proyecto Arrow recomienda
**Parquet** para almacenamiento de largo plazo (Feather no está pensado como
formato de archivo estable). Úsalo solo como caché de trabajo, no como archivo.

Resumen práctico:

| Uso | Formato recomendado | Lee Excel PQ (Mac) | Lee Python/R/DuckDB |
|---|---|---|---|
| Tablero (Power Query) | CSV plano | Sí | Sí |
| Almacén portable | `.csv.gz` (gzip) | Solo con paso M manual | Sí (transparente) |
| Análisis / máx. compresión | Parquet (zstd) | No | Sí |
| Caché de trabajo Py↔R | Feather | No | Sí (no para archivo) |

Notas finales:
- La capa consolidada es **reproducible** desde el crudo, así que aquí el criterio
  es espacio/comodidad, no preservación: si dudas, gzip y listo.
- **DuckDB** es una gran herramienta gratuita para consultar directamente
  `.csv.gz` o `.parquet` (incluso con SQL y sin cargar todo a memoria), útil para
  las tablas grandes de Automóviles.
- Mantén un formato y nivel de compresión **consistentes** entre años para evitar
  sorpresas al re-leer toda la serie.

---

## Estado de verificación

- **Parseo** (índice + listados): `test_scraper_cnsf.py` (fixtures que replican
  SharePoint con ruido de `__doPostBack` y `.xls`/`.xlsx` mezclados).
- **Orquestación** (SHA-256, estado, detección de cambios, versionado, dry-run):
  `test_orquestacion_cnsf.py` con un servidor falso (sin red). Cubre: descarga
  inicial, corrida sin cambios, cambio de contenido detectado aun con el mismo
  tamaño reportado, archivado de la versión previa, y modo `verificar` sin tocar
  disco.
- **Consolidación**: deriva de columnas validada con un año simulado.
- **Procesador de autos** (`procesar_autos_cnsf.py`): `test_procesar_autos_cnsf.py`
  valida con datos sintéticos la unión multi-año, la resolución de catálogos
  (código + `_desc`, Marca→Marca/Tipo, catálogo entero Subtipo), el centinela
  `ND`→etiqueta sin perder filas, la deriva de columnas y la salida gzip.
- **Pendiente en tu máquina**: descargas en vivo (el entorno de desarrollo bloquea
  `cnsf.gob.mx`) y la unión multi-año con datos reales. Tras la primera descarga
  real, revisa `_reporte.json` por categoría y pásame cualquier encabezado que
  debió emparejar y no lo hizo.

## Related
[[HAZ_MOC]] · Home: [[_INDEX]]

#arm/haz #type/pipeline
