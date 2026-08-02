"""Sector-differentiated equity mark scales — the OQ-INT-11 distribution rule.

Composes per-name relative sensitivities ``gamma_i`` for the Mexican book
equities from three layers (config: ``configs/equity_mark_scales.yaml``):

- ``G[i, s]`` — per-name state asset shares (hand-collected public disclosures;
  population shares as the national-proxy fallback, [Bressan2024]'s coarse tier);
- ``S[sector, p]`` — sector x peril-group susceptibility tiers in ``[0, 1]``
  ([CEPAL2014DaLA], [ECB2021EconomyWide], [Bressan2024], [Kruttli2025], CNSF
  evidence for the hidro ordering);
- ``H[s, p]`` — CENAPRED per-capita damage intensity: climate-scope state x
  peril damage deflated to MDP-2025 (GEN-13) over INEGI Censo 2020 population.

``gamma_raw_i = sum_s G[i,s] * sum_p S[sector_i,p] * H[s,p]``, renormalized so
the book-notional-weighted mean is exactly 1: the INT-17 book-level mark is
redistributed across names, never re-estimated. The scales feed the
``target_scales`` channel option of ``ClimateJumpProcess.from_config``
(DC-CCR-SIM-2), where each name's lognormal median becomes ``median * gamma_i``
with ``sigma``/``sign`` unchanged.

Spanish column names and entidad spellings are the data contract (INT-07).
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import pandas as pd

_CLIMATE_SCOPE = "si"


def load_damage_intensity(
    panel_csv: str | Path,
    *,
    deflator: Mapping[int, float],
    peril_groups: Mapping[str, list[str]],
    population: Mapping[str, float],
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    """Per-capita damage intensity ``H[entidad, peril_group]`` in MDP-2025 per person.

    Reads the CENAPRED state x year x peril panel (DC-HAZ-CENAPRED-1), keeps the
    climate scope (GEN-12), deflates ``danio_mdp`` to the deflator's latest year
    (GEN-13), maps ``peril_canonico`` into the configured peril groups, sums over
    the window, and divides by state population.

    Raises if any climate-scope peril in the window is missing from
    ``peril_groups`` (an unmapped peril would silently drop damage) or if the
    panel names an entidad without a population entry.
    """
    panel = pd.read_csv(panel_csv)
    mask = panel["en_alcance_climatico"].eq(_CLIMATE_SCOPE) & panel["anio"].between(
        start_year, end_year
    )
    panel = panel.loc[mask, ["entidad", "anio", "peril_canonico", "danio_mdp"]].copy()

    index = pd.Series(deflator).astype(float)
    missing_years = sorted(set(panel["anio"].astype(int)) - set(index.index))
    if missing_years:
        raise ValueError(f"deflator missing years: {missing_years}")
    base = index.loc[index.index.max()]
    panel["danio_mdp"] = panel["danio_mdp"] * (base / index.loc[panel["anio"]].to_numpy())

    group_of = {peril: group for group, perils in peril_groups.items() for peril in perils}
    unmapped = sorted(set(panel["peril_canonico"]) - set(group_of))
    if unmapped:
        raise ValueError(f"peril_groups leaves climate-scope perils unmapped: {unmapped}")
    panel["peril_group"] = panel["peril_canonico"].map(group_of)

    damage = panel.pivot_table(
        index="entidad", columns="peril_group", values="danio_mdp", aggfunc="sum", fill_value=0.0
    )
    missing_pop = sorted(set(damage.index) - set(population))
    if missing_pop:
        raise ValueError(f"population missing entidades: {missing_pop}")
    pop = pd.Series(population).astype(float)
    return damage.div(pop.reindex(damage.index), axis=0)


def book_equity_weights(eq_desk_csv: str | Path, targets: list[str]) -> pd.Series:
    """Book MXN equity exposure per risk-factor name, normalized to sum 1.

    The Mexican book's equity desk holds, per name, an ATM long call plus a 95%
    short put with share-count notionals (INT-21) — MXN exposure is the call
    (ATM) strike times its notional. Restricted to ``targets`` so desk rows for
    names outside the jump channel cannot skew the renormalization.
    """
    desk = pd.read_csv(eq_desk_csv)
    calls = desk[desk["put/call"].eq("call") & desk["underlying"].isin(targets)]
    missing = sorted(set(targets) - set(calls["underlying"]))
    if missing:
        raise ValueError(f"EQ desk has no call row for targets: {missing}")
    exposure = (calls["notional"] * calls["K"]).groupby(calls["underlying"]).sum()
    return exposure / exposure.sum()


def compose_scales(
    equities: list[dict],
    *,
    susceptibility: Mapping[str, Mapping[str, float]],
    geo_exposure: Mapping[str, Mapping[str, float]],
    population: Mapping[str, float],
    intensity: pd.DataFrame,
    weights: pd.Series,
) -> pd.DataFrame:
    """Per-name scales: ``gamma_raw`` composed, ``gamma`` renormalized to the book.

    ``equities`` are the ``configs/mexican_book.yaml`` entries (``rf``/``sector``);
    ``geo_exposure`` maps rf name -> hand-collected block with ``estados``
    ({entidad: raw magnitude — passengers, property counts}) and optionally
    ``resto_nacional`` (a magnitude spread over population shares, for "top
    states named, rest aggregate" disclosures) — every other name uses
    population shares (the national-proxy tier). Result is indexed by rf name
    with columns ``sector, geo_tier, gamma_raw, gamma``;
    ``(weights * gamma).sum() == 1`` up to float precision.
    """
    pop = pd.Series(population).astype(float)
    pop_shares = pop / pop.sum()

    rows = []
    for eq in equities:
        name, sector = eq["rf"], eq["sector"]
        s_row = susceptibility.get(sector)
        if s_row is None:
            raise ValueError(f"susceptibility has no row for sector {sector!r} ({name})")
        missing_perils = sorted(set(intensity.columns) - set(s_row))
        if missing_perils:
            raise ValueError(f"sector {sector!r} misses peril groups: {missing_perils}")
        # felt_by_peril[s, p] = S[sector, p] * H[s, p] — kept per peril group so the
        # flat gamma and its Phase B per-peril components come from one pass
        # (gamma_raw = sum over columns; OQ-INT-11 a).
        felt_by_peril = intensity.mul(pd.Series(s_row).reindex(intensity.columns), axis=1)
        block = geo_exposure.get(name)
        if block:
            g = pd.Series(block["estados"], dtype=float)
            unknown = sorted(set(g.index) - set(pop.index))
            if unknown:
                raise ValueError(f"{name} exposicion_geografica names unknown entidades: {unknown}")
            resto = float(block.get("resto_nacional", 0.0))
            if resto:
                g = g.add(resto * pop_shares, fill_value=0.0)
            g = g / g.sum()
            tier = "asset_states"
        else:
            g = pop_shares
            tier = "national_proxy"
        raw_by_peril = felt_by_peril.reindex(g.index).fillna(0.0).mul(g, axis=0).sum(axis=0)
        row = {"rf": name, "sector": sector, "geo_tier": tier}
        row.update({f"gamma_raw_{p}": float(v) for p, v in raw_by_peril.items()})
        row["gamma_raw"] = float(raw_by_peril.sum())
        rows.append(row)

    scales = pd.DataFrame(rows).set_index("rf")
    if (scales["gamma_raw"] <= 0).any():
        bad = scales.index[scales["gamma_raw"] <= 0].tolist()
        raise ValueError(f"gamma_raw must be positive (LognormalMark medians): {bad}")
    w = weights.reindex(scales.index)
    if w.isna().any():
        raise ValueError(f"weights missing names: {scales.index[w.isna()].tolist()}")
    denom = (w * scales["gamma_raw"]).sum()
    scales["gamma"] = scales["gamma_raw"] / denom
    # Per-peril components share the flat denominator, so sum_p gamma_<p> == gamma
    # exactly and Phase B redistributes without re-estimating (INT-24 principle).
    for peril in intensity.columns:
        scales[f"gamma_{peril}"] = scales[f"gamma_raw_{peril}"] / denom
    return scales


def peril_mix_from_events(
    events_csv: str | Path,
    *,
    deflator: Mapping[int, float],
    peril_groups: Mapping[str, list[str]],
    start_year: int,
    end_year: int,
    min_damage_mdp: float,
    cluster_storms: bool = False,
) -> pd.Series:
    """Event-frequency peril mix ``pi[group]`` from the jump trigger set (Phase B).

    ``cluster_storms`` counts one arrival per merged named storm instead of one
    per state row (the OQ-INT-11 f grain), passed through to the loader.

    Loads the same discrete climate-scope CENAPRED event set the INT-20 arrival
    intensity is fit on (:func:`~climateCCR.calibration.impact.hazard_jump.
    load_climate_events` with the ``mayores_200mdp`` spec: registry window,
    real-terms threshold), maps ``peril_canonico`` into the configured groups and
    returns normalized *frequency* shares — the label distribution of the
    arrivals the ``intensity`` counts, so labeling is measurement-consistent
    with lambda (user decision 2026-07-30; the damage mix already lives inside
    the per-peril gamma components). Raises on trigger-set perils missing from
    ``peril_groups`` (a silently dropped label would bias the mix).
    """
    from climateCCR.calibration.impact.hazard_jump import load_climate_events

    events = load_climate_events(
        events_csv,
        start_year=start_year,
        end_year=end_year,
        min_damage_mdp=min_damage_mdp,
        deflator=deflator,
        cluster_storms=cluster_storms,
    )
    group_of = {peril: group for group, perils in peril_groups.items() for peril in perils}
    unmapped = sorted(set(events["peril_canonico"]) - set(group_of))
    if unmapped:
        raise ValueError(f"peril_groups leaves trigger-set perils unmapped: {unmapped}")
    counts = events["peril_canonico"].map(group_of).value_counts()
    return (counts / counts.sum()).sort_index()


def cnsf_uso_peril_evidence(cnsf_csv: str | Path, *, top_usos: int = 15) -> pd.DataFrame:
    """CNSF hidro paid-loss shares by USO x TIPO DE EVENTO — the S-ordering evidence.

    Normalized shares of ``MONTO PAGADO`` across the top property uses (rows) and
    event types (columns) in the hidrometeorológico line: the empirical support
    for ranking building-sector susceptibility (e.g. HOTEL vs TIENDA vs FÁBRICA)
    in the hidro-driven columns of the S matrix. Evidence only — levels in the
    config stay literature tiers.
    """
    df = pd.read_csv(cnsf_csv, low_memory=False)
    for col in ("USO", "TIPO DE EVENTO"):
        df[col] = df[col].astype(str).str.strip().str.upper()
    keep = df.groupby("USO")["MONTO PAGADO"].sum().nlargest(top_usos).index
    table = df[df["USO"].isin(keep)].pivot_table(
        index="USO", columns="TIPO DE EVENTO", values="MONTO PAGADO", aggfunc="sum", fill_value=0.0
    )
    return table / table.to_numpy().sum()
