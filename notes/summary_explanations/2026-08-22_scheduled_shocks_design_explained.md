# The scheduled-shock (fase) design, explained (2026-08-22)

Session decision `INT-33` — the `OQ-INT-12` design ruling and the Phase-1 engine slice. This note explains what the new machinery means, how to interpret what it will produce, and why the design is the robust one given the canon.

## What was built and what it means

Until now every NGFS transition scenario was an *instantaneous t=0 state*: the curve, equity spots, and spreads are shocked once, and the whole Monte Carlo re-runs from that shocked starting point (the **nivel** flavor; **trayectoria** reshapes the t=0 curve by maturity-dated deltas but still reprices at t=0). The new `ScheduledShockOverlay` is the third flavor — **fase** — where the scenario *path* arrives **inside the simulation**: at each simulation date, the prevailing NGFS delta is applied to the simulated risk-factor paths.

Mechanically, the overlay is a list of $(t, \text{value})$ paths per risk factor — decimal rate deltas for the short-rate factor, $\log(1+\text{adjustment})$ factors for equities — interpolated onto the simulation grid and converted to per-step marks that ride the *same* seam the physical climate jump uses (`apply_jump_overlay`). No randomness is involved: every Monte-Carlo path receives identical marks, because the scenario is one deterministic trajectory, not a source of path heterogeneity.

## The three conventions and how to read them

**t=0 stays the observed market.** The overlay is pinned to zero at the valuation date; the path-prevailing delta applies from the first simulation step. Interpretation: the baseline book at t=0 is priced off *real* observed data — the scenario counterfactual has not happened in that data — and the scenario state catches up at the first grid step (typically one day later). The payoff is an exact reduction: a **constant path reproduces the nivel state at every reporting date after 0D**, which makes fase-vs-nivel differences attributable to *path timing*, never to a level discrepancy (the `MKT-NGFS-09` flat-reduction discipline one level up, unit-tested).

**The rate leg tracks its path exactly.** The HW1F overlay decays any mark through the mean reversion ($e^{-\alpha\,dt}$), which would erode a policy-rate step that the scenario says is *held*. The schedule therefore inverts the recursion — $m_i = \Delta(t_{i+1}) - \Delta(t_i)e^{-\alpha\,dt_i}$ — so the overlay equals the scenario delta at every grid date to $10^{-12}$ relative precision, with $\alpha$ read from the engine's own calibration (one source of truth). Interpretation caveat for the manuscript: at future dates a single-factor model can only move the curve along its one factor, so the shock propagates through the model's $B(t,T)/\alpha$ loading — the separate sovereign long-anchor delta of the t=0 flavors cannot be imposed mid-simulation; fase rate results are therefore *model-consistent* rather than *anchor-blended* beyond t=0.

**Equity legs are multiplicative log factors.** A sector's `equity_relative_adjustment` path becomes $\log(1+\text{adj})$ increments accumulated on the simulated price paths — the same mathematics as the physical jump marks, so the physical and transition channels compose order-independently and remain approximately separable (the `INT-31` overlay-invariance reading carries over).

## Why this architecture (and not the alternatives)

The deciding property is **bit-identity**: consuming zero RNG and riding the existing overlay seam means an absent `scheduled_shocks` block leaves every stream — diffusion and Poisson substream — bit-for-bit unchanged, so the golden baselines (`CCR-MIG-03`) needed no re-base and the full suite stayed green. The θ(t)/drift-modification alternative was rejected as *mathematically equivalent* (a deterministic $\Delta\theta(t)$ produces exactly an additive deterministic function on $r(t)$; a GBM drift schedule is exactly a cumulative log overlay) at the cost of editing the golden-locked `simulate` internals. Valuation-side time-indexed inputs remain the right tool for the one leg the simulation seam cannot carry — **spreads**, which are frozen t=0 pricer inputs — and that is Phase 2 of the arc.

## What Phase 1 does *not* yet do

No committed run config carries the block yet: the producer (`pipelines/22`, NGFS paths → schedule configs), the spread leg, the trajectory-λ(t) rider (in the arc by user ruling, with the `HAZ-STOCH-06` regime-break caveat), and the phased result matrix are the remaining sessions. The equity vol surface stays t=0 sticky-strike and CVA keeps discounting off today's curve — both documented conventions, unchanged by this build.

## Related
Decisions: [[DECISIONS]] (`INT-33`, `MKT-NGFS-09`, `INT-31`) · Read-log: [[2026-08-22_scheduled_shocks_design]] · Prior explanation: [[2026-08-20_irs_simple_act360_explained]] · Arms: [[CCR_MOC]] · [[MKT_MOC]] · Home: [[_INDEX]]
#arm/int #type/explanation
