import numpy as np
import pandas as pd

from .interest_rate_swap import InterestRateSwap
from .equity_european_option import EquityEuropeanOption


class Portfolio:
    def __init__(self, netting_agreement_id):
        self.netting_agreement_id = netting_agreement_id
        self.trade_inventory = None
        self.collateral_inventory = None
        self.netting_sets = None
        self.vm_collateral_agreements = None
        self.im_collateral_agreements = None
        self.tlia_collateral_agreements = None
        self.portfolio_underlyings = None
        self.portfolio_valuation_dates = None
        self.settlement_currency = None
        self.initialized = False

    def __str__(self):
        text = f'Portfolio with netting_agreement_id: {self.netting_agreement_id}'
        if self.trade_inventory is not None:
            text += '\n- including trade_IDs: ' + \
                str(list(self.trade_inventory.keys()))
        if self.netting_sets is not None:
            text += '\n- including netting_sets: ' + \
                str(list(self.netting_sets.keys()))
        if self.portfolio_underlyings is not None:
            text += '\n- with underlyings: ' + str(self.portfolio_underlyings)
        if self.portfolio_valuation_dates is not None:
            text += f'\n- with {len(self.portfolio_valuation_dates)} valuation points.'

        text += '\n' + ('AVAILABLE' if self.initialized else 'NOT AVAILABLE')
        return(text)

    def load(self, global_parameters):
        master_ledger = pd.read_csv(global_parameters['prototype_data_paths']['position_keeping_system'] +
                                    global_parameters['prototype_data_files']['position_keeping_system'])
        oe_haircuts = pd.read_csv(global_parameters['prototype_data_paths']['collateral_models'] +
                                  global_parameters['prototype_data_files']['collateral_models']['OE_haircuts'])
        risk_factors = pd.read_csv(global_parameters['prototype_data_paths']['RFs_attributes'] +
                                   global_parameters['prototype_data_files']['RFs_attributes']['all_RFs_mapping'])
        self.load_trade_inventory(
            global_parameters, master_ledger, risk_factors)
        self.load_portfolio_properties(global_parameters)
        self.load_netting_sets(master_ledger)
        self.load_VM_collateral_agreements(
            global_parameters, master_ledger, oe_haircuts)
        self.load_portfolio_underlyings()
        self.load_portfolio_valuation_dates()
        self.initialized = (self.netting_sets is not None) and np.all(
            [trade.is_initialized for trade in self.trade_inventory.values()])

    def load_trade_inventory(self, global_parameters, master_ledger, risk_factors):
        self.trade_inventory = {}
        for _, row in master_ledger.iterrows():
            if row['netting_agreement_id'] == self.netting_agreement_id:
                trade_type = master_ledger[master_ledger.trade_id ==
                                           row.trade_id].feed.iloc[0]
                if trade_type == 'IRS':
                    trade = InterestRateSwap(row['trade_id'])
                elif trade_type == 'EQ_EUR_OPT':
                    trade = EquityEuropeanOption(row['trade_id'])
                else:
                    raise ValueError(
                        f'Trade type {trade_type} is not implemented.')

                trade.load(global_parameters, risk_factors)
                self.trade_inventory[row['trade_id']] = trade

    def load_netting_sets(self, master_ledger):
        self.netting_sets = {}
        for _, row in master_ledger.iterrows():
            if row['netting_agreement_id'] == self.netting_agreement_id:
                netting_set_name = f"{self.netting_agreement_id}_{row['netting_set']}"
                if netting_set_name not in self.netting_sets.keys():
                    self.netting_sets[netting_set_name] = []

                self.netting_sets[netting_set_name].append(row['trade_id'])

    def load_VM_collateral_agreements(self, global_parameters, master_ledger, oe_haircuts):
        self.vm_collateral_agreements = {}
        for _, row in master_ledger.iterrows():
            if row['netting_agreement_id'] == self.netting_agreement_id:
                if row['vm_agreement'] in self.vm_collateral_agreements.keys():
                    self.vm_collateral_agreements[row['vm_agreement']]['trade_ids'].append(
                        row['trade_id'])
                else:
                    if row['vm_agreement'] != 'NOT_AVAILABLE':
                        self.vm_collateral_agreements[row['vm_agreement']] = {}
                        self.vm_collateral_agreements[row['vm_agreement']]['trade_ids'] = [
                            row['trade_id']]

        for vm_agreement in self.vm_collateral_agreements.keys():
            self.vm_collateral_agreements[vm_agreement]['contractual_terms'] = pd.read_csv(
                global_parameters['prototype_data_paths']['counterparties'] + str(self.netting_agreement_id) + '/' + vm_agreement + '_terms.csv')
#            self.vm_collateral_agreements[vm_agreement]['collateral_underlyings'] = [
#            ]
#            for i in range(0, self.vm_collateral_agreements[vm_agreement]['contractual_terms'].at[0, 'collateral_types_R']):
#                pass_type = self.vm_collateral_agreements[vm_agreement][
#                    'contractual_terms'].at[0, f'type_R_{i+1}']
#                pass_currency = oe_haircuts[oe_haircuts['product']
#                                            == pass_type].currency.iloc[0]
#                if pass_currency != 'USD':
#                    pass_underlying = f'{pass_currency}_USD_FX_RATE'
#                    if pass_underlying not in self.vm_collateral_agreements[vm_agreement]['collateral_underlyings']:
#                        self.vm_collateral_agreements[vm_agreement]['collateral_underlyings'].append(
#                            pass_underlying)
#
#            for i in range(0, self.vm_collateral_agreements[vm_agreement]['contractual_terms'].at[0, 'collateral_types_P']):
#                pass_type = self.vm_collateral_agreements[vm_agreement][
#                    'contractual_terms'].at[0, f'type_P_{i+1}']
#                pass_currency = oe_haircuts[oe_haircuts['product']
#                                            == pass_type].currency.iloc[0]
#                if pass_currency != 'USD':
#                    pass_underlying = f'{pass_currency}_USD_FX_RATE'
#                    if pass_underlying not in self.vm_collateral_agreements[vm_agreement]['collateral_underlyings']:
#                        self.vm_collateral_agreements[vm_agreement]['collateral_underlyings'].append(
#                            pass_underlying)
#
    def load_portfolio_underlyings(self):
        # TODO(to be added: IM and TL_IA)
        self.portfolio_underlyings = set([])
        for trade in self.trade_inventory.values():
            self.portfolio_underlyings.update(trade.trade_underlyings)
            if trade.trade_currency != 'USD':
                self.portfolio_underlyings.add(
                    f'{trade.trade_currency}_USD_FX_RATE')
            if self.settlement_currency != 'USD':
                self.portfolio_underlyings.add(
                    f'{self.settlement_currency}_USD_FX_RATE')

#        for vm_agreement in self.vm_collateral_agreements.values():
#            self.portfolio_underlyings.update(
#                vm_agreement['collateral_underlyings'])

    def load_portfolio_valuation_dates(self):
        self.portfolio_valuation_dates = []
        for trade in self.trade_inventory.values():
            for date in trade.trade_cashflows_dates:
                if date not in self.portfolio_valuation_dates:
                    self.portfolio_valuation_dates.append(date)

    def load_portfolio_properties(self, global_parameters):
        portfolio_properties = pd.read_csv(
            global_parameters['prototype_data_paths']['counterparties'] + str(self.netting_agreement_id) + '/counterparty_properties.csv')
        self.settlement_currency = portfolio_properties[portfolio_properties.netting_agreement_id ==
                                                        self.netting_agreement_id].settlement_currency.iloc[0]
