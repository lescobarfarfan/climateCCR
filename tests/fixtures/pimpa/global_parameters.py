"""
Creates the dictionaries that contain all global parameters.
"""
import os

# Fixture copy of PIMPA's prototype config. Data root is configurable so the
# regression harness can point it at tests/fixtures/pimpa/ (defaults to 'data/'
# to match the original CWD-relative behaviour). Parameter VALUES are unchanged.
GLOBAL_DATA_PATH = os.environ.get("PIMPA_DATA_ROOT", "data/")


trades_path = {
    'EQ': GLOBAL_DATA_PATH + 'portfolio_data/desks/EQ/',
    'FX': GLOBAL_DATA_PATH + 'portfolio_data/desks/FX/',
    'IR': GLOBAL_DATA_PATH + 'portfolio_data/desks/IR/',
}


data_paths = {
    'backtesting_data': GLOBAL_DATA_PATH + 'backtesting_Data/',
    'collateral_models': GLOBAL_DATA_PATH + 'calibration_data/collateral_models/',
    'counterparties': GLOBAL_DATA_PATH + 'portfolio_data/counterparties/',
    'market_data': GLOBAL_DATA_PATH + 'market_data/',
    'position_keeping_system': GLOBAL_DATA_PATH + 'portfolio_data/positions_keeping_system/',
    'pricing': GLOBAL_DATA_PATH + 'calibration_data/pricing_models/',
    'RFE': GLOBAL_DATA_PATH + 'calibration_data/RFE_models/',
    'RFs_attributes': GLOBAL_DATA_PATH + 'RFs_attributes/',
    'trades': trades_path,
}


backtesting_file_names = {
    'sample_set': 'sample_set_NASDAQ',
}


collateral_file_names = {
    'OE_haircuts': 'OE_haircuts.csv'
}


market_data_file_names = {
    'historical_fixings': 'Historical_Fixings.csv',
    'spread_to_discount_curve': 'Spread_to_Discount_Curve.csv',
    'equity_implied_volatility_surface': 'Equity_Implied_Volatility_Surface.csv',
    'equity_spot': 'Equity_Spot.csv',
}


pricing_file_names = {
    'pricing_BM_calibration': '',
    'pricing_GBM_calibration': 'Pricing_GBM_Calibration.csv',
    'pricing_FactorGBM_calibration': 'Pricing_FactorGBM_Calibration.csv',
    'pricing_HW1F_calibration': 'Pricing_HW1F_Calibration.csv',
    'pricing_HW2F_calibration': 'Pricing_HW2F_Calibration.csv',
}


rfe_file_names = {
    'RFE_BM_calibration': '',
    'RFE_GBM_calibration': 'RFE_GBM_Calibration.csv',
    'RFE_FactorGBM_calibration': 'RFE_FactorGBM_Calibration.csv',
    'RFE_HW1F_calibration': 'RFE_HW1F_Calibration.csv',
    'RFE_HW2F_calibration': 'RFE_HW2F_Calibration.csv',
    'RFE_correlation_matrix': 'RFE_Correlation_Matrix.csv',
}


rf_attributes_file_names = {
    'all_RFs_mapping': 'All_RFs_Mapping.csv',
}


irs_trades_file_names = {
    'IRS': 'IRS.csv',
}


eq_trades_file_names = {
    'EQ_EUR_OPT': 'EQ_EUROPEAN_OPTIONS.csv',
}


trades_file_names = {
    'IR': irs_trades_file_names,
    'EQ': eq_trades_file_names,
}


data_file_names = {
    'backtesting_data': backtesting_file_names,
    'collateral_models': collateral_file_names,
    'market_data': market_data_file_names,
    'position_keeping_system': 'master_ledger.csv',
    'counterparty_properties': 'counterparty_properties.csv',
    'pricing': pricing_file_names,
    'RFE': rfe_file_names,
    'RFs_attributes': rf_attributes_file_names,
    'trades': trades_file_names,
}


calibration_parameters = {
    'Pricing_HW1F_calibration': {'IRS_Pricer': {'calibration_method': 'direct_input'}, 'EQ_EUR_OPT_Pricer': {'calibration_method': 'direct_input'}},
    'RFE_HW1F_calibration': {'USD_ZERO_YIELD_CURVE': {'calibration_method': 'direct_input'}},
    'RFE_GBM_calibration': {
        'EUR_USD_FX_RATE': {'calibration_method': 'direct_input'},
        'GBP_USD_FX_RATE': {'calibration_method': 'direct_input'},
        'CREDIT_SUISSE_SHARE': {}
    }
}


market_data_folders = {
    'RFE_BM_calibration': data_paths['RFE'] + rfe_file_names['RFE_BM_calibration'],
    'RFE_GBM_calibration': data_paths['RFE'] + rfe_file_names['RFE_GBM_calibration'],
    'RFE_HW1F_calibration': data_paths['RFE'] + rfe_file_names['RFE_HW1F_calibration'],
    'Pricing_BM_calibration': data_paths['pricing'] + pricing_file_names['pricing_BM_calibration'],
    'Pricing_GBM_calibration': data_paths['pricing'] + pricing_file_names['pricing_GBM_calibration'],
    'Pricing_HW1F_calibration': data_paths['pricing'] + pricing_file_names['pricing_HW1F_calibration'],
    'historical_fixings': data_paths['market_data'] + market_data_file_names['historical_fixings'],
    'spread_to_discount_curve': data_paths['market_data'] + market_data_file_names['spread_to_discount_curve'],
    'equity_implied_volatility_surface': data_paths['market_data'] + market_data_file_names['equity_implied_volatility_surface'],
    'equity_spot': data_paths['market_data'] + market_data_file_names['equity_spot'],
}

pricer_mapping = {
    'IRS': 'InterestRateSwapPricer',
    'EQ_EUR_OPT': 'EquityEuropeanOptionPricer',
}

global_parameters = {
    'B3_grid': ['0D', '1D', '1W', '2W', '1M', '6M', '1Y', '2Y', '5Y', '10Y', '20Y', '50Y'],
    'date_format': '%Y-%m-%d',
    'IR_curves_tenors': ['0.08333333', '1', '5', '10', '30'],
    'n_paths': 10000,
    'prototype_data_files': data_file_names,
    'prototype_data_paths': data_paths,
    'random_state': 233423,
    'settlement_currency': 'USD',
    'calibration_parameters': calibration_parameters,
    'market_data_by_service': market_data_folders,
    'pricer_mapping': pricer_mapping
}
