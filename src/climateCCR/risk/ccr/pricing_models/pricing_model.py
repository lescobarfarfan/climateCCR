from abc import abstractmethod

import numpy as np

from climateCCR.simulation.simulated_hw1f_curve import SimulatedHW1FCurve


class PricingModel:
    def __init__(self, name) -> None:
        self.calibration = None
        self.name = name

    def discount_factors(self, curve, short_rate, t, T, valuation_date, global_parameters):
        """``P(t, T)`` per path, shape ``(n_paths, len(T))``, for the rate pricers.

        Off the simulated HW1F state through the pricer's own calibration — the
        engine's rate mapping — or, when ``global_parameters["realised_curves"]``
        maps ``valuation_date`` to a ``NelsonSiegelFit``, off that observed zero
        curve: the realised reprice of pipelines/31 (``n_paths = 1``), whose rate
        legs then discount on the curve actually quoted at each reporting date
        instead of the model-mapped one (OQ-INT-14 a). An absent key or an
        unmapped date is the unchanged ``SimulatedHW1FCurve`` call.
        """
        realised = global_parameters.get("realised_curves") if global_parameters else None
        fit = realised.get(valuation_date) if realised else None
        if fit is None:
            return SimulatedHW1FCurve(short_rate).get_value(
                calibration=self.calibration[curve],
                t_date=t,
                T_date=T,
                initial_date=None,
                return_log=False,
            )
        tau = np.asarray(T, dtype=float) - float(t)
        return np.exp(-tau * fit.zero(tau)).reshape(1, -1)

    def price(
        self,
        trade_ids,
        trade_inventory,
        valuation_dates,
        scenarios,
        market_data,
        global_parameters,
        pricer_parameters=None,
    ):
        return {
            trade_id: self.price_single_trade(
                trade_inventory[trade_id],
                valuation_dates,
                scenarios,
                market_data,
                global_parameters,
                pricer_parameters,
            )
            for trade_id in trade_ids
        }

    @abstractmethod
    def price_single_trade(
        self,
        trade,
        valuation_dates,
        scenarios,
        market_data,
        global_parameters,
        pricer_parameters=None,
    ):
        pass

    @abstractmethod
    def calibrate(self, market_data, calibration_parameters):
        pass

    @abstractmethod
    def get_market_dependencies(self, trade_underlyings, risk_factors, calibration_parameters):
        pass
