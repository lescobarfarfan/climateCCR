from datetime import datetime

from .trade import Trade
from ..utils.calendar_utils import generate_fixings_and_payments_schedule


class EquityEuropeanOption(Trade):
    def __init__(self, trade_id):
        super().__init__(trade_id, 'EQ_EUR_OPT', 'EQ')

    def load_additional_trade_attributes(self, global_parameters, risk_factors):
        self.trade_attributes['maturity'] = datetime.strptime(
            self.trade_attributes['maturity'], global_parameters['date_format'])

        trade_underlyings = [self.trade_attributes['underlying']]
        trade_underlyings.append(risk_factors[risk_factors['type'] == 'DISCOUNT_CURVE'][risk_factors[risk_factors['type']
                                 == 'DISCOUNT_CURVE']['currency'] == self.trade_attributes['currency']]['name'].iloc[0])
        trade_underlyings.append(
            self.trade_attributes['underlying'][:-6] + '_IMPLIED_VOLATILITY_SURFACE')
        return self.trade_attributes['currency'], trade_underlyings, []
