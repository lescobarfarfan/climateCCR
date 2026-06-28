from abc import abstractmethod


class PricingModel:
    def __init__(self, name) -> None:
        self.calibration = None
        self.name = name

    def price(self, trade_ids, trade_inventory, valuation_dates, scenarios, market_data, global_parameters, pricer_parameters=None):
        return {trade_id: self.price_single_trade(trade_inventory[trade_id], valuation_dates, scenarios, market_data, global_parameters, pricer_parameters) for trade_id in trade_ids}

    @abstractmethod
    def price_single_trade(self, trade, valuation_dates, scenarios, market_data, global_parameters, pricer_parameters=None):
        pass

    @abstractmethod
    def calibrate(self, market_data, calibration_parameters):
        pass

    @abstractmethod
    def get_market_dependencies(self, trade_underlyings, risk_factors, calibration_parameters):
        pass
