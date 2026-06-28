---
description: End-of-session ritual — produce the Decided/Changed/Open digest, fold it into the canon, and commit.
allowed-tools: Read, Edit, Bash(git add:*), Bash(git status:*), Bash(git diff:*), Bash(git commit:*)
disable-model-invocation: true
---
Run the end-of-chat ritual from `context/WORKFLOW.md` §2.

1. Produce a 5–10 line digest with three sections — **Decided**, **Changed**, **Open** — as one-line
   statements. Each decision gets a stable arm-prefixed ID (`GEN-*` / `INT-*` / `CCR-*` / `MKT-*` /
   `HAZ-*`), today's date, and a reference key (or `[ref?]` if missing), naming the files/modules
   touched. No filler.
2. Fold it into `context/DECISIONS.md` — one line per decision. **Edit superseded lines in place;
   do not append duplicates** ("promote, don't duplicate"; mark `→ SUPERSEDED by [date]` only where
   the history is load-bearing).
3. Then update the rest only if it changed: a contract → `context/DATA_CONTRACTS.md`; a new term →
   `context/GLOSSARY.md`; a reference used/confirmed → `context/REFERENCES.md` (unconfirmed → §99);
   something opened/closed → `context/OPEN_QUESTIONS.md`.
4. Show me the diff, then commit with a message naming the module/arm touched, keeping **behaviour
   changes separate from packaging/move changes** (`GEN-09`).
