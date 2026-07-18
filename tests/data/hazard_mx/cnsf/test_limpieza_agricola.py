"""Correcciones de magnitud del ramo agrícola (limpieza_cnsf §6).

Frames sintéticos mínimos que ejercitan cada regla: superficie ×1000 (emisión y
siniestros, ambas vías), suma ×FIX (firma con prima y vía historial), y los
renglones que NO deben tocarse (limpios, pecuarios, moneda extranjera, firma débil).
"""

import pandas as pd
import pytest
from limpieza_cnsf import (
    COL_PRIMA_EMITIDA,
    COL_SUMA_ASEGURADA,
    COL_SUP_ASEGURADA,
    COL_SUP_SINIESTRADA,
    FIX_PROMEDIO_ANUAL,
    corregir_magnitudes_agricola_emision,
    corregir_magnitudes_agricola_siniestros,
)


def _fila_emision(anio, entidad, cultivo, sup, suma, prima, tipo="Agrícola", moneda="Nacional"):
    return {
        "TIPO SEGURO": tipo,
        "MONEDA": moneda,
        "anio": anio,
        "ENTIDAD": entidad,
        "CULTIVO": cultivo,
        COL_SUP_ASEGURADA: sup,
        COL_SUMA_ASEGURADA: suma,
        COL_PRIMA_EMITIDA: prima,
    }


@pytest.fixture
def emision():
    filas = [
        # (a) superficie ×1000: 10 MXN/ha implícito, ÷1000 => 10,000 MXN/ha en banda
        _fila_emision(2015, "Sinaloa", "Maíz dulce", 6_100_000, 61_000_000, 2_000_000),
        # (b) fix_a: 400k MXN/ha con tasa de prima 0.25% en 2022
        _fila_emision(2022, "Sonora", "Trigo", 100, 40_000_000, 100_000),
        # historial 2019-2021 de Jalisco-Agave a 20k MXN/ha (mediana para fix_b)
        _fila_emision(2019, "Jalisco", "Agave", 100, 2_000_000, 60_000),
        _fila_emision(2020, "Jalisco", "Agave", 100, 2_000_000, 60_000),
        _fila_emision(2021, "Jalisco", "Agave", 100, 2_000_000, 60_000),
        # (b) fix_b: prima 0, 300k MXN/ha = 15x su mediana histórica, 2023
        _fila_emision(2023, "Jalisco", "Agave", 100, 30_000_000, 0),
        # firma débil: prima 0 y SIN historial propio -> NO corregir
        _fila_emision(2024, "Chihuahua", "Arándano", 50, 15_000_000, 0),
        # limpio: 20k MXN/ha, tasa 3%
        _fila_emision(2015, "Jalisco", "Caña", 1_000, 20_000_000, 600_000),
        # fuera de máscara: pecuario y moneda extranjera con valores absurdos
        _fila_emision(2015, "Sonora", "Bovino", 5_000_000, 50_000_000, 1_000_000, tipo="Pecuario"),
        _fila_emision(2022, "Sonora", "Trigo", 100, 40_000_000, 100_000, moneda="Dólares"),
    ]
    return pd.DataFrame(filas)


def test_emision_corrige_y_audita(emision):
    corregido, auditoria = corregir_magnitudes_agricola_emision(emision)

    # (a) superficie ÷1000, montos intactos
    assert corregido.loc[0, COL_SUP_ASEGURADA] == 6_100
    assert corregido.loc[0, COL_SUMA_ASEGURADA] == 61_000_000
    assert corregido.loc[0, "dq_correccion"] == "superficie_div1000"
    assert corregido.loc[0, "dq_valor_original"] == 6_100_000

    # (b) suma ÷FIX del año, superficies/prima intactas
    assert corregido.loc[1, COL_SUMA_ASEGURADA] == pytest.approx(
        40_000_000 / FIX_PROMEDIO_ANUAL[2022]
    )
    assert corregido.loc[1, "dq_correccion"] == "suma_div_fix"
    assert corregido.loc[5, COL_SUMA_ASEGURADA] == pytest.approx(
        30_000_000 / FIX_PROMEDIO_ANUAL[2023]
    )
    assert corregido.loc[5, "dq_correccion"] == "suma_div_fix"

    # sin tocar: firma débil, limpio, pecuario, moneda extranjera, historial
    for idx in (2, 3, 4, 6, 7, 8, 9):
        assert corregido.loc[idx, "dq_correccion"] == ""
        assert corregido.loc[idx, COL_SUMA_ASEGURADA] == emision.loc[idx, COL_SUMA_ASEGURADA]
        assert corregido.loc[idx, COL_SUP_ASEGURADA] == emision.loc[idx, COL_SUP_ASEGURADA]

    # auditoría: un renglón por corrección; el original no se muta
    assert len(auditoria) == 3
    assert set(auditoria["regla"]) == {"superficie_div1000", "suma_div_fix"}
    assert "dq_correccion" not in emision.columns


def _fila_siniestro(anio, entidad, cultivo, sup, monto, tipo="Agrícola", moneda="Nacional"):
    return {
        "TIPO SEGURO": tipo,
        "MONEDA": moneda,
        "anio": anio,
        "ENTIDAD": entidad,
        "CULTIVO": cultivo,
        COL_SUP_SINIESTRADA: sup,
        "MONTO DEL SINIESTRO OCURRIDO": monto,
        "MONTO PAGADO": monto,
    }


def test_siniestros_dos_vias(emision):
    em_corregida, _ = corregir_magnitudes_agricola_emision(emision)
    siniestros = pd.DataFrame(
        [
            # vía razón: 10.1 MXN/ha siniestrada, imposiblemente bajo
            _fila_siniestro(2010, "Chiapas", "Maíz", 49_500_000, 500_000_000),
            # vía emisión: monto 0 pero superficie 820x la asegurada corregida (6,100 ha)
            _fila_siniestro(2015, "Sinaloa", "Maíz dulce", 5_000_000, 0),
            # limpio: 10k MXN/ha
            _fila_siniestro(2015, "Jalisco", "Caña", 1_000, 10_000_000),
        ]
    )

    corregido, auditoria = corregir_magnitudes_agricola_siniestros(
        siniestros, emision_corregida=em_corregida
    )

    assert corregido.loc[0, COL_SUP_SINIESTRADA] == 49_500
    assert corregido.loc[1, COL_SUP_SINIESTRADA] == 5_000
    assert (corregido.loc[[0, 1], "dq_correccion"] == "superficie_div1000").all()
    assert corregido.loc[2, "dq_correccion"] == ""
    assert corregido.loc[2, COL_SUP_SINIESTRADA] == 1_000
    assert len(auditoria) == 2

    # sin emisión de referencia, la vía monto=0 no puede delatar la fila 1
    solo_razon, _ = corregir_magnitudes_agricola_siniestros(siniestros)
    assert solo_razon.loc[1, "dq_correccion"] == ""
    assert solo_razon.loc[0, "dq_correccion"] == "superficie_div1000"
