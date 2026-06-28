# 00 · README — Integrated project context

**Project:** `climateCCR` — a computational module that carries a financial
institution through **data retrieval → calibration → simulation → risk metrics**, with
**climate-related risk** wired into every stage, applied to **Mexico**.

**Last compaction:** 2026-06-15
**Scope of this synthesis:** consolidated from three previously-separate claude.ai projects
(`Tesis QF` / `climateCCR`, `financial_instruments`, `Climate-Nature-Risks_Calibration`). It merges
their six canon documents and their working notes/code inventories into one canon. Chat histories
in the three original projects are **not** reachable from the new project; this canon is the
durable carry-over. See §6 for provenance.

---

## 1. What this is

These documents are the **single source of truth** for the integrated project's context. They
replace the scattered prose, decisions, and contracts that previously lived in three projects'
chats. They are **living** documents: edit them in place, do not accumulate duplicates.

The project is one pipeline with three contributing arms. **The CCR arm is the architectural
spine**; the other two arms feed the same pipeline:

| Arm | Origin project | Role in the integrated project |
|---|---|---|
| **CCR** — framework & spine | `Tesis QF` / `climateCCR` | **The framework.** Installable `src/`-layout package, reproducible `infra`, the PIMPA counterparty-credit engine + its multi-factor simulation structure, and a signatures + inference core (role under review). Runs calibration → simulation → risk and reads out the change. |
| **MKT** — calibration & simulation engine | `financial_instruments` | **The stochastic engine.** Hull–White / Vasicek calibration to Banxico SIE data (one risk-factor model alongside GBM), NGFS rate-shock translation, Monte-Carlo VaR/ES, a physical-risk dashboard, a climate-credit overlay, weather-derivative literature. |
| **HAZ** — estimation engine for the climate↔price link | `Climate-Nature-Risks_Calibration` | **The estimator.** Mexican hazard/loss pipelines (CNSF, IBTrACS, CENAPRED, drought) that yield the intensity `λ` and per-event impact driving the climate shock; CLIMADA subnational impact-function calibration; compound-Poisson / Cox loss modelling and parametric pricing. |

The arms share **Mexico as the unit of analysis** and the **shared `infra` + reproducibility
standard** (§ `GEN-*`). They form **one machine** with one objective (`INT-09`): test and quantify a
relationship between financial asset prices / risk factors and climate events, and measure via Monte
Carlo how financial risk changes when climate is incorporated. The integrating mechanism is a
**climate-driven jump process** (`INT-10`): HAZ estimates `λ` + impact → a Poisson/Cox jump carries
the shock → it lands on a GBM (price) or Hull–White (rate) diffusion → Monte Carlo over the
jump-diffusion gives the change vs baseline. The remaining choices (which process a shock hits, the
jump↔diffusion dependence, fixed vs trajectory climate, where signatures fit) are in
`OPEN_QUESTIONS.md` → `OQ-INT-*` / `OQ-CCR-07`.

**Cross-cutting standards (non-negotiable, unified across arms):** every analytical decision carries
a real, checkable reference (or is marked `[eng]`); raw data is version-pinned with provenance;
pipelines are reproducible, idempotent, and deterministic (reconstructor scripts as the source of
truth, never pickled objects); every stochastic run writes a manifest (config + git commit + seed +
versions); all work is under git/GitHub. Full standard in `DECISIONS.md` → `GEN-*` and `WORKFLOW.md`.

---

## 2. Document map

| Document | Purpose |
|---|---|
| `00_README_CONTEXT.md` | This file. Entry point + arm map + ID scheme + maintenance rules. |
| `DECISIONS.md` | Dated log, one line per decision, grouped by arm/module, each with a stable ID and a reference key. |
| `DATA_CONTRACTS.md` | Input/output specs: file names, grain, key columns, units, conventions, crosswalks. |
| `GLOSSARY.md` | Terms, acronyms, proper nouns, one line each + a content-word retrieval index. |
| `REFERENCES.md` | Verified bibliography with DOIs/URLs; each entry points to the decision IDs it backs. |
| `OPEN_QUESTIONS.md` | Open items and unresolved decisions, each with a stable ID; integration questions first. |
| `WORKFLOW.md` | The reproducibility + version-control workflow and the **end-of-chat ritual** that keeps this canon alive. |

