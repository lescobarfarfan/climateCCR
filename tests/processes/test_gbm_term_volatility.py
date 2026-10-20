"""GBM term-structure volatility at the endpoint tenors (OQ-CCR-13).

The dictionary-volatility branch integrates a piecewise-constant ATM vol over
the surface tenors. Its branches used strict inequalities, so a simulation
time *equal* to the first or last tenor matched none of them and silently
reused the previous time's variance (or raised on a one-element grid). The
endpoints are now inclusive; these tests pin the integrated variance there and
on a daily grid that hits the 5Y tenor exactly (1825/365 == 5.0).
"""

import numpy as np
from climateCCR.processes.diffusions.geometric_brownian_motion import GeometricBrownianMotion

TENORS = {1 / 52: 0.20, 1 / 12: 0.22, 0.25: 0.25, 1.0: 0.30, 5.0: 0.35}


def _gbm():
    gbm = GeometricBrownianMotion("X_SHARE")
    gbm.calibration = {"initial_value": 1.0, "drift": 0.0, "volatility": dict(TENORS)}
    return gbm


def _integrated_variance(t):
    """Reference: piecewise-constant vol on [0, t0], [t0, t1], ...; the last vol extends."""
    edges = np.array([0.0] + list(TENORS))
    vols = np.array(list(TENORS.values()))
    var = 0.0
    for k in range(1, len(edges)):
        lo, hi = edges[k - 1], edges[k]
        if t <= lo:
            return var
        var += (min(t, hi) - lo) * vols[k - 1] ** 2
    if t > edges[-1]:
        var += (t - edges[-1]) * vols[-1] ** 2
    return var


def test_endpoint_tenors_are_handled():
    gbm = _gbm()
    assert np.isclose(gbm.volatility(np.array([5.0]))[0], np.sqrt(_integrated_variance(5.0)))
    assert np.isclose(gbm.volatility(np.array([1 / 52]))[0], 0.20 * np.sqrt(1 / 52))


def test_daily_grid_through_the_last_tenor_is_monotone_and_exact():
    gbm = _gbm()
    t = np.arange(0, 1826) / 365  # day 1825 is exactly the 5Y tenor
    vola = gbm.volatility(t)
    assert np.all(np.isfinite(vola))
    assert np.all(np.diff(vola**2) >= -1e-15)
    assert np.isclose(vola[-1], np.sqrt(_integrated_variance(5.0)))
    for i in (0, 1, 7, 30, 91, 365, 1000, 1824):
        assert np.isclose(vola[i], np.sqrt(_integrated_variance(t[i]))), i


def test_beyond_the_last_tenor_extends_with_the_last_vol():
    gbm = _gbm()
    assert np.isclose(gbm.volatility(np.array([7.0]))[0], np.sqrt(_integrated_variance(7.0)))
