from datetime import datetime

from .trade import Trade


class FloatingRateNote(Trade):
    """Floating-rate cebur (28-day TIIE reset + sobretasa), the local-market FRN.

    Trade attributes (desk CSV columns, CCR-RISK-04 semantics): notional,
    currency, ``coupon`` = the *contractual* sobretasa (decimal margin over the
    index, fixed at issuance — never shocked), ``spread`` = the *discount*
    margin (decimal; equals the issuance sobretasa at build time and is the
    column the NGFS bond leg shocks), long/short, maturity. The discount curve
    is resolved from the trade currency; the 28-day schedule is implied by the
    maturity via ``frn_cashflow_times`` at pricing time.
    """

    def __init__(self, trade_id):
        super().__init__(trade_id, "BOND_FRN", "DEBT")

    def load_additional_trade_attributes(self, global_parameters, risk_factors):
        self.trade_attributes["maturity"] = datetime.strptime(
            self.trade_attributes["maturity"], global_parameters["date_format"]
        )

        discount_curves = risk_factors[risk_factors["type"] == "DISCOUNT_CURVE"]
        trade_underlyings = [
            discount_curves[discount_curves["currency"] == self.trade_attributes["currency"]][
                "name"
            ].iloc[0]
        ]

        return self.trade_attributes["currency"], trade_underlyings, []
