# climateCCR — Claude Code project instructions

climateCCR is a climate-risk-aware financial-risk pipeline for **Mexico**:
`data → calibration → simulation → risk metrics`, with climate wired into every
stage. It is **one machine with three arms** (`INT-09/10/11`):

- **CCR** — the framework/spine: the `src/` package, `infra` (✅ built), the PIMPA
  counterparty-credit engine (`risk.ccr`), signatures + inference.
- **MKT** — the stochastic engine: Hull–White / Vasicek / GBM calibration to
  Banxico SIE data, NGFS rate-shock translation, Monte-Carlo VaR/ES, dashboards.
- **HAZ** — the estimator: Mexican hazard/loss pipelines (CNSF, IBTrACS,
  CENAPRED, drought) yielding the intensity `λ` and per-event impact that drive
  the climate jump; CLIMADA impact-function calibration; loss modelling.

The integrating mechanism is a climate-driven **jump-diffusion** (`INT-10`): HAZ
estimates `λ` + impact → a Poisson/Cox jump → it lands on a GBM (price) or
Hull–White (rate) diffusion → Monte Carlo gives the change vs baseline.

## The context canon (authoritative — read before deciding)

The single source of truth lives in `context/`:

| File | Holds |
|---|---|
| `context/00_README_CONTEXT.md` | Entry point, arm map, ID scheme, maintenance rules. |
| `context/DECISIONS.md` | Every decision, one line, stable ID, date, reference key. |
| `context/DATA_CONTRACTS.md` | I/O specs: names, grain, columns, units, crosswalks. |
| `context/GLOSSARY.md` | Terms + a content-word retrieval index. |
| `context/REFERENCES.md` | Verified bibliography; §99 = to-confirm. |
| `context/OPEN_QUESTIONS.md` | Open items; integration questions first. |
| `context/WORKFLOW.md` | Working discipline + the end-of-session ritual. |

**Before working on or deciding anything in an arm, read the relevant
`context/` file(s).** The canon is authoritative: if anything you recall
conflicts with it, the canon wins. Do not contradict a logged decision without
flagging it and proposing a supersede. For *where files go*, follow
`ASSET_MAP.md`, `REPO_STRUCTURE.md`, and `CONSOLIDATION_PLAN.md`.

## This repo is also an Obsidian vault

