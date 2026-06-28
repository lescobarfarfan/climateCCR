# Diseño del pipeline de Automóviles (CNSF)

Basado en el análisis de los `.mdb` de **Autos Individual** (2007–2024) y **Autos
Flotilla** (2008/2009, 2014, 2015, 2020, 2021, 2024).

### Diferencias de Flotilla vs Individual (confirmadas)

La estructura y los catálogos de Flotilla son casi idénticos a Individual (misma
evolución por años, mismos catálogos con las mismas llaves). Tres diferencias:

1. **Columna/catálogo extra `Tipo de poliza`** (Clave→Descripcion: 1=Flotilla,
   2=Plan Piso, 3=Otros), presente en Emisión, Siniestros y Unidades Expuestas en
   todos los años. Ya está en `catalogos_autos_cnsf.json` (catálogo + uniones);
   Individual lo ignora porque sus tablas no tienen esa columna.
2. **Nombres de columna en distinta caja/número** (p. ej. Individual
   "Monto de Siniestros"/"Tipo de Perdida"/"Causa del siniestro" vs Flotilla
   "Monto de siniestro"/"Tipo de perdida"/"Causa del Siniestro"; Emisión usa
   "Tipo de **P**oliza" pero Siniestros "Tipo de **p**oliza"). Por eso el
   procesador empareja las uniones por **nombre normalizado** (sin acentos, sin
   distinguir mayúsculas), de modo que **una sola config** sirve para ambos.
3. **Tablas temporales de Access** (`~TMPCLP…`, copias basura) en algunos años
   (p. ej. 2015). No requieren nada: el procesador solo lee las tablas por nombre
   (hechos + catálogos), nunca enumera todas, así que esas `~TMP` jamás se tocan.

El procesador es el mismo para ambos subsectores; solo cambia la subcarpeta de
entrada (`individual/`, `flotilla/`) y la de salida (`automoviles_individual/`,
`automoviles_flotilla/`).

---

## 1. Hallazgos del análisis

### 1.1 Evolución de la estructura (qué tablas hay por año)

| Año(s) | Cambio estructural |
|---|---|
| **2007** | **Formato DISTINTO (ancho).** Emisión/Siniestros con una columna por cobertura (`PRIMA_DM`, `PRIMA_RT`, `SA_GM`, `MTO_SIN_RCB`…). Catálogos: `Marca`, `Modelo`, `Entidad`, `Tipo de vehiculo`, `Clave_amis`, `Descripcion de variables`. **Incompatible** con el resto. |
| **2008–2013** | Formato largo. Aparecen `Cobertura`, `Tipo de perdida`, `Unidades Expuestas` (sustituye a `Modelo`). Catálogo `Marca`. |
| **2014** | `Marca` → **`Marca_tipo`** (mismas columnas CLAVE/MARCA/TIPO). Aparece `Forma de Venta` (en Emisión). |
| **2015** | Aparece **`Subtipo de Seguro`** (catálogo + columna). |
| **2020** | Aparece **`Causa del Siniestro`** (catálogo + columna en Siniestros). |
| **2021** | Aparece **`Prima Devengada Acumulada`** (Emisión). |
| **2022–2024** | Estable. |

Dos cortes mayores coinciden con los otros sectores (**2015** y **2020/2021**),
más el origen atípico (**2007**) y el canónico (**2024**).

### 1.2 Esquema canónico (2024)

- **Emisión** (14 col): Entidad, Marca, Tipo de Vehiculo, Forma de Venta,
  Cobertura, Subtipo de Seguro, Deducible, Numero de Vehiculos, Prima Emitida,
  Prima Cedida, Prima Devengada, Comision Directa, Suma Asegurada, Prima
  Devengada Acumulada. (~3.38 M filas en 2024)
- **Siniestros** (16 col): Tipo de Vehiculo, Marca, Deducible, Cobertura,
  Entidad, Tipo de Perdida, Subtipo de Seguro, Causa del siniestro, Numero de
  Vehiculos, Monto de Siniestros, Monto Pagado, Salvamentos, Gastos de Ajuste,
  Monto de Deducible, Monto Reaseguro, Monto Recuperado. (~586 K filas)
- **Unidades Expuestas** (auto-específica): Clave AMIS, Modelo, Subtipo de
  Seguro, Unidades Expuestas. (~264 K filas)

### 1.3 Cosas que definen el diseño

- **Todo son códigos guardados como texto** (Entidad "17", Marca "0124",
  Cobertura "06"…), tanto en Emisión como en Siniestros. Ambas tablas necesitan
  **resolverse contra catálogos** (no como en los xlsx, donde ya venían textos).
- **Faltantes = `"ND"`** (confirmado: muchos primeros renglones de Siniestros
  traen `ND` en vehículo/marca/deducible/subtipo). Se tratan con LEFT JOIN +
  etiqueta "No disponible", **sin perder filas**.
- **Renombre de catálogo `Marca`→`Marca_tipo`**: el resolutor acepta ambos
  nombres (alias).
- **Desajustes de llave**: `Subtipo de Seguro` es entero en el catálogo pero
  texto en el hecho ("0"); `Tipo de Vehiculo` es `Text(3)` en el hecho y
  `Text(2)` en el catálogo. Hay que **normalizar la llave** antes de unir.
- **Volumen**: Emisión suma ~20 M+ filas en 17 años → **CSV obligatorio** y
  **procesamiento por año** (no cargar todo en memoria).
- **`Deducible`** no tiene catálogo (se conserva el código tal cual).
- **2007 es un caso aparte** (formato ancho): requiere un adaptador propio o
  excluirse (ver decisiones).

El mapa completo de uniones (columna del hecho → catálogo → llave → descripción)
está en **`catalogos_autos_cnsf.json`**.

