"""
agregacion_sequia.py
====================
Agrega un campo en malla (índice de sequía) a nivel ESTATAL mediante media
ponderada por área de intersección celda-estado.

Por qué ponderación por área (y no muestreo por centroide):
  Las entidades pequeñas (p. ej. CDMX, ~1,485 km^2, ~2 celdas a 0.25 grados) pueden
  desaparecer de un panel en malla si se muestrea solo el centroide de la celda
  (artefacto de discretización ya observado en el panel de viento IBTrACS a 0.5 grados).
  La intersección exacta en una proyección de ÁREA IGUAL asigna a cada estado el
  promedio ponderado de TODAS las celdas que lo tocan, así ningún estado se pierde.

Fallback:
  Si un estado no intersecta ninguna celda CON DATO (p. ej. estado costero cuyas
  celdas caen en máscara oceánica NaN), se asigna el valor de la celda con dato
  más cercana a su centroide. Es un seguro extra para entidades pequeñas/costeras.

Fuente autoritativa de polígonos: INEGI, Marco Geoestadístico Nacional
(32 entidades federativas). La ruta se pasa por bandera --shp-estados.
"""

from __future__ import annotations
import logging
import numpy as np
import geopandas as gpd
from shapely.geometry import box

import config_sequia as cfg

log = logging.getLogger("sequia.agregacion")


def _malla_a_celdas(lats: np.ndarray, lons: np.ndarray) -> gpd.GeoDataFrame:
    """Construye polígonos de celda a partir de los centros de la malla regular."""
    lats = np.asarray(lats, float); lons = np.asarray(lons, float)
    dlat = np.median(np.diff(np.sort(np.unique(lats))))
    dlon = np.median(np.diff(np.sort(np.unique(lons))))
    registros, ij = [], []
    for i, la in enumerate(lats):
        for j, lo in enumerate(lons):
            registros.append(box(lo - dlon / 2, la - dlat / 2,
                                  lo + dlon / 2, la + dlat / 2))
            ij.append((i, j))
    g = gpd.GeoDataFrame({"i": [a for a, _ in ij], "j": [b for _, b in ij]},
                         geometry=registros, crs=cfg.CRS_GEOGRAFICO)
    return g


def calcular_pesos(lats, lons, estados: gpd.GeoDataFrame):
    """Precalcula, una sola vez, los pesos de área celda->estado.

    Devuelve un dict: clave_estado -> lista de (i, j, peso_normalizado).
    Reutilizable para todos los tiempos / escalas / miembros (la malla es fija).
    """
    celdas = _malla_a_celdas(lats, lons).to_crs(cfg.CRS_EQUIAREA)
    est = estados.to_crs(cfg.CRS_EQUIAREA)
    pesos = {}
    for _, fila in est.iterrows():
        clave = fila[cfg.CLAVE_ESTADO]
        inter = celdas.intersection(fila.geometry)
        areas = inter.area.values
        tot = areas.sum() # type: ignore
        if tot <= 0:
            pesos[clave] = {"tipo": "fallback",
                            "centroide": fila.geometry.centroid}
            continue
        sel = areas > 0 # type: ignore
        w = areas[sel] / tot
        pesos[clave] = {"tipo": "area",
                        "ij": list(zip(celdas.loc[sel, "i"].astype(int), # type: ignore
                                       celdas.loc[sel, "j"].astype(int))), # type: ignore
                        "w": w}
    return pesos, celdas


def agregar_campo(campo: np.ndarray, lats, lons, pesos, celdas) -> dict:
    """Agrega un campo 2D (lat, lon) a valor por estado usando pesos precalculados.

    campo: arreglo (nlat, nlon) con posibles NaN (máscara oceánica).
    """
    salida = {}
    for clave, p in pesos.items():
        if p["tipo"] == "fallback":
            salida[clave] = _valor_celda_mas_cercana(campo, lats, lons,
                                                      p["centroide"], celdas)
            continue
        vals, ws = [], []
        for (i, j), w in zip(p["ij"], p["w"]):
            v = campo[i, j]
            if np.isfinite(v):
                vals.append(v); ws.append(w)
        if ws:
            ws = np.array(ws); ws /= ws.sum()  # renormaliza si hubo celdas NaN
            salida[clave] = float(np.dot(np.array(vals), ws))
        else:
            # Todas las celdas del estado eran NaN -> fallback por cercanía.
            centro = celdas.dissolve().geometry.iloc[0]  # placeholder seguro
            salida[clave] = _valor_celda_mas_cercana(
                campo, lats, lons,
                gpd.GeoSeries([box(lons.min(), lats.min(), lons.max(), lats.max())],
                              crs=cfg.CRS_GEOGRAFICO).geometry.iloc[0].centroid, # type: ignore
                celdas)
    return salida


def _valor_celda_mas_cercana(campo, lats, lons, centroide, celdas):
    """Valor de la celda CON DATO más cercana al centroide (en grados)."""
    cy, cx = centroide.y, centroide.x
    mejor_val, mejor_d = np.nan, np.inf
    for i, la in enumerate(np.asarray(lats, float)):
        for j, lo in enumerate(np.asarray(lons, float)):
            v = campo[i, j]
            if not np.isfinite(v):
                continue
            d = (la - cy) ** 2 + (lo - cx) ** 2
            if d < mejor_d:
                mejor_d, mejor_val = d, v
    return float(mejor_val)
