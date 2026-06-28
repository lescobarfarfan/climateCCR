# Guía: explorar y extraer las bases MDB de la CNSF (Automóviles) en macOS

Las categorías como **Automóviles** no publican Excel: el enlace del portal es un
`.zip` que adentro trae una base **Microsoft Access `.mdb`** con varias tablas
(Emisión, Siniestros, **catálogos** con claves, y tablas extra propias de autos).

Esta guía cubre, de punta a punta y **sin software de pago**:
1. preparar el entorno,
2. inventariar la base (tablas, esquema con relaciones, conteos),
3. convertirla a **SQLite** para explorarla con una interfaz gráfica,
4. (alternativa) exportar tablas a **CSV**,
5. qué información extraer para diseñar el pipeline.

El driver ODBC de Excel para Mac **no se usa aquí**: es de pago y la prueba
gratuita corta a 3 filas por tabla. Esta ruta es libre y maneja tablas grandes.

---

> **Atajo:** todo esto está automatizado en el script **`explorar_mdb_cnsf.sh`**.
> Corre `./explorar_mdb_cnsf.sh "2024 Automoviles Bases.mdb"` (o `*.mdb` para varios
> años) y genera el inventario, esquema, muestras, CSV y la base SQLite de una vez.
> Los comandos manuales de abajo están corregidos para **nombres de tabla con
> espacios** (p. ej. "Causa del Siniestro"): se recorren con `while IFS= read -r t`,
> nunca con `for t in $(...)`, porque esto último parte los nombres por los espacios.

## 1. Preparar el entorno (una sola vez)

Necesitas Homebrew. Si no lo tienes:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Instala las herramientas:

```bash
brew install mdbtools sqlite        # mdbtools: leer .mdb | sqlite3: crear la BD
brew install --cask db-browser-for-sqlite   # interfaz gráfica para explorar
```

- **mdbtools**: utilidades de línea de comandos para leer Access (`mdb-tables`,
  `mdb-schema`, `mdb-count`, `mdb-export`). Hace *streaming*, así que aguanta
  tablas grandes sin truenes.
- **DB Browser for SQLite**: app gratuita (sqlitebrowser.org) para navegar la
  base, ver la estructura y correr consultas/JOINs.

---

## 2. Descomprimir e inventariar la base

```bash
# Ubícate donde está el zip de Automóviles
cd ~/Downloads/cnsf_autos          # ajusta la ruta

unzip "Automoviles Bases.zip"      # ajusta el nombre real
# Confirma el nombre del .mdb resultante:
ls -lh *.mdb
MDB="2024 Automoviles Bases.mdb"   # <-- pon aquí el nombre exacto del archivo
```

### 2.1 Lista de tablas

```bash
mdb-tables -1 "$MDB"               # una tabla por línea
```

### 2.2 Conteo de filas por tabla (para saber qué es catálogo y qué es dato)

```bash
while IFS= read -r t; do
  printf '%8s  %s\n' "$(mdb-count "$MDB" "$t")" "$t"
done < <(mdb-tables -1 "$MDB") | sort -n
```

Los **catálogos** tendrán pocas filas (decenas/cientos); **Emisión/Siniestros**
y tablas de detalle tendrán miles/millones.

### 2.3 Esquema COMPLETO con relaciones (clave para el pipeline)

```bash
mdb-schema --relations --indexes "$MDB" > esquema_autos.sql
```

Este archivo muestra columnas, tipos, índices y **claves foráneas** (cómo se
vinculan los catálogos con Emisión/Siniestros). Es lo más valioso para diseñar
la resolución de claves.

> Si ves acentos rotos (archivos Access viejos, formato "Jet3"):
> ```bash
> export MDB_JET3_CHARSET=cp1252
> ```
> y vuelve a correr los comandos.

---

## 3. Convertir el `.mdb` a SQLite (recomendado para explorar)

SQLite te deja navegar todo y hacer JOINs entre catálogos y tablas — justo lo que
Excel+ODBC no permite.

