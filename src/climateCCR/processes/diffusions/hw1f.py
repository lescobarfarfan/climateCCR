# Hull-White 1-Factor model (HW1F)
# ================================
# Model calibration:
# ------------------
# Rt_curve={'0.08333333':0.0028, '1':0.0061,'5':0.0097,'10':0.016,'30':0.028}
# HW1F_model_parameters={'Rt_curve':Rt_curve,'alpha':0.05,'vola':0.01}
# random_increments=norm.rvs(loc=0, scale=1, size=(global_parameters['n_paths']*(len(time)-1)))

# HW1F paths generations
# ----------------------

import numpy as np

from climateCCR.utils.calendar_utils import transform_dates_to_time_differences

from .risk_factor_evolution import RiskFactorEvolution


class HW1F(RiskFactorEvolution):
    def __init__(self, name) -> None:
        super().__init__(name, 1, "linear")
        self.instantaneous_forward_rate = None

    def __str__(self):
        result = super().__str__()
        result += "\n 1 Factor Hull White"
        result += f'\n - alpha: {self.calibration["alpha"]}'
        result += f'\n - volatility: {self.calibration["volatility"]}'
        return result

    def _compute_curvature_adjustment(self, t):
        return (
            self.calibration["volatility"] ** 2
            / (2 * self.calibration["alpha"] ** 2)
            * (1 - np.exp(-self.calibration["alpha"] * t)) ** 2
        )

    def mean(self, t):
        return self.instantaneous_forward_rate(t) + self._compute_curvature_adjustment(t)

    def volatility(self, t):
        return (
            self.calibration["volatility"]
            / np.sqrt(2 * self.calibration["alpha"])
            * np.sqrt(1 - np.exp(-2 * self.calibration["alpha"] * t))
        )

    def calibrate(self, market_data, calibration_parameters):
        calibration_method = calibration_parameters["RFE_HW1F_calibration"][self.name].get(
            "calibration_method", "market_implied"
        )
        if calibration_method == "direct_input":
            self.calibration = market_data["RFE_HW1F_calibration"][self.name]
        else:
            pass

        self.instantaneous_forward_rate = self.calibration[
            "rate_curve"
        ].get_interpolated_instantaneous_forward_rate()

    def simulate(self, simulation_dates, random_increments):
        # random increments: number of rows is the number of paths
        # simulation according to Andersen/Piterbarg Proposition 10.1.7
        simulation_times = transform_dates_to_time_differences(
            simulation_dates[0], simulation_dates
        )
        result = np.zeros((random_increments.shape[0], len(simulation_times)))

        for i, t_step in enumerate(np.diff(simulation_times)):
            result[:, i + 1] = (
                result[:, i] * np.exp(-self.calibration["alpha"] * t_step)
                + self.volatility(t_step) * random_increments[:, i, 0]
            )

        return (
            result
            + self.instantaneous_forward_rate(simulation_times)
            + self._compute_curvature_adjustment(simulation_times)
        )

    def get_dependencies(self, calibration_parameters):
        calibration_method = calibration_parameters["RFE_HW1F_calibration"][self.name].get(
            "calibration_method", "market_implied"
        )
        if calibration_method == "direct_input":
            return set([("RFE_HW1F_calibration", self.name)])
        else:
            pass
