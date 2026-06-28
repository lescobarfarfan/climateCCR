#!/usr/bin/env bash
#
# explorar_mdb_cnsf.sh
# ====================
# Inventaria y extrae bases Microsoft Access (.mdb) de la CNSF (Automóviles, etc.)
# de forma reproducible y SIN romperse con nombres de tabla que tienen espacios
# (p. ej. "Causa del Siniestro", "Forma de Venta").
#
# Por cada .mdb genera una carpeta con:
#   tablas.txt              lista de tablas (una por línea)
#   conteos.txt             filas por tabla (ordenado), para distinguir catálogo vs dato
#   esquema_relaciones.sql  mdb-schema --relations --indexes (estructura + llaves)
#   esquema_sqlite.sql      esquema en dialecto SQLite (si tu mdbtools lo soporta)
#   muestras.txt            encabezado + primeras filas de cada tabla (ver códigos y "ND")
#   csv/<Tabla>.csv         export completo de cada tabla (nombre de archivo saneado)
#   <archivo>.sqlite        base navegable en DB Browser for SQLite (si hay sqlite3)
#
# USO:
#   chmod +x explorar_mdb_cnsf.sh
#   ./explorar_mdb_cnsf.sh "2024 Automoviles Bases.mdb"
#   ./explorar_mdb_cnsf.sh *.mdb                 # varios años de una vez
#
# OPCIONES (variables de entorno):
#   SALIDA=carpeta     carpeta base de resultados        (default: salida_mdb)
#   MUESTRA_N=5        filas de muestra por tabla         (default: 5)
#   CHARSET=cp1252     arregla acentos en Access viejos   (default: vacío)
#   SIN_CSV=1          no exportar CSV completos (solo inventario/muestras/sqlite)
#   SIN_SQLITE=1       no construir la base SQLite
#
# El truco clave para los espacios: NO usar  for t in $(mdb-tables ...)  (eso parte
# por espacios), sino leer línea por línea con  while IFS= read -r t.

set -uo pipefail

: "${SALIDA:=salida_mdb}"
: "${MUESTRA_N:=5}"
: "${CHARSET:=}"
: "${SIN_CSV:=0}"
: "${SIN_SQLITE:=0}"
[ -n "$CHARSET" ] && export MDB_JET3_CHARSET="$CHARSET"

log() { printf '%s\n' "$*" >&2; }
err() { printf 'ERROR: %s\n' "$*" >&2; }

# --- Dependencias -----------------------------------------------------------
for bin in mdb-tables mdb-schema mdb-export mdb-count; do
  command -v "$bin" >/dev/null 2>&1 || {
    err "Falta '$bin'. Instálalo con:  brew install mdbtools"; exit 1; }
done
HAY_SQLITE=1
if [ "$SIN_SQLITE" = "1" ] || ! command -v sqlite3 >/dev/null 2>&1; then
  HAY_SQLITE=0
  [ "$SIN_SQLITE" = "1" ] || log "Aviso: no encontré 'sqlite3'; me salto la conversión a SQLite (brew install sqlite)."
fi

[ "$#" -ge 1 ] || { err "Uso: $0 <archivo1.mdb> [archivo2.mdb ...]"; exit 1; }

# Reemplaza espacios y diagonales por guion bajo (para nombres de archivo).
sanitizar() { local s="$1"; s="${s// /_}"; s="${s//\//_}"; printf '%s' "$s"; }

