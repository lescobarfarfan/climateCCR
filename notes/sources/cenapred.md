# Fuente de datos: CENAPRED — Impacto socioeconómico de desastres — Tier 1

**Peril canónico:** todos (multi-peril); rol de **impacto** (pérdida TOTAL, no asegurada).
**Rol en el proyecto:** puente asegurado→económico — relativizar la pérdida CNSF (penetración = pagado asegurado ÷ daño total) y proveer el daño observado para calibrar funciones de impacto.
**Estado:** scripts construidos y probados con datos sintéticos fieles al crudo; descarga real pendiente de correr en la máquina del usuario (dominios CENAPRED bloqueados en sandbox, igual que CNSF).
**Documento principal:** `referencias_riesgo_catastrofico.md` (§5.4 Tier 1 #3, §5.5).

---

## 1. Qué es y por qué es Tier 1

CENAPRED publica desde 2000 la serie *Impacto socioeconómico de los principales desastres ocurridos en la República Mexicana* (24+ volúmenes), el acervo nacional de referencia sobre el **costo total** de los desastres. La evaluación valora las afectaciones de los sectores público, privado y social, en su mayoría a **costo de reposición**, con una metodología **basada en la DaLA de la CEPAL** adaptada a México. Importante: sus montos **difieren de FONDEN** (que solo reconstruye infraestructura pública y vivienda en pobreza patrimonial) — es pérdida económica total, no gasto fiscal. Por eso es el denominador natural para medir la brecha de protección frente a la pérdida asegurada CNSF.

## 2. Fuentes y URLs (verificadas)

1. **Base abierta a NIVEL EVENTO (machine-readable), 2000–2015:**
   `https://www.cenapred.unam.mx/DatosAbiertos/BASE_IMPACTO_SOCIOECONOMICO_DESASTRES_2000_2015.csv`
   (publicada vía datos.gob.mx, institución CENAPRED). Estructura por evento: fechas, año, mes, tipo (`HIDRO`/`GEO`), subtipo (`CT`, `LLUV`, `DESLIZ`, …), clave(s) y nombre(s) de estado(s), municipios, descripción, defunciones, población afectada, viviendas, escuelas, ha de cultivo, km de carretera, **daños totales (millones MXN corrientes)** y **millones USD**, tipo de declaratoria, fuente y nombre del evento (p. ej. *Ciclón Juliette*).

2. **Publicaciones 2016+** — conviven en **tres dominios** (`cenapred.unam.mx`, `olmeca.cenapred.unam.mx`, `cenapred.gob.mx`); `olmeca` expone un **índice Apache navegable** (`/es/Publicaciones/archivos/`) que lista todo el directorio — el modo `sync` lo scrapea por regex, así que descubre años nuevos y extensos faltantes automáticamente. Inventario verificado (semillas del scraper):

   | Año | Resumen ejecutivo | Documento extenso |
   |---|---|---|
   | 2016 | `unam.mx/.../368-RESUMENEJECUTIVOIMPACTO2016.PDF` | `gob.mx/.../384-IMPACTO2016OEFINAL12FEBRERO2018.PDF` |
   | 2017 | `unam.mx/.../403-NO.19-RESUMENEJECUTIVOIMPACTO2017.PDF` | `unam.mx/.../415-IMPACTO_SOCIOECONOMICO_2017.PDF` |
   | 2018 | `olmeca/.../409-RESUMENEJECUTIVOIMPACTO2018.PDF` | `gob.mx/.../430-IMPACTO_SOCIOECONOMICO_2018.PDF` |
   | 2019 | `unam.mx/.../429-RESUMENEJECUTIVOIMPACTO2019.PDF` ⚠️ | `gob.mx/.../457-IMPACTO_SOCIOECONOMICO_2019.PDF` |
   | 2020 | `gob.mx/.../455-RESUMENEJECUTIVOIMPACTO2020.PDF` ⚠️ | `gob.mx/.../482-IMPACTO_SOCIOECONOMICO_2020.PDF` |
   | 2021 | `unam.mx/.../487-RESUMENEJECUTIVOIMPACTO2021.PDF` ⚠️ | `unam.mx/.../493-IMPACTO_SOCIOECONOMICO_2021.PDF` |
   | 2022 | `gob.mx/.../494-RESUMENEJECUTIVOIMPACTO2022.pdf` | `olmeca/.../501-IMPACTO_SOCIOECONOMICO_2022.PDF` |
   | 2023 | `gob.mx/.../504-RESUMENEJECUTIVOIMPACTO2023.PDF` | `gob.mx/.../517-IMPACTO_SOCIOECONOMICO_2023.PDF` |
   | 2024 | solo resumen (vía buscador de publicaciones) ⚠️ | aún no publicado |

   **Serie de extensos 2016–2023 COMPLETA con URL verificada** (hueco real: solo 2024). Corrida real confirmó además que el descubrimiento sobre el índice olmeca recupera los **extensos 2000–2015** (corroboración del CSV) y que los espejos importan: los mismos archivos existen en los tres dominios pero **cada dominio bloquea rutas distintas con 403** (olmeca sirvió su índice y los PDFs antiguos pero bloqueó `501-…2022`; gob.mx sirve los PDFs pero bloquea su listado) → el scraper hace **fallback automático entre espejos** y registra la `url_efectiva` en la procedencia. ⚠️ = el resumen de ese año reporta estados solo como **porcentajes de los top** y agrupa el resto en "otros estados" (2021: 32% en "otros") → **no utilizable** para el panel estatal (ver §6bis). Último recurso: `olmeca/.../archivos.zip` (4.5 GB, el acervo completo).

3. Cifras de control para validar la ingesta (de los propios resúmenes): 2022 = 16,600 MDP en 570 eventos; 2023 = 88,910 MDP en 393 eventos (año Otis); 2024 = 14,434 MDP en 283 eventos.

## 3. Almacenamiento robusto, log y procedencia

```
datos/datos_CENAPRED/
  crudos/                                # NUNCA se modifica
    BASE_IMPACTO_SOCIOECONOMICO_DESASTRES_2000_2015.csv
    RESUMEN_{2016..}.pdf / EXTENSO_{2016..}.pdf
    _procedencia.json                    # URL, sha256, bytes, fecha UTC por archivo
  captura/                               # capturas manuales estructuradas (ver §6bis)
    captura_extenso_{anio}.csv
  consolidados/
    impacto_estado_anio_peril.csv        # ESTRUCTURA A, CSV 2000-2015
    eventos_cenapred_climada.csv         # ESTRUCTURA B, CSV 2000-2015
    impacto_multiestado.csv              # multi-estado no repartidos (2000-2015)
    impacto_estado_anio_peril_extensos.csv  # ESTRUCTURA A, capturas 2016+
    eventos_cenapred_climada_extensos.csv   # ESTRUCTURA B, capturas 2016+
    catalogo_fenomenos_climaticos.csv       # CATÁLOGO ocurrencia clima (evento×estado)
  _log_cenapred.log                      # log de control de cada corrida
```

## 4. Scripts

- **`src/descarga_cenapred.py`** — modos `--modo sync|verificar|descargar` (patrón `scraper_cnsf.py`):
  - `sync`: descarga el CSV si falta y **descubre** PDFs nuevos en la página de publicaciones (regex sobre `RESUMENEJECUTIVOIMPACTO{AAAA}`), bajando solo lo faltante → **sabe si hay información que actualizar** (un año nuevo aparece en la página ⇒ se detecta y baja).
  - `verificar`: compara checksums locales vs `_procedencia.json` (sin red).
  - `descargar`: re-descarga todo. Reintentos con backoff y User-Agent (patrón SIAP).
- **`src/procesar_cenapred.py`** — limpieza y generación de las DOS estructuras. El encabezado real se **valida contra un mapa de conceptos** (`CONCEPTOS`); si un requerido no empata, **falla ruidosamente** con un reporte de columnas (no procesa a ciegas). Limpieza: números con separador de miles → float; entidades con `limpieza_cnsf.clasificar_entidad` (mismo estándar CNSF); montos en MXN **corrientes** (deflactar aparte, igual que CNSF); subtipos sin mapeo → `__SIN_MAPEO__` con aviso.
- **`src/procesar_captura_extensos.py`** — valida e integra las capturas manuales de los extensos 2016+ (§6bis): columnas requeridas, `pagina_pdf` obligatoria, total anual vs `CIFRAS_CONTROL` (falla si desvía >5%), mapeo de perils con la misma taxonomía, salidas A/B `*_extensos.csv`. Plantilla en `plantillas/captura_extenso_PLANTILLA.csv`.

## 5. Las dos estructuras de salida (y por qué son distintas)

La calibración de este proyecto y la calibración de funciones de impacto en CLIMADA (rama del chat de funciones de daño; ver `diseno_calibracion_funciones_impacto_mexico.md`) requieren **granos distintos**:

| | **A: panel** `impacto_estado_anio_peril.csv` | **B: eventos** `eventos_cenapred_climada.csv` |
|---|---|---|
| Grano | (entidad, año, peril canónico) | EVENTO individual |
| Consumidor | λ(estado, año) y severidad; penetración vs CNSF (que es estado×año) | `climada.util.calibrate`: daño observado por evento vs `Impact` modelado del evento |
| Multi-estado | **Excluido y NO repartido** (principio del proyecto: sin certeza no se fabrica estructura espacial); va a `impacto_multiestado.csv` para reconciliación nacional | **Conservado como UN registro** con `estados = E1|E2|…`: la calibración suma el impacto modelado sobre esos estados y lo compara con el daño observado total — análogo estado-evento del esquema país-evento de Eberenz et al. (2021) con EM-DAT |
| Campos clave | n_eventos, danio_mdp, danio_mdd, defunciones, pob_afectada, viviendas | evento_id, **nombre_evento** (emparejable con IBTrACS `NAME`+año → SID), fechas, peril, estados, danio_mdp/mdd, declaratoria, fuente, descripción |
| Alcance | clima (con bandera `en_alcance_climatico`) | TODOS los eventos (sismo/volcán con bandera `no`, útiles para validar la ingesta) |

**CATÁLOGO de fenómenos climáticos (`catalogo_fenomenos_climaticos.csv`).** Tercera salida, pedida para uso transversal: una fila por **(evento climático × estado afectado)** con año, mes, fechas (inicio/fin/duración), peril canónico, subtipo, nombre del evento, municipios (texto crudo; mayoría "Varios municipios"), y el **daño como total del evento** con banderas `multi_estado`/`n_estados_evento` — es un catálogo de **ocurrencia** del peligro: explotar por estado es legítimo para presencia, pero el daño NO se reparte (se etiqueta como conjunto). Útil como insumo directo de frecuencia λ, cross-check con declaratorias/IBTrACS, y esqueleto del empate hazard↔pérdida. Las capturas de extensos 2016+ alimentan el mismo catálogo al compartir esquema.

El **empalme B↔IBTrACS** para ciclones: `nombre_evento` (p. ej. "Ciclón Odile") + año → `NAME`/`SEASON` de IBTrACS → `SID` → huella de viento del evento → daño modelado vs `danio_mdp`. Esa es exactamente la pareja (hazard por evento, daño observado por evento) que pide la calibración de `v_half`.

## 6. Supuestos de procesamiento (cada uno con su referencia o justificación)

1. **Daño total a costo de reposición, metodología CEPAL-adaptada** — declarado por CENAPRED en los resúmenes ejecutivos; la DaLA de la CEPAL es el estándar regional de evaluación de daños y pérdidas (CEPAL, *Handbook for Disaster Assessment*, 2014).
2. **Montos en MXN corrientes** (millones). No se deflactan aquí: la deflactación es un paso común a CNSF/CENAPRED (INPC, Banxico/INEGI) para mantener consistencia entre numerador y denominador de la penetración.
3. **Multi-estado: no repartir.** Mismo principio documentado para CNSF (recuadro §4 del documento principal): el daño conjunto reportado no trae distribución por estado y repartirlo (igualitario o proporcional) fabricaría estructura espacial. En A se excluye (y se reporta su % del daño total en el log); en B se conserva como un registro porque el esquema de calibración por evento puede consumirlo sin repartir.
4. **GEO (sismo/volcán/tsunami) fuera del alcance climático** pero conservado con bandera — coherente con la exclusión de geofísicos del proyecto (v0.2) y útil como control de ingesta.
5. **Mapeo de subtipos a perils canónicos** (`PERILS_CENAPRED`) alineado al catálogo CNSF (`mapa_perils_seguros_a_canonico.csv`); lo no reconocido va a `__SIN_MAPEO__` para revisión manual, nunca asignación silenciosa (mismo patrón que `mapear_peril` de `limpieza_cnsf`).
6. **Encabezados del crudo CONFIRMADOS contra la descarga real** (24 columnas; el mapa `CONCEPTOS` quedó fijado a ellos y la validación ruidosa se mantiene como guardia ante futuros cambios). Hallazgos incorporados de la inspección real:
   - **Dos fechas** (`Fecha de Inicio`/`Fecha de Fin`): se parsean (d-m-aa, dayfirst) y se deriva `duracion_dias`; el texto crudo se conserva en `*_raw` porque sequías largas traen rangos textuales no parseables ("Mayo de 2000 a marzo de 2001") — esas filas quedan con fecha NaT y texto íntegro, nunca se inventan fechas.
   - **`Clasificacion del fenomeno` = nivel 1** (Geológico/Hidrometeorológico/…) y **`Tipo de fenomeno` = subtipo** (Ciclón tropical, Sequía, …) — el mapeo de perils opera sobre el subtipo, consistente con la regla de §6bis.
   - **No hay columna de nombre del evento**: para ciclones, el nombre viene dentro de `Observaciones` ("Ciclon Carlotta. El Huracan decrecio…"). `extraer_nombre_evento` lo extrae por regex (tipo + Nombre propio capitalizado, incl. depresiones numeradas "Once-E"), evitando falsos positivos como "el huracán decreció" o el genérico "ciclón tropical". Este nombre alimenta el empalme B↔IBTrACS; las filas sin nombre se emparejan por fechas+estados.
   - **Codificación: latin1** (confirmado en corrida real; utf-8 falla en acentos/ñ). El lector intenta utf-8 estricto y cae a latin1 con aviso en el log — nunca `errors="replace"`, que produciría mojibake silencioso.
   - Columnas adicionales conservadas en B: `Sustancia involucrada` (químico-tecnológicos) y `Documentado`.
7. **Catálogo de CÓDIGOS del crudo confirmado contra la corrida real completa** (el crudo usa códigos, no palabras). Clima=sí: `CT` ciclón tropical, `LLUV`, `INUN/INUND`, `SEQ`, `HELADA`, `BT` bajas temperaturas, `GRAN`, `NEV`, `TORN`, `FV` fuertes vientos, `TS` tormenta severa *[confirmar etiqueta]*, `TE` tormenta eléctrica *[confirmar]*, `MT` marea de tormenta *[confirmar]*, `MF` mar de fondo, `OC` onda cálida, `DESLIZ` (bajo GEO), **`IF` incendio forestal (bajo QUIM — 504 eventos; la trampa LGPC de §6bis confirmada en datos)**. Fuera de alcance con etiqueta legible: `IU` incendio urbano, `FUG`, `EXPL`, `DERME`, `INTOX`, `FLAM` (QUIM); `ATRANS` accidente de transporte (1,555 eventos), `ATRAB`, `DERRS` (SOCIO); `EPI`, `PLAG`, `TOX` (SAN); `SIS`, `VOLC`, `TSU` (GEO). **Regla de fallback por clasificación:** subtipos no reconocidos bajo QUIM/SOCIO/SAN mapean automáticamente a fuera-de-alcance (etiqueta `Clasificación (código)`, silencioso); el aviso ruidoso `__SIN_MAPEO__` se reserva para HIDRO/GEO desconocidos — los únicos potencialmente climáticos que exigen revisión manual.
8. **Robustecimientos de la corrida real:** (a) separador de estados por coma **y conjunción "y"/"e"** ("Morelos y Sonora", "Tabasco y Veracruz"); (b) typo `Chichuahua`→Chihuahua añadido a `limpieza_cnsf`; (c) `Varios estados`/`Todo el pais`/`Nacional` clasifican como **no localizado** (se conservan en B para reconciliación, fuera del panel y del catálogo — no repartir); (d) fechas con sentinela **`SD`** (sin dato) → NA limpio antes del parseo; (e) el nombre del ciclón se busca en `Observaciones` **y también en `Descripción`** (inconsistencia confirmada: no todos los CT lo traen en Observaciones; CENAPRED como fuente es más consistente que CENACOM), con columna `nombre_origen`; los CT sin nombre se cuentan en el log y se empalman con IBTrACS por **fechas+estados**.
7. **2016+ desde PDFs:** los resúmenes ejecutivos se descargan como crudo con procedencia, pero la **extracción tabular de PDFs es un paso aparte** (semi-manual o con parser dedicado) que se documentará cuando se aborde; las cifras de control de §2.3 sirven para validarla. Honestidad: hasta entonces, la serie machine-readable termina en 2015 y la penetración 2016+ usará los agregados anuales de los resúmenes.

## 6bis. Extracción 2016+: el problema de asignación y la decisión de captura

**Diagnóstico del problema que motiva esta sección.** Los agregados por estado de los *resúmenes ejecutivos* tienen dos defectos estructurales, independientes de la calidad de extracción del PDF: (1) **mezclan perils** — el caso CDMX 2017 lo ilustra: su monto está dominado por el sismo del 19-S, no atribuible al clima; un total estatal mixto no puede entrar al panel climático aunque se extraiga perfectamente; y (2) **son incompletos por diseño desde 2019** — porcentajes de los estados top y un residuo "otros estados" sin detalle (32% del total en 2021). **Conclusión de diseño: el grano utilizable es el EVENTO/fenómeno, nunca el total estatal mixto.** Con datos por evento, el sismo es una fila `Geológico/Sismo` que el pipeline marca `en_alcance_climatico = no` automáticamente — el problema desaparece porque nunca se usa la tabla equivocada. Los **documentos extensos** (serie completa 2016–2022, §2) sí traen ese detalle por fenómeno/evento/estado.

**Decisión: captura MANUAL ESTRUCTURADA, no parser automático.** Evaluación honesta de costo: el universo es pequeño y acotado (7 documentos, +1 por año), los diseños cambian año con año (confirmado por el usuario), y un parser robusto exigiría una plantilla por año más QA visual de cada salida — es decir, trabajo manual disfrazado, con riesgo de errores **silenciosos** en montos: el peor defecto posible para un dataset de calibración. La captura manual con esquema fijo es más rápida (~1–3 h por año contra ~1 semana de desarrollo+debug del parser) y, sobre todo, **auditable**. La reproducibilidad no se pierde, se traslada del código al protocolo:

1. **Esquema fijo** (`plantillas/captura_extenso_PLANTILLA.csv`): `anio, fenomeno_nivel1, subtipo_texto, nombre_evento, fecha_texto, entidad, danio_mdp, defunciones, pob_afectada, pagina_pdf, notas`. Un archivo por año en `datos/datos_CENAPRED/captura/captura_extenso_{anio}.csv`.
2. **Procedencia por página obligatoria**: cada cifra cita la página del PDF (cuyo sha256 está en `_procedencia.json`) — cualquier número es re-verificable contra el documento exacto.
3. **Validación ruidosa** (`src/procesar_captura_extensos.py`): la suma anual capturada se compara contra la cifra de control nacional del resumen (`CIFRAS_CONTROL`, tolerancia 5% por refinaciones del extenso); desviaciones mayores **detienen** el proceso. Salidas en las mismas estructuras A/B (`*_extensos.csv`), con multi-estado no repartido (solo en B).
4. Apoyo opcional: pre-extraer tablas candidatas con `pdfplumber`/`camelot` para reducir tecleo, pero el entregable es siempre el CSV verificado por humano.

**Taxonomía para empatar con el CSV 2000–2015.** Los extensos se estructuran por los capítulos de la Ley General de Protección Civil; el empate es:

| Capítulo del extenso (nivel 1) | Subtipos típicos | Equivalente CSV 2000–2015 | `peril_canonico` | ¿Clima? |
|---|---|---|---|---|
| Hidrometeorológicos | ciclón tropical, lluvias, inundación, sequía, helada, nevada, granizada, vientos/tornado, onda cálida | `HIDRO` / `CT, LLUV, INUN, SEQ, …` | según subtipo | **sí** |
| Geológicos | sismo, volcán, tsunami | `GEO` / `SIS, VOLC` | Sismo, Act. volcánica, Tsunami | no |
| Geológicos | **deslizamiento / inestabilidad de laderas** | `GEO` / `DESLIZ` | Deslizamiento | **sí** (detonado por lluvia — igual que en el CSV, donde `DESLIZ` viene bajo `GEO`) |
| Químico-tecnológicos | **incendio forestal** | — | Incendio forestal | **sí** (proxy; el hazard viene de CONAFOR/FIRMS) |
| Químico-tecnológicos (resto), Sanitario-ecológicos (p. ej. **COVID, que domina 2020**), Socio-organizativos | explosiones, epidemias, concentraciones | — | fuera | no |

La regla operativa: **el alcance climático se decide por SUBTIPO, no por capítulo** (deslizamiento es capítulo geológico pero clima=sí; incendio forestal es químico-tecnológico pero clima=sí; COVID queda fuera automáticamente). Esto es exactamente lo que codifica `mapear_peril` y garantiza que la serie 2016+ capturada sea homogénea con la 2000–2015 procesada del CSV.

**Cobertura resultante por ventana:** 2000–2015 → CSV abierto (pipeline automático); 2016–2023 → capturas estructuradas de los **extensos** (serie disponible, protocolo de arriba; 2023 con cifra de control 88,910 MDP); **2024 → único hueco real** (solo resumen): puente provisional con los totales nacionales *por fenómeno* del resumen + DesInventar/EM-DAT para el detalle por evento, hasta que el extenso 2024 se publique (`sync` lo detectará).

**Sobre reconstruir montos desde noticias/comunicados: NO.** Contraviene los estándares del proyecto: cifras periodísticas son preliminares, metodológicamente heterogéneas (daño ≠ pérdida ≠ gasto fiscal), con sesgo de cobertura y no re-derivables. Uso aceptable: desambiguación cualitativa puntual de un evento (fecha/estado), documentada, nunca como cifra del panel. El complemento institucional correcto para validación cruzada 2016+ es **DesInventar Sentinel** (evento/municipal, etiquetado por fenómeno, machine-readable; Tier 2 #6) y **EM-DAT** para eventos mayores.

## 7. Reproducibilidad (resumen)

1. `python src/descarga_cenapred.py --modo sync` → crudos + `_procedencia.json` + log.
   - **Si falla con `CERTIFICATE_VERIFY_FAILED`** (visto en corrida real, macOS): (a) instalar `certifi` (`pip install certifi`) o correr `Install Certificates.command` del instalador de Python — el script usa `certifi` automáticamente si está; (b) si persiste, es la **cadena de certificados incompleta del servidor** de gobierno: re-correr con `--inseguro` (decisión explícita, con advertencia en el log; nunca fallback silencioso) y validar después la integridad con `--modo verificar` (sha256 de `_procedencia.json`).
2. `python src/descarga_cenapred.py --modo verificar` → integridad de los crudos (checksums).
   - Ante `403 Forbidden` en un archivo puntual, el scraper prueba automáticamente los **dominios espejo** (gob.mx ↔ unam.mx ↔ olmeca) y corta los reintentos inútiles (403/404/410 son definitivos).
3. `python src/procesar_cenapred.py` → estructuras A, B y multi-estado en `consolidados/`.
4. Versionar en git scripts, este documento, `_procedencia.json` y el log; los crudos pesados se verifican por checksum.

## 7bis. Inspección en Excel (nota operativa)

Las salidas de `consolidados/` son **CSV UTF-8 (sin BOM), RFC 4180, finales de línea LF** (los crudos 2016+ se leen como latin1 según §6, pero el pipeline **emite** UTF-8). Están pensadas para consumirse con parsers conformes —`pandas`, módulo `csv`, R `readr`/`read.csv`—, donde se leen **sin problema en cualquier sistema operativo**. El CSV canónico es la **fuente de verdad** del pipeline y **no se modifica** para acomodar a Excel.

**No abrir los `.csv` con doble clic ni importarlos con el conector CSV de Excel (incluido Power Query).** Excel los rompe de dos formas independientes:

1. **Acentos/caracteres especiales (mojibake).** Excel asume la codepage del sistema (Windows-1252) en lugar de UTF-8. Se mitiga eligiendo origen **65001: Unicode (UTF-8)** al importar.
2. **Registros partidos.** El campo `municipios` (en `catalogo_fenomenos_climaticos.csv`) y `municipio` (en `eventos_cenapred_climada.csv`) traen saltos de línea incrustados heredados del crudo de CENAPRED. El importador de Excel corta el registro en esos saltos y desplaza las columnas: aparecen filas donde `evento_id` muestra un nombre de municipio en vez del patrón `CEN-AAAA-NNNNN`. **Este defecto persiste aunque el encoding se importe bien** — Power Query con UTF-8 corrige los acentos pero NO el desfase de filas (verificado empíricamente: una corrida del catálogo con 3,046 registros se importó como 3,076 filas; las +30 son exactamente los saltos incrustados).

**Forma correcta de explorar en Excel:** convertir a `.xlsx` con Python (el parser es Python, no Excel) y abrir ese archivo. Los saltos incrustados quedan dentro de la celda sin partir el registro y los acentos quedan correctos:

```python
import pandas as pd
df = pd.read_csv("consolidados/catalogo_fenomenos_climaticos.csv")
df.to_excel("catalogo_fenomenos_climaticos.xlsx", index=False)
```

El `.xlsx` resultante es una **vista desechable**: no entra a git ni al pipeline (§7.4); el CSV sigue siendo la única fuente de verdad.

## 8. Referencias

- **CENAPRED.** *Impacto socioeconómico de los principales desastres ocurridos en la República Mexicana* (serie anual, 24+ volúmenes; resúmenes ejecutivos 2016–2024 en cenapred.gob.mx/es/Publicaciones). — fuente primaria.
- **CENAPRED (datos abiertos).** *Base de impacto socioeconómico de desastres 2000–2015* (CSV, cenapred.unam.mx/DatosAbiertos; catalogada en datos.gob.mx). — fuente machine-readable.
- **CEPAL (2014).** *Handbook for Disaster Assessment* (metodología DaLA). — base metodológica declarada por CENAPRED. *[confirmar edición exacta citada por CENAPRED]*
- **Eberenz, S., S. Lüthi & D. N. Bresch (2021).** Regional tropical cyclone impact functions for globally consistent risk assessments. *NHESS* 21, 393–415. — esquema de calibración por evento contra daños reportados que consume la estructura B (DOI 10.5194/nhess-21-393-2021).
- **Aznar-Siguan, G. & D. N. Bresch (2019).** CLIMADA v1. *GMD* 12, 3085–3097. — plataforma destino de la estructura B.

## Related
[[HAZ_MOC]] · Home: [[_INDEX]]

#arm/haz #type/source
