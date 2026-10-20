"""Units for the S-tier jitter of pipelines/11: per-sector substreams, ladder, structural zeros.

The jitter used to draw one step per nonzero cell from a single generator over every
row of the S matrix in config order, so adding or reordering rows outside the book
shifted the Mexican draws (OQ-GEN-04 a). Each sector now draws from its own substream
keyed by its name; these tests lock the invariance, the ladder semantics, the step law
and a small synthetic golden of the composed ordering statistic.
"""

import importlib.util
import sys
import zlib
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml
from climateCCR.calibration.impact.sector_scales import compose_scales
from scipy.stats import kendalltau

REPO_ROOT = Path(__file__).resolve().parents[2]
LADDER = [0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0]
POPULATION = {"Costa": 1_000_000, "Sierra": 4_000_000}
EQUITIES = [
    {"rf": "HOTELCO_SHARE", "sector": "hoteles"},
    {"rf": "AGROCO_SHARE", "sector": "agroalimentos"},
    {"rf": "MINECO_SHARE", "sector": "mineria"},
]
SECTORS = ["hoteles", "agroalimentos", "mineria"]
S = {
    "hoteles": {"ciclon": 1.0, "sequia": 0.1},
    "agroalimentos": {"ciclon": 0.3, "sequia": 0.7},
    "mineria": {"ciclon": 0.2, "sequia": 0.5},
    "telecom": {"ciclon": 0.05, "sequia": 0.0},  # a row outside the book, with a structural zero
}
WEIGHTS = pd.Series({"HOTELCO_SHARE": 0.4, "AGROCO_SHARE": 0.4, "MINECO_SHARE": 0.2})
GEO = {"HOTELCO_SHARE": {"estados": {"Costa": 10}}}


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def s_tier():
    return _load("s_tier_sensitivity", "pipelines/11_s_tier_sensitivity.py")


def _intensity():
    return pd.DataFrame({"ciclon": [3e-4, 5e-5], "sequia": [1e-5, 1e-4]}, index=["Costa", "Sierra"])


def _gamma(susceptibility):
    return compose_scales(
        EQUITIES,
        susceptibility=susceptibility,
        geo_exposure=GEO,
        population=POPULATION,
        intensity=_intensity(),
        weights=WEIGHTS,
    )["gamma"]


def test_jitter_draws_per_sector_are_invariant_to_other_rows(s_tier):
    ladder = np.array(LADDER)
    a = s_tier.jitter_tables(S, ["hoteles", "agroalimentos"], seed=7, n_draws=50, ladder=ladder)
    reordered = {
        "telecom": S["telecom"],
        "agroalimentos": S["agroalimentos"],
        "extra": {"ciclon": 0.3, "sequia": 0.3},
        "hoteles": S["hoteles"],
    }
    b = s_tier.jitter_tables(
        reordered, ["agroalimentos", "hoteles"], seed=7, n_draws=50, ladder=ladder
    )
    for k in range(50):
        assert a[k]["hoteles"] == b[k]["hoteles"]
        assert a[k]["agroalimentos"] == b[k]["agroalimentos"]
    # a shorter run is a prefix of a longer one; rows outside `sectors` are copied verbatim
    c = s_tier.jitter_tables(S, ["hoteles"], seed=7, n_draws=20, ladder=ladder)
    for k in range(20):
        assert c[k]["hoteles"] == a[k]["hoteles"]
        assert c[k]["agroalimentos"] == S["agroalimentos"]
        assert c[k]["telecom"] == S["telecom"]
    # the seed matters
    d = s_tier.jitter_tables(S, ["hoteles"], seed=8, n_draws=20, ladder=ladder)
    assert any(d[k]["hoteles"] != c[k]["hoteles"] for k in range(20))


def test_jitter_respects_ladder_and_structural_zeros(s_tier):
    tables = s_tier.jitter_tables(
        S, ["hoteles", "telecom"], seed=1, n_draws=3000, ladder=np.array(LADDER)
    )
    steps = []
    for table in tables:
        assert table["telecom"]["sequia"] == 0.0  # structural zero: no channel, not a level
        for sector in ("hoteles", "telecom"):
            for peril, value in table[sector].items():
                if S[sector][peril] > 0:
                    assert value in LADDER
                    assert abs(LADDER.index(value) - LADDER.index(S[sector][peril])) <= 1
        steps.append(LADDER.index(table["hoteles"]["sequia"]) - LADDER.index(0.1))
    shares = np.bincount(np.array(steps) + 1, minlength=3) / len(steps)
    assert np.allclose(shares, 1 / 3, atol=0.03)  # -1 / 0 / +1 with probability 1/3 each


def test_tier_ladder_and_book_sectors(s_tier):
    assert s_tier.tier_ladder(S, list(S)).tolist() == LADDER
    assert s_tier.tier_ladder(S, ["mineria"]).tolist() == [0.2, 0.5]
    assert s_tier.book_sectors(EQUITIES + [{"rf": "X_SHARE", "sector": "hoteles"}]) == SECTORS


def test_sector_stream_is_stable_and_distinct_over_the_config(s_tier):
    assert s_tier.sector_stream("hoteles") == zlib.crc32(b"s_tier_jitter:hoteles")
    rows = yaml.safe_load(
        (REPO_ROOT / "configs" / "equity_mark_scales.yaml").read_text(encoding="utf-8")
    )["susceptibility"]
    assert len({s_tier.sector_stream(sector) for sector in rows}) == len(rows)


def test_jitter_mini_golden(s_tier):
    tables = s_tier.jitter_tables(S, SECTORS, seed=233423, n_draws=200, ladder=np.array(LADDER))
    assert tables[0]["hoteles"] == {"ciclon": 1.0, "sequia": 0.2}
    assert tables[0]["agroalimentos"] == {"ciclon": 0.2, "sequia": 1.0}
    assert tables[0]["mineria"] == {"ciclon": 0.2, "sequia": 0.5}
    gamma0 = _gamma(S)
    taus = np.array(
        [
            kendalltau(gamma0.to_numpy(), _gamma(t).reindex(gamma0.index).to_numpy()).statistic
            for t in tables
        ]
    )
    assert np.round(taus[:5], 6).tolist() == [1.0, 1.0, 0.333333, 1.0, 1.0]
    assert np.median(taus) == pytest.approx(1.0)
    assert taus.min() == pytest.approx(1 / 3, abs=1e-6)


def test_band_label(s_tier):
    prefix = "climate_jump_real_comparison"
    assert s_tier.band_label(prefix, prefix) == "headline"
    assert s_tier.band_label(f"{prefix}_ct_anchor", prefix) == "ct_anchor"
    assert (
        s_tier.band_label("climate_jump_real_mexican_floor", "climate_jump_real_mexican") == "floor"
    )
