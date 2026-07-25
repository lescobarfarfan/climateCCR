import numpy as np

from climateCCR.calibration.financial.bond_yield import bono_cashflows
from climateCCR.simulation.simulated_hw1f_curve import SimulatedHW1FCurve
from climateCCR.utils.calendar_utils import transform_dates_to_time_differences

from .pricing_model import PricingModel


class FixedCouponBondPricer(PricingModel):
    """Fixed-coupon bond off the simulated discount curve plus a static spread.

    MtM(t) = ±(notional / 100) · Σ_i cf_i · P(t, T_i) · exp(-spread · (T_i − t)),
    with P(t, T_i) reconstructed from the simulated HW1F short rate exactly as
    the IRS pricer does, and the residual cashflows per 100 face from
    ``bono_cashflows`` (182-day periods). The spread is the issuance sobretasa,
    constant for the life of the trade.
    # ponytail: static spread; per-path spread dynamics need a credit risk factor
    """

    def __init__(self, name=None) -> None:
        super().__init__(name)

    def calibrate(self, market_data, calibration_parameters):
        calibration_method = calibration_parameters["Pricing_HW1F_calibration"][self.name].get(
            "calibration_method", "market_implied"
        )
        if calibration_method == "direct_input":
            self.calibration = market_data["Pricing_HW1F_calibration"]

    def price_single_trade(
        self,
        trade,
        valuation_dates,
        scenarios,
        market_data,
        global_parameters,
        pricer_parameters=None,
    ):
        ls_factor = -1 if trade.get_attribute("long/short") == "short" else 1
        trade_mtms = np.empty((global_parameters["n_paths"], len(valuation_dates)))
        discount_curve = trade.trade_underlyings[0]
        notional = trade.get_attribute("notional")
        coupon = trade.get_attribute("coupon")
        spread = trade.get_attribute("spread")
        maturity = trade.get_attribute("maturity")

        for i, valuation_date in enumerate(valuation_dates):
            plazo_dias = (maturity - valuation_date).days
            if plazo_dias <= 0:
                trade_mtms[:, i] = 0
                continue

            times_days, amounts = bono_cashflows(plazo_dias, coupon)
            tau = times_days / 365.0  # years from the valuation date (Act/365)
            t = transform_dates_to_time_differences(valuation_dates[0], valuation_date)
            discount_factors = SimulatedHW1FCurve(scenarios[discount_curve][:, i]).get_value(
                calibration=self.calibration[discount_curve],
                t_date=t,
                T_date=t + tau,
                initial_date=None,
                return_log=False,
            )
            trade_mtms[:, i] = (
                ls_factor
                * notional
                / 100.0
                * (discount_factors @ (amounts * np.exp(-spread * tau)))
            )

        return trade_mtms

    def get_market_dependencies(self, trade_underlyings, risk_factors, calibration_parameters):
        dependencies = set()
        for underlying in trade_underlyings:
            if underlying[-5:] == "CURVE":
                calibration_method = calibration_parameters["Pricing_HW1F_calibration"][
                    self.name
                ].get("calibration_method", "market_implied")
                if calibration_method == "direct_input":
                    dependencies.update([("Pricing_HW1F_calibration", underlying)])

        return dependencies
