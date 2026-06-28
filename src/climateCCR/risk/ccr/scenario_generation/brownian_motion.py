# Brownian Motion (BM)
# ====================

# Model calibration:
# ------------------
# BM_model_parameters={'starting_value':4,'drift':-0.2,'vola':1.4}
# random_increments=norm.rvs(loc=0, scale=1, size=(global_parameters['n_paths']*(len(time)-1)))

# BM paths generations
# --------------------

import numpy as np

from .risk_factor_evolution import RiskFactorEvolution
from ..utils.calendar_utils import transform_dates_to_time_differences


class BrownianMotion(RiskFactorEvolution):
    def __init__(self, name) -> None:
        super().__init__(name, 1, 'linear')

    def __str__(self):
        result = super().__str__()
        result += '\n Brownian Motion'
        result += f'\n - drift: {self.calibration["drift"]}'
        result += f'\n - volatility: {self.calibration["volatility"]}'
        result += f'\n - initial_value: {self.calibration["initial_value"]}'
        return result

    def mean(self, t):
        return self.calibration['initial_value'] + self.calibration['drift'] * t

    def volatility(self, t):
        return self.calibration['volatility'] * np.sqrt(t)

    def calibrate(self, market_data, calibration_parameters):
        calibration_method = calibration_parameters['RFE_BM_calibration'][self.name].get(
            'calibration_method', 'market_implied')
        if calibration_method == 'direct_input':
            self.calibration = market_data['RFE_BM_calibration'][self.name]
        else:
            pass

    def simulate(self, simulation_dates, random_increments):
        # random increments: number of rows is the number of paths
        simulation_times = transform_dates_to_time_differences(
            simulation_dates[0], simulation_dates)
        fluctuations = random_increments[:, :,
                                         0] * np.sqrt(np.diff(simulation_times))
        fluctuations = np.concatenate(
            (np.zeros((fluctuations.shape[0], 1)), fluctuations), axis=1)
        fluctuations = np.cumsum(fluctuations, axis=1) * \
            self.calibration['volatility']
        drift = self.calibration['drift'] * simulation_times
        return self.calibration['initial_value'] + drift + fluctuations

    def get_dependencies(self, calibration_parameters):
        calibration_method = calibration_parameters['RFE_BM_calibration'][self.name].get(
            'calibration_method', 'market_implied')
        if calibration_method == 'direct_input':
            return set([('RFE_BM_calibration', self.name)])
        else:
            pass
