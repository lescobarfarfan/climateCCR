"""Prueba de procesar_autos_cnsf.py con datos sintéticos.

Sustituye (monkeypatch) las costuras que tocan mdbtools/zip por datos en memoria,
y verifica: unión de 2008 (subconjunto) + 2024 (canónico), centinela ND ->
"No disponible", expansión de Marca a Marca_desc/Tipo_desc, deriva (columnas
faltantes rellenadas vacías) y salida comprimida gzip legible.
"""

import json
import tempfile
from pathlib import Path

import pandas as pd
import procesar_autos_cnsf as P

# La config canónica viaja junto al script, no con el CWD de pytest.
CONFIG_JSON = Path(P.__file__).resolve().parent / "config" / "catalogos_autos_cnsf.json"

# --- datos sintéticos por año/tabla -------------------------------------- #
DATA = {
    2008: {
        # Emisión 2008: SIN 'Forma de Venta' ni 'Subtipo de Seguro' (subconjunto)
        "Emision": pd.DataFrame(
            {
                "Entidad": ["01"],
                "Marca": ["0124"],
                "Tipo de Vehiculo": ["01"],
                "Cobertura": ["06"],
                "Deducible": ["0"],
                "Numero de Vehiculos": ["10"],
                "Prima Emitida": ["100.5"],
            }
        ),
        "Entidad": pd.DataFrame({"Estado": ["01", "17"], "Nombre": ["Aguascalientes", "Morelos"]}),
        "Marca": pd.DataFrame({"CLAVE": ["0124"], "MARCA": ["NISSAN"], "TIPO": ["SEDAN"]}),
        "Cobertura": pd.DataFrame({"Clave": ["06"], "Descripcion": ["Daños"]}),
        "Tipo de vehiculo": pd.DataFrame({"Clave": ["01"], "Tipo de vehiculo": ["Automovil"]}),
    },
    2024: {
        # Emisión 2024: esquema canónico completo. Fila 2 con Marca='ND'.
        "Emision": pd.DataFrame(
            {
                "Entidad": ["17", "01"],
                "Marca": ["0124", "ND"],
                "Tipo de Vehiculo": ["01", "01"],
                "Forma de Venta": ["05", "05"],
                "Cobertura": ["06", "06"],
                "Subtipo de Seguro": ["0", "0"],
                "Deducible": ["0", "1"],
                "Numero de Vehiculos": ["5", "3"],
                "Prima Emitida": ["50.0", "30.0"],
            }
        ),
        "Entidad": pd.DataFrame({"Estado": ["01", "17"], "Nombre": ["Aguascalientes", "Morelos"]}),
        "Marca_tipo": pd.DataFrame({"CLAVE": ["0124"], "MARCA": ["NISSAN"], "TIPO": ["SEDAN"]}),
        "Cobertura": pd.DataFrame({"Clave": ["06"], "Descripcion": ["Daños"]}),
        "Tipo de vehiculo": pd.DataFrame({"Clave": ["01"], "Tipo de vehiculo": ["Automovil"]}),
        "Forma de Venta": pd.DataFrame({"Clave": ["05"], "Descripcion": ["Agente"]}),
        "Subtipo de Seguro": pd.DataFrame({"Clave": ["0"], "Descripcion": ["Tradicional"]}),
    },
}


def _anio(mdb: Path) -> int:
    return int(P.RE_ANIO.search(str(mdb)).group(0))


def _patch(monkey_target):
    def _descomprimir(zip_path, destino):
        return Path(f"mdb-{_anio(Path(zip_path))}")

    def _columnas(mdb, tabla):
        df = DATA.get(_anio(mdb), {}).get(tabla)
        return list(df.columns) if df is not None else None

    def _leer_completa(mdb, tabla):
        df = DATA.get(_anio(mdb), {}).get(tabla)
        return None if df is None else df.copy()

    def _iter_chunks(mdb, tabla, chunksize=P.CHUNK):
        df = DATA.get(_anio(mdb), {}).get(tabla)
        if df is not None:
            yield df.copy()

    monkey_target._descomprimir = _descomprimir
    monkey_target._columnas = _columnas
    monkey_target._leer_completa = _leer_completa
    monkey_target._iter_chunks = _iter_chunks


