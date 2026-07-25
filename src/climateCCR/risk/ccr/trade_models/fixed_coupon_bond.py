from datetime import datetime

from .trade import Trade


class FixedCouponBond(Trade):
    """Fixed-coupon bullet bond (cebures / Bonos M style, 182-day coupon periods).

    Trade attributes (desk CSV columns): notional, currency, coupon (decimal
    annual rate), spread (decimal, static — fixed at issuance), long/short,
    maturity. The discount curve is resolved from the trade currency, like
    EquityEuropeanOption; the cashflow schedule is implied by the maturity via
    ``bono_cashflows`` at pricing time, so no schedule columns are needed.
    """

    def __init__(self, trade_id):
        super().__init__(trade_id, "BOND_FIXED", "DEBT")

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
