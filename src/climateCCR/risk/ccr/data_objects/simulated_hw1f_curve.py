import numpy as np

from .simulated_data import SimulatedData
from ..utils.calendar_utils import transform_dates_to_time_differences


class SimulatedHW1FCurve(SimulatedData):
    def __init__(self, short_rate) -> None:
        super().__init__()
        self.short_rate = short_rate

    def get_value(self, **kwargs):
        if (kwargs['initial_date'] != None):
            t = transform_dates_to_time_differences(
                kwargs['initial_date'], kwargs['t_date'])
            T = transform_dates_to_time_differences(
                kwargs['initial_date'], kwargs['T_date'])
        else:
            t = kwargs['t_date']
            T = kwargs['T_date']

        B = self.HW1F_B_tT(kwargs['calibration']['alpha'], T - t)
        A = self.HW1F_A_tT(kwargs['calibration'], t, T, B)

        return_log = kwargs.get('return_log', False)
        if return_log:
            return np.log(A) - np.outer(self.short_rate, B)
        else:
            return A * np.exp(-np.outer(self.short_rate, B))

    def HW1F_B_tT(self, a, t):
        return np.reshape((1 - np.exp(-a * t)) / a, (1, -1))

    def HW1F_A_tT(self, model_parameters, t_date, T_date, B=None, initial_date=None):
        if (initial_date != None):
            t = transform_dates_to_time_differences(initial_date, t_date)
            T = transform_dates_to_time_differences(initial_date, T_date)
        else:
            t = t_date
            T = T_date

        P_t = model_parameters['rate_curve'].get_interpolated_discount_factor(
            t)
        P_T = model_parameters['rate_curve'].get_interpolated_discount_factor(
            T)
        F_t = model_parameters['rate_curve'].get_interpolated_instantaneous_forward_rate()(
            t)
        if B is None:
            B = self.HW1F_B_tT(model_parameters['alpha'], T - t)
        return np.reshape((P_T / P_t) * np.exp(B * F_t - (model_parameters['volatility'] ** 2) / (4 * model_parameters['alpha']) * (1 - np.exp(-2 * model_parameters['alpha'] * t)) * B ** 2), (1, -1))
