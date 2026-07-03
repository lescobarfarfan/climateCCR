# WORKFLOW — Keeping the canon alive & the project reproducible

This file states the working discipline for the integrated project. It folds in the original
`END_OF_CHAT_RITUAL.md` (the step that prevents fragmentation) and extends it with the unified
reproducibility / version-control standard (`DECISIONS.md` → `GEN-*`). It is part of the **context
canon** so the discipline is itself version-controlled. ~2 minutes per chat beats reconstructing
context from scratch later.

---

## 0. The one rule that makes the rest work

**Keep the whole thesis in ONE project.** Chat search is scoped to the current project. The entire
reason for this consolidation is that the work was scattered across three projects and their
histories couldn't see each other. Do not spin off sub-projects again. If you ever must, run the
ritual (§2) inside each and merge by hand into this canon.

---

## 1. The canon (what these files are)

The `context/` folder is the **single source of truth for context** — decisions, contracts,
vocabulary, references, open items, and this workflow. They are **living** documents:

| File | Holds |
|---|---|
| `00_README_CONTEXT.md` | Entry point, arm map, ID scheme, maintenance rules. |
| `DECISIONS.md` | Every decision, one line, stable ID, date, reference key. |
| `DATA_CONTRACTS.md` | I/O specs: names, grain, columns, units, conventions, crosswalks. |
| `GLOSSARY.md` | Terms + a content-word retrieval index. |
| `REFERENCES.md` | Verified bibliography; §99 = to-confirm. |
| `OPEN_QUESTIONS.md` | Open items, integration questions first. |
| `WORKFLOW.md` | This file. |

**Code is not consolidated here.** The repository is its own source of truth — connect it to the
project so code is read directly. Theory docs live in `notes/theory/`; papers in `literature/`.

---

## 2. End-of-chat ritual (do this before closing any working chat)

1. Ask Claude for the **closing digest** (template below).
2. Fold the digest into `DECISIONS.md` (one line per point, with a stable arm-prefixed ID, date, and reference key).
3. If a **contract** changed (file name, grain, column, units), edit `DATA_CONTRACTS.md`.
4. If a **term** appeared, add it to `GLOSSARY.md`.
5. If a **reference** was used or confirmed, add/verify it in `REFERENCES.md` (unconfirmed → §99).
6. If something is **open** (or got closed), update `OPEN_QUESTIONS.md`.
7. Write the **session read-log** — `notes/reading/YYYY-MM-DD_<slug>.md`: per decision made, *what
   to read* (work + specific chapters/sections) and *why* (which decision/code it backs), using
   `REFERENCES.md` citation keys; linked from its arm MOC(s). Always, even if not asked (`GEN-21`).
8. Commit in git with a message naming the module/arm touched.

> **Promote, don't duplicate.** If a decision supersedes another, **edit** the old line (or mark it
> `→ SUPERSEDED by [date]` only when the history matters); do not append a second. One source of
> truth per fact, or the stale version resurfaces in retrieval.

### Digest template (request it verbatim)

> Before we close: give me a 5–10 line digest of this chat with three sections — **Decided**,
> **Changed**, **Open** — as one-line statements, each decision with a stable arm-prefixed ID, a
> date, and a reference key (or `[ref?]` if missing), naming the files/modules touched. No filler.

Expected shape:

```
Decided:
- <ARM-MODULE-ID> [date] <topic> … — [RefKey]
Changed:
- <ID> <what superseded a prior decision> — was: […]
Open:
- <OQ-ID> <open question> → OPEN_QUESTIONS
```

---

## 3. Recalling context in a new chat (search by content words)

Retrieval matches on **content**, not on the act of conversing. Name the real topic. A ready-made
list of phrases is the **content-word index** at the end of `GLOSSARY.md` (§J). Examples:

- ✅ "recall the **state↔storm crosswalk** decision and the **CENAPRED multi-state** handling"
- ✅ "what's left of the **Holland wind-profile bug** and the **Kaplan-DeMaria decay**"
- ✅ "summarize the **PIMPA → risk.ccr migration** and the **iteritems fix**"
- ✅ "the **364-day Cetes one-year pillar** decision and the **simple-interest SIE conversion**"
- ❌ "that thing we discussed about the curve the other day"

For a cross-cutting synthesis:

> Search our past chats in this project and produce a consolidated summary of every decision about
> **[module: e.g. the IBTrACS wind field / the Hull–White calibration / the randomized-signature reservoir]**.

You can also point at an ID directly: "expand on `HAZ-IBTRACS-05` and its reference," or
"what's blocking `OQ-INT-01`?"

---

## 4. Reproducibility standard (`GEN-*`, enforced by `infra`)

Every result a thesis figure depends on must be reconstructible from raw inputs + a recorded seed.

- **Seeds** — all randomness routes through `infra.set_seed` / `get_rng`; the seed is recorded in the run manifest. (`GEN-07`)
- **Run manifests** — every stochastic run writes `results/manifests/<run_id>.json` (config + git commit + seed + package versions + timestamps). Nothing stochastic runs outside it. (`GEN-06`)
- **Raw-data provenance** — every raw artifact carries a provenance record (`_procedencia.json`-style): URL/dataset, sha256, bytes, date, version/DOI/request. (`GEN-02`)
- **Deterministic reconstructors** — derived artifacts come from scripts, never pickles. (`GEN-04`)
- **Idempotent pipelines** — re-running skips completed work unless forced (`--forzar`/`--force`). (`GEN-05`)
- **Config over hard-coding** — parameters in `configs/*.yaml`; paths via `infra.ProjectPaths` (no CWD-relative paths). (`GEN-08`)
- **Currency** — store in current MXN; deflate (INEGI INPC) downstream. (`GEN-13`)
- **Exclude, don't impute** — unlocated/ambiguous data is excluded and documented, never fabricated. (`GEN-03`)