---

## 2. Arquitectura propuesta

Dos capas, como pediste: **verificación/actualización integrada** y
**procesamiento independiente**.

```
            ┌─────────────────────────────────────────────┐
            │  CAPA COMPARTIDA  (scraper_cnsf.py)           │
            │  descarga + verificación + estado             │
            │  - reconoce .zip (autos) ✔  [ya integrado]    │
            │  - sha256, manifest, _estado.json, versionado │
            │  - decide nuevo / cambiado / sin_cambio       │
            └───────────────┬───────────────┬──────────────┘
                            │               │
         sectores xlsx ─────┘               └───── automóviles (.zip)
                 │                                       │
   ┌─────────────▼─────────────┐         ┌───────────────▼───────────────┐
   │ consolidar_cnsf.py        │         │ procesar_autos_cnsf.py  (NUEVO)│
   │ (Emisión/Suma/Siniestros) │         │ INDEPENDIENTE                  │
   └───────────────────────────┘         │  unzip → mdb → extraer →       │
                                          │  resolver catálogos →          │
                                          │  alinear deriva → CSV          │
                                          │  (individual y flotillas)      │
                                          └────────────────────────────────┘
```

- **Integrado** (ya hecho): el scraper trata los `.zip` igual que los xlsx —los
  descarga, calcula su SHA-256, los registra en el `manifest` y el `_estado.json`,
  detecta cambios y versiona. Solo agregué `.zip` a las extensiones.
- **Independiente**: el procesamiento de autos vive en un módulo aparte
  (`procesar_autos_cnsf.py`), porque su lógica (MDB + catálogos + 2 subsectores)
  no tiene nada que ver con los xlsx. En `--modo sync` se enruta así: las
  categorías xlsx van a `consolidar_cnsf`; **automóviles** va al procesador de
  autos. (El consolidador xlsx de hecho ignora autos solo: no encuentra `.xlsx`.)

---

## 3. El procesador de autos

`procesar_autos_cnsf.py`, por subsector (individual / flotilla):

**Organización por subsector (descarga y procesamiento).** El scraper descarga
cada `.zip` a una **subcarpeta por subsector** según el nombre del archivo:
`automoviles/individual/…` y `automoviles/flotilla/…`. El procesador respeta esa
estructura: lee las subcarpetas (y, por compatibilidad, también `.zip` sueltos en
`automoviles/` clasificados por el nombre). Así no se mezclan los subsectores.

**El año se toma del nombre del `.zip`.** En algunos años (p. ej. 2008–2009) el
`.mdb` extraído NO trae el año en su nombre; solo el `.zip` lo tiene. El pipeline
nunca usa el nombre del `.mdb` para el año: lo deriva del `.zip` y cada año se
extrae a su propia carpeta temporal, así que no hay colisión aunque el `.mdb`
interno tenga un nombre genérico.

Pasos:

1. **Descomprimir** cada `.zip` a un `.mdb` (en una carpeta de trabajo temporal).
2. **Leer** con mdbtools (`mdb-export`), tabla por tabla.
3. **Cargar catálogos** del año (son chicos) en diccionarios `código → descripción`.
4. Para cada **tabla de hecho** (Emisión, Siniestros, Unidades Expuestas):
   - leer **por año** y en **chunks** (Emisión es enorme),
   - **resolver** cada columna-código vía LEFT JOIN con su catálogo
     (normalizando la llave; `ND`/sin match → "No disponible", fila conservada),
   - **alinear la deriva**: esquema canónico = año más reciente, rellenar
     columnas faltantes en años viejos, reportar,
   - **anexar** al CSV de salida (streaming, no acumular en memoria).
5. Emitir **un CSV por (subsector, tabla)** + un `_reporte.json`.

### Salida

```
datos/cnsf_consolidado/
  automoviles_individual/
    emision.csv[.gz]
    siniestros.csv[.gz]
    unidades_expuestas.csv[.gz]
    _reporte.json
  automoviles_flotilla/
    ... (misma forma)
```

### Resolución de códigos (propuesta por defecto)

Conservar el **código** y **agregar** la descripción como columna nueva
(sufijo `_desc`), p. ej. `Entidad` (código) + `Entidad_desc` ("Aguascalientes").
Es reversible y auditable, y Power Query usa la que prefieras. `Marca` se expande
a dos: `Marca_desc` (MARCA) y `Marca_tipo_desc` (TIPO).

---

## 4. Decisiones que necesito confirmar antes de construir

1. **2007**: ¿lo **excluimos** del consolidado (recomendado para v1; son 17 años
   2008–2024 igual) o quieres un **adaptador** que "despivotee" su formato ancho
   (una fila por cobertura) para incorporarlo?
2. **Códigos**: ¿te sirve el default **código + columna `_desc`**, o prefieres
   **reemplazar** el código por la descripción, o **dejar solo el código**?
3. **Marca**: ¿expandir a `Marca_desc` + `Marca_tipo_desc` (MARCA y TIPO)?
4. **Unidades Expuestas**: ¿lo quieres como **tercer CSV** (unido a `Clave_amis`),
   o por ahora solo Emisión y Siniestros?
5. **Centinela**: para autos confirmo solo `"ND"` → "No disponible" con la fila
   conservada (LEFT JOIN). ¿Algún otro valor que hayas visto como faltante?

Con tus respuestas armo `procesar_autos_cnsf.py` y el enrutamiento en el
`--modo sync` del scraper. La config de catálogos/uniones ya está lista en
`catalogos_autos_cnsf.json` (reutilizable para flotillas).

## Related
[[HAZ_MOC]] · Home: [[_INDEX]]

#arm/haz #type/pipeline
