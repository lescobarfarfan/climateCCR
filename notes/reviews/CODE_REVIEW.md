# Code review & improvement recommendations

*Working note — keep in the gitignored `notes/` folder. Not part of the published thesis.*

This reviews the two uploaded codebases (`pimpa`, `randomized_signature`) and lists concrete, prioritized changes to fold them into the `climateCCR` package. Items are tagged **[BUG]** (incorrect / will crash), **[REPRO]** (reproducibility), **[PKG]** (packaging/imports), or **[NICE]** (quality/maintainability).

---

## A. Cross-cutting (both codebases)

1. **[PKG] No `__init__.py`, no `pyproject.toml`.** Neither package is installable; PIMPA relies on a CWD-relative `data/` path and the rand-sig tests use `sys.path.append("..")`. **Fix:** adopt the `src/climateCCR/` layout, add `__init__.py` to every subpackage, write a `pyproject.toml`, and `pip install -e .`. This is the single change that resolves the import pain and should be done first.

2. **[NICE] Duplicated `utils/utilities.py` / `utils/calendar_utils.py`.** The calendar/date helpers are copy-pasted across both projects (and already drift: PIMPA's `generate_simulation_dates_schedule` takes `global_parameters`, the rand-sig one takes `date_format`). **Fix:** unify into a single `climateCCR.utils` (or `climateCCR.infra.calendar`) module; delete the copies.

3. **[REPRO] Seeding is inconsistent.** PIMPA threads `random_state` into `multivariate_normal` (good); the randomized signature uses bare `np.random.*` with no seed (bad). **Fix:** route all randomness through a single `climateCCR.infra.set_seed` + explicit `np.random.Generator` instances.

4. **[NICE] Configuration is a module-level mutable dict** (`global_parameters.py`). Hard to track per run and easy to mutate accidentally. **Fix:** load typed config from `configs/*.yaml`; resolve all paths centrally; snapshot the resolved config into each run manifest.

---

## B. PIMPA

### B1. Correctness / compatibility
1. **[BUG] `DataFrame.iteritems()` is used in 4 places** (`market_data_objects/market_data_builder.py` lines ~15/23/53 and `utils/notebook_tools.py` ~121). `iteritems` was **removed in pandas 2.0**, so this crashes on any modern environment. **Fix:** replace with `.items()`. Add a pinned pandas version to `environment.yml` regardless.
2. **[NICE] Stray `from calendar import calendar`** in `brownian_motion.py`, `geometric_brownian_motion.py`, `hw1f.py` — unused and confusing (shadows the stdlib name). **Fix:** delete.
3. **[NICE] Dead/commented code** in `Portfolio.load_VM_collateral_agreements` (collateral-underlyings block) and IM/TL-IA TODOs. **Fix:** either implement or remove; don't ship commented blocks.

### B2. Calibration is not actually calibration
4. **[NICE → BLOCKER for the thesis] PIMPA only supports `calibration_method='direct_input'`** — it reads pre-computed parameter CSVs. The `market_implied` branches for HW1F/BM are `pass`. To run on real public data you must build the new `calibration` module that *produces* those parameter objects (GBM drift/vol via log-returns MLE; HW1F `alpha`/`sigma`/curve fit). Keep PIMPA's `'direct_input'` contract so the engine itself needs no changes — calibration just fills the inputs.

### B3. Metric coverage
5. **[NICE] Add EPE and Effective EPE.** `compute_exposures` already builds the EE profile per default grid point; EPE (time-average of EE) and Effective EPE (Basel running-max construction) are a few lines on top of the existing arrays.
6. **[NICE] Add CVA / xVA.** Currently absent. Needs a counterparty hazard-rate / survival curve, LGD, and discounting along the exposure profile. Natural home: a thin `risk/xva.py` consuming the EE profile the evaluator already produces. This is also where a *climate-conditioned credit spread* would enter — a clean link to the thesis.

### B4. Robustness
7. **[NICE] Hardcoded USD assumptions and `# TODO` FX requirements** in `mtm_trades_aggregation` / `collateral_requirements_calculation` (non-USD trades require the relevant FX rate to be simulated, silently). **Fix:** validate that required FX risk factors are present and raise a clear error if not.
8. **[NICE] No logging.** Replace notebook-print patterns with `climateCCR.infra` logging so valuation runs are auditable.

---

## C. Randomized signature (`pyrandsigSDE`)

These are the items to fix **before** any thesis result depends on this code.

1. **[BUG] Solver calls the reservoir with the wrong arguments.**
   - `RandomizedSignatureSDESolver.train` calls `self.randsing.compute_signatures()` with **no args**,
     but `RandomisedSignature.compute_signatures(self, z0, A, b)` **requires** `z0, A, b`. It will raise
     `TypeError` immediately.
   - `predict` calls `compute_signatures(sig_level, activation)` — also the wrong signature. **Fix:** call `generate_random_parameters(...)` once, **store** `z0, A, b` as attributes of the `RandomisedSignature` instance, and reuse the *same* `z0, A, b` in both `train` and `predict` (a reservoir must be fixed between fit and inference).

2. **[BUG] 2D vs 3D shape inconsistency.** `compute_signatures` sets `self.signature = Z` with shape `(sig_level, N)` for a **single** path, but `train` indexes `self.randsing.signature.shape[2]` and reshapes as if it were a **batch** `(sig_level, N, n_paths)`. One of the two must change. **Fix:** decide the canonical layout (recommend `(n_paths, N, sig_level)` to match PIMPA's path-major convention) and make `compute_signatures` vectorised over paths.

3. **[REPRO] Reservoir is never seeded.** `generate_random_parameters` uses `np.random.uniform/normal` with no generator; `train` accepts `seed=111` but never uses it. The reservoir (and therefore every downstream result) is non-reproducible. **Fix:** pass a seeded `np.random.Generator` into parameter generation and store the seed in the run manifest.

4. **[BUG] `examples/tests.py` imports `simulate_random_increments` from `utils.utilities`, which does not exist there.** The script cannot run as shipped. **Fix:** add the function to the unified utils (it should produce `(n_paths, n_steps, dim)` standard-normal increments) or update the import.

5. **[NICE] Possible off-by-one in `__reservoirfield`.** `A`/`b` are sized `(sig_level, sig_level, dim+1)` / `(sig_level, 1, dim+1)`, but the loop runs `for i in range(d)` with `d = path.shape[0]` (= `dim`), so the `+1` channel (typically the time/constant lift) is never used. Confirm against Compagnoni et al. (2023): if a time channel is intended, augment the path with a constant/time coordinate and loop over `dim+1`; otherwise drop the `+1` from the parameter shapes.

6. **[NICE] README is a stub** ("*add references*"). Replace with the Compagnoni et al. (2023) citation and a one-paragraph description once the API is stabilised.

---

## D. Suggested integration order (maps to the project plan)

1. Stand up `infra` (seeds, config, logging, manifests).
2. Create the `src/climateCCR` skeleton + `pyproject.toml`; move PIMPA in **unchanged in behaviour**, add `__init__.py`, fix the **[BUG]** pandas `iteritems` issue, and get the prototype CSV run green as a regression fixture.
3. Promote `processes` + `simulation` out of `scenario_generation`.
4. Move the randomized-signature code in and fix the **[BUG]/[REPRO]** items (C1–C4) with a unit test that reproduces a known fit under a fixed seed.
5. Build `data`, then `calibration`, then re-run PIMPA on real public data.
6. Then `inference`, then `viz`.

> Principle: **change behaviour and packaging in separate commits.** First make PIMPA importable with
> identical numerical output (locked by a regression test on the prototype CSVs), *then* extend it.

## Related
[[CCR_MOC]] · Home: [[_INDEX]]

#arm/ccr #type/review
