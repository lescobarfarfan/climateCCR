from datetime import datetime

import numpy as np

from climateCCR.simulation.simulated_hw1f_curve import SimulatedHW1FCurve
from climateCCR.utils.calendar_utils import (
    time_step_from_frequency,
    transform_dates_to_time_differences,
)

from .pricing_model import PricingModel


class InterestRateSwapPricer(PricingModel):
    def __init__(self, name=None) -> None:
        super().__init__(name)

    def generate_residual_payments_schedule(self, valuation_date, payments_schedule):
        return [d for d in payments_schedule if d >= valuation_date]

    def generate_residual_fixings_schedule(
        self, first_valuation_date, fixings_schedule, nr_residual_payments
    ):
        remaining_fixings = [d for d in fixings_schedule if d >= first_valuation_date]
        nr_remaining_fixings = min(nr_residual_payments, len(remaining_fixings))
        return remaining_fixings[-nr_remaining_fixings:]

    def generate_shifted_payments_schedule(self, payments_schedule, payments_frequency):
        time_step = time_step_from_frequency(payments_frequency)
        return [d + time_step for d in payments_schedule]

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
        """Price one IRS per (path, valuation date) off the simulated HW1F state.

        Conventions (2026-08-20, OQ-CCR-10; fixing semantics from the 2026-08-12
        audit, OQ-CCR-06): money accruals are **Act/360 on both legs** and each
        period pays ``notional * accrual_360 * (floating - K)`` at its payment
        date; the floating rate is the valuation-date-conditional **simple
        Act/360 forward** ``(P(t_val,start)/P(t_val,end) - 1) / accrual_360``
        (both bond prices functions of the same simulated short rate) — the
        MKT-SIE-04 TIIE quoting convention, shared with the FRN pricer. Model
        time (curve coordinates) stays Act/365. The ``payer/receiver`` flag
        carries the market meaning: ``payer`` pays the fixed leg K and receives
        floating (``MtM = sum N*accrual_360*(F - K)*DF``). Fixings that occurred
        before the valuation date in simulated time are proxied by the
        valuation-date forward over the same span (the engine stores no per-path
        fixing history); a valuation date inside the trade's first period uses
        the real historical fixing of the period's own (previous) fixing date.
        """
        pr_factor = 1 if trade.get_attribute("payer/receiver") == "payer" else -1
        trade_mtms = np.empty((global_parameters["n_paths"], len(valuation_dates)))
        payments_frequency = trade.get_attribute("payments_frequency")
        underlyings = trade.trade_underlyings
        simulated_underlying = [rf for rf in underlyings if rf in scenarios]
        if len(simulated_underlying) == 1:
            simulated_underlying = simulated_underlying[0]
        elif len(simulated_underlying) == 0:
            raise ValueError(f"Nothing to simulate for trade {trade.trade_id}.")
        else:
            raise ValueError(f"Too many risk factors to simulate for {trade.trade_id}.")

        nonsimulated_risk_factors = [rf for rf in underlyings if rf not in scenarios]
        if len(nonsimulated_risk_factors) == 0:
            nonsimulated_underlying = None
        elif len(nonsimulated_risk_factors) == 1:
            nonsimulated_underlying = nonsimulated_risk_factors[0]
        else:
            raise ValueError(f"Too many spread curves for {trade.trade_id}.")

        if nonsimulated_underlying is not None:
            spread_to_discount_curve_object = market_data["spread_to_discount_curve"][
                nonsimulated_underlying
            ]

        time_step = time_step_from_frequency(payments_frequency)
        t0 = valuation_dates[0]
        strike = trade.get_attribute("K")
        notional = trade.get_attribute("notional")
        calibration = self.calibration[simulated_underlying]

        for i, valuation_date in enumerate(valuation_dates):
            if valuation_date > trade.get_attribute("maturity"):
                trade_mtms[:, i] = 0
            else:
                # identify the residual payments and their fixings
                residual_payments_schedule = self.generate_residual_payments_schedule(
                    valuation_date, trade.get_attribute("payments_schedule")
                )
                residual_fixings_schedule = self.generate_residual_fixings_schedule(
                    t0,
                    trade.get_attribute("fixings_schedule"),
                    len(residual_payments_schedule),
                )
                spliced = len(residual_fixings_schedule) == len(residual_payments_schedule) - 1
                if not spliced and len(residual_fixings_schedule) != len(
                    residual_payments_schedule
                ):
                    raise ValueError("Something is wrong with the residual fixing schedule.")

                simulated_curve = SimulatedHW1FCurve(scenarios[simulated_underlying][:, i])
                t_val = transform_dates_to_time_differences(t0, valuation_date)
                pay_times = transform_dates_to_time_differences(
                    t0, list(residual_payments_schedule)
                )
                fixing_times = transform_dates_to_time_differences(
                    t0, list(residual_fixings_schedule)
                )
                # window length in model time (Act/365 — curve coordinates) vs the
                # money daycount fraction of the same days on Act/360 (OQ-CCR-10)
                accruals = np.reshape(
                    transform_dates_to_time_differences(
                        t0,
                        self.generate_shifted_payments_schedule(
                            residual_fixings_schedule, payments_frequency
                        ),
                    )
                    - fixing_times,
                    (1, -1),
                )
                accruals_360 = accruals * (365.0 / 360.0)

                # discounting off the valuation-date state, as before
                discount_factors = simulated_curve.get_value(
                    calibration=calibration,
                    t_date=t_val,
                    T_date=pay_times,
                    initial_date=None,
                    return_log=False,
                )

                # Each period's floating rate is the t_val-conditional simple Act/360
                # forward over its accrual window: (P(t_val, start) / P(t_val, end)
                # - 1) / accrual_360, both bonds functions of r(t_val) — the
                # MKT-SIE-04 TIIE convention, shared with the FRN pricer (OQ-CCR-10).
                # A fixing that already occurred in *simulated* time (the engine keeps
                # no per-path fixing history) is proxied by the valuation-date forward
                # over the same accrual span.
                effective_fixing_times = np.maximum(np.asarray(fixing_times), t_val)
                p_start = simulated_curve.get_value(
                    calibration=calibration,
                    t_date=t_val,
                    T_date=effective_fixing_times,
                    initial_date=None,
                    return_log=False,
                )
                p_end = simulated_curve.get_value(
                    calibration=calibration,
                    t_date=t_val,
                    T_date=effective_fixing_times + accruals.ravel(),
                    initial_date=None,
                    return_log=False,
                )
                floating_rates = (p_start / p_end - 1.0) / accruals_360
                if nonsimulated_underlying is not None:
                    floating_rates = (
                        floating_rates
                        + spread_to_discount_curve_object.get_interpolated_rates(
                            np.asarray(fixing_times)
                        ).reshape(1, -1)
                    )

                # pricing: each period pays notional * accrual_360 * (floating - K)
                future_discount_factors = discount_factors[:, 1:] if spliced else discount_factors
                trade_mtms[:, i] = notional * np.sum(
                    future_discount_factors * accruals_360 * (floating_rates - strike) * pr_factor,
                    axis=1,
                )

                # valuation date inside the first period: its floating rate fixed in
                # real history at the fixing *preceding* the next scheduled one.
                if spliced:
                    previous_fixing = residual_fixings_schedule[0] - time_step
                    missing_date = datetime.strftime(
                        previous_fixing, global_parameters["date_format"]
                    )
                    missing_fixing = market_data["historical_fixings"][simulated_underlying].loc[
                        missing_date
                    ]
                    if nonsimulated_underlying is not None:
                        missing_fixing = (
                            missing_fixing
                            + market_data["historical_fixings"][nonsimulated_underlying].loc[
                                missing_date
                            ]
                        )
                    first_accrual_360 = transform_dates_to_time_differences(
                        previous_fixing, previous_fixing + time_step
                    ) * (365.0 / 360.0)
                    trade_mtms[:, i] += (
                        notional
                        * first_accrual_360
                        * (float(missing_fixing) - strike)
                        * discount_factors[:, 0]
                        * pr_factor
                    )

        return trade_mtms

    def get_market_dependencies(self, trade_underlyings, risk_factors, calibration_parameters):
        dependencies = set()
        for underlying in trade_underlyings:
            if risk_factors[underlying].asset_type[:6] == "SPREAD":
                spread_to_discount_curve = underlying
                discount_curve = risk_factors[underlying].reference
            else:
                spread_to_discount_curve = None
                discount_curve = underlying

            dependencies.update([("historical_fixings", discount_curve)])
            if spread_to_discount_curve is not None:
                dependencies.update(
                    [
                        ("spread_to_discount_curve", spread_to_discount_curve),
                        ("historical_fixings", spread_to_discount_curve),
                    ]
                )

            calibration_method = calibration_parameters["Pricing_HW1F_calibration"][self.name].get(
                "calibration_method", "market_implied"
            )
            if calibration_method == "direct_input":
                dependencies.update([("Pricing_HW1F_calibration", discount_curve)])

        return dependencies
