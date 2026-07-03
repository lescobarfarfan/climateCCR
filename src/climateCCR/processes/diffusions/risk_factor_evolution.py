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

    def apply_jump_overlay(self, paths, step_marks, simulation_dates):
        """Superimpose climate jump marks on simulated paths (DC-CCR-SIM-2).

        Each subclass owns how a jump enters its dynamics (additive on a
        mean-reverting state, multiplicative on a log-price, ...). ``paths`` is
        the ``simulate`` output ``(n_paths, n_dates)``; ``step_marks`` is the
        summed mark landing at each step ``(n_paths, n_dates - 1)``, where step
        column ``i`` lands on date ``i + 1``. Returns the jumped paths; must not
        mutate ``paths``.
        """
        raise NotImplementedError(
            f"{type(self).__name__} does not define a climate jump overlay; "
            "add apply_jump_overlay to make it a valid jump target (DC-CCR-SIM-2)"
        )

    def __str__(self):
        return f"{self.name} with {self.number_of_risk_drivers} risk drivers"
