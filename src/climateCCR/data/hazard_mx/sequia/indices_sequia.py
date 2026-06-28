"""
indices_sequia.py
=================
Cálculo propio de SPI y SPEI a partir de insumos crudos de ERA5 (P y PET mensuales),
para uno o varios periodos de referencia y escalas de acumulación.

Por qué cálculo propio (Opción II del diseño):
  El producto oficial ERA5-Drought está estandarizado a un periodo FIJO (1991-2020)
  y un índice ya estandarizado NO se puede re-estandarizar a otra base (la
  transformación es no lineal a través de la distribución ajustada). Para comparar
  dos periodos de referencia de forma metodológicamente limpia hay que recalcular
  ambos con el MISMO código desde las acumulaciones crudas. El producto oficial se
  usa solo como benchmark de validación (ver validacion_sequia.py).

Procedimiento (idéntico para ambos periodos de referencia):
  1. Acumular la variable (P para SPI; balance D = P - PET para SPEI) en ventana
     móvil de n meses.
  2. Para CADA mes calendario por separado (elimina la estacionalidad), ajustar la
     distribución sobre los años del periodo de referencia.
  3. Transformar toda la serie con la CDF ajustada y mapear a la normal estándar:
     indice = Phi^{-1}(F(x)). Se satura a +/- LIMITE_INDICE.

Distribuciones (decisión de modelación, ver config_sequia.py):
  - SPI : Gamma de 2 parámetros (Thom 1958) con corrección de ceros.
  - SPEI: log-logística de 3 parámetros por L-momentos (Vicente-Serrano et al. 2010).
"""

from __future__ import annotations
import logging
import numpy as np
from scipy import special
from scipy.stats import norm

import config_sequia as cfg

log = logging.getLogger("sequia.indices")


# --------------------------------------------------------------------------- #
# 1. Acumulación en ventana móvil de n meses.
# --------------------------------------------------------------------------- #
def acumular_ventana(serie: np.ndarray, n: int) -> np.ndarray:
    """Suma móvil de n meses. Los primeros n-1 valores quedan como NaN.

    serie: arreglo 1D ordenado cronológicamente (mensual).
    """
    serie = np.asarray(serie, dtype=float)
    acumulada = np.full_like(serie, np.nan)
    if n <= 1:
        return serie.copy()
    csum = np.cumsum(np.nan_to_num(serie, nan=0.0))
    hay_nan = np.isnan(serie)
    nan_csum = np.cumsum(hay_nan.astype(int))
    for t in range(n - 1, len(serie)):
        # Si hay algún NaN dentro de la ventana, la acumulación es NaN.
        if (nan_csum[t] - (nan_csum[t - n] if t - n >= 0 else 0)) > 0:
            continue
        acumulada[t] = csum[t] - (csum[t - n] if t - n >= 0 else 0.0)
    return acumulada


# --------------------------------------------------------------------------- #
# 2a. SPI: Gamma de 2 parámetros (estimador de Thom 1958) con corrección de ceros.
# --------------------------------------------------------------------------- #
def _ajustar_gamma_thom(x: np.ndarray):
    """Devuelve (alpha, beta, q) para la mezcla cero/Gamma.

    q = P(precipitación = 0); la Gamma se ajusta sobre los valores > 0.
    """
    x = x[np.isfinite(x)]
    n = x.size
    if n == 0:
        return np.nan, np.nan, np.nan
    ceros = x[x <= 0.0]
    pos = x[x > 0.0]
    q = ceros.size / n
    if pos.size < 4:  # muestra insuficiente para ajustar la Gamma
        return np.nan, np.nan, q
    media = pos.mean()
    A = np.log(media) - np.log(pos).mean()
    A = max(A, 1e-9)
    alpha = (1.0 / (4.0 * A)) * (1.0 + np.sqrt(1.0 + (4.0 * A) / 3.0))
    beta = media / alpha
    return alpha, beta, q


def _cdf_gamma_mezcla(x: np.ndarray, alpha, beta, q) -> np.ndarray:
    """CDF de la mezcla: F(0)=q ; F(x>0)=q + (1-q)*Gamma_cdf(x)."""
    F = np.full_like(x, np.nan, dtype=float)
    finitos = np.isfinite(x)
    if not np.isfinite(alpha):
        return F
    # Gamma regularizada incompleta inferior = gammainc(alpha, x/beta).
    G = special.gammainc(alpha, np.where(finitos, np.clip(x, 0, None), 0.0) / beta)
    F = np.where(finitos, q + (1.0 - q) * G, np.nan)
    F = np.where(finitos & (x <= 0.0), q, F)
    return F


