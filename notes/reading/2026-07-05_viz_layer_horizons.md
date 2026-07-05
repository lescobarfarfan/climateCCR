# Read-log — 2026-07-05 · the viz layer, analysis horizons & grid densification

Session decisions: `INT-15` (viz = cross-cutting layer, contract-shaped inputs), `GEN-22` (figure standard + validated palette), `CCR-SIM-01` (reporting grid ≠ sampling grid; daily densification), and the `OQ-INT-07` severity-trend interface note. What to read to own them, in priority order:

1. **[AndersenPiterbarg2010] — *Interest Rate Modeling*, Vol. II, §10.1 (esp. Proposition 10.1.7).** The exact-discretization recursion `processes.diffusions.hw1f` implements. Backs the load-bearing claim of `CCR-SIM-01`: because the transition law is exact over *any* step, densifying the grid changes where paths are sampled, never their marginal law — without this, "daily vs event-driven grids give (distributionally) the same EE/PE" is an article of faith, and you can't explain why the *numbers* still moved (the draw stream changed, not the law).
2. **[Glasserman2003] — *Monte Carlo Methods in Financial Engineering*, Ch. 3 §§3.1–3.3 (generating sample paths: exact GBM solution, Gaussian short-rate models).** The general exact-simulation-vs-Euler distinction behind both diffusions; explains why there is **no $\Delta t$ convergence parameter** anywhere in the engine (the question this session started from).
3. **[ContTankov2004] — *Financial Modelling with Jump Processes*, Ch. 6 (simulation of jump processes; also Ch. 2 §2.5 on the Poisson process).** Backs the per-step event *binning* the channel uses and the arrivals mechanism check: $E[N(t)] = \lambda t$ is an identity, so the straight line in `event_arrivals` is the validation *passing* — reading this stops you from mistaking it for an over-simplification (the simplification lives in $\lambda$ constant + i.i.d. marks, `INT-13`).
4. **[IPCC_AR6] — AR6 WG1, Ch. 11 (weather & climate extremes) — §99, confirm before citing.** The empirical basis for the `OQ-INT-07` note: frequency/severity trends of climate extremes are the reason trajectory $\lambda(t)$ and *time-aware* mark samplers are the required upgrade path before any calibrated result — and the reason the homogeneous-Poisson demo must stay labelled placeholder.
5. **[Merton1976] — skim §2 again.** The independence assumption (`INT-13`) that makes jump-on − baseline read as *purely* the climate component — the property every figure in the new pipeline visualizes; one section, cheap to re-anchor.

No academic reference backs the palette/figure standard (`GEN-22`, `[eng]`): it rests on the runnable CVD validator (colorblind-safety is computed, not judged by eye), which is itself the method to remember.

## Related
Backs: [[DECISIONS]] (`INT-15`, `GEN-22`, `CCR-SIM-01`) · [[DATA_CONTRACTS]] (`DC-CCR-RISK-3`) · [[OPEN_QUESTIONS]] (`OQ-INT-07`) · previous log: [[2026-07-02_climate_jump_channel]] · MOC: [[CCR_MOC]] · Home: [[_INDEX]]
#arm/int #type/reading
