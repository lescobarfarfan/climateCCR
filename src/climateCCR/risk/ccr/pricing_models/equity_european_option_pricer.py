import numpy as np

from .pricing_model import PricingModel
from ..utils.calendar_utils import transform_dates_to_time_differences
from scipy.stats import norm


class EquityEuropeanOptionPricer(PricingModel):
    def __init__(self, name=None) -> None:
        super().__init__(name)

    def put_pricer(self, S, K, sigma, r, t):
        d1 = (np.log(S / K) + (r + sigma * sigma / 2) * t) / \
            (sigma * np.sqrt(t))
        d2 = d1 - sigma*np.sqrt(t)
        return norm.cdf(-d2) * K * np.exp(-r*t) - norm.cdf(-d1) * S

    def call_pricer(self, S, K, sigma, r, t):
        d1 = (np.log(S / K) + (r + sigma * sigma / 2) * t) / \
            (sigma * np.sqrt(t))
        d2 = d1 - sigma*np.sqrt(t)
        return norm.cdf(d1) * S - norm.cdf(d2) * K * np.exp(-r*t)

    def calibrate(self, market_data, calibration_parameters):
        calibration_method = calibration_parameters['Pricing_HW1F_calibration'][self.name].get('calibration_method','market_implied') 
        if calibration_method == 'direct_input':
            #The dependency is correct and originated by the need of simulating the short rate in the BS formula
            self.calibration = market_data['Pricing_HW1F_calibration']
        else:
            pass

    # I am implementing sticky strike valuation. This can be easily changed to sticky delta.
    def price_single_trade(self, trade, valuation_dates, scenarios, market_data, global_parameters, pricer_parameters=None):
        ls_factor = -1 if trade.get_attribute('long/short') == 'short' else 1
        trade_mtms = np.empty(
            (global_parameters['n_paths'], len(valuation_dates)))
        underlyings = trade.trade_underlyings
        S = trade.get_attribute('underlying')
        S_implied_vol = S[:-6] + '_IMPLIED_VOLATILITY_SURFACE'
        discount_curve = underlyings[underlyings !=
                                     S and underlyings != S_implied_vol]
        T = transform_dates_to_time_differences(
            valuation_dates[0], trade.get_attribute('maturity'))
        K = trade.get_attribute('K')
        r_scenarios = scenarios[discount_curve]
        S_scenarios = scenarios[S]
        S_0 = S_scenarios[0, 0]
        S_implied_vol_object = market_data['equity_implied_volatility_surface'][S_implied_vol]
        S_implied_vol_values = {t: S_implied_vol_object.get_interpolated_surface(K/S_0,
                                                                                 transform_dates_to_time_differences(valuation_dates[0], t))[0] for t in valuation_dates}

        simulated_underlying = [rf for rf in underlyings if rf in scenarios]
        if len(simulated_underlying) == 0:
            raise ValueError(
                f'Nothing to simulate for trade {trade.trade_id}.')

        for i, valuation_date in enumerate(valuation_dates):
            if valuation_date > trade.get_attribute('maturity'):
                trade_mtms[:, i] = 0
            else:
                t = T - \
                    transform_dates_to_time_differences(
                        valuation_dates[0], valuation_date)
                sigma = S_implied_vol_values[valuation_date]
                if trade.get_attribute('put/call') == 'call':
                    trade_mtms[:, i] = ls_factor*trade.get_attribute('notional')*self.call_pricer(
                        S_scenarios[:, i], K, sigma, r_scenarios[:, i], t)
                elif trade.get_attribute('put/call') == 'put':
                    trade_mtms[:, i] = ls_factor*trade.get_attribute('notional')*self.put_pricer(
                        S_scenarios[:, i], K, sigma, r_scenarios[:, i], t)
                else:
                    raise ValueError(f'Undefined put/call indicator.')

        return trade_mtms

    def get_market_dependencies(self, trade_underlyings, risk_factors, calibration_parameters):
        dependencies = set()

        for underlying in trade_underlyings:
            if underlying[-5:] == 'CURVE':
                dependencies.update([('historical_fixings', underlying)])
                calibration_method = calibration_parameters['Pricing_HW1F_calibration'][self.name].get(
                    'calibration_method', 'market_implied')
                if calibration_method == 'direct_input':
                    dependencies.update(
                        [('Pricing_HW1F_calibration', underlying)])
            elif underlying[-7:] == 'SURFACE':
                dependencies.update(
                    [('equity_implied_volatility_surface', underlying)])
            else:
                pass

        return dependencies
