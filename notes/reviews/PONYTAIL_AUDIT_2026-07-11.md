# PONYTAIL_AUDIT_2026-07-11 — repo-wide over-engineering sweep

> First run of the `ponytail` plugin's `/ponytail-audit` on the whole tree (2026-07-11). Findings verified (call-site grep per claim), applied the same day under `CCR-MIG-09` / `HAZ-SCRAPER-CNSF-10`, working principle codified as `GEN-25`. Scope was over-engineering only — correctness, security, and performance were explicitly out of scope. Net: ≈255 lines of dead or duplicated code removed; both locked regression baselines (`CCR-MIG-03`) bit-for-bit green throughout.

## Applied cuts (ranked, biggest first)

1. **delete** `src/climateCCR/risk/ccr/utils/notebook_tools.py` (~139 lines; whole `risk/ccr/utils/` package) — six helpers, zero call sites repo-wide. Supersedes the `CCR-MIG-05` "stays a CCR-local dev helper" clause. Full inventory below.
2. **yagni** `infra.ProjectPaths`: unread properties `src`, `data`, `data_raw`, `data_interim`, `data_processed`, `notes` removed; `configs`/`results`/`logs`/`manifests`/`ensure()` stay (the used surface).
3. **yagni** `simulation.ScenarioGenerator` ABC folded into `MultiRiskFactorSimulation`; `simulation.SimulatedData` ABC folded into `SimulatedHW1FCurve` — one subclass each, never used polymorphically; the ABC-only `name`/`__str__` scaffolding was itself dead.
4. **delete** `utils.calendar_utils`: `generate_simulation_dates_schedule`, `generate_payments_schedule` — no callers (the IRS trade model uses `generate_fixings_and_payments_schedule`, which stays).
5. **shrink** the verbatim-duplicated `build_jump_process()` in `pipelines/01` and `pipelines/02` → `ClimateJumpProcess.from_config(jump_config)` classmethod (schema: the `climate_jumps` block of `configs/climate_jump_demo.yaml`).
6. **delete** `simulation.CorrelationMatrix.get_underlying` / `.get_cholesky_correlation_matrix` — never called.
7. **shrink** CNSF: `procesar_autos_cnsf` now imports `_sin_acentos`/`_slug` from `consolidar_cnsf` (bare-name sibling import, the `HAZ-SCRAPER-CNSF-09` mechanism) instead of carrying identical copies.
8. **delete** small dead weight: `Portfolio.collateral_inventory`/`im_collateral_agreements`/`tlia_collateral_agreements` (never read), a commented-out IM/TLIA block, `CCR_Valuation_Session.gross_exposure`/`gross_pe` (never read), the no-op `+= 0` else-branch in the collateral loop, four `else: pass` branches in the two pricers.
9. **stdlib** `calendar_utils`: `argparse.ArgumentError` misused as a generic exception → `ValueError` (the one-arg `ArgumentError(...)` call would itself `TypeError` at raise time); `isinstance(x, list | np.ndarray)` union form.

## Rejected cuts (deliberate, with rationale)

- **`_sha256` ×4** (`descarga_ibtracs`, `descarga_cenapred`, `scraper_cnsf`, `scraper_sequia`): NOT deduped. The four hazard scripts are deliberately standalone Spanish CLIs (no package `__init__`, bare-name sibling imports only — `HAZ-SCRAPER-CNSF-09`, `INT-07`, documented in `tests/conftest.py`); a shared helper would package-couple them for an 18-line saving. The duplication is the price of that design.
- **`scraper_cnsf._slug`**: NOT unified with the consolidator's `_slug`. It is a *different* implementation (manual accent map, no `ñ` folding: `_slug("Daños")` → `da_os`, not `danos`) whose output is baked into on-disk category directories and `_estado.json`; unifying would silently re-slug paths and break idempotent re-runs (`GEN-05`).
- **`scikit-learn`**: declared but unimported; kept on purpose for the planned signatures readout (`CCR-SIG-04`).

## `notebook_tools.py` inventory (what was removed, for a leaner rebuild when needed)

Removed at commit `refactor(ccr): delete dead code flagged by the ponytail audit`; recoverable verbatim from git history, but the intent (`CCR-MIG-09`) is to **rebuild leaner, in the right home** — plotting belongs in `climateCCR.viz` (contract-shaped inputs, `INT-15`), statistical checks belong in `tests/` — not to restore the module.

The module ("auxiliary functions for plotting data", PIMPA-era, matplotlib + `scipy.stats.pearsonr` + `Curve` + `transform_dates_to_time_differences`):

- `simulate_single_risk_factor(model, simulation_dates, number_paths, number_of_risk_drivers=1)` — drew its own `np.random.normal` increments (unseeded — violates `GEN-07`) and returned one model's simulated paths as a `DataFrame` (columns = dates). Rebuild: a seeded fixture/helper in `tests/` if needed.
- `plot_rfe_paths(paths, simulation_dates, model_name)` — two-panel figure: first path and all paths vs time (years). Rebuild target: `viz.processes` (which already plots path envelopes under the `GEN-22` style).
- `test_rfe_mean_and_vola(paths, simulation_dates, model)` — plotted simulated vs exact mean and volatility curves per `model.return_type` (`linear`/`logarithmic`); relied on `model.mean(times)`/`model.volatility(times)`. Rebuild: a real `pytest` assertion on moments (no plot), plus a `viz` moment-comparison figure if a thesis figure ever needs it.
- `test_scenarios_marginal_distributions(paths, scenario_object)` — looped `test_rfe_mean_and_vola` over `scenario_object.simulated_risk_factors`.
- `test_scenarios_correlations(paths, scenario_object, correlation_matrix)` — realised (Pearson, on linear/log returns per factor) vs input correlations for every factor pair; returned the comparison `DataFrame` + max abs deviation. Rebuild: a `pytest` tolerance check on `MultiRiskFactorSimulation` output (candidate regression test for the correlated-draw contract, `DC-CCR-SIM-1`).
- `calibration_data_to_dict(file_path)` — parsed a wide calibration CSV (`rate_curve_V*/T*` column pairs) into `{name: {feature: value, "rate_curve": Curve}}`. Overlaps `MarketDataBuilder`'s `'direct_input'` loading (`DC-CCR-CAL-1`); if the wide-CSV form is ever needed, put it in `calibration.financial`.

## Related

Backs: [[DECISIONS]] (`CCR-MIG-09`, `HAZ-SCRAPER-CNSF-10`, `CCR-SIG-04`, `GEN-25`) · reads with [[CODE_REVIEW]] (the original PIMPA review this complements) · [[DATA_CONTRACTS]] (`DC-CCR-SIM-1` fold note). Arms: [[CCR_MOC]] · [[HAZ_MOC]] · Home: [[_INDEX]]

#arm/ccr #arm/haz #type/review
