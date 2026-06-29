import numpy as np

from scipy.stats import multivariate_normal
from .scenario_generator import ScenarioGenerator


class MultiRiskFactorSimulation(ScenarioGenerator):
    def __init__(self, risk_factors, correlation_matrix):
        super().__init__("MultiRiskFactorSimulation")
        self.simulated_risk_factors = risk_factors
        self.correlation_matrix = correlation_matrix.get_sub_correlation_matrix(
            [rf.name for rf in risk_factors]).get_correlation_matrix()

    def generate_scenarios(self, valuation_dates, simulation_parameters):
        nr_risk_drivers = 0
        for rf in self.simulated_risk_factors:
            nr_risk_drivers += rf.model.number_of_risk_drivers

        random_increments = multivariate_normal(
            mean=[0] * nr_risk_drivers,
            cov=self.correlation_matrix,
            seed=simulation_parameters['random_state']
        ).rvs(size=(simulation_parameters['n_paths'], len(valuation_dates)-1))
        
        if nr_risk_drivers == 1:
            pass_random_increments = random_increments
            random_increments = np.empty((simulation_parameters['n_paths'], len(valuation_dates)-1,1))
            random_increments[:,:,0] = pass_random_increments

        random_paths = {}
        index_risk_drivers = 0
        for rf in self.simulated_risk_factors:
            random_paths[rf.name] = rf.model.simulate(valuation_dates, random_increments[:, :, index_risk_drivers:(
                index_risk_drivers+rf.model.number_of_risk_drivers)])
            random_paths[rf.name + '_dates'] = valuation_dates
            index_risk_drivers += rf.model.number_of_risk_drivers

        return random_paths
