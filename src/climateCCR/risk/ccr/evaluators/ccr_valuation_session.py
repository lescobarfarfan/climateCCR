from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta

from climateCCR.calibration.financial.market_data_builder import MarketDataBuilder
from climateCCR.simulation.multi_risk_factor_simulation import MultiRiskFactorSimulation

from ..pricing_models.equity_european_option_pricer import EquityEuropeanOptionPricer
from ..pricing_models.interest_rate_swap_pricer import InterestRateSwapPricer


class CCR_Valuation_Session:
    def __init__(self, portfolio):
        self.portfolio = portfolio
        self.market_data_builder = MarketDataBuilder()
        self.mpor_d = None
        self.market_data = None
        self.scenario_generator = None
        self.risk_factors = None
        self.correlation_matrix = None
        self.pe_quantiles = None
        self.trade_pricer_mapping = None
        self.market_dependencies = None
        self.initialized = False
        self.b3_default_grid = None
        self.b3_closeout_grid = None
        self.simulation_dates = None

        self.scenarios = None
        self.scenarios_MtMs = None
        self.scenarios_portfolio_values = None
        self.scenarios_collateral_requirements = None
        self.uncollateralised_ee = None
        self.uncollateralised_pe = None
        self.collateralised_ee = None
        self.collateralised_pe = None

    def generate_time_grids(self, today_date, global_parameters):
        today = datetime.strptime(today_date, global_parameters["date_format"])
        self.b3_default_grid = []
        self.b3_closeout_grid = []
        for B3_horizon in global_parameters["B3_grid"]:
            number = int(B3_horizon[:-1])
            if B3_horizon[-1] == "D":
                self.b3_default_grid.append(today + relativedelta(days=number))
            elif B3_horizon[-1] == "W":
                self.b3_default_grid.append(today + relativedelta(weeks=number))
            elif B3_horizon[-1] == "M":
                self.b3_default_grid.append(today + relativedelta(months=number))
            elif B3_horizon[-1] == "Y":
                self.b3_default_grid.append(today + relativedelta(months=12 * number))
            else:
                raise ValueError(f"Do not know tenor {B3_horizon[-1]}")

            self.b3_closeout_grid.append(self.b3_default_grid[-1] + relativedelta(days=self.mpor_d))

        simulation_schedule = np.unique(
            self.b3_default_grid + self.b3_closeout_grid + self.portfolio.portfolio_valuation_dates
        )
        self.simulation_dates = [d for d in simulation_schedule if d >= self.b3_default_grid[0]]

        # Optional densification: cap the spacing of the simulation grid (e.g.
        # 1 = daily) so the path dynamics exist *between* reporting/cashflow
        # dates. The diffusions are exact-transition, so this changes no
        # marginal law — only where paths are sampled (and hence the draw
        # stream). Absent/None keeps the sparse event-driven grid and every
        # locked baseline bit-for-bit (CCR-MIG-03). [eng]
        max_step_days = global_parameters.get("simulation_max_step_days")
        if max_step_days:
            step = timedelta(days=int(max_step_days))
            dense = [self.simulation_dates[0]]
            for date in self.simulation_dates[1:]:
                while date - dense[-1] > step:
                    dense.append(dense[-1] + step)
                dense.append(date)
            self.simulation_dates = dense

    def get_pricers(self, pricer_mapping):
        self.trade_pricer_mapping = {}
        for trade in self.portfolio.trade_inventory.values():
            if trade.trade_type not in self.trade_pricer_mapping:
                if pricer_mapping[trade.trade_type] == "InterestRateSwapPricer":
                    self.trade_pricer_mapping[trade.trade_type] = [
                        InterestRateSwapPricer("IRS_Pricer"),
                        [],
                    ]
                elif pricer_mapping[trade.trade_type] == "EquityEuropeanOptionPricer":
                    self.trade_pricer_mapping[trade.trade_type] = [
                        EquityEuropeanOptionPricer("EQ_EUR_OPT_Pricer"),
                        [],
                    ]

                else:
                    raise ValueError(
                        f"Pricer {pricer_mapping[trade.trade_type]} is not implemented."
                    )

            self.trade_pricer_mapping[trade.trade_type][1].append(trade.trade_id)

    def get_market_dependencies(self, global_parameters):
        self.market_dependencies = set()
        for pricer_info in self.trade_pricer_mapping.values():
            trade_underlyings = set()
            for trade_id in pricer_info[1]:
                trade_underlyings.update(self.portfolio.trade_inventory[trade_id].trade_underlyings)

            self.market_dependencies.update(
                pricer_info[0].get_market_dependencies(
                    trade_underlyings,
                    self.risk_factors,
                    global_parameters["calibration_parameters"],
                )
            )

        for rf in self.risk_factors.values():
            if rf.simulated:
                self.market_dependencies.update(
                    rf.model.get_dependencies(global_parameters["calibration_parameters"])
                )

    def calibrate_models(self, global_parameters):
        _ = [
            rf.model.calibrate(self.market_data, global_parameters["calibration_parameters"])
            for rf in self.risk_factors.values()
            if rf.simulated
        ]
        _ = [
            pricer_info[0].calibrate(self.market_data, global_parameters["calibration_parameters"])
            for pricer_info in self.trade_pricer_mapping.values()
        ]

    def mtm_scenarios_valuation(self, global_parameters):
        self.scenarios_MtMs = {}
        for pricer_info in self.trade_pricer_mapping.values():
            self.scenarios_MtMs.update(
                pricer_info[0].price(
                    pricer_info[1],
                    self.portfolio.trade_inventory,
                    self.simulation_dates,
                    self.scenarios,
                    self.market_data,
                    global_parameters,
                )
            )

    def mtm_trades_aggregation(self, global_parameters):
        self.scenarios_portfolio_values = np.zeros(
            (global_parameters["n_paths"], len(self.simulation_dates))
        )
        for netting_set_id, trades in self.portfolio.netting_sets.items():
            if netting_set_id[-4:] == "MAIN":
                for trade_id in trades:
                    trade_currency = self.portfolio.trade_inventory[trade_id].trade_currency
                    if trade_currency == "USD":
                        self.scenarios_portfolio_values += self.scenarios_MtMs[trade_id]
                    else:
                        # TODO(): this requires that FX rates for the trade_currency
                        # is always simulated
                        self.scenarios_portfolio_values += (
                            self.scenarios_MtMs[trade_id]
                            / self.scenarios[f"{trade_currency}_USD_FX_RATE"]
                        )
            else:
                for trade_id in trades:
                    trade_currency = self.portfolio.trade_inventory[trade_id].trade_currency
                    if trade_currency == "USD":
                        self.scenarios_portfolio_values += np.maximum(
                            self.scenarios_MtMs[trade_id], 0
                        )
                    else:
                        self.scenarios_portfolio_values += np.maximum(
                            self.scenarios_MtMs[trade_id]
                            / self.scenarios[f"{trade_currency}_USD_FX_RATE"],
                            0,
                        )

        if self.portfolio.settlement_currency != "USD":
            # TODO(): this requires that FX rates for the trade_currency is always simulated
            self.scenarios_portfolio_values *= self.scenarios[
                f"{self.portfolio.settlement_currency}_USD_FX_RATE"
            ]

    def collateral_requirements_calculation(self, global_parameters):
        self.scenarios_collateral_requirements = np.zeros(
            (global_parameters["n_paths"], len(self.simulation_dates))
        )

        for vm_collateral_agreement in self.portfolio.vm_collateral_agreements.items():
            # uncollateralised trades have no agreement and contribute nothing here
            if vm_collateral_agreement[0] != "NOT_AVAILABLE":
                # Pass variable to compute the MtM of the VM agreement
                pass_vm_collateral_agreement_requirement = np.zeros(
                    (global_parameters["n_paths"], len(self.simulation_dates))
                )

                # If the counterparty is posting collateral, determine the effective T
                # as T+MTA, USD units
                R_flag = vm_collateral_agreement[1]["contractual_terms"]["WE_RECEIVE_R"].iloc[0]
                if R_flag == "YES":
                    T_R_TOT = (
                        vm_collateral_agreement[1]["contractual_terms"]["T_R"].iloc[0]
                        + vm_collateral_agreement[1]["contractual_terms"]["MTA_R"].iloc[0]
                    )
                # if we are posting collateral to the counterparties, determine the
                # effective T as +MTA, USD units
                P_flag = vm_collateral_agreement[1]["contractual_terms"]["WE_POST_P"].iloc[0]
                if P_flag == "YES":
                    T_P_TOT = (
                        vm_collateral_agreement[1]["contractual_terms"]["T_P"].iloc[0]
                        + vm_collateral_agreement[1]["contractual_terms"]["MTA_P"].iloc[0]
                    )

                for trade_id in vm_collateral_agreement[1]["trade_ids"]:
                    trade_currency = self.portfolio.trade_inventory[trade_id].trade_currency
                    if trade_currency == "USD":
                        pass_vm_collateral_agreement_requirement += self.scenarios_MtMs[trade_id]
                    else:
                        pass_vm_collateral_agreement_requirement += (
                            self.scenarios_MtMs[trade_id]
                            / self.scenarios[f"{trade_currency}_USD_FX_RATE"]
                        )
                if R_flag == "YES":
                    self.scenarios_collateral_requirements += np.maximum(
                        pass_vm_collateral_agreement_requirement - T_R_TOT, 0
                    )
                if P_flag == "YES":
                    self.scenarios_collateral_requirements += np.minimum(
                        pass_vm_collateral_agreement_requirement + T_P_TOT, 0
                    )

        if self.portfolio.settlement_currency != "USD":
            self.scenarios_collateral_requirements *= self.scenarios[
                f"{self.portfolio.settlement_currency}_USD_FX_RATE"
            ]

    def compute_exposures(self):
        self.uncollateralised_ee = np.zeros((1, len(self.b3_default_grid)))
        self.collateralised_ee = np.zeros((1, len(self.b3_default_grid)))
        self.uncollateralised_pe = {
            quantile: np.zeros((1, len(self.b3_closeout_grid))) for quantile in self.pe_quantiles
        }
        self.collateralised_pe = {
            quantile: np.zeros((1, len(self.b3_closeout_grid))) for quantile in self.pe_quantiles
        }
        count_array = 0
        count_grid_default = 0
        count_grid_closeout = 0
        for date in self.simulation_dates:
            if date in self.b3_default_grid:
                self.uncollateralised_ee[0, count_grid_default] = np.mean(
                    np.maximum(self.scenarios_portfolio_values[:, count_array], 0), axis=0
                )
                last_collateral_balance = self.scenarios_collateral_requirements[:, count_array]
                for quantile in self.pe_quantiles:
                    self.uncollateralised_pe[quantile][0, count_grid_default] = np.quantile(
                        self.scenarios_portfolio_values[:, count_array], q=quantile, axis=0
                    )
                count_grid_default += 1

            if date in self.b3_closeout_grid:
                self.collateralised_ee[0, count_grid_closeout] = np.mean(
                    np.maximum(
                        self.scenarios_portfolio_values[:, count_array] - last_collateral_balance, 0
                    ),
                    axis=0,
                )
                for quantile in self.pe_quantiles:
                    self.collateralised_pe[quantile][0, count_grid_closeout] = np.quantile(
                        self.scenarios_portfolio_values[:, count_array] - last_collateral_balance,
                        q=quantile,
                        axis=0,
                    )
                count_grid_closeout += 1

            count_array += 1

    def run(self, today_date, global_parameters, pe_quantiles=None, mpor_d=14):
        if pe_quantiles is None:
            pe_quantiles = [0.99]
        self.pe_quantiles = pe_quantiles
        self.mpor_d = mpor_d

        # setting up the valuation sesion
        self.generate_time_grids(today_date, global_parameters)
        self.risk_factors = self.market_data_builder.get_risk_factors(
            self.portfolio.portfolio_underlyings, global_parameters
        )
        self.get_pricers(global_parameters["pricer_mapping"])
        self.get_market_dependencies(global_parameters)
        self.correlation_matrix = self.market_data_builder.load_covariance_matrix(
            global_parameters, [rf.name for rf in self.risk_factors.values() if rf.simulated]
        )
        self.scenario_generator = MultiRiskFactorSimulation(
            [rf for rf in self.risk_factors.values() if rf.simulated], self.correlation_matrix
        )

        # load the data and price the trades
        self.market_data = self.market_data_builder.load_market_data(
            self.market_dependencies, global_parameters
        )
        self.calibrate_models(global_parameters)
        self.scenarios = self.scenario_generator.generate_scenarios(
            self.simulation_dates, global_parameters
        )
        self.mtm_scenarios_valuation(global_parameters)

        # computing exposures
        self.mtm_trades_aggregation(global_parameters)
        self.collateral_requirements_calculation(global_parameters)
        self.compute_exposures()

    def get_exposures(self):
        result = pd.DataFrame(
            {
                "default_times": self.b3_default_grid,
                "uncollateralized_ee": self.uncollateralised_ee[0, :],
            }
        )
        for quantile in self.uncollateralised_pe:
            result[f"uncollateralized_pe_{quantile}"] = self.uncollateralised_pe[quantile][0, :]

        if len(self.portfolio.vm_collateral_agreements) > 0:
            result["collateralized_ee"] = self.collateralised_ee[0, :]
            for quantile in self.collateralised_pe:
                result[f"collateralized_pe_{quantile}"] = self.collateralised_pe[quantile][0, :]

        return result
