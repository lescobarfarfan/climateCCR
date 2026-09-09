# NGFS application flavors — nivel, trayectoria, fase (the two-workflow recipe)

Operational note for the three ways an NGFS short-term transition scenario is applied to the Mexican book (`OQ-INT-12` c; decisions `MKT-NGFS-06/09`, `INT-33/34`). It says which pipeline produces what, the exact run flags, where each readout lands, and the conventions every comparison must respect. Numbers live in the canon ([[DECISIONS]]), not here.

## The three flavors in one line each

**nivel** — the t=0 state: the signed peak of each anchor and sector path over 2025–2030 is applied once to a *shocked copy of the book* (curve, equity spots, cebur spreads) and the whole Monte Carlo runs from that state (`MKT-NGFS-06/08`; the headline transition convention, `MKT-NGFS-09`).

**trayectoria** — still a t=0 state, but each zero pillar takes the anchor delta prevailing at its *own maturity date* (a maturity-dated curve reshape; rates only — `MKT-NGFS-09`, the robustness flavor).

**fase** — the path arrives *inside the simulation*: the unshocked book is priced off the observed market at t=0 and a deterministic scheduled overlay applies the scenario delta prevailing at each simulation date to the simulated rate and equity factors (`INT-33/34`); the credit-spread channel is valuation-side — the bond pricers read a per-issuer spread schedule at each reporting date (`OQ-INT-12` b).

## Workflow A — nivel / trayectoria (shocked book roots)

1. `pipelines/16_ngfs_shock_curves.py [--config configs/ngfs_shock_trayectoria.yaml]` copies `data/ccr_book_mx` to `data/ccr_book_mx_ngfs[_trayectoria]/<scen>/` and rewrites the shocked CSVs (the curve; nivel also the equity spots and the `BONDS.csv` spreads).
2. `pipelines/01_climate_jump_demo.py --config configs/climate_jump_real_mexican{,_ct_anchor,_floor}.yaml --book-config configs/mexican_book.yaml --data-root data/ccr_book_mx_ngfs/<scen> --horizonte largo --etiqueta ngfs_<scen>[_trayectoria]` — one run per scenario × λ band; the run directory is the config stem plus the etiqueta.
3. `pipelines/17_ngfs_epe_readout.py [--config configs/ngfs_shock_trayectoria.yaml]` reads the `readout` block of the flavor's shock config → `results/ngfs_epe_readout[_trayectoria]/`.

## Workflow B — fase (the same book plus a fragment)

1. `pipelines/22_ngfs_scheduled_shocks.py [--forzar]` emits one fragment per scenario, `results/ngfs_scheduled_shocks/<SCEN>.yaml`: `rate_shocks` (the EIRIN policy-rate delta, decimal), `equity_shocks` (the CLIMACRED sector adjustments as log factors on the 26 names), `spread_shocks` (the excl-policy corporate spread deltas, decimal, on the 18 issuers) — one Act/365 axis per channel from the valuation date, raw published deltas (the t=0 point carries the delta already accumulated at the valuation date), points at or beyond decimal 2031.0 dropped, the last value held beyond.
2. `pipelines/01_climate_jump_demo.py --config configs/climate_jump_real_mexican{,_ct_anchor,_floor}.yaml --book-config configs/mexican_book.yaml --data-root data/ccr_book_mx --horizonte largo --etiqueta ngfs_<scen>_fase --choques-programados results/ngfs_scheduled_shocks/<SCEN>.yaml` — the fragment applies to BOTH legs (jump-off and jump-on), so jump-on − jump-off stays the pure physical channel; the fragment's `valuation_date` must equal the run config's (loud check) and its spread channel must name at least one issuer of the book (loud check).
3. `pipelines/17_ngfs_epe_readout.py --config configs/ngfs_scheduled.yaml` → `results/ngfs_epe_readout_fase/` (the `readout` block of the producer config, `flavor: fase`).

## Readout artifacts (every flavor)

`book_epe_deltas.csv` — one row per scenario × band: `transition_pct` (scenario jump-off vs base jump-off; band-independent by construction), `combined_pct` (scenario jump-on vs base jump-off), `jump_within_pct` (the scenario run's own jump-on vs jump-off — the physical channel under that transition state). The base is always the unshocked headline run `climate_jump_real_mexican` (jump-off), so the three flavors are like-for-like on the `INT-23` metric.

`book_profile_deltas.csv` — the same three deltas per reporting pillar (whole-book EE summed over the netting sets; `pillar_index` 0 = the 0D valuation date).

## Conventions every comparison respects

- **t=0 is the observed market in every flavor, so fase 0D rows are zero-delta by construction** (the `INT-33` pin). The fase readout asserts this per NAID and fails loudly otherwise — a 0D delta is a bug signal, not a result. Nivel and trayectoria *do* move 0D (they revalue the book itself), so per-pillar fase-vs-nivel comparisons start at the first post-0D pillar; the book-EPE metric itself is unchanged (the 0D pillar carries $\approx 2.7 \times 10^{-5}$ of the 50-year trapezoid weight).
- **`DAPS_NAM` is transition-only** (jump-off vs jump-off): NGFS physical-embedding narratives are never combined with the HAZ jump (`INT-29`).
- **CVA keeps t=0 discount factors**: the fase legs in `configs/cva.yaml` use `curve: base` (their book root is unshocked); the nivel legs discount off their own shocked curve (`CCR-RISK-06`).
- **Transition deltas are band-independent**; combined and jump-within are band-specific.
- **The fase rate leg carries the policy anchor only** — the single-factor model propagates it through its own $B(t,T)/\alpha$ loading, so the sovereign long anchor of the t=0 flavors is absent (`INT-33`); fase transition deltas are model-consistent, not anchor-blended.
- **The fase spread leg is a prevailing level**: at each reporting date the bond pricers use $\max(s_0 + \Delta s(t), 0)$ on all remaining cashflows — the nivel `spread + delta` semantics per date, floored at 0 like the nivel leg (CFE floors under HWTP in both flavors), deliberately not a forward-integrated spread.
- **The physical band under a transition state** is the `jump_within_pct` column; separability (`INT-31/34`) is the finding that it barely depends on the flavor.

## Archived vintages

`results/ngfs_epe_readout_solo_tasas` — the rate-only nivel readout before the equity/corporate leg (`INT-30`). `results/ngfs_epe_readout_fase_sin_spread`, the `…_fase_sin_spread` run directories and the `fase_*_sin_spread` CVA legs — the fase state with the rate and equity channels only, before the Phase-2 spread channel; its manifest records the config state that produced it.

## Figures

`pipelines/23_ngfs_fase_figures.py` (`configs/ngfs_fase_figures.yaml`) → `results/figures/ngfs_fase/`: the scheduled paths per scenario, the $\lambda(t)$ riders vs the constant headline with the expected cumulative arrivals, the three-flavor transition comparison, one delta matrix per flavor, and the post-0D per-pillar transition profiles. `pipelines/19` carries the `riders` strip; `pipelines/02` renders a rider run's own figure set (its arrivals check integrates $\lambda(t)$).

## Related
Reads with: [[MKT_MOC]] · [[CCR_MOC]] · [[2026-08-22_scheduled_shocks_design_explained]] · [[2026-08-27_fase_producer_results_explained]] · [[DATA_CONTRACTS]] (`DC-CCR-SIM-2`, `DC-MKT-NGFS-2`). Home: [[_INDEX]]
#arm/int #type/pipeline
