# Read-log — landing on a second machine and reproducing across CPU architectures (2026-10-20)

Readings behind today's decisions — the cross-machine reproduction standard (`GEN-39`), the deterministic tie-break rule (`GEN-40`) and the `GEN-37` amendment: why identical software on two CPU architectures gives different last bits, what "reproduces" can honestly mean, and the mechanics of the lockfile and of the sorts. Procedure and measurements: [[linux_landing_reproduction]].

## Priority readings

1. **`[Goldberg1991]`** — Goldberg, *What Every Computer Scientist Should Know About Floating-Point Arithmetic*: the rounding and ulp sections, and the "Systems Aspects" section (extended precision, fused operations, why compilers and libraries differ). **Why:** the measured $\le 10^{-13}$ relative differences on the PIMPA goldens and the $\le 10^{-8}$ of column scale on the chain are rounding-order effects of different BLAS, libm and FMA choices per CPU architecture (`GEN-39`); without it the temptation is to read them as bugs, or to chase byte identity the pin never promised.
2. **`[NumPySort]`** — the `numpy.sort` reference (the `kind` table: quicksort is introsort and not stable; `stable` is timsort/radix) and the NumPy 2.x release notes on the x86-simd-sort dispatch. **Why:** `GEN-40` — tied numeric keys are ordered by the CPU's sort kernel unless `kind="stable"` is asked for; the one reported number that moved (`INT-27` tercile spread, +0.43 % → +0.45 %) and the seven artifact sites that now sort stably.
3. **`[Glasserman2003]`** ch. 2 (random number generation: streams, substreams, reproducibility). **Why:** the S-tier jitter finding (`OQ-GEN-04` a, `INT-25` re-reading): one draw per config sector couples unrelated config edits to the random stream; substreams keyed by name are the remedy the jump channel already uses (`infra.get_stream_rng`, `INT-14`).
4. **`[CondaLock]`** — the conda-lock docs: the unified lockfile, `conda-lock install`, `--update`, multi-platform solves. **Why:** the `GEN-37` pin is a lockfile; today's `xlrd` relock and the "env equals lockfile" check (`conda list --explicit` against the platform block).
5. `context/WORKFLOW.md` §4 and `GEN-30/37/38` in [[DECISIONS]] — the standard this session extends: manifests as the tripwire, Monte-Carlo precision across seeds, the numerics pin.

## Related
Session notes: [[2026-10-20_cross_machine_reproduction_explained]] · procedure: [[linux_landing_reproduction]] · decisions: [[DECISIONS]] (`GEN-37/39/40`, `INT-22/25/27`) · open: [[OPEN_QUESTIONS]] (`OQ-GEN-03/04`) · [[CCR_MOC]] · [[MKT_MOC]] · [[HAZ_MOC]]. Home: [[_INDEX]]
#arm/int #arm/ccr #arm/mkt #arm/haz #type/reading