Two companion docs sit one level up (outside `context/`) and describe the **repository** rather than
the project's intellectual content:
- `../README.md` — the integrated **project map** (vision, arm map, end-to-end pipeline, status).
- `../REPO_STRUCTURE.md` — the recommended **repository layout** and how the modules wire together.
- `../ASSET_MAP.md` — the **migration map**: every existing note/script → its destination in the new repo.

**Code is not consolidated in this canon.** The repository (`src/climateCCR/…`) is its own source of
truth. Connect the repo to the new project so the code is read directly; these `.md` files capture
*decisions, contracts, vocabulary, references, and workflow* — not source. The substantive **theory
docs** (Hull–White, CLIMADA calibration, change-of-measure, the catastrophe-risk master doc, etc.)
travel with the repo under `notes/theory/` and are pointed to from here, not copied in.

---

## 3. ID scheme (for fast lookup and cross-reference)

Every decision and open question has a stable, **arm-prefixed** ID so either of us can point at a
specific block. Arm prefixes: `CCR` · `MKT` · `HAZ` · `INT` (integration) · `GEN` (cross-cutting).

- **Decisions** — `<ARM>-<MODULE>-NN`.
  - `GEN-*` general/reproducibility standards (shared).
  - `INT-*` integration decisions (new, cross-arm).
  - CCR modules: `ARCH` (architecture/packaging), `INFRA`, `MIG` (migration), `SIG` (signatures), `CAL` (statistical calibration), `RISK`, `RES` (research design), `LIT` (literature workflow).
  - MKT modules: `SCOPE`, `IR` (Hull–White), `MEAS` (change of measure), `SIE` (Banxico data), `CURVE`, `CALIB`, `STRESS`, `NGFS`, `MC`, `CREDIT`, `PHYS` (dashboard), `WD` (weather derivatives).
  - HAZ modules: `CLEAN-CNSF`, `SCRAPER-CNSF`, `IBTRACS`, `CENAPRED`, `CLIMADA`, `DROUGHT`, `SOURCES`, `STOCH`.
- **Data contracts** — `DC-<ARM>-<MODULE>-N`; cross-cutting `DC-CONV-*`; joins `DC-XWALK-*`.
- **Open questions** — `OQ-<ARM>-NN`; integration `OQ-INT-NN`.
- **References** — citation keys like `[Holland1980]`, `[Eberenz2021]`, defined in `REFERENCES.md`.

Example cross-reference: "`HAZ-IBTRACS-04` is backed by `[Holland1980]`; its output contract is
`DC-HAZ-IBTRACS-2`; the calibration it feeds is `HAZ-CLIMADA-08`."

> **Note on legacy IDs.** The HAZ arm carried real stable IDs in its origin project (e.g.
> `IBTRACS-04`); these are preserved verbatim, only arm-prefixed (`HAZ-IBTRACS-04`). The MKT and CCR
> arms logged decisions by date and module tag without per-line IDs; IDs were assigned during this
> consolidation, so an `MKT-…`/`CCR-…` number is new but the decision and its date are original.

---

## 4. Maintenance rules

**(a) Promote, don't duplicate.** When a new decision supersedes an old one, **edit** the canonical
entry in place (or mark it `→ SUPERSEDED by [date]` only if the history is load-bearing); do not
append a second live version. One source of truth per fact — otherwise the stale version resurfaces
in retrieval and contaminates context.

**(b) End-of-chat ritual.** Before closing a working chat, request the 5–10 line digest
(Decided / Changed / Open) and fold it into `DECISIONS.md`, updating the other docs if a contract,
term, reference, or open item changed. Incremental beats archaeology. Full template in `WORKFLOW.md`.

