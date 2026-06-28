# Phase 0 — Foundation: packaging, infra, PIMPA migration

*Tracked guide. One of these per phase (see notes/PROJECT_PLAN.md for the schedule).*
*Target: ~2–3 weeks at ~15 hrs/week.*

This scaffold delivers tasks **0.1 and 0.2**. Tasks **0.3–0.5** (migrating PIMPA in and locking a
regression test) are the remaining Phase-0 work and are checklisted below.

---

## What this scaffold already contains (0.1 + 0.2 — done)

- **Installable `src/` layout** with `pyproject.toml` declaring the `climateCCR` package, and an
  `environment.yml`. After `pip install -e .`, imports work from anywhere.
- **`climateCCR.infra`** — the cross-cutting layer:
  - `set_seed` / `get_rng` (`reproducibility.py`) — one source of truth for randomness.
  - `load_config` + `Config` (`config.py`) — typed config from `configs/default.yaml`.
  - `get_logger` (`logging_utils.py`) — console + rotating file logging.
  - `RunManifest` (`manifest.py`) — per-run record (config + git commit + seed + versions).
  - `ProjectPaths` (`paths.py`) — root-anchored paths (kills the CWD-relative data path).
- **Placeholder subpackages** (`data`, `processes`, `calibration`, `simulation`, `signatures`,
  `inference`, `risk`, `viz`) each with a docstring naming its future contents and phase.
- **`pipelines/00_smoke_test.py`** — end-to-end infra check.
- **`tests/test_infra.py`** — pins the seeding reproducibility guarantee.
- **`.gitignore`** (with `notes/` intentionally tracked) and **`.pre-commit-config.yaml`**.

## First commands

```bash
cd climateCCR
git init && git add -A && git commit -m "Phase 0: scaffold + infra layer"
conda env create -f environment.yml && conda activate climateCCR   # or venv + pip install -e ".[dev]"
pre-commit install
pytest            # infra tests should pass
python pipelines/00_smoke_test.py   # writes results/manifests/<run_id>.json
```

---

## Remaining Phase-0 checklist (0.3–0.5)

### 0.3 — Move PIMPA into `climateCCR.risk` *(behaviour unchanged)*
- [ ] Copy PIMPA's subpackages (`data_objects`, `market_data_objects`, `scenario_generation`,
      `pricing_models`, `trade_models`, `evaluators`, `utils`) under `src/climateCCR/risk/` and add
      `__init__.py` to each.
- [ ] **Fix the blocker:** replace `DataFrame.iteritems()` with `.items()` (4 sites — see
      `notes/CODE_REVIEW.md` B1.1). Remove the stray `from calendar import calendar` imports.
- [ ] Replace the CWD-relative data path: resolve PIMPA's data directory via `ProjectPaths`
      instead of `GLOBAL_DATA_PATH = 'data/'`. (The prototype CSVs can live under a test fixtures dir.)
- [ ] Keep `global_parameters` working for now, but route the seed through `infra.set_seed`.
- [ ] Commit this as a **pure move + minimal-fix** change (no behaviour change beyond the pandas fix).

### 0.4 — Lock a regression test
- [ ] Add `tests/test_pimpa_regression.py` that runs a `CCR_Valuation_Session` on the prototype CSVs
      under a fixed seed and asserts the EE/PE profile matches a saved baseline (store the baseline as a
      small CSV/NPZ fixture). This protects every later refactor.

### 0.5 — Confirm clean imports
- [ ] From a notebook and from a script in different directories, confirm
      `from climateCCR.risk import CCR_Valuation_Session` (or the chosen public name) works with no
      path hacks.

**Phase-0 Definition of Done:** `import climateCCR` works anywhere; PIMPA runs from the package; the
infra tests and the PIMPA regression test are green; a clean initial git history exists.

---

## Notes / decisions to record as you go
- Final public API names for the `risk` layer (e.g. keep `CCR_Valuation_Session` or rename to
  `CCRValuationSession`?).
- Where the PIMPA prototype CSVs should live (test fixtures vs. `data/`).
- Whether `processes`/`simulation` get promoted now or at the start of Phase 2 (recommended: Phase 2,
  to keep the Phase-0 move purely mechanical).

## Related
[[CCR_MOC]] · Home: [[_INDEX]]

#arm/ccr #type/plan
