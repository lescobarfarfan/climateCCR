"""
descarga_ibtracs.py
===================
Descarga los datos CRUDOS de IBTrACS (NOAA/NCEI) y registra su PROCEDENCIA para
reproducibilidad total. No transforma nada: solo baja los archivos tal cual y deja
constancia (URL, versión, fecha de descarga UTC, sha256, tamaño).

Diseño (igual que el pipeline CNSF):
  datos/datos_IBTrACS/crudos/        <- archivos fuente, NUNCA se modifican
      ibtracs.EP.list.v04r01.csv
      ibtracs.NA.list.v04r01.csv
      _procedencia.json              <- manifiesto reproducible

Fuente: International Best Track Archive for Climate Stewardship (IBTrACS) v04r01.
  Knapp, K. R., et al. (2010), BAMS 91, 363-376.  DOI del dataset: 10.25921/82ty-9e16
  CSV: https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/v04r01/access/csv/

Nota de entorno: en el sandbox de desarrollo el dominio ncei.noaa.gov puede estar
bloqueado; la descarga real se corre en la máquina del usuario.
"""

from __future__ import annotations
import hashlib
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

VERSION = "v04r01"
BASE_URL = ("https://www.ncei.noaa.gov/data/"
            "international-best-track-archive-for-climate-stewardship-ibtracs/"
            f"{VERSION}/access/csv/")

# Subconjuntos por cuenca relevantes para México: Pacífico Este (EP) y Atlántico Norte (NA).
# Cada subconjunto incluye todas las tormentas con >=1 posición en esa cuenca.
ARCHIVOS = {
    "EP": f"ibtracs.EP.list.{VERSION}.csv",
    "NA": f"ibtracs.NA.list.{VERSION}.csv",
}

DOC_COLUMNAS = (f"{BASE_URL.replace('access/csv/', 'doc/')}"
                f"IBTrACS_{VERSION}_column_documentation.pdf")

DIR_CRUDOS = Path("datos/datos_IBTrACS/crudos")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def descargar(dir_crudos: Path = DIR_CRUDOS, force: bool = False,
              timeout: int = 120) -> dict:
    """
    Descarga los CSV de IBTrACS a dir_crudos (idempotente: no rebaja si ya existe,
    salvo force=True) y escribe/actualiza _procedencia.json.
    """
    dir_crudos.mkdir(parents=True, exist_ok=True)
    procedencia = {
        "fuente": "IBTrACS (NOAA/NCEI)",
        "version": VERSION,
        "doi": "10.25921/82ty-9e16",
        "cita": "Knapp, K. R., et al. (2010), BAMS 91, 363-376.",
        "doc_columnas": DOC_COLUMNAS,
        "fecha_descarga_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "archivos": {},
    }
    for cuenca, nombre in ARCHIVOS.items():
        destino = dir_crudos / nombre
        url = BASE_URL + nombre
        if destino.exists() and not force:
            print(f"[descarga_ibtracs] ya existe, se omite: {destino.name} (usar force=True para rebajar)")
        else:
            print(f"[descarga_ibtracs] descargando {url} ...")
            try:
                urllib.request.urlretrieve(url, destino)
            except Exception as e:
                print(f"[descarga_ibtracs] ERROR al descargar {url}: {e}", file=sys.stderr)
                raise
        procedencia["archivos"][cuenca] = {
            "nombre": destino.name,
            "url": url,
            "sha256": _sha256(destino) if destino.exists() else None,
            "bytes": destino.stat().st_size if destino.exists() else None,
        }
    (dir_crudos / "_procedencia.json").write_text(
        json.dumps(procedencia, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[descarga_ibtracs] procedencia escrita en {dir_crudos/'_procedencia.json'}")
    return procedencia


if __name__ == "__main__":
    descargar(force="--force" in sys.argv)
