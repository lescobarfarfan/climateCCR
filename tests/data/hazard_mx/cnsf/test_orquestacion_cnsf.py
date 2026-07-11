"""
Prueba de la lógica de sincronización del scraper CNSF SIN red.
Monkeypatch de las tres costuras de red: inventario_remoto, _head_meta, _descargar_a.
"""

import hashlib
import shutil
from pathlib import Path

import scraper_cnsf as S
from scraper_cnsf import ArchivoCNSF, cargar_estado, guardar_estado, sincronizar

CAT = "Agrícola y Animales"
SLUG = "agricola_y_animales"

# "Servidor" falso: url -> {data, last_modified, etag}
REMOTO: dict = {}


def _arch(anio, nombre, kb):
    url = f"https://www.cnsf.gob.mx/.../AyA Bases/{nombre}"
    return ArchivoCNSF(
        categoria=CAT,
        categoria_slug=SLUG,
        anio=anio,
        nombre_archivo=nombre,
        url=url,
        ext=".xlsx",
        tamano_kb=kb,
    )


def _set_remoto(url, data: bytes, lm="Mon, 01 Jan 2024 00:00:00 GMT", etag='"v1"'):
    REMOTO[url] = {"data": data, "last_modified": lm, "etag": etag}


# --- parches de red ---
def fake_head(session, url, timeout=30):
    e = REMOTO[url]
    return {"bytes": len(e["data"]), "last_modified": e["last_modified"], "etag": e["etag"]}


def fake_descargar_a(session, url, tmp_path, **kw):
    data = REMOTO[url]["data"]
    Path(tmp_path).write_bytes(data)
    return len(data), hashlib.sha256(data).hexdigest()


def aplicar_parches():
    S._head_meta = fake_head
    S._descargar_a = fake_descargar_a


def main():
    aplicar_parches()
    out = Path("/home/claude/prueba_sync")
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    a2024 = _arch(2024, "2024 Agricola Bases.xlsx", 544)
    a2023 = _arch(2023, "2023 Agricola Bases.xlsx", 584)
    _set_remoto(a2024.url, b"CONTENIDO-2024-v1" * 100)
    _set_remoto(a2023.url, b"CONTENIDO-2023-v1" * 100)

    # ---------- Run 1: descarga inicial ----------
    estado = cargar_estado(out)
    r1 = sincronizar(None, [a2024, a2023], out, estado)
    guardar_estado(out, estado)
    assert (r1.nuevos, r1.cambiados, r1.sin_cambio) == (2, 0, 0), vars(r1)
    assert (out / SLUG / "2024 Agricola Bases.xlsx").exists()
    assert estado[a2024.clave()]["sha256"] == hashlib.sha256(REMOTO[a2024.url]["data"]).hexdigest()
    assert r1.categorias_cambiadas == {SLUG}
    print("Run1 OK: 2 nuevos, sha256 guardado:", estado[a2024.clave()]["sha256"][:12], "...")

    # ---------- Run 2: sin cambios ----------
    estado = cargar_estado(out)
    r2 = sincronizar(None, [a2024, a2023], out, estado)
    guardar_estado(out, estado)
    assert (r2.nuevos, r2.cambiados, r2.sin_cambio) == (0, 0, 2), vars(r2)
    assert r2.categorias_cambiadas == set()
    print("Run2 OK: sin cambios, 0 descargas, categorias_cambiadas vacío")

    # ---------- Run 3: 2024 cambia de contenido + aparece 2022 ----------
    _set_remoto(
        a2024.url,
        b"CONTENIDO-2024-v2-DISTINTO" * 100,
        lm="Tue, 01 Apr 2025 00:00:00 GMT",
        etag='"v2"',
    )  # mismo kb en listado
    a2022 = _arch(2022, "2022 Agricola Bases.xlsx", 631)
    _set_remoto(a2022.url, b"CONTENIDO-2022-v1" * 100)

    sha_2024_v1 = estado[a2024.clave()]["sha256"]
    estado = cargar_estado(out)
    r3 = sincronizar(None, [a2024, a2023, a2022], out, estado)
    guardar_estado(out, estado)
    assert (r3.nuevos, r3.cambiados, r3.sin_cambio) == (1, 1, 1), vars(r3)
    # versión previa de 2024 archivada
    vers = list((out / "_versiones" / SLUG).glob("2024 Agricola Bases.*.xlsx"))
    assert len(vers) == 1, vers
    assert sha_2024_v1[:8] in vers[0].name, vers[0].name
    # sha de 2024 actualizado al v2
    assert estado[a2024.clave()]["sha256"] == hashlib.sha256(REMOTO[a2024.url]["data"]).hexdigest()
    assert estado[a2024.clave()]["sha256"] != sha_2024_v1
    assert r3.categorias_cambiadas == {SLUG}
    print("Run3 OK: 1 nuevo (2022), 1 cambiado (2024 detectado por content-length/etag),")
    print("         versión previa archivada:", vers[0].name)

    # ---------- Modo verificar (dry) sobre un cambio futuro, sin escribir ----------
    _set_remoto(a2023.url, b"CONTENIDO-2023-v2" * 120, etag='"v2"')
    estado = cargar_estado(out)
    rep = S._reporte_verificacion(None, [a2024, a2023, a2022], estado, out)
    assert rep["cambiados"] == 1 and rep["sin_cambio"] == 2 and rep["nuevos"] == 0, rep
    # verificar NO debe haber descargado/modificado disco
    assert estado[a2023.clave()]["sha256"] == hashlib.sha256(b"CONTENIDO-2023-v1" * 100).hexdigest()
    print("Verificar OK: detecta 1 cambiado (2023) en dry-run, sin tocar disco")

    print("\nTODAS LAS PRUEBAS DE ORQUESTACIÓN PASARON")


if __name__ == "__main__":
    main()