**(c) Search by content words.** When asking Claude to recall, name the real topic — "the
state↔storm crosswalk decision", "the 364-day Cetes one-year pillar", "the randomized-signature
solver bugs" — not meta-words ("that thing we discussed"). Retrieval matches on content. A
content-word index lives at the end of `GLOSSARY.md`.

**(d) Every analytical decision carries a reference.** Methodological/scientific decisions cite a
key from `REFERENCES.md`. Pure engineering decisions (a filename regex, a path fix) need none — mark
them `[eng]` rather than inventing a citation.

**(e) Compact periodically.** Every few chats, ask Claude to read these docs plus recent chats and
emit a deduplicated, reorganized version; replace the old docs and update the "Last compaction" date.

**(f) One project from now on.** Chat search is scoped to the current project. The whole point of
this consolidation is that the thesis now lives in **one** project. Resist the urge to spin off
sub-projects again; if you must, run the ritual inside each and merge by hand into this canon.

---

## 5. How to use this set

- **Orient** in `../README.md` (the project map) and this file.
- **Look up a decision and its rationale** in `DECISIONS.md` (dated, one line each, with supersedes).
- **Implement / wire up data** from `DATA_CONTRACTS.md` (series IDs, columns, units, conventions, crosswalks).
- **Resolve a term or a search keyword** in `GLOSSARY.md`.
- **Cite something** from `REFERENCES.md` (verified) — never invent a citation; unconfirmed items live in §99.
- **See what's unresolved** in `OPEN_QUESTIONS.md` (integration questions `OQ-INT-*` come first).
- **Keep the canon alive** with `WORKFLOW.md` (the ritual + reproducibility rules).
- **Set up / navigate the repo** with `../REPO_STRUCTURE.md` and `../ASSET_MAP.md`.

---

## 6. Source provenance for this synthesis

Reconstructed from the carried-over canon and notes of three projects. Dates inside the companion
docs that predate 2026-06-15 are original where the origin project recorded them, and **approximate
(reconstructed from document vintages)** for the MKT arm, whose decision dates were partly inferred.

- **CCR arm** — `Tesis QF`: `README.md`, `PROJECT_PLAN.md`, `PHASE_0.md`, `CODE_REVIEW.md`,
  `DECISIONS.md`, `DATA_CONTRACTS.md`, `GLOSSARY.md`, `OPEN_QUESTIONS.md`; the working `climateCCR`
  scaffold (`infra` implemented; other subpackages placeholders).
- **MKT arm** — `financial_instruments`: `00_PROJECT_CONTEXT.md`, `01_DECISIONS.md`,
  `02_DATA_CONTRACTS.md`, `03_GLOSSARY.md`, `04_OPEN_QUESTIONS.md`; theory notes (Hull–White ×8,
  Vasicek, change-of-measure, NGFS, Monte-Carlo, Mexican data/instruments, weather derivatives) and a
  47-entry climate-finance LaTeX bibliography.
- **HAZ arm** — `Climate-Nature-Risks_Calibration`: `00_README_CONTEXT.md`, `README.md`,
  `DECISIONS.md`, `DATA_CONTRACTS.md`, `GLOSSARY.md`, `REFERENCES.md`, `OPEN_QUESTIONS.md`; the
  catastrophe-risk master doc, per-source provenance notes, and ~5,600 lines of pipeline code.
- **Root** — `END_OF_CHAT_RITUAL.md` (folded into `WORKFLOW.md`).


---

## Related
[[_INDEX]] · [[DECISIONS]] · [[DATA_CONTRACTS]] · [[GLOSSARY]] · [[REFERENCES]] · [[OPEN_QUESTIONS]] · [[WORKFLOW]] · [[README]] · [[REPO_STRUCTURE]] · [[ASSET_MAP]] · MOCs: [[CCR_MOC]] · [[MKT_MOC]] · [[HAZ_MOC]]
#arm/int #type/workflow
