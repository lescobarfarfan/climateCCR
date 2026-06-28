from datetime import datetime

from .trade import Trade
from ..utils.calendar_utils import generate_fixings_and_payments_schedule


class InterestRateSwap(Trade):
    def __init__(self, trade_id):
        super().__init__(trade_id, 'IRS', 'IR')

    def load_additional_trade_attributes(self, global_parameters, risk_factors):
        self.trade_attributes['maturity'] = datetime.strptime(
            self.trade_attributes['maturity'], global_parameters['date_format'])

        first_fixing_date = datetime.strptime(
            self.trade_attributes['first_fixing_date'], global_parameters['date_format'])
        last_fixing_date = datetime.strptime(
            self.trade_attributes['last_fixing_date'], global_parameters['date_format'])
        first_payment_date = datetime.strptime(
            self.trade_attributes['first_payment_date'], global_parameters['date_format'])
        last_payment_date = datetime.strptime(
            self.trade_attributes['last_payment_date'], global_parameters['date_format'])
        self.trade_attributes['fixings_schedule'], self.trade_attributes['payments_schedule'] = generate_fixings_and_payments_schedule(
            first_fixing_date, last_fixing_date, first_payment_date, last_payment_date, self.trade_attributes['payments_frequency'])

        trade_underlyings = [self.trade_attributes['floating_rate']]
        if risk_factors.type[risk_factors['name'] == self.trade_attributes['floating_rate']].iloc[0][:6] == 'SPREAD':
            trade_underlyings.append(
                risk_factors.reference[risk_factors['name'] == self.trade_attributes['floating_rate']].iloc[0])

        return self.trade_attributes['currency'], trade_underlyings, self.trade_attributes['fixings_schedule']
