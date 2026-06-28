"""
validacion_sequia.py
====================
Valida el cálculo PROPIO de SPI/SPEI (periodo 1991-2020) contra el producto oficial
ERA5-Drought de Copernicus.

Razón: solo si reproducimos al producto oficial (que también usa 1991-2020) podemos
confiar en los números del periodo 1961-1990, que NO existe como producto oficial y
solo se obtiene por cálculo propio. Es el control de calidad que habilita la Opción II.

Diferencia metodológica conocida y esperada: nuestro SPEI usa log-logística por
L-momentos (Vicente-Serrano et al. 2010); ERA5-Drought usa logística generalizada.
La validación cuantifica esa brecha (correlación, sesgo, RMSE) por escala. Si la
brecha fuera grande, se revisaría la elección de distribución (decisión documentada).
"""

from __future__ import annotations
import logging
from pathlib import Path
import numpy as np

import config_sequia as cfg

log = logging.getLogger("sequia.validacion")


def _metricas(propio: np.ndarray, oficial: np.ndarray) -> dict:
    """Correlación de Pearson, sesgo medio y RMSE sobre puntos comparables."""
    m = np.isfinite(propio) & np.isfinite(oficial)
    a, b = propio[m], oficial[m]
    if a.size < 10:
        return {"n": int(a.size), "corr": np.nan, "sesgo": np.nan, "rmse": np.nan}
    return {
        "n": int(a.size),
        "corr": float(np.corrcoef(a, b)[0, 1]),
        "sesgo": float(np.mean(a - b)),
        "rmse": float(np.sqrt(np.mean((a - b) ** 2))),
    }


def validar(args, raiz: Path) -> dict:
    """Compara, por índice y escala, el cálculo propio (ref 1991-2020) contra el
    benchmark oficial. Devuelve y registra un reporte de métricas."""
    import xarray as xr
    dir_crudos = raiz / cfg.DIR_CRUDOS
    dir_cons = raiz / cfg.DIR_CONSOLIDADOS

    reporte = {}
    # Benchmarks oficiales: era5drought_{spi|spei}_oficial.nc
    oficiales = list(dir_crudos.glob("era5drought_*oficial.nc"))

    for tipo in args.indices:
        for n in args.escalas:
            propio_p = dir_cons / f"{tipo}{n}_ref1991-2020.nc"
            if not propio_p.exists():
                log.warning("No existe %s; salto.", propio_p.name)
                continue
            propio = xr.open_dataarray(propio_p).mean("number")
            # Localiza la variable/escala correspondiente en el producto oficial.
            of = _cargar_oficial(oficiales, tipo, n)
            if of is None:
                log.warning("Sin benchmark oficial para %s-%d; salto.", tipo, n)
                continue
            propio_al, of_al = xr.align(propio, of, join="inner")
            m = _metricas(propio_al.values, of_al.values)
            reporte[f"{tipo}{n}"] = m
            log.info("Validación %s-%d: n=%d corr=%.3f sesgo=%+.3f rmse=%.3f",
                     tipo, n, m["n"], m["corr"], m["sesgo"], m["rmse"])

    # Umbral orientativo: corr>=0.95 y |sesgo|<=0.1 => reproducción satisfactoria.
    ruta = dir_cons / "reporte_validacion.json"
    import json
    ruta.write_text(json.dumps(reporte, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info("Reporte de validación -> %s", ruta.name)
    return reporte


def _cargar_oficial(oficiales, tipo, n):
    """Devuelve el DataArray oficial para el índice/escala dados, o None.
    Empareja por el código del nombre: era5drought_{spi|spei}_oficial.nc."""
    import xarray as xr
    for ruta in oficiales:
        nombre = f"_{ruta.stem.lower()}_"
        es_spei = "_spei_" in nombre
        if (tipo == "spei") != es_spei:
            continue
        ds = xr.open_dataset(ruta)
        for v in ds.data_vars:
            da = ds[v]
            # Selecciona la escala si existe como dimensión/coordenada.
            if "accumulation_period" in da.dims:
                try:
                    da = da.sel(accumulation_period=n)
                except Exception:
                    continue
            if "number" in da.dims:
                da = da.mean("number")
            return da
    return None