```bash
SQLITE="autos.sqlite"
rm -f "$SQLITE"

# 3.1 Crear la estructura (esquema en dialecto SQLite)
mdb-schema "$MDB" sqlite | sqlite3 "$SQLITE"

# 3.2 Cargar los datos de cada tabla
while IFS= read -r t; do
  echo "Cargando: $t"
  ( echo "BEGIN;"; mdb-export -I sqlite "$MDB" "$t"; echo "COMMIT;" ) | sqlite3 "$SQLITE"
done < <(mdb-tables -1 "$MDB")

echo "Listo -> $SQLITE"
```

Ábrelo en **DB Browser for SQLite**:
- Pestaña **Database Structure**: ves todas las tablas y sus columnas.
- Pestaña **Execute SQL**: corre consultas, p. ej. unir Emisión con un catálogo:

```sql
-- Ejemplo (ajusta nombres de tabla/columna a los reales del esquema):
SELECT e.*, c.descripcion AS cobertura_desc
FROM   Emision e
LEFT JOIN CatCobertura c ON c.clave = e.cobertura
LIMIT 100;
```

> **Si tu versión de mdbtools no acepta el backend `sqlite`** (raro, pero pasa en
> versiones viejas): usa la ruta CSV de la sección 4 e importa los CSV en DB
> Browser (File ▸ Import ▸ Table from CSV file). El `esquema_autos.sql` del paso
> 2.3 te sigue dando el mapa de relaciones.

---

## 4. (Alternativa) Exportar tablas a CSV

Útil si solo quieres ver datos en Excel/Numbers o para alimentar el consolidador.

```bash
mkdir -p csv
while IFS= read -r t; do
  safe="${t// /_}"; safe="${safe//\//_}"   # nombre de archivo sin espacios
  mdb-export "$MDB" "$t" > "csv/${safe}.csv"
done < <(mdb-tables -1 "$MDB")
ls -lh csv/
```

Cada CSV abre directo en Excel/Numbers y en Power Query (Data ▸ Get Data ▸ From
Text/CSV), que en Mac **sí** funciona.

---

## 5. Qué extraer para diseñar el pipeline

Cuando termines de explorar, lo más útil para mí es:

1. **`esquema_autos.sql`** (el de `--relations`) — el mapa de tablas y claves.
2. La **salida de conteos** del paso 2.2 (qué tablas son catálogo vs. datos).
3. Los **catálogos completos** en CSV (son chicos): `csv/Cat*.csv` o equivalentes.
4. De **Emisión** y **Siniestros**: los **encabezados** y unas **20–50 filas de
   muestra** (no hace falta todo):
   ```bash
   mdb-export "$MDB" Emision    | head -50 > muestra_emision.csv
   mdb-export "$MDB" Siniestros | head -50 > muestra_siniestros.csv
   ```

Con eso puedo diseñar la extensión del pipeline para Automóviles:
- bajar el `.zip` (hay que agregar `.zip` a las extensiones del scraper),
- extraer el `.mdb`,
- exportar Emisión/Siniestros y **resolver las claves de catálogo** a sus valores
  legibles (los JOINs),
- emitir los CSV consolidados igual que en las demás categorías.

---

## Apéndice — comandos de referencia (mdbtools)

| Comando | Para qué |
|---|---|
| `mdb-tables -1 base.mdb` | listar tablas (una por línea) |
| `mdb-schema --relations --indexes base.mdb` | esquema + claves foráneas + índices |
| `mdb-schema base.mdb sqlite` | esquema en dialecto SQLite |
| `mdb-count base.mdb Tabla` | número de filas |
| `mdb-export base.mdb Tabla > Tabla.csv` | exportar tabla a CSV |
| `mdb-export -I sqlite base.mdb Tabla` | exportar como INSERT (SQLite) |
| `export MDB_JET3_CHARSET=cp1252` | arreglar acentos en archivos Access viejos |
