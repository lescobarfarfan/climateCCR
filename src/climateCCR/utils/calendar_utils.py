"""
Defines auxiliary functions for date manipulation

TODO:
    - replace while loops by list comprehensions
"""

from argparse import ArgumentError
import numpy as np
import numbers

from datetime import datetime
from dateutil.relativedelta import relativedelta


_PAYMENT_FREQUENCY_TRANSLATION_DICTIONARY = {
    'weekly': 1/52,
    'bi-weekly': 1/26,
    'monthly': 1/12,
    'quarterly': 1/4,
    'semi-annually': 1/2,
    'annually': 1.0,
}


_TIME_STEP_TRANSLATION_DICTIONARY = {
    'daily': relativedelta(days=1),
    'weekly': relativedelta(weeks=1),
    'bi-weekly': relativedelta(weeks=2),
    'monthly': relativedelta(months=1),
    'quarterly': relativedelta(months=3),
    'semi-annually': relativedelta(months=6),
    'annually': relativedelta(months=12),
}


def transform_dates_to_time_differences(t0_date, simulation_dates):
    if isinstance(simulation_dates, list) or isinstance(simulation_dates, np.ndarray):
        time = np.asarray([(d - t0_date).days / 365 for d in simulation_dates])
    elif isinstance(simulation_dates, datetime):
        time = (simulation_dates - t0_date).days / 365
    else:
        raise TypeError(
            f'simulation_dates is of type {type(simulation_dates)}, must be in [list, Number].')

    return time


def payments_frequency_in_y(payments_frequency):
    return _PAYMENT_FREQUENCY_TRANSLATION_DICTIONARY[payments_frequency]


def time_step_from_frequency(payments_frequency):
    return _TIME_STEP_TRANSLATION_DICTIONARY[payments_frequency]


def generate_payment_schedule_from_time_steps(first_date, last_date, time_step):
    payments_schedule = []
    current_date = first_date
    while current_date <= last_date:
        payments_schedule.append(current_date)
        current_date += time_step

    return np.asarray(payments_schedule)


def generate_simulation_dates_schedule(starting_date, final_date, valuation_frequency, global_parameters):
    starting_date = datetime.strptime(
        starting_date, global_parameters['date_format'])
    final_date = datetime.strptime(
        final_date, global_parameters['date_format'])
    time_step = time_step_from_frequency(valuation_frequency)
    return generate_payment_schedule_from_time_steps(starting_date, final_date, time_step)


def generate_payments_schedule(first_payment_date, last_payment_date, payments_frequency):
    if (first_payment_date >= last_payment_date):
        raise ValueError(
            'Provided dates are not consistent: first_payment_date >= last_payment_date')

    time_step = time_step_from_frequency(payments_frequency)
    return generate_payment_schedule_from_time_steps(first_payment_date, last_payment_date, time_step)


def generate_fixings_and_payments_schedule(first_fixing_date, last_fixing_date, first_payment_date, last_payment_date, payments_frequency):
    if (first_fixing_date >= last_fixing_date) or (first_payment_date >= last_payment_date) or (first_fixing_date > first_payment_date) or (last_fixing_date > last_payment_date):
        raise ValueError(
            'Provided fixing and payments dates are not consistent')

    time_step = time_step_from_frequency(payments_frequency)
    return generate_payment_schedule_from_time_steps(first_fixing_date, last_fixing_date, time_step), generate_payment_schedule_from_time_steps(first_payment_date, last_payment_date, time_step)


def translate_tenor_to_years(tenor):
    if tenor[-1] == 'D':
        return int(tenor[:-1]) / 365

    if tenor[-1] == 'W':
        return int(tenor[:-1]) / 52

    if tenor[-1] == 'M':
        return int(tenor[:-1]) / 12

    if tenor[-1] == 'Y':
        return int(tenor[:-1])

    raise ArgumentError(f'{tenor[-1]} is not a valid tenor.')
