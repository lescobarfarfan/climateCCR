---
description: Periodic canon compaction — dedupe/reorganize the seven canon files and check link integrity.
allowed-tools: Read, Edit, Bash(git add:*), Bash(git status:*), Bash(git diff:*), Bash(git commit:*)
disable-model-invocation: true
---
Periodic compaction per `context/WORKFLOW.md` §7.

1. Read the eight canon files: `context/00_README_CONTEXT.md`, `DECISIONS.md`, `DATA_CONTRACTS.md`,
   `GLOSSARY.md`, `OPEN_QUESTIONS.md`, `REFERENCES.md`, `WORKFLOW.md`, `HISTORY.md`; snapshot them
   first with `python tools/canon_inventory.py snapshot <before.json>` (IDs, keys, links, numbers).
2. Emit a deduplicated, reorganized version of each, flagging what you superseded (edit in place;
   mark `→ SUPERSEDED by [date]` only where the history is load-bearing): earlier dated updates of a
   decision move to `HISTORY.md` §1 (the latest stays inline with a `HISTORY#ID` wikilink pointer),
   resolved open questions to `HISTORY.md` §3, stale `ref?` / `(§99)` markers on verified keys stripped.
3. Verify cross-references resolve — decision IDs, `DC-*`, `OQ-*`, reference keys — and that
   `[[wikilinks]]` and MOC coverage are intact (run `/link-check` if available).
4. Replace the files, update **"Last compaction"** in `00_README_CONTEXT.md`, run
   `python tools/canon_inventory.py compare <before.json> <after.json>` (zero losses is the gate),
   show me the diff, and commit (docs commit, separate from any behaviour change — `GEN-09`).
