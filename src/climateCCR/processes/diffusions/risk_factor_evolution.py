from abc import abstractmethod


class RiskFactorEvolution:
    def __init__(self, name, number_of_risk_drivers, return_type) -> None:
        self.name = name
        self.calibration = None
        self.number_of_risk_drivers = number_of_risk_drivers
        self.return_type = return_type

    @abstractmethod
    def mean(self, t):
        pass

    @abstractmethod
    def volatility(self, t):
        pass

    @abstractmethod
    def calibrate(self, market_data, calibration_parameters):
        pass

    @abstractmethod
    def simulate(self, simulation_dates, random_increments):
        pass

    @abstractmethod
    def get_dependencies(self):
        pass

    def __str__(self):
        return f"{self.name} with {self.number_of_risk_drivers} risk drivers"
