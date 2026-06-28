import pandas as pd

from abc import abstractmethod


class Trade:
    def __init__(self, trade_id, trade_type, trade_asset_class):
        self.trade_id = trade_id
        self.trade_type = trade_type
        self.trade_asset_class = trade_asset_class
        self.trade_attributes = None
        self.trade_currency = None
        self.trade_underlyings = None
        self.trade_cashflows_dates = None
        self.is_initialized = False

    def __str__(self):
        text = f'Trade with trade_id: {self.trade_id}'
        if self.trade_type is not None:
            text += f'\n- trade type: {self.trade_type}'
            text += f'\n- asset class: {self.trade_asset_class}'
        if self.trade_attributes is not None:
            text += f'\n- trade currency: {self.trade_currency}'
            text += f'\n- trade underlyings: {self.trade_underlyings}'
            text += f'\n- trade attributes keys: {list(self.trade_attributes.keys())})'
            text += f'\n- with {len(self.trade_cashflows_dates)} valuation points.'
        text += '\n' + \
            ('AVAILABLE' if self.is_initialized else 'NOT AVAILABLE')
        return(text)

    def load(self, global_parameters, risk_factors):
        trade_set = pd.read_csv(global_parameters['prototype_data_paths']['trades'][self.trade_asset_class] +
                                global_parameters['prototype_data_files']['trades'][self.trade_asset_class][self.trade_type])
        pass_index = trade_set.index[trade_set['trade_id'] == self.trade_id][0]
        self.trade_attributes = {
            attribute: trade_set.at[pass_index, attribute] for attribute in trade_set.columns}
        del self.trade_attributes['trade_id']

        if self.trade_attributes is not None:
            self.trade_currency, self.trade_underlyings, self.trade_cashflows_dates = self.load_additional_trade_attributes(
                global_parameters, risk_factors)
            self.is_initialized = True

    def get_attribute(self, attribute):
        return self.trade_attributes[attribute]

    @abstractmethod
    def load_additional_trade_attributes(self, global_parameters, risk_factors):
        pass
