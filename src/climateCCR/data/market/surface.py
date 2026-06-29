"""Class that implements surface interpolation

Base day counting is done in unit of days, not of years
"""

import numpy as np
from scipy.interpolate import RectBivariateSpline

from climateCCR.utils.calendar_utils import translate_tenor_to_years


class Surface:
    def __init__(self, vol_surface) -> None:
        tenors = np.asarray([translate_tenor_to_years(x) for x in vol_surface.columns], dtype=float)
        strikes = np.asarray([float(x) for x in vol_surface.index], dtype=float)
        values = vol_surface.to_numpy(dtype=float)  # (n_strikes, n_tenors)

        # RectBivariateSpline requires strictly-increasing axes; sort and reorder.
        t_order = np.argsort(tenors)
        k_order = np.argsort(strikes)
        self.tenors = tenors[t_order]
        self.strikes = strikes[k_order]
        self.values = values[np.ix_(k_order, t_order)]

        # interp2d(kind='linear') was removed in SciPy 1.14. A degree-1 (kx=ky=1)
        # RectBivariateSpline on a regular grid is bilinear interpolation -- scipy's
        # documented near bug-for-bug replacement (CCR-MIG-02 extension, 2026-06-28).
        # z must be shape (len(x), len(y)) == (len(tenors), len(strikes)).
        self._spline = RectBivariateSpline(self.tenors, self.strikes, self.values.T, kx=1, ky=1)

    def get_interpolated_surface(self, K, t):
        # Mirrors the old interp2d(t, K): returns vols flattened so that [0] is the
        # scalar vol for scalar inputs (the consumer in EquityEuropeanOptionPricer).
        t_arr = np.atleast_1d(np.asarray(t, dtype=float))
        K_arr = np.atleast_1d(np.asarray(K, dtype=float))
        return self._spline(t_arr, K_arr, grid=True).T.ravel()

    def get_interpolated_ATM_curve(self, t):
        return self.get_interpolated_surface(1.0, t)
