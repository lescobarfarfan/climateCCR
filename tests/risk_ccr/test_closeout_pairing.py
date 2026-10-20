"""Close-out exposures net the collateral balance frozen at their own default date (OQ-CCR-11).

Close-out j is default j + MPOR. The exposure loop used to keep a single
"last balance seen" and, walking the simulation dates in order, the 2W
default date (day 14) overwrote it before the 0D/1D/1W close-outs (days
14/15/21) were reached — so those three close-outs netted the 2W balance.
A synthetic four-date grid with distinct balances per date pins the pairing.
"""

from datetime import datetime, timedelta

import numpy as np
from climateCCR.risk.ccr.evaluators.ccr_valuation_session import CCR_Valuation_Session


def test_closeout_nets_the_balance_frozen_at_its_own_default_date():
    session = CCR_Valuation_Session(None)
    d0 = datetime(2020, 1, 1)
    session.mpor_d = 14
    session.b3_default_grid = [d0 + timedelta(days=k) for k in (0, 1, 7, 14)]
    session.b3_closeout_grid = [d + timedelta(days=14) for d in session.b3_default_grid]
    session.simulation_dates = sorted(set(session.b3_default_grid + session.b3_closeout_grid))
    session.pe_quantiles = [0.99]
    n = len(session.simulation_dates)
    values = np.vstack([100.0 + np.arange(n), 50.0 + np.arange(n)])  # 2 paths x n dates
    balances = np.vstack([10.0 * np.arange(n), 5.0 * np.arange(n)])  # distinct per date
    session.scenarios_portfolio_values = values
    session.scenarios_collateral_requirements = balances

    session.compute_exposures()

    index = {date: i for i, date in enumerate(session.simulation_dates)}
    for j, (default_date, closeout_date) in enumerate(
        zip(session.b3_default_grid, session.b3_closeout_grid, strict=True)
    ):
        net = values[:, index[closeout_date]] - balances[:, index[default_date]]
        assert session.collateralised_ee[0, j] == np.mean(np.maximum(net, 0))
        assert session.collateralised_pe[0.99][0, j] == np.quantile(net, 0.99)
        # the uncollateralised profile is unaffected by the pairing
        assert session.uncollateralised_ee[0, j] == np.mean(
            np.maximum(values[:, index[default_date]], 0)
        )
