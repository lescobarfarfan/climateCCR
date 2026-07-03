# Read-log · 2026-07-02 — The climate jump channel

**Session:** provisional resolution of the jump-channel knobs (`INT-13`, closing `OQ-INT-03` a/b)
and the `DC-CCR-SIM-2` build (`INT-14`): `processes/jumps/`, the per-diffusion overlays, the
substream seeding, the jump regression fixture, and the lognormal demo.

Readings ordered by priority: **1–3 are load-bearing** for this session's decisions — without them
the modelling choices read as arbitrary; 4–6 support and extend.

1. **`[ContTankov2004]`** Cont & Tankov, *Financial Modelling with Jump Processes* — Ch. 2 §2.5–2.6
   (the Poisson process and compound Poisson processes), Ch. 3 (building jump processes and jump
   measures), Ch. 6 (simulating jump processes).
   **Why:** the mathematical backbone of the whole channel. Per-step event counting, mark
   aggregation, and the jump-diffusion decomposition `dX = diffusion + Σ marks` are implemented in
   exactly these terms in `processes/jumps/climate_jump_process.py`; this is the canonical reference
   behind `INT-10/13` and the one to cite first in the methodology chapter.
2. **`[Merton1976]`** Merton, *Option Pricing when Underlying Stock Returns Are Discontinuous*
   (J. Financial Economics 3, 125–144) — the whole paper is short; focus on §2 (the process) and
   §3 (the independence assumption).
   **Why:** the original price-channel jump-diffusion. The GBM overlay (marks multiplicative in the
   log-price, `apply_jump_overlay` in `geometric_brownian_motion.py`), the independent
   jump↔diffusion assumption, and the Gaussian/lognormal mark families are Merton's structure —
   defending the price channel starts here.
3. **`[AndersenPiterbarg2010]`** Andersen & Piterbarg, *Interest Rate Modeling* — §10.1 around
   **Proposition 10.1.7** (exact simulation of the Hull–White short rate).
   **Why:** PIMPA's `hw1f.py::simulate` implements this recursion, and the rate-jump overlay reuses
   it — which is *why* a rate mark decays at `exp(-α Δt)` and why adding the overlay to finished
   paths is exactly equivalent to injecting marks inside the simulation loop. Understanding the
   proposition is understanding the rate channel's correctness argument.
4. **`[BrigoMercurio2006]`** Brigo & Mercurio, *Interest Rate Models — Theory and Practice*, Ch. 3
   (Hull–White) and the jump-extension discussions (e.g. JCIR).
   **Why:** context for jump-extended short-rate models; the modelling convention "marks enter `dr`
   and mean-revert away" (rather than shifting the curve permanently) is standard there, which is
   the choice `INT-14` encodes.
5. **`[Klugman]`** Klugman, Panjer & Willmot, *Loss Models* (§99 — edition to confirm,
   `OQ-HAZ-07`) — severity distributions (lognormal/Pareto) and compound-Poisson aggregation.
   **Why:** the `LognormalMark` shape assumption in the demo config is borrowed from the actuarial
   severity tradition; this is the family HAZ's calibration (`OQ-HAZ-12` → `OQ-INT-07`) will most
   likely deliver, so the placeholder and the eventual estimate stay in one family.
6. **NumPy documentation, “Parallel random number generation” (SeedSequence spawning)** — [eng], no
   canon key needed (`GEN-01`). https://numpy.org/doc/stable/reference/random/parallel.html
   **Why:** the independence guarantee behind `infra.get_stream_rng`, which is what makes
   “jump-on − baseline = the climate component” a *provable* property of the engine rather than a
   hope (`INT-09`, `GEN-07`) — the substream trick is the reproducibility core of `INT-14`.

## Related
Decisions: [[DECISIONS]] (`INT-13`, `INT-14`, `GEN-21`) · Contract: [[DATA_CONTRACTS]]
(`DC-CCR-SIM-2`, `DC-XWALK-4`) · Open: [[OPEN_QUESTIONS]] (`OQ-INT-07`, `OQ-INT-03` c) ·
Bibliography: [[REFERENCES]] · Arms: [[CCR_MOC]] · [[MKT_MOC]] · [[HAZ_MOC]] · Home: [[_INDEX]]

#arm/int #type/reading
