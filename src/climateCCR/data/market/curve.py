""" Class that implements curve interpolation

Base day counting is done in unit of days, not of years
"""

import numpy as np

from scipy.interpolate import interp1d
from climateCCR.utils.calendar_utils import translate_tenor_to_years


class Curve:
    def __init__(self, curve_values) -> None:
        self.tenors = np.asarray([translate_tenor_to_years(x)
                                 for x in curve_values.keys()])
        self.rates = np.asarray(list(curve_values.values()))
        self.interpolated_rates = interp1d(
            self.tenors,
            self.rates,
            kind='quadratic',
            bounds_error=False,
            fill_value=(self.rates[0], self.rates[-1]))

    def get_interpolated_rates(self, t):
        return self.interpolated_rates(t)

    def get_interpolated_discount_factor(self, t):
        return np.exp(-t * self.interpolated_rates(t))

    def get_interpolated_instantaneous_forward_rate(self):
        time_daily = np.linspace(
            self.tenors[0], self.tenors[-1] * 365, int(self.tenors[-1] * 365) + 1) / 365
        Ft_curve_interpolated = - \
            np.diff(np.log(self.get_interpolated_discount_factor(time_daily))) * 365
        return interp1d(
            time_daily[1:],
            Ft_curve_interpolated,
            kind='quadratic',
            bounds_error=False,
            fill_value=(Ft_curve_interpolated[0], Ft_curve_interpolated[-1]))
