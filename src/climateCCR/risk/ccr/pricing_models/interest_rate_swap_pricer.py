import numpy as np

from datetime import datetime

from .pricing_model import PricingModel
from ..utils.calendar_utils import time_step_from_frequency, payments_frequency_in_y, transform_dates_to_time_differences
from ..data_objects.simulated_hw1f_curve import SimulatedHW1FCurve


class InterestRateSwapPricer(PricingModel):
    def __init__(self, name=None) -> None:
        super().__init__(name)

    def generate_residual_payments_schedule(self, valuation_date, payments_schedule):
        return [d for d in payments_schedule if d >= valuation_date]

    def generate_residual_fixings_schedule(self, first_valuation_date, fixings_schedule, nr_residual_payments):
        remaining_fixings = [
            d for d in fixings_schedule if d >= first_valuation_date]
        nr_remaining_fixings = min(
            nr_residual_payments, len(remaining_fixings))
        return remaining_fixings[-nr_remaining_fixings:]

    def generate_shifted_payments_schedule(self, payments_schedule, payments_frequency):
        time_step = time_step_from_frequency(payments_frequency)
        return [d + time_step for d in payments_schedule]

    def calibrate(self, market_data, calibration_parameters):
        calibration_method = calibration_parameters['Pricing_HW1F_calibration'][self.name].get(
            'calibration_method', 'market_implied')
        if calibration_method == 'direct_input':
            self.calibration = market_data['Pricing_HW1F_calibration']
        else:
            pass

    def price_single_trade(self, trade, valuation_dates, scenarios, market_data, global_parameters, pricer_parameters=None):
        pr_factor = - \
            1 if trade.get_attribute('payer/receiver') == 'payer' else 1
        trade_mtms = np.empty(
            (global_parameters['n_paths'], len(valuation_dates)))
        payments_frequency = trade.get_attribute('payments_frequency')
        underlyings = trade.trade_underlyings
        simulated_underlying = [rf for rf in underlyings if rf in scenarios]
        if len(simulated_underlying) == 1:
            simulated_underlying = simulated_underlying[0]
        elif len(simulated_underlying) == 0:
            raise ValueError(
                f'Nothing to simulate for trade {trade.trade_id}.')
        else:
            raise ValueError(
                f'Too many risk factors to simulate for {trade.trade_id}.')

        nonsimulated_risk_factors = [
            rf for rf in underlyings if rf not in scenarios]
        if len(nonsimulated_risk_factors) == 0:
            nonsimulated_underlying = None
        elif len(nonsimulated_risk_factors) == 1:
            nonsimulated_underlying = nonsimulated_risk_factors[0]
        else:
            raise ValueError(f'Too many spread curves for {trade.trade_id}.')

        if nonsimulated_underlying is not None:
            spread_to_discount_curve_object = market_data['spread_to_discount_curve'][nonsimulated_underlying]

        for i, valuation_date in enumerate(valuation_dates):
            if valuation_date > trade.get_attribute('maturity'):
                trade_mtms[:, i] = 0
            else:
                # identify the residual payments and their fixings
                residual_payments_schedule = self.generate_residual_payments_schedule(
                    valuation_date, trade.get_attribute('payments_schedule'))
                residual_fixings_schedule = self.generate_residual_fixings_schedule(
                    valuation_dates[0], trade.get_attribute('fixings_schedule'), len(residual_payments_schedule))
                shifted_residual_fixing_schedule = self.generate_shifted_payments_schedule(
                    residual_fixings_schedule, payments_frequency)

                # simulated quantities
                discount_factors = SimulatedHW1FCurve(scenarios[simulated_underlying][:, i]).get_value(
                    calibration=self.calibration[simulated_underlying], t_date=valuation_date, T_date=residual_payments_schedule, initial_date=valuation_dates[0], return_log=False)
                floating_rates = -SimulatedHW1FCurve(scenarios[simulated_underlying][:, i]).get_value(calibration=self.calibration[simulated_underlying], t_date=residual_fixings_schedule,
                                                                                                      T_date=shifted_residual_fixing_schedule, initial_date=valuation_dates[0], return_log=True) / payments_frequency_in_y(payments_frequency)
                if nonsimulated_underlying is not None:
                    floating_rates += spread_to_discount_curve_object.get_interpolated_rates(
                        transform_dates_to_time_differences(valuation_dates[0], residual_fixings_schedule))

                # correcting for valuation date between a fixing and a payment
                if len(residual_fixings_schedule) == len(residual_payments_schedule) - 1:
                    missing_date = datetime.strftime(
                        residual_fixings_schedule[0], global_parameters['date_format'])
                    missing_fixing = market_data['historical_fixings'][simulated_underlying].loc[missing_date]
                    if nonsimulated_underlying is not None:
                        missing_fixing = missing_fixing + \
                            market_data['historical_fixings'][nonsimulated_underlying].loc[missing_date]

                    missing_fixing = (
                        missing_fixing - trade.get_attribute('K')) * discount_factors[:, 0] * pr_factor
                    discount_factors = np.delete(discount_factors, 0, 1)
                elif len(residual_fixings_schedule) != len(residual_payments_schedule):
                    raise ValueError(
                        f'Something is wrong with the residual fixing schedule.')

                # pricing
                trade_mtms[:, i] = trade.get_attribute('notional') * np.sum(discount_factors * (
                    floating_rates - trade.get_attribute('K')) * pr_factor, axis=1)
                if len(residual_fixings_schedule) < len(residual_payments_schedule):
                    trade_mtms[:, i] += missing_fixing

        return trade_mtms

    def get_market_dependencies(self, trade_underlyings, risk_factors, calibration_parameters):
        dependencies = set()
        for underlying in trade_underlyings:
            if risk_factors[underlying].asset_type[:6] == 'SPREAD':
                spread_to_discount_curve = underlying
                discount_curve = risk_factors[underlying].reference
            else:
                spread_to_discount_curve = None
                discount_curve = underlying

            dependencies.update([('historical_fixings', discount_curve)])
            if spread_to_discount_curve is not None:
                dependencies.update([('spread_to_discount_curve', spread_to_discount_curve), (
                    'historical_fixings', spread_to_discount_curve)])

            calibration_method = calibration_parameters['Pricing_HW1F_calibration'][self.name].get(
                'calibration_method', 'market_implied')
            if calibration_method == 'direct_input':
                dependencies.update(
                    [('Pricing_HW1F_calibration', discount_curve)])
            else:
                pass

        return dependencies