`context/`, `notes/`, `literature/`, and the root hubs (`_INDEX.md`, `*_MOC.md`)
form an [Obsidian](https://obsidian.md) vault. Full conventions: `OBSIDIAN_SETUP.md`.
When editing or creating notes, **maintain the graph**:

- **Wikilinks by filename:** `[[DECISIONS]]`, `[[CCR_MOC]]`, `[[Hull_White_Comprehensive]]`.
  Obsidian resolves them across folders by basename, so they survive moves.
- **Every note ends with a `## Related` footer** linking its neighbours and home
  (`Home: [[_INDEX]]`), and carries `#arm/<ccr|mkt|haz|int>` + `#type/<…>` tags.
- **The MOCs are the hubs.** A new `notes/{theory,sources,pipelines,…}` note must
  be linked from its arm MOC (`[[CCR_MOC]]`/`[[MKT_MOC]]`/`[[HAZ_MOC]]`); `_INDEX`
  is the home note that branches to the MOCs and the canon.
- **The ID scheme is the fine-grained anchor** (`CCR-MIG-02`, `DC-CCR-SIM-2`,
  `OQ-INT-07`) — searchable across the vault.
- When renaming/moving a note, **update the inbound links** (or note it for the
  user to run `:Obsidian rename`, which updates backlinks). GitHub doesn't render
  wikilinks — that's expected; the vault is Obsidian-first.

## Non-negotiable rules

- **One source of truth per fact.** Supersede by **editing the canonical entry in
  place** (or mark `→ SUPERSEDED by [date]` only if history is load-bearing).
  Never append a second live version.
- **Every analytical / modelling decision carries a real, checkable reference**
  from `context/REFERENCES.md`, or is marked `[eng]`. Never invent a citation;
  unconfirmed refs → `REFERENCES.md` §99 (`GEN-01`).
- **Reproducibility (`GEN-*`):** randomness through `infra.set_seed`/`get_rng`
  with the seed recorded; every stochastic run writes a manifest to
  `results/manifests/<run_id>.json`; derived artifacts from deterministic
  reconstructor scripts, **never pickles**; idempotent pipelines
  (`--forzar`/`--force`); parameters in `configs/*.yaml`, paths via
  `infra.ProjectPaths`; amounts in current MXN, deflate (INEGI INPC) downstream.
- **Bilingual boundary (`INT-07`):** public Python APIs in English; Spanish data
  identifiers, CLI flags, and institution names kept **verbatim**.
- **Diagrams in Mermaid** (fenced ` ```mermaid `), never ASCII/box art (`GEN-14`);
  directory/file trees stay plain code blocks.
- **Scope:** geophysical perils (earthquake/volcano) are **out** — *climate* risk
  only (`GEN-12`).
- **ID scheme:** arm-prefixed `<ARM>-<MODULE>-NN` (`CCR`/`MKT`/`HAZ`/`INT`/`GEN`);
  see `context/00_README_CONTEXT.md` §3.

## Code standards

- Python: **PEP 8 + Google Python Style Guide.** Type hints on public APIs.
- **Minimalism (`GEN-25`, ponytail/YAGNI):** the simplest solution that works —
  reuse what the repo has > stdlib > an installed dependency > minimal new code;
  no speculative abstractions (one-implementation interfaces, config nobody sets).
  **Never at the cost of robustness**: validation, error handling, reproducibility,
  and standard practice always stay; a *new* dependency is welcome when it
  demonstrably buys a more robust, scalable, future-proof implementation. The
  `ponytail` plugin enforces this in-session; `/ponytail-audit` sweeps the repo.
- Format/lint with **`ruff`** + **`black`** (line length 100); both clean before commit.
- Tests: **`pytest`** units per module + ≥1 end-to-end test on a tiny fixture (PIMPA
  prototype CSVs — `GEN-11`). Lock the PIMPA EE/PE baseline before refactors (`CCR-MIG-03`).
- Specialised scripts (R, Stan, …) integrated from Python where they earn it.
- Version control (`GEN-09`): small descriptive commits; **separate behaviour
  changes from packaging/move changes**.
- Branching (`GEN-16`): **commit directly to `main` by default** — a branch/worktree
  (+ PR) only when the task genuinely risks the mainline: baseline-touching refactors
  (`CCR-MIG-03`), large moves/migrations, discardable experiments, parallel sessions.
  Background jobs enforce worktree isolation; there, skip the PR and hand back a local
  `git merge --ff-only` one-liner instead.

### Common commands
```bash
pip install -e ".[dev]"   # editable install (run once); or: conda env create -f environment.yml
pytest                    # run the test suite
ruff check . && black .   # lint + format
pre-commit install        # enable the ruff+black hooks
```

## Session workflow (manual commands + nudges)

Project slash commands (see `.claude/commands/`):

- **`/warmstart`** — start of every session; full project-state recap from the canon.
- **`/digest`** — end of every session; Decided/Changed/Open digest → writes the canon + commits.
- **`/link-check`** — audit the Obsidian vault (broken wikilinks, orphans, MOC coverage, tags).
- **`/new-note`** — scaffold a vault note in the right folder, born linked to its MOC and `_INDEX`.
- **`/compact-canon`** — periodic dedup/reorg of the canon + link integrity.
- **`/handoff-to-claude-ai`** — package the canon to return to the claude.ai project (rollback).

Because these are manual and I am forgetful:

- **At the start of a session, if I have not yet run `/warmstart`, remind me to.**
- **When I signal I'm wrapping up — or after any substantive decision — offer to
  run `/digest`.** If a session added or moved notes, also offer `/link-check`.
- **Never edit `context/` files outside the `/digest` (or `/compact-canon`) flow
  without showing me the diff first.**

## Memory

Claude Code **auto memory is disabled** (`.claude/settings.json`). The
version-controlled canon in `context/` is the single source of truth — do not
rely on auto memory for project decisions (`GEN-15`, §4a of the canon).