# --------------------------------------------------------------------------- #
# 2b. SPEI: log-logística de 3 parámetros por L-momentos (Vicente-Serrano 2010).
# --------------------------------------------------------------------------- #
def _pwm(x: np.ndarray):
    """Probability Weighted Moments (w0,w1,w2) con posición de trazado de
    Vicente-Serrano (2010): F_i = (i-0.35)/N sobre la muestra ordenada ascendente."""
    x = np.sort(x[np.isfinite(x)])
    N = x.size
    if N < 4:
        return None
    i = np.arange(1, N + 1)
    F = (i - 0.35) / N
    w0 = x.mean()
    w1 = np.sum((1.0 - F) * x) / N
    w2 = np.sum((1.0 - F) ** 2 * x) / N
    return w0, w1, w2


def _ajustar_loglogistica(x: np.ndarray):
    """Parámetros (alpha escala, beta forma, gamma ubicación) de la log-logística
    de 3 parámetros por L-momentos (ec. de Vicente-Serrano et al. 2010)."""
    res = _pwm(x)
    if res is None:
        return np.nan, np.nan, np.nan
    w0, w1, w2 = res
    denom = (6.0 * w1 - w0 - 6.0 * w2)
    if abs(denom) < 1e-12:
        return np.nan, np.nan, np.nan
    beta = (2.0 * w1 - w0) / denom
    if not np.isfinite(beta) or beta <= 0:
        return np.nan, np.nan, np.nan
    try:
        g1 = special.gamma(1.0 + 1.0 / beta)
        g2 = special.gamma(1.0 - 1.0 / beta)
    except Exception:
        return np.nan, np.nan, np.nan
    if not (np.isfinite(g1) and np.isfinite(g2)):
        return np.nan, np.nan, np.nan
    alpha = (w0 - 2.0 * w1) * beta / (g1 * g2)
    gamma_ = w0 - alpha * g1 * g2
    if not np.isfinite(alpha) or alpha <= 0:
        return np.nan, np.nan, np.nan
    return alpha, beta, gamma_


def _cdf_loglogistica(x: np.ndarray, alpha, beta, gamma_) -> np.ndarray:
    """F(x) = [1 + (alpha/(x-gamma))^beta]^{-1} para x > gamma."""
    F = np.full_like(x, np.nan, dtype=float)
    if not np.isfinite(alpha):
        return F
    finitos = np.isfinite(x)
    dx = np.where(finitos, x - gamma_, np.nan)
    # Para x <= gamma la log-logística no está definida; se asigna prob. muy baja.
    valido = finitos & (dx > 0)
    F = np.where(valido, 1.0 / (1.0 + (alpha / np.where(valido, dx, np.nan)) ** beta), F)
    F = np.where(finitos & (dx <= 0), 1e-6, F)
    return F


# --------------------------------------------------------------------------- #
# 3. Estandarización por mes calendario sobre el periodo de referencia.
# --------------------------------------------------------------------------- #
def _estandarizar(acumulada: np.ndarray, anios: np.ndarray, meses: np.ndarray,
                  anio_ini: int, anio_fin: int, tipo: str) -> np.ndarray:
    """Ajusta la distribución por mes calendario sobre [anio_ini, anio_fin] y
    transforma toda la serie a la normal estándar.

    tipo: "spi" (Gamma) o "spei" (log-logística).
    """
    indice = np.full_like(acumulada, np.nan, dtype=float)
    for mes in range(1, 13):
        sel_mes = meses == mes
        if not sel_mes.any():
            continue
        en_ref = sel_mes & (anios >= anio_ini) & (anios <= anio_fin)
        x_ref = acumulada[en_ref]
        x_ref = x_ref[np.isfinite(x_ref)]
        if x_ref.size < 4:
            continue

        if tipo == "spi":
            alpha, beta, q = _ajustar_gamma_thom(x_ref)
            F = _cdf_gamma_mezcla(acumulada[sel_mes], alpha, beta, q)
        else:  # spei
            alpha, beta, gamma_ = _ajustar_loglogistica(x_ref)
            F = _cdf_loglogistica(acumulada[sel_mes], alpha, beta, gamma_)

        # Phi^{-1}(F), saturado para evitar +/- inf en las colas.
        F = np.clip(F, 1e-7, 1 - 1e-7)
        z = norm.ppf(F)
        z = np.clip(z, -cfg.LIMITE_INDICE, cfg.LIMITE_INDICE)
        indice[sel_mes] = z
    return indice


# --------------------------------------------------------------------------- #
# API principal: SPI/SPEI sobre una serie temporal 1D (una celda / un miembro).
# --------------------------------------------------------------------------- #
def spi_serie(precip: np.ndarray, anios, meses, n, anio_ini, anio_fin):
    acc = acumular_ventana(precip, n)
    return _estandarizar(acc, np.asarray(anios), np.asarray(meses),
                         anio_ini, anio_fin, "spi")


def spei_serie(precip, pet, anios, meses, n, anio_ini, anio_fin):
    # Balance hídrico climático D = P - PET (ambos en las mismas unidades).
    balance = np.asarray(precip, float) - np.asarray(pet, float)
    acc = acumular_ventana(balance, n)
    return _estandarizar(acc, np.asarray(anios), np.asarray(meses),
                         anio_ini, anio_fin, "spei")
