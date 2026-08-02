"""Unit tests for the OQ-INT-11 sector-scale composition (sector_scales.py)."""

import pandas as pd
import pytest
from climateCCR.calibration.impact.sector_scales import (
    book_equity_weights,
    compose_scales,
    load_damage_intensity,
)

DEFLATOR = {2020: 50.0, 2021: 100.0}
POPULATION = {"Costa": 1_000_000, "Sierra": 4_000_000}
PERIL_GROUPS = {"ciclon": ["Ciclón tropical"], "sequia": ["Sequía"]}


def _panel_csv(tmp_path):
    frame = pd.DataFrame(
        {
            "entidad": ["Costa", "Costa", "Sierra", "Sierra"],
            "anio": [2020, 2021, 2021, 2021],
            "peril_canonico": ["Ciclón tropical", "Ciclón tropical", "Sequía", "Fuera"],
            "en_alcance_climatico": ["si", "si", "si", "no"],
            "danio_mdp": [100.0, 100.0, 400.0, 999.0],
        }
    )
    path = tmp_path / "panel.csv"
    frame.to_csv(path, index=False)
    return path


def test_damage_intensity_deflates_groups_and_normalizes_per_capita(tmp_path):
    intensity = load_damage_intensity(
        _panel_csv(tmp_path),
        deflator=DEFLATOR,
        peril_groups=PERIL_GROUPS,
        population=POPULATION,
        start_year=2020,
        end_year=2021,
    )
    # Costa ciclón: 100 * (100/50) + 100 = 300 MDP-2021 over 1M people.
    assert intensity.loc["Costa", "ciclon"] == pytest.approx(300.0 / 1_000_000)
    # Sierra sequía: 400 / 4M; the out-of-scope row is dropped.
    assert intensity.loc["Sierra", "sequia"] == pytest.approx(400.0 / 4_000_000)
    assert intensity.loc["Sierra", "ciclon"] == 0.0


def test_damage_intensity_rejects_unmapped_peril(tmp_path):
    with pytest.raises(ValueError, match="unmapped"):
        load_damage_intensity(
            _panel_csv(tmp_path),
            deflator=DEFLATOR,
            peril_groups={"ciclon": ["Ciclón tropical"]},  # Sequía unmapped
            population=POPULATION,
            start_year=2020,
            end_year=2021,
        )


def _intensity():
    return pd.DataFrame({"ciclon": [3e-4, 0.0], "sequia": [0.0, 1e-4]}, index=["Costa", "Sierra"])


EQUITIES = [
    {"rf": "HOTELCO_SHARE", "sector": "hoteles"},
    {"rf": "AGROCO_SHARE", "sector": "agroalimentos"},
]
SUSCEPTIBILITY = {
    "hoteles": {"ciclon": 1.0, "sequia": 0.0},
    "agroalimentos": {"ciclon": 0.0, "sequia": 1.0},
}


def test_compose_scales_renormalizes_to_book_anchor():
    weights = pd.Series({"HOTELCO_SHARE": 0.5, "AGROCO_SHARE": 0.5})
    scales = compose_scales(
        EQUITIES,
        susceptibility=SUSCEPTIBILITY,
        geo_exposure={"HOTELCO_SHARE": {"estados": {"Costa": 10}}},
        population=POPULATION,
        intensity=_intensity(),
        weights=weights,
    )
    assert (weights * scales["gamma"]).sum() == pytest.approx(1.0, abs=1e-12)
    assert scales.loc["HOTELCO_SHARE", "geo_tier"] == "asset_states"
    assert scales.loc["AGROCO_SHARE", "geo_tier"] == "national_proxy"
    # The coastal hotel feels the full Costa ciclón intensity (3e-4); the agro
    # name feels the population-weighted sequía intensity (0.8 * 1e-4).
    ratio = scales.loc["HOTELCO_SHARE", "gamma"] / scales.loc["AGROCO_SHARE", "gamma"]
    assert ratio == pytest.approx(3e-4 / (0.8 * 1e-4))


def test_compose_scales_resto_nacional_blends_population():
    geo = {"HOTELCO_SHARE": {"estados": {"Costa": 8}, "resto_nacional": 2}}
    scales = compose_scales(
        EQUITIES,
        susceptibility=SUSCEPTIBILITY,
        geo_exposure=geo,
        population=POPULATION,
        intensity=_intensity(),
        weights=pd.Series({"HOTELCO_SHARE": 0.5, "AGROCO_SHARE": 0.5}),
    )
    # G = (Costa 8 + 2 * pop shares) / 10 -> Costa 8.4/10; ciclón intensity only.
    concentrated = compose_scales(
        EQUITIES,
        susceptibility=SUSCEPTIBILITY,
        geo_exposure={"HOTELCO_SHARE": {"estados": {"Costa": 10}}},
        population=POPULATION,
        intensity=_intensity(),
        weights=pd.Series({"HOTELCO_SHARE": 0.5, "AGROCO_SHARE": 0.5}),
    )
    assert scales.loc["HOTELCO_SHARE", "gamma_raw"] == pytest.approx(
        0.84 * concentrated.loc["HOTELCO_SHARE", "gamma_raw"]
    )