---

## 5. Version control & repository hygiene (`GEN-09/10/11`)

- **git/GitHub throughout** — small descriptive commits; feature branches; tags for milestones.
- **Separate concerns per commit** — change *behaviour* and *packaging/moves* in distinct commits (e.g. "move PIMPA in, behaviour-unchanged" then "extend PIMPA" — `CCR-MIG-01`).
- **Tracked vs ignored** — `notes/`, `context/`, and `literature/*.md` are **tracked**; `data/` and `results/` are **git-ignored** (keep folder structure with `.gitkeep`). Large data goes out-of-band (DVC or a documented external store).
- **Tests** — `pytest` units per module + ≥1 end-to-end integration test on a tiny fixture (the PIMPA prototype CSVs are an ideal regression fixture — `CCR-MIG-03`).
- **Quality gates** — pre-commit (black/ruff); type hints on public APIs.
- **Secrets** — API keys via environment variables / a git-ignored `.env`.

---

## 6. Literature workflow (`CCR-LIT-*`)

- Convert paper PDFs with **`marker`** → keep the **full output folder in git** under `literature/Author_Year_ShortTitle/`.
- Put **only the `.md`** into project knowledge; **drop the `.json`** (layout noise); add figures to chat **on demand** (more for empirical papers, rarely for methodology-heavy ones).
- Maintain `literature/refs.bib` as the authoritative BibTeX the manuscript compiles against; verify DOIs there, not by hand in prose.
- **Diagrams** are authored in **Mermaid** (fenced ` ```mermaid ` blocks), never hand-aligned ASCII/box-drawing art (`GEN-14`); directory/file trees stay plain code blocks.

---

## 7. Periodic compaction

Every few chats:

> Read `00_README_CONTEXT.md`, `DECISIONS.md`, `DATA_CONTRACTS.md`, `GLOSSARY.md`,
> `OPEN_QUESTIONS.md`, and `REFERENCES.md` plus recent chats in this project, and emit a
> deduplicated, reorganized version of each. Flag what you superseded.

Replace the old docs with the result and update "Last compaction" in `00_README_CONTEXT.md`.

---

## 8. New-chat warm-start (optional but useful)

When opening a fresh working chat, paste or point Claude at the canon and state the focus:

> Context is in `context/`. Today I'm working on **[module/arm]**. Before we start, recall the
> relevant decisions (by ID or content words) and the open questions that gate this work, then
> we'll proceed. At the end I'll ask for the closing digest.

This puts the decisions, contracts, and open items in front of the model up front, and sets the
expectation of the end-of-chat digest so nothing is lost.

## 9. Working in Claude Code (operating mode)

Claude Code is the primary interface (`GEN-15`); claude.ai is the rollback path
(`/handoff-to-claude-ai`). Setup steps live in `CLAUDE_CODE_ONBOARDING.md`; the **durable discipline**
is:

- **Launch at the repo root** so both `src/climateCCR/…` and `context/` are in scope. Keep a root
  `CLAUDE.md` that points at the canon and restates the load-bearing rules (`GEN-01/07/09`,
  `INT-01/07`); it is loaded automatically each session.
- **The canon is the memory.** With project chat-search no longer the retrieval path, `context/`
  *is* the retrieval mechanism — so the end-of-chat ritual (§2) matters more, not less. Open a working
  session with the §8 warm-start (have Claude read the relevant canon), close it with the digest
  folded back in.
- **Single writer for the canon.** Edit `context/` from **one** Claude Code session at a time
  (`GEN-16`). Parallel agents run in **git worktrees created outside the Obsidian-indexed folder**,
  reserved for code-heavy arm work; never let two checkouts edit the same note.
- **External data** goes to a drive exposed via `additionalDirectories`, with output roots resolved
  through `infra.ProjectPaths`/`configs` (`GEN-08/10/15`); the repo stays on the primary disk.
- **Model per task.** Run the main session on an Opus-tier model for integration/migration reasoning;
  delegate fast lookups to a Haiku-tier subagent (`.claude/agents/`). Switching the main model
  mid-session reprocesses the conversation, so prefer a fresh session over a switch in long chats.
- **Effort per task.** Effort — the adaptive-reasoning / thinking-budget dial, a *separate* knob from
  the model — is set with `/effort`. Default the project to `high` (or `xhigh`) via `effortLevel` in
  `.claude/settings.json`; bump to `max` / `ultracode` per-session for hard reasoning (the `INT-10`
  jump-diffusion wiring, the randomized-signature solver, `calibration` design); drop to `low` /
  `medium` for mechanical migration edits. Thinking tokens bill like output tokens, so escalate where
  being wrong is costly, not by default. (`GEN-20`)
- **Commit discipline unchanged** (§5): small commits, behaviour separated from packaging/moves
  (`GEN-09`); `data/`/`results/` git-ignored, `context/`/`notes/`/`literature/*.md` tracked.


---

## Related
Reads with: [[00_README_CONTEXT]] · [[DECISIONS]] · [[OPEN_QUESTIONS]] · [[OBSIDIAN_SETUP]] (the vault this workflow maintains). Home: [[_INDEX]]
#arm/int #type/workflow
