import numpy as np

from climateCCR.calibration.financial.bond_yield import FRN_PERIOD_DAYS, frn_cashflow_times
from climateCCR.simulation.simulated_hw1f_curve import SimulatedHW1FCurve
from climateCCR.utils.calendar_utils import transform_dates_to_time_differences

from .pricing_model import PricingModel


class FloatingRateNotePricer(PricingModel):
    """FRN cebur off the simulated curve: projected 28-day index + sobretasa.

    Per remaining period i (28-day schedule from ``frn_cashflow_times``), the
    index leg is the curve-implied simple Act/360 forward over the accrual
    (MKT-SIE-04, the TIIE quoting convention), the single-curve proxy of the
    28-day TIIE the trade actually resets on:

        F_i = (P(t, S_i) / P(t, T_i) − 1) · 360 / 28,   S_i = T_i − 28d

    MtM(t) = ±(notional / 100) · Σ_i P(t, T_i) · exp(−spread · τ_i) ·
             [(F_i + coupon) · 28/360 · 100 + (100 if i = n)],

    with ``coupon`` the contractual sobretasa (fixed at issuance) and
    ``spread`` the static discount margin — the shockable column, so a credit
    shock lowers the price while the contractual margin stays put. At issuance
    (spread = coupon) the bond prices near par at each reset, the standard FRN
    result. The current period's already-fixed index is approximated by the
    stub forward from the current path state (S clamped to t): exact for the
    stub's par value, and the ≤28-day fixing lag is immaterial at the B3
    reporting grain.
    # ponytail: static discount margin + single-curve TIIE proxy; per-path
    # spread dynamics need a credit risk factor (OQ-INT-10 b scope)
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
        margin = trade.get_attribute("coupon")  # contractual sobretasa over the index
        spread = trade.get_attribute("spread")  # discount margin (NGFS-shockable)
        maturity = trade.get_attribute("maturity")
        accrual = FRN_PERIOD_DAYS / 360.0

        for i, valuation_date in enumerate(valuation_dates):
            plazo_dias = (maturity - valuation_date).days
            if plazo_dias <= 0:
                trade_mtms[:, i] = 0
                continue

            times_days = frn_cashflow_times(plazo_dias)
            tau = times_days / 365.0  # years from the valuation date (Act/365)
            tau_fix = np.maximum(times_days - FRN_PERIOD_DAYS, 0.0) / 365.0
            t = transform_dates_to_time_differences(valuation_dates[0], valuation_date)
            curve = SimulatedHW1FCurve(scenarios[discount_curve][:, i])
            p_pay = curve.get_value(
                calibration=self.calibration[discount_curve],
                t_date=t,
                T_date=t + tau,
                initial_date=None,
                return_log=False,
            )
            p_fix = curve.get_value(
                calibration=self.calibration[discount_curve],
                t_date=t,
                T_date=t + tau_fix,
                initial_date=None,
                return_log=False,
            )
            forward_simple = (p_fix / p_pay - 1.0) / accrual
            amounts = (forward_simple + margin) * accrual * 100.0
            amounts[:, -1] += 100.0
            trade_mtms[:, i] = (
                ls_factor * notional / 100.0 * (p_pay * np.exp(-spread * tau) * amounts).sum(axis=1)
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
