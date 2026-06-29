# Geometric Brownian Motion (GBM)
# ===============================

# Model calibration:
# ------------------
#     GBM_model_parameters={'starting_value':4,'drift':0.2,'vola':0.4}
#     random_increments=norm.rvs(loc=0, scale=1, size=(global_parameters['n_paths']*(len(time)-1)))

# GBM paths generations
# ---------------------

import numpy as np

from climateCCR.utils.calendar_utils import transform_dates_to_time_differences

from .risk_factor_evolution import RiskFactorEvolution


class GeometricBrownianMotion(RiskFactorEvolution):
    def __init__(self, name) -> None:
        super().__init__(name, 1, "logarithmic")

    def __str__(self):
        result = super().__str__()
        result += "\n Geometric Brownian Motion"
        result += f'\n - drift: {self.calibration["drift"]}'
        result += f'\n - volatility: {self.calibration["volatility"]}'
        result += f'\n - initial_value: {self.calibration["initial_value"]}'
        return result

    def mean(self, t):
        # return self.calibration['initial_value'] * np.exp(self.calibration['drift'] * t)
        if isinstance(self.calibration["volatility"], dict):
            vol = self.volatility(t)
        else:
            vol = self.calibration["volatility"] * np.sqrt(t)

        mean_value = (
            np.log(self.calibration["initial_value"]) + self.calibration["drift"] * t - 0.5 * vol**2
        )

        return mean_value

    # When a dictionary is presented, the vol is constructed as piece-wise constant
    # based on the ATM curve for the pre-specified tenors.
    def volatility(self, t):
        if isinstance(self.calibration["volatility"], dict):
            equity_vola_tenors = np.array(list(self.calibration["volatility"].keys()))
            equity_vola_tenors_extended = np.append([0], equity_vola_tenors)
            equity_vola_values = np.array(list(self.calibration["volatility"].values()))
            variance = []
            for tenor in t:
                if tenor > equity_vola_tenors[-1]:
                    variance_tenor = (tenor - equity_vola_tenors[-1]) * equity_vola_values[-1] ** 2
                    sum_variance_previous_tenors = np.sum(
                        np.diff(equity_vola_tenors_extended) * equity_vola_values**2
                    )
                elif tenor < equity_vola_tenors[0]:
                    variance_tenor = tenor * equity_vola_values[0] ** 2
                    sum_variance_previous_tenors = 0
                elif tenor < equity_vola_tenors[-1] and tenor > equity_vola_tenors[0]:
                    index_tenor = np.where(equity_vola_tenors > tenor)[0][0]
                    variance_tenor = (
                        tenor - equity_vola_tenors[(index_tenor - 1)]
                    ) * equity_vola_values[index_tenor] ** 2
                    sum_variance_previous_tenors = np.sum(
                        np.diff(equity_vola_tenors_extended)[0:index_tenor]
                        * equity_vola_values[0:index_tenor] ** 2
                    )
                variance.append(variance_tenor + sum_variance_previous_tenors)
            vola = np.sqrt(np.array(variance))
        else:
            vola = self.calibration["volatility"] * np.sqrt(t)

        return vola

    def calibrate(self, market_data, calibration_parameters):
        calibration_method = calibration_parameters["RFE_GBM_calibration"][self.name].get(
            "calibration_method", "market_implied"
        )
        if calibration_method == "direct_input":
            self.calibration = market_data["RFE_GBM_calibration"][self.name]
        else:
            self.calibration = {}
            self.calibration["initial_value"] = market_data["equity_spot"][self.name]["spot"]
            self.calibration["drift"] = 0
            S_implied_vol_object = market_data["equity_implied_volatility_surface"][
                self.name[:-6] + "_IMPLIED_VOLATILITY_SURFACE"
            ]
            self.calibration["volatility"] = {
                t: S_implied_vol_object.get_interpolated_ATM_curve(t)[0]
                for t in S_implied_vol_object.tenors
            }

    def simulate(self, simulation_dates, random_increments):
        # random increments: number of rows is the number of paths
        simulation_times = transform_dates_to_time_differences(
            simulation_dates[0], simulation_dates
        )
        integrated_vol = self.volatility(simulation_times)
        step_vol = np.sqrt(np.diff(integrated_vol**2))
        fluctuations = random_increments[:, :, 0] * step_vol - 0.5 * step_vol**2
        fluctuations = np.concatenate((np.zeros((fluctuations.shape[0], 1)), fluctuations), axis=1)
        fluctuations = np.cumsum(fluctuations, axis=1)
        drift = self.calibration["drift"] * simulation_times
        return self.calibration["initial_value"] * np.exp(drift + fluctuations)

    def get_dependencies(self, calibration_parameters):
        calibration_method = calibration_parameters["RFE_GBM_calibration"][self.name].get(
            "calibration_method", "market_implied"
        )
        if calibration_method == "direct_input":
            return set([("RFE_GBM_calibration", self.name)])
        else:
            dependencies = set()
            dependencies.update(
                [
                    (
                        "equity_implied_volatility_surface",
                        self.name[:-6] + "_IMPLIED_VOLATILITY_SURFACE",
                    )
                ]
            )
            dependencies.update([("equity_spot", self.name)])
            return dependencies
