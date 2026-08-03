"""Units for the NGFS short-term connector (data/scenarios/ngfs.py)."""

import pandas as pd
import pytest
from climateCCR.data.scenarios import anchor_peaks, load_short_term, policy_rate_delta, sector_peak
from climateCCR.data.scenarios.ngfs import SOVEREIGN_INCL_POLICY, sovereign_adjustment

REGION = "EIRIN 1.0|North America"


def tidy_fixture() -> pd.DataFrame:
    """A miniature of the pipelines/15 tidy schema: 2 years, 2 scenarios."""
    rows = []
    policy = {
        ("Baseline", 2025): [5.0, 5.0, 5.0, 5.0],
        ("Baseline", 2026): [5.0, 5.0, 5.0, 5.0],
        ("HWTP", 2025): [5.0, 5.1, 5.2, 5.3],
        ("HWTP", 2026): [5.5, 6.2, 6.0, 5.8],  # peak delta +1.2 pp at 2026 Q2
    }
    for (scenario, year), values in policy.items():
        for quarter, value in zip(["Q1", "Q2", "Q3", "Q4"], values, strict=True):
            rows.append(
                {
                    "model": "EIRIN",
                    "scenario": scenario,
                    "region": REGION,
                    "variable": "Policy rate",
                    "unit": "%",
                    "year": year,
                    "subannual": quarter,
                    "value": value,
                }
            )
    for year, value in [(2025, 0.3), (2026, -1.5)]:  # signed peak -1.5 pp at 2026
        rows.append(
            {
                "model": "CLIMACRED",
                "scenario": "HWTP",
                "region": "Mexico - MEX",
                "variable": SOVEREIGN_INCL_POLICY,
                "unit": "pp vs BAU",
                "year": year,
                "subannual": "Year",
                "value": value,
            }
        )
    return pd.DataFrame(rows)


def with_time(frame: pd.DataFrame, tmp_path):
    """Round-trip through load_short_term to get the derived time column."""
    frame.to_csv(tmp_path / "fixture.csv", index=False)
    return load_short_term(tmp_path)


def test_policy_rate_delta_differences_against_baseline(tmp_path):
    frame = with_time(tidy_fixture(), tmp_path)
    delta = policy_rate_delta(frame, "HWTP", region=REGION)
    assert len(delta) == 8
    assert delta.loc[delta["time"] == 2026.25, "delta_pp"].item() == pytest.approx(1.2)
    assert delta.loc[delta["time"] == 2025.0, "delta_pp"].item() == pytest.approx(0.0)


def test_sovereign_adjustment_is_already_a_delta(tmp_path):
    frame = with_time(tidy_fixture(), tmp_path)
    sov = sovereign_adjustment(frame, "HWTP")
    assert list(sov["delta_pp"]) == pytest.approx([0.3, -1.5])


def test_anchor_peaks_signed_max_within_window(tmp_path):
    frame = with_time(tidy_fixture(), tmp_path)
    deltas = anchor_peaks(frame, "HWTP", region=REGION, window=(2025.0, 2026.0))
    assert deltas.short_pp == pytest.approx(1.2)  # max |delta| on the quarterly grid
    assert deltas.short_peak_time == pytest.approx(2026.25)
    assert deltas.long_pp == pytest.approx(-1.5)  # sign preserved
    assert deltas.long_peak_time == pytest.approx(2026.5)  # 'Year' maps mid-year


def test_sector_peak_signed_max_of_already_delta_series(tmp_path):
    frame = tidy_fixture()
    for year, value in [(2025, -3.0), (2026, 8.5), (2027, -2.0)]:  # |peak| 8.5 at 2026
        frame.loc[len(frame)] = {
            "model": "CLIMACRED",
            "scenario": "HWTP",
            "region": "Mexico - MEX",
            "variable": "equity_relative_adjustment|Crude Oil",
            "unit": "% vs BAU",
            "year": year,
            "subannual": "Year",
            "value": value,
        }
    frame = with_time(frame, tmp_path)
    peak, when = sector_peak(
        frame, "HWTP", variable="equity_relative_adjustment|Crude Oil", window=(2025.0, 2027.0)
    )
    assert peak == pytest.approx(8.5)  # sign preserved, max |value|
    assert when == pytest.approx(2026.5)
    with pytest.raises(KeyError):
        sector_peak(frame, "SWUC", variable="equity_relative_adjustment|Crude Oil")


def test_unknown_scenario_raises(tmp_path):
    frame = with_time(tidy_fixture(), tmp_path)
    with pytest.raises(KeyError):
        policy_rate_delta(frame, "SWUC", region=REGION)
    with pytest.raises(KeyError):
        sovereign_adjustment(frame, "SWUC")
