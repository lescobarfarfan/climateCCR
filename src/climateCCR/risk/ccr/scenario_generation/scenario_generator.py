from abc import abstractmethod


class ScenarioGenerator:
    def __init__(self, name) -> None:
        self.name = name

    @abstractmethod
    def generate_scenarios(self, valuation_dates, simulation_parameters):
        pass

    def __str__(self):
        return self.name
