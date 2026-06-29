import pandas as pd

from climateCCR.data.market.curve import Curve
from climateCCR.data.market.surface import Surface
from climateCCR.simulation.correlation_matrix import CorrelationMatrix
from climateCCR.simulation.risk_factor import RiskFactor


class MarketDataBuilder:
    def __init__(self) -> None:
        pass

    def load_row_with_simple_features_only(self, row):
        result = {}
        for feat_name, feat_value in row.items():
            result[feat_name] = feat_value
        return result

    def load_row_with_one_curve(self, row):
        result = {}
        rate_curve_tenors = {}
        rate_curve_values = {}
        for feat_name, feat_value in row.items():
            if feat_name[0:11] == "rate_curve_":
                if feat_name[11] == "V":
                    rate_curve_values[feat_name[12:]] = feat_value
                elif feat_name[11] == "T":
                    rate_curve_tenors[feat_name[12:]] = feat_value
                else:
                    raise ValueError(f"Do not know what {feat_name} is.")
            else:
                result[feat_name] = feat_value

        if len(rate_curve_tenors) > 0 or len(rate_curve_values) > 0:
            if len(rate_curve_tenors) != len(rate_curve_values):
                raise ValueError("Unequal number of tenors and values for rate curve!")

            rate_curve = {}
            for index, tenor in rate_curve_tenors.items():
                rate_curve[tenor] = rate_curve_values[index]

            result["rate_curve"] = Curve(rate_curve)

        return result

    # The data are stored with sequence K1 T1...TN K2 T1...TN K3 T1...TN...
    def load_row_with_one_surface(self, row):
        result = {}
        vol_surface_tenors = {}
        vol_surface_strikes = {}
        vol_surface_values = {}
        for feat_name, feat_value in row.items():
            if feat_name[0:27] == "IMPLIED_VOLATILITY_SURFACE_":
                if feat_name[27] == "V":
                    vol_surface_values[feat_name[27:]] = feat_value
                elif feat_name[27] == "T":
                    vol_surface_tenors[feat_name[27:]] = feat_value
                elif feat_name[27] == "K":
                    vol_surface_strikes[feat_name[27:]] = feat_value
                else:
                    raise ValueError(f"Do not know what {feat_name} is.")
            else:
                result[feat_name] = feat_value

        if len(vol_surface_tenors) > 0 or len(vol_surface_values) > 0:
            if len(vol_surface_tenors) * len(vol_surface_strikes) != len(vol_surface_values):
                raise ValueError(
                    "Unequal number of tenors/strikes and values for implied volatility surface!"
                )

            vol_surface = pd.DataFrame(
                index=vol_surface_strikes.values(), columns=vol_surface_tenors.values()
            )
            count = 1
            for strike in vol_surface_strikes.values():
                for tenor in vol_surface_tenors.values():
                    pass_key = "V" + str(count)
                    # Single-step .loc assignment: chained `vol_surface[tenor].loc[strike] = …`
                    # silently no-ops under pandas >=3.0 Copy-on-Write (CCR-MIG-02 extension).
                    vol_surface.loc[strike, tenor] = vol_surface_values[pass_key]
                    count = count + 1
            result = Surface(vol_surface)
        return result

    def load_market_data(self, market_dependencies, global_parameters):
        files_to_load = set([item[0] for item in market_dependencies])
        data_loads = {}
        for name in files_to_load:
            data_loads[name] = pd.read_csv(
                global_parameters["market_data_by_service"][name], index_col=0
            )

        market_data = {}
        for item in market_dependencies:
            if item[0] not in market_data:
                market_data[item[0]] = {}

            if item[0] == "spread_to_discount_curve":
                market_data[item[0]][item[1]] = self.load_row_with_one_curve(
                    data_loads[item[0]].loc[item[1]]
                )["rate_curve"]

            elif item[0] == "historical_fixings":
                market_data[item[0]][item[1]] = data_loads[item[0]][item[1]]

            elif item[0] in [
                "RFE_BM_calibration",
                "RFE_GBM_calibration",
                "Pricing_BM_calibration",
                "Pricing_GBM_calibration",
            ]:
                market_data[item[0]][item[1]] = self.load_row_with_simple_features_only(
                    data_loads[item[0]].loc[item[1]]
                )

            elif item[0] in ["RFE_HW1F_calibration", "Pricing_HW1F_calibration"]:
                market_data[item[0]][item[1]] = self.load_row_with_one_curve(
                    data_loads[item[0]].loc[item[1]]
                )

            elif item[0] == "equity_implied_volatility_surface":
                market_data[item[0]][item[1]] = self.load_row_with_one_surface(
                    data_loads[item[0]].loc[item[1]]
                )

            elif item[0] == "equity_spot":
                market_data[item[0]][item[1]] = self.load_row_with_simple_features_only(
                    data_loads[item[0]].loc[item[1]]
                )

            else:
                raise ValueError(f"No dependency implementation for {item[0]}.")

        return market_data

    def load_covariance_matrix(self, global_parameters, underlyings):
        correlation_matrix = CorrelationMatrix(
            file_path=global_parameters["prototype_data_paths"]["RFE"]
            + global_parameters["prototype_data_files"]["RFE"]["RFE_correlation_matrix"]
        )
        return correlation_matrix.get_sub_correlation_matrix(underlyings)

    def get_risk_factors(self, portfolio_underlyings, global_parameters):
        risk_factors = pd.read_csv(
            global_parameters["prototype_data_paths"]["RFs_attributes"]
            + global_parameters["prototype_data_files"]["RFs_attributes"]["all_RFs_mapping"]
        )
        result = {}
        for _, row in risk_factors.iterrows():
            if row["name"] in portfolio_underlyings:
                is_simulated = row.simulated == "YES"
                result[row["name"]] = RiskFactor(
                    name=row["name"],
                    asset_class=row.asset_class,
                    asset_type=row.type,
                    currency=row.currency,
                    simulated=is_simulated,
                    model_name=row.model,
                    reference=row.reference,
                )

        return result
