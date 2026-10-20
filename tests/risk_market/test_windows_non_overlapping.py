"""Per-horizon non-overlapping subsets of a config-driven initialisation grid (BCBS 2010 ¶13)."""

import pandas as pd
import pytest
from climateCCR.risk.market import horizon_spec, init_dates, non_overlapping

ANNUAL = [f"{year}-07-15" for year in range(2016, 2026)]


def test_horizon_spec_reads_the_b3_letters():
    assert horizon_spec("0D") == {"days": 0}
    assert horizon_spec("1W") == {"days": 7}
    assert horizon_spec("3M") == {"months": 3}
    assert horizon_spec("2Y") == {"months": 24}
    with pytest.raises(ValueError):
        horizon_spec("1Q")


def test_non_overlapping_keeps_every_date_up_to_the_annual_horizon():
    for label in ("1W", "1M", "3M", "1Y"):
        kept = non_overlapping(ANNUAL, horizon_spec(label))
        assert [t.strftime("%Y-%m-%d") for t in kept] == ANNUAL


def test_non_overlapping_thins_the_longer_horizons():
    two = [t.year for t in non_overlapping(ANNUAL, horizon_spec("2Y"))]
    three = [t.year for t in non_overlapping(ANNUAL, horizon_spec("3Y"))]
    assert two == [2016, 2018, 2020, 2022, 2024]
    assert three == [2016, 2019, 2022, 2025]


def test_non_overlapping_matches_init_dates_on_a_regular_grid():
    spec = horizon_spec("3Y")
    regular = init_dates("2016-07-15", "2026-07-17", spec)
    assert non_overlapping(regular, spec) == regular
    # order and duplicates do not matter; a date just short of the horizon is dropped
    assert non_overlapping(["2019-07-15", "2016-07-15", "2019-07-14"], spec) == [
        pd.Timestamp("2016-07-15"),
        pd.Timestamp("2019-07-15"),
    ]
