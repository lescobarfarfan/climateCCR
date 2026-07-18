"""Smoke test del inspector de calidad de datos (climateCCR.data.inspeccion).

Panel sintético determinista con UN error de magnitud plantado (superficie ×1000,
el patrón "Maíz dulce Sinaloa 2015"); el inspector debe marcarlo como
`error_probable` y escribir hallazgos.csv + resumen.md + figuras.
"""

import matplotlib

matplotlib.use("Agg")

import pandas as pd
from climateCCR.data.inspeccion import inspect_dataset, resolve_column, robust_z


def _panel() -> pd.DataFrame:
    filas = []
    for e, entidad in enumerate(["Sinaloa", "Jalisco", "Sonora"]):
        for c, cultivo in enumerate(["Maíz dulce", "Trigo"]):
            for anio in range(2008, 2025):
                sup = 900 + 50 * ((anio + e + c) % 7)
                valor_ha = 18_000 + 300 * ((anio - 2008) % 5) + 1_000 * e
                filas.append(
                    {
                        "ENTIDAD": entidad,
                        "CULTIVO": cultivo,
                        "anio": anio,
                        "SUPERFICIE ASEGURADA\n(HECTÁREAS)": sup,
                        "SUMA ASEGURADA": sup * valor_ha,
                    }
                )
    df = pd.DataFrame(filas)
    plantado = (df["ENTIDAD"] == "Sinaloa") & (df["CULTIVO"] == "Maíz dulce") & (df["anio"] == 2015)
    df.loc[plantado, "SUPERFICIE ASEGURADA\n(HECTÁREAS)"] *= 1000  # montos intactos
    return df


def test_detecta_error_x1000_y_escribe_salidas(tmp_path):
    tabla = inspect_dataset(
        _panel(),
        tmp_path,
        time_col="anio",
        group_cols=("entidad", "cultivo"),  # resolución laxa de nombres
        ratios=(("suma asegurada", "superficie asegurada (hectáreas)"),),
        source="panel sintético",
    )

    errores = tabla[tabla["triaje"] == "error_probable"]
    assert not errores.empty
    assert errores["donde"].str.contains("Sinaloa").any()
    assert errores["donde"].str.contains("2015").any()
    # los demás grupos no producen errores probables (sin falsos positivos)
    assert not errores["donde"].str.contains("Sonora|Jalisco").any()

    assert (tmp_path / "hallazgos.csv").exists()
    assert (tmp_path / "resumen.md").exists()
    assert list((tmp_path / "figuras").glob("*.png"))


def test_utilidades_basicas():
    df = pd.DataFrame({"SUMA ASEGURADA": [1.0]})
    assert resolve_column(df, "suma  asegurada") == "SUMA ASEGURADA"
    z = robust_z(pd.Series([10.0, 11, 9, 10, 12, 10, 1000]))
    assert z.abs().idxmax() == 6 and z.abs().max() > 5
