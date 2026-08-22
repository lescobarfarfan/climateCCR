# Read-log — the scheduled-shock design + engine slice (2026-08-22)

Session decision: `INT-33` (the `OQ-INT-12` design ruling — deterministic scheduled marks through the jump-overlay seam, Phase-1 engine slice built; `OQ-INT-12` slimmed to the producer/spread/matrix arc). Readings ordered by priority.

1. **`[ContTankov2004]` — Cont & Tankov, *Financial Modelling with Jump Processes*, the jump-diffusion simulation chapter (path superposition of a deterministic/jump component on a diffusion).** Why: the seam `INT-33` reuses — `apply_jump_overlay` superimposes a component on finished diffusion paths, and the equivalence "deterministic drift perturbation ≡ deterministic path overlay" that justified rejecting the θ(t)-modification alternative is the same superposition argument; without it the architecture choice reads as convenience instead of an exact equivalence at lower blast radius.
2. **`[BrigoMercurio2006]` — Brigo & Mercurio, *Interest Rate Models*, §3.3 (Hull–White bond reconstruction, the $B(t,T)$ loading).** Why: the manuscript note fixed by `INT-33` — an in-simulation rate shock moves the *future* curve only through the model's own $B(t,T)/\alpha$ loading, so the two-anchor tenor blend of the t=0 flavors (`MKT-NGFS-06`) cannot be imposed at future dates in a one-factor world; §3.3 is also where the decay recursion the compensation inverts ($m_i = \Delta(t_{i+1}) - \Delta(t_i)e^{-\alpha\,dt_i}$) comes from.
3. **`[NGFS2025ST]` — NGFS short-term scenarios, the technical documentation (path grain and window semantics: quarterly EIRIN policy rate, annual CLIMACRED sector adjustments, 2025–2030 window).** Why: what the fase legs will consume in the producer session — the hold-beyond-window clamp and the t=0-prevailing-delta convention are readings of these paths' semantics, and the phased equity/spread application is exactly what the trajectory flavor's config deferred (`MKT-NGFS-09`).

## Related
Decisions: [[DECISIONS]] (`INT-33`) · Explanation: [[2026-08-22_scheduled_shocks_design_explained]] · Prior read-log: [[2026-08-20_irs_convention_alignment]] · Arms: [[CCR_MOC]] · [[MKT_MOC]] · Home: [[_INDEX]]
#arm/int #type/reading