def test_compose_scales_rejects_unknown_state_and_zero_gamma():
    with pytest.raises(ValueError, match="unknown entidades"):
        compose_scales(
            EQUITIES,
            susceptibility=SUSCEPTIBILITY,
            geo_exposure={"HOTELCO_SHARE": {"estados": {"Atlantis": 1}}},
            population=POPULATION,
            intensity=_intensity(),
            weights=pd.Series({"HOTELCO_SHARE": 0.5, "AGROCO_SHARE": 0.5}),
        )
    with pytest.raises(ValueError, match="positive"):
        compose_scales(
            EQUITIES,
            susceptibility={**SUSCEPTIBILITY, "hoteles": {"ciclon": 0.0, "sequia": 0.0}},
            geo_exposure={},
            population=POPULATION,
            intensity=_intensity(),
            weights=pd.Series({"HOTELCO_SHARE": 0.5, "AGROCO_SHARE": 0.5}),
        )


def test_book_equity_weights_uses_call_strikes(tmp_path):
    desk = pd.DataFrame(
        {
            "underlying": ["A_SHARE", "A_SHARE", "B_SHARE", "B_SHARE"],
            "put/call": ["call", "put", "call", "put"],
            "notional": [100.0, 100.0, 300.0, 300.0],
            "K": [10.0, 9.5, 1.0, 0.95],
        }
    )
    path = tmp_path / "eq.csv"
    desk.to_csv(path, index=False)
    weights = book_equity_weights(path, ["A_SHARE", "B_SHARE"])
    # MXN exposure: A 100*10 = 1000, B 300*1 = 300 (puts ignored).
    assert weights["A_SHARE"] == pytest.approx(1000 / 1300)
    with pytest.raises(ValueError, match="C_SHARE"):
        book_equity_weights(path, ["A_SHARE", "C_SHARE"])


def test_compose_scales_peril_components_sum_to_gamma():
    # Phase B decomposition: the per-peril columns share the flat denominator,
    # so sum_p gamma_<p> == gamma exactly and zero-susceptibility perils carry
    # an exact zero component (the c = 0 masking source).
    weights = pd.Series({"HOTELCO_SHARE": 0.5, "AGROCO_SHARE": 0.5})
    scales = compose_scales(
        EQUITIES,
        susceptibility=SUSCEPTIBILITY,
        geo_exposure={"HOTELCO_SHARE": {"estados": {"Costa": 10}}},
        population=POPULATION,
        intensity=_intensity(),
        weights=weights,
    )
    recomposed = scales["gamma_ciclon"] + scales["gamma_sequia"]
    pd.testing.assert_series_equal(recomposed, scales["gamma"], check_names=False)
    assert scales.loc["HOTELCO_SHARE", "gamma_sequia"] == 0.0
    assert scales.loc["AGROCO_SHARE", "gamma_ciclon"] == 0.0


def test_peril_mix_from_events_frequency_shares(tmp_path):
    from climateCCR.calibration.impact.sector_scales import peril_mix_from_events

    frame = pd.DataFrame(
        {
            "anio": [2020, 2020, 2021, 2021, 2021, 2021],
            "duracion_dias": [2.0, 3.0, 1.0, None, 4.0, 400.0],
            "peril_canonico": ["Ciclón tropical"] * 3 + ["Sequía"] * 3,
            "en_alcance_climatico": ["si", "si", "si", "si", "no", "si"],
            # nominal 60 in 2020 deflates to 120 (base 2021) -> above threshold
            "danio_mdp": [60.0, 40.0, 150.0, 200.0, 999.0, 999.0],
        }
    )
    path = tmp_path / "events.csv"
    frame.to_csv(path, index=False)
    mix = peril_mix_from_events(
        path,
        deflator=DEFLATOR,
        peril_groups=PERIL_GROUPS,
        start_year=2020,
        end_year=2021,
        min_damage_mdp=100.0,
    )
    # Kept: ciclón 2020/60->120, ciclón 2021/150, sequía 2021/200 (NaN duration
    # is discrete). Dropped: 2020/40->80 below bar, out-of-scope, 400-day
    # aggregate. Frequency shares: ciclón 2/3, sequía 1/3.
    assert mix["ciclon"] == pytest.approx(2 / 3)
    assert mix["sequia"] == pytest.approx(1 / 3)
    with pytest.raises(ValueError, match="unmapped"):
        peril_mix_from_events(
            path,
            deflator=DEFLATOR,
            peril_groups={"ciclon": ["Ciclón tropical"]},
            start_year=2020,
            end_year=2021,
            min_damage_mdp=100.0,
        )


def test_peril_mix_from_events_cluster_storms(tmp_path):
    from climateCCR.calibration.impact.sector_scales import peril_mix_from_events

    frame = pd.DataFrame(
        {
            "anio": [2021, 2021, 2021],
            "duracion_dias": [2.0, 2.0, 1.0],
            "peril_canonico": ["Ciclón tropical", "Ciclón tropical", "Sequía"],
            "en_alcance_climatico": ["si"] * 3,
            "danio_mdp": [150.0, 150.0, 200.0],
            "nombre_evento": ["Huracán Rick", "Huracán Rick", None],
        }
    )
    path = tmp_path / "events.csv"
    frame.to_csv(path, index=False)
    kwargs = dict(
        deflator=DEFLATOR,
        peril_groups=PERIL_GROUPS,
        start_year=2021,
        end_year=2021,
        min_damage_mdp=100.0,
    )
    # Unclustered: 2 ciclón rows + 1 sequía. Clustered: Rick merges -> 1 + 1.
    assert peril_mix_from_events(path, **kwargs)["ciclon"] == pytest.approx(2 / 3)
    mix = peril_mix_from_events(path, cluster_storms=True, **kwargs)
    assert mix["ciclon"] == pytest.approx(1 / 2)
    assert mix["sequia"] == pytest.approx(1 / 2)
