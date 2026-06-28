"""
Defines auxiliary functions for plotting data
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from scipy.stats import pearsonr

from .calendar_utils import transform_dates_to_time_differences
from ..market_data_objects.curve import Curve
from ..market_data_objects.correlation_matrix import CorrelationMatrix


def simulate_single_risk_factor(model, simulation_dates, number_paths, number_of_risk_drivers=1):
    random_increments = np.random.normal(
        size=(number_paths, len(simulation_dates)-1, number_of_risk_drivers))
    return pd.DataFrame(model.simulate(simulation_dates, random_increments), columns=simulation_dates)


def plot_rfe_paths(paths, simulation_dates, model_name):
    if isinstance(paths, pd.DataFrame):
        paths = paths.to_numpy()
    times = transform_dates_to_time_differences(
        simulation_dates[0], simulation_dates)

    fig, axarr = plt.subplots(1, 2)
    fig.suptitle('Paths of ' + model_name, fontsize=25)
    fig.set_figheight(6)
    fig.set_figwidth(12)
    axarr[0].plot(times, paths[0, :])
    axarr[0].set_xlabel('Time(y)', fontsize=15)
    axarr[0].set_ylabel('Paths', fontsize=15)
    axarr[1].plot(times, paths.T)
    axarr[1].set_xlabel('Time(y)', fontsize=15)
    axarr[1].set_ylabel('Paths', fontsize=15)
    plt.show()


def test_rfe_mean_and_vola(paths, simulation_dates, model):
    if isinstance(paths, pd.DataFrame):
        paths = paths.to_numpy()
    model_name = model.name
    times = transform_dates_to_time_differences(
        simulation_dates[0], simulation_dates)

    if model.return_type == 'linear':
        mean_simulation = np.apply_along_axis(np.mean, 0, paths)
        vola_simulation = np.apply_along_axis(np.std, 0, paths)
    elif model.return_type == 'logarithmic':
        mean_simulation = np.apply_along_axis(np.mean, 0, np.log(paths))
        vola_simulation = np.apply_along_axis(
            np.std, 0, np.log(paths / paths[0, 0]))
    else:
        raise ValueError(
            f'Return type {model.return_type} is not implemented.')

    mean_exact = model.mean(times)
    vola_exact = model.volatility(times)

    fig, axarr = plt.subplots(1, 2)
    fig.suptitle('Comparison of Mean and Volatility for ' +
                 model_name, fontsize=25)
    fig.set_figheight(6)
    fig.set_figwidth(12)
    axarr[0].plot(times, mean_simulation, color='blue', label='simulated mean')
    axarr[0].plot(times, mean_exact, color='green', label='exact mean')
    axarr[0].set_xlabel('t', fontsize=15)
    axarr[0].set_ylabel('mean functions', fontsize=15)
    axarr[0].legend()
    axarr[1].plot(times, vola_simulation, color='blue', label='simulated vola')
    axarr[1].plot(times, vola_exact, color='green', label='exact vola')
    axarr[1].set_xlabel('t', fontsize=15)
    axarr[1].set_ylabel('volatility', fontsize=15)
    axarr[1].legend()
    plt.show()


def test_scenarios_marginal_distributions(paths, scenario_object):
    for rf in scenario_object.simulated_risk_factors:
        test_rfe_mean_and_vola(
            paths[rf.name], paths[rf.name + '_dates'], rf.model)


def test_scenarios_correlations(paths, scenario_object, correlation_matrix):
    returns = {}
    for rf in scenario_object.simulated_risk_factors:
        if rf.model.return_type == 'linear':
            returns[rf.name] = np.diff(paths[rf.name]).flatten()
        elif rf.model.return_type == 'logarithmic':
            returns[rf.name] = np.diff(np.log(paths[rf.name])).flatten()
        else:
            raise ValueError(
                f'Return type {rf.model.return_type} is not implemented.')

    realised_correlations = []
    true_correlations = []
    index = []
    for rf1 in scenario_object.simulated_risk_factors:
        for rf2 in scenario_object.simulated_risk_factors:
            if rf1.name <= rf2.name:
                index.append(rf1.name + '_X_' + rf2.name)
                realised_correlations.append(
                    pearsonr(returns[rf1.name], returns[rf2.name])[0])
                true_correlations.append(
                    correlation_matrix.get_value(rf1.name, rf2.name))

    result = pd.DataFrame(index=index, data={
                          'realised_correlations': realised_correlations, 'true_correlations': true_correlations})
    return result, (result.realised_correlations - result.true_correlations).abs().max()


def calibration_data_to_dict(file_path):
    data = pd.read_csv(file_path, index_col=0)
    market_data = {}
    for name, row in data.iterrows():
        market_data[name] = {}
        rate_curve_tenors = {}
        rate_curve_values = {}
        for feat_name, feat_value in row.items():
            if feat_name[0:11] == 'rate_curve_':
                if feat_name[11] == 'V':
                    rate_curve_values[feat_name[12:]] = feat_value
                elif feat_name[11] == 'T':
                    rate_curve_tenors[feat_name[12:]] = feat_value
                else:
                    raise ValueError(f'Do not know what {feat_name[0:12]} is.')
            else:
                market_data[name][feat_name] = feat_value

        if len(rate_curve_tenors) > 0 or len(rate_curve_values) > 0:
            if len(rate_curve_tenors) != len(rate_curve_values):
                raise ValueError('Unequal number of tenors and values!')

            rate_curve = {}
            for index, tenor in rate_curve_tenors.items():
                rate_curve[tenor] = rate_curve_values[index]

            market_data[name]['rate_curve'] = Curve(rate_curve)

    return market_data