procesar() {
  local MDB="$1"
  [ -f "$MDB" ] || { err "No existe el archivo: $MDB"; return 1; }

  local stem dir csvdir anio tag
  stem="$(basename "$MDB")"; stem="${stem%.*}"
  dir="$SALIDA/$(sanitizar "$stem")"
  csvdir="$dir/csv"
  mkdir -p "$dir"

  # Año extraído del nombre (primer 19xx/20xx). Portable bash+zsh con grep.
  anio="$(printf '%s' "$stem" | grep -oE '(19|20)[0-9]{2}' | head -1 || true)"
  tag="${anio:+_$anio}"          # "_2024" si hay año; "" si no se encontró

  # Rutas de salida con el año en el nombre.
  local tablas="$dir/tablas$tag.txt"
  local conteos="$dir/conteos$tag.txt"
  local muestras="$dir/muestras$tag.txt"

  log "==============================================================="
  log "Procesando: $MDB   (año: ${anio:-?})"
  log "Salida:     $dir"

  # 1) Lista de tablas (una por línea; preserva espacios).
  if ! mdb-tables -1 "$MDB" > "$tablas"; then
    err "No pude leer las tablas de $MDB (¿archivo dañado o no es .mdb?)"; return 1
  fi
  local n; n="$(grep -c . "$tablas" || true)"
  log "Tablas encontradas: $n"

  # 2) Esquema con relaciones e índices (con respaldo si faltan esas banderas).
  mdb-schema --relations --indexes "$MDB" > "$dir/esquema_relaciones$tag.sql" 2>/dev/null \
    || mdb-schema "$MDB" > "$dir/esquema_relaciones$tag.sql"

  # 3) Conteos + 4) muestras + export CSV — recorriendo LÍNEA POR LÍNEA.
  : > "$conteos"
  : > "$muestras"
  [ "$SIN_CSV" = "1" ] || mkdir -p "$csvdir"

  while IFS= read -r t || [ -n "$t" ]; do
    [ -z "$t" ] && continue
    local c; c="$(mdb-count "$MDB" "$t" 2>/dev/null || echo '?')"
    printf '%10s  %s\n' "$c" "$t" >> "$conteos"

    {
      printf '\n===== %s  (%s filas) =====\n' "$t" "$c"
      mdb-export "$MDB" "$t" 2>/dev/null | head -n "$((MUESTRA_N + 1))"
    } >> "$muestras"

    if [ "$SIN_CSV" != "1" ]; then
      if ! mdb-export "$MDB" "$t" > "$csvdir/$(sanitizar "$t").csv" 2>/dev/null; then
        err "No pude exportar a CSV la tabla: $t"
      fi
    fi
  done < "$tablas"

  sort -n "$conteos" -o "$conteos"

  # 5) Conversión a SQLite (si hay sqlite3 y el backend 'sqlite' funciona).
  if [ "$HAY_SQLITE" -eq 1 ]; then
    local db="$dir/$(sanitizar "$stem").sqlite"
    rm -f "$db"
    if mdb-schema "$MDB" sqlite > "$dir/esquema_sqlite$tag.sql" 2>/dev/null && [ -s "$dir/esquema_sqlite$tag.sql" ]; then
      sqlite3 "$db" < "$dir/esquema_sqlite$tag.sql"
      while IFS= read -r t || [ -n "$t" ]; do
        [ -z "$t" ] && continue
        if ! { echo "BEGIN;"; mdb-export -I sqlite "$MDB" "$t" 2>/dev/null; echo "COMMIT;"; } | sqlite3 "$db"; then
          err "No pude cargar a SQLite la tabla: $t"
        fi
      done < "$tablas"
      log "SQLite -> $db  (ábrelo en DB Browser for SQLite)"
    else
      log "Aviso: tu mdbtools no soporta el backend 'sqlite'. Quedan los CSV en $csvdir/."
      rm -f "$dir/esquema_sqlite$tag.sql"
    fi
  fi

  log "Hecho: $MDB"
}

rc=0
for f in "$@"; do
  procesar "$f" || rc=1
done

log ""
log "=== TERMINADO ==="
log "Por cada archivo, revisa en $SALIDA/<nombre>/ :"
log "  conteos_<año>.txt y tablas_<año>.txt  -> qué tablas hay (compara años con 'diff')"
log "  esquema_relaciones_<año>.sql          -> estructura y llaves"
log "  muestras_<año>.txt                    -> ver códigos y faltantes ('ND')"
log "  csv/ y el .sqlite                     -> datos completos"
exit $rc