def test_descubrir_subcarpetas():
    """descubrir_zips prioriza subcarpetas por subsector y respalda con sueltos."""
    config = json.loads(CONFIG_JSON.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as t:
        r = Path(t) / "automoviles"
        (r / "individual").mkdir(parents=True)
        (r / "flotilla").mkdir()
        (r / "individual" / "Autos_individual 2008.ZIP").write_bytes(b"")  # .ZIP mayúscula
        (r / "individual" / "Autos Individual 2024.zip").write_bytes(b"")
        (r / "flotilla" / "Autos Flotilla 2009.zip").write_bytes(b"")
        (r / "Autos_individual 2014.zip").write_bytes(b"")  # suelto (compat)
        (r / "salida_mdb.zip").write_bytes(b"")  # ruido a ignorar
        (r / "salida_mdb").mkdir()
        z = P.descubrir_zips(r, config)
        assert sorted(z["individual"]) == [2008, 2014, 2024], z
        assert sorted(z["flotilla"]) == [2009], z
    print("OK: descubrimiento por subcarpetas individual/flotilla + respaldo suelto")


def test_flotilla_normalizado():
    """Las columnas de flotilla (minúsculas/singular + 'Tipo de poliza') deben
    resolverse con la MISMA config que individual, vía emparejamiento normalizado."""
    config = json.loads(CONFIG_JSON.read_text(encoding="utf-8"))
    chunk = pd.DataFrame(
        {
            "Tipo de poliza": ["1", "ND"],  # minúscula; catálogo Tipo de poliza
            "Tipo de vehiculo": ["01", "01"],  # individual usa 'Tipo de Vehiculo'
            "Tipo de perdida": ["01", "01"],  # individual usa 'Tipo de Perdida'
            "Causa del Siniestro": ["06", "06"],  # config tiene 'Causa del siniestro'
            "Monto de siniestro": ["10", "20"],  # medida (sin catálogo)
        }
    )
    lookups = {
        "Tipo de poliza": {"1": ("Flotilla",)},
        "Tipo de vehiculo": {"01": ("Automovil",)},
        "Tipo de perdida": {"01": ("Robo total",)},
        "Causa del Siniestro": {"06": ("Choque",)},
    }
    out = P.resolver_chunk(chunk.copy(), "Siniestros", config, lookups, {"ND"}, "No disponible")
    assert out.loc[0, "Tipo de poliza_desc"] == "Flotilla"
    assert out.loc[1, "Tipo de poliza_desc"] == "No disponible"  # centinela ND
    # 'Tipo de Vehiculo' (config) ~ 'Tipo de vehiculo'
    assert out.loc[0, "Tipo de vehiculo_desc"] == "Automovil"
    assert out.loc[0, "Tipo de perdida_desc"] == "Robo total"
    # 'Causa del siniestro' (config) ~ 'Causa del Siniestro'
    assert out.loc[0, "Causa del Siniestro_desc"] == "Choque"
    orden = P._orden_salida(list(chunk.columns), "Siniestros", config)
    for c in ("Tipo de poliza_desc", "Tipo de vehiculo_desc", "Causa del Siniestro_desc"):
        assert c in orden, c
    print("OK flotilla: Tipo de poliza + columnas minúscula resueltas con la misma config")


def test_anio_nombres_heterogeneos():
    """El año debe detectarse con espacios, guiones bajos, mezcla y mayúsculas."""
    casos = {
        "Autos individual 2017.zip": 2017,
        "Autos_individual_2018.zip": 2018,  # all-underscore (el bug original)
        "Autos_individual 2015.zip": 2015,
        "AUTOS_FLOTILLA_2009.ZIP": 2009,
        "Autos Individual 2024.zip": 2024,
        "salida_mdb.zip": None,
    }
    for nombre, esperado in casos.items():
        assert P._año_de(nombre) == esperado, (nombre, P._año_de(nombre))
    print("OK: año detectado con espacios/guiones/mezcla/mayúsculas")


def main():
    _patch(P)
    test_anio_nombres_heterogeneos()
    test_descubrir_subcarpetas()
    test_flotilla_normalizado()
    config = json.loads(CONFIG_JSON.read_text(encoding="utf-8"))

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "automoviles"
        root.mkdir()
        # zips vacíos: solo el nombre importa (las costuras están parcheadas)
        (root / "Autos_individual 2008.zip").write_bytes(b"")
        (root / "Autos_individual 2024.zip").write_bytes(b"")
        out = Path(tmp) / "out"

        P.procesar(root, out, config, compresion="gzip")

        csv_gz = out / "automoviles_individual" / "emision.csv.gz"
        assert csv_gz.exists(), "no se generó el CSV comprimido"
        df = pd.read_csv(csv_gz, dtype=str, keep_default_na=False)  # lee gzip transparente

        print("Columnas de salida:\n ", list(df.columns))
        print("Filas:", len(df))

        # provenance
        for c in ("subsector", "anio", "archivo_origen"):
            assert c in df.columns, f"falta columna {c}"
        assert set(df["anio"]) == {"2008", "2024"}, "deben unirse ambos años"

        # interleave código + _desc y expansión de Marca
        for c in (
            "Entidad",
            "Entidad_desc",
            "Marca",
            "Marca_desc",
            "Tipo_desc",
            "Forma de Venta",
            "Forma de Venta_desc",
            "Subtipo de Seguro",
            "Subtipo de Seguro_desc",
        ):
            assert c in df.columns, f"falta columna {c}"

        # resolución de catálogos
        f2024 = df[df["anio"] == "2024"].reset_index(drop=True)
        fila0 = f2024.iloc[0]
        assert fila0["Entidad"] == "17" and fila0["Entidad_desc"] == "Morelos"
        assert fila0["Marca"] == "0124" and fila0["Marca_desc"] == "NISSAN"
        assert fila0["Tipo_desc"] == "SEDAN"
        assert (
            fila0["Subtipo de Seguro"] == "0" and fila0["Subtipo de Seguro_desc"] == "Tradicional"
        ), "el catálogo entero (Subtipo) debe resolverse contra el código texto '0'"

        # centinela ND -> etiqueta, fila conservada
        fila_nd = f2024.iloc[1]
        assert (
            fila_nd["Marca"] == "ND"
            and fila_nd["Marca_desc"] == "No disponible"
            and fila_nd["Tipo_desc"] == "No disponible"
        ), "ND debe etiquetarse, no perderse"

        # deriva 2008: columnas canónicas ausentes -> vacías; sus _desc vacíos
        f2008 = df[df["anio"] == "2008"].reset_index(drop=True).iloc[0]
        assert (
            f2008["Forma de Venta"] == "" and f2008["Forma de Venta_desc"] == ""
        ), "columnas ausentes en 2008 deben quedar vacías"
        assert f2008["Subtipo de Seguro"] == "" and f2008["Subtipo de Seguro_desc"] == ""
        # pero las que sí existen se resuelven (Marca via catálogo 'Marca')
        assert f2008["Marca_desc"] == "NISSAN" and f2008["Tipo_desc"] == "SEDAN"

        # reporte de deriva
        rep = json.loads((out / "automoviles_individual" / "_reporte.json").read_text())
        der = rep["tablas"][0]["deriva_por_anio"]
        assert "2008" in der and "Forma de Venta" in der["2008"]["faltantes_rellenadas_vacio"]

    print("\nOK: unión de años, código+_desc, Marca->Marca/Tipo, ND->etiqueta, deriva y gzip")


if __name__ == "__main__":
    main()
