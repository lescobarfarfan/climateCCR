---
description: End-of-session ritual — produce the Decided/Changed/Open digest, write the session read-log, fold it all into the canon, and commit.
allowed-tools: Read, Write, Edit, Bash(git add:*), Bash(git status:*), Bash(git diff:*), Bash(git commit:*)
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
4. **Write the session read-log — always, even if not asked.** Create
   `notes/reading/YYYY-MM-DD_<slug>.md` (today's date, short topic slug) listing the recommended
   readings needed to fully understand this session's decisions: for each item, **what to read**
   (author, work, the specific chapters/sections — not just the title) and **why** (which decision
   or code it backs, what breaks in your understanding without it). Order by priority. Use citation
   keys from `context/REFERENCES.md`; any reading not yet there gets added in step 3 (verified, or
   §99 if unconfirmed — never invented). Vault conventions apply: `## Related` footer linking the
   relevant MOC(s), the decision-backing notes, and `Home: [[_INDEX]]`; tags `#type/reading` +
   `#arm/<…>`; link the note from its arm MOC(s). If a session made no analytical decisions (pure
   mechanics), a one-line read-log saying so is enough.
5. Show me the diff, then commit with a message naming the module/arm touched, keeping **behaviour
   changes separate from packaging/move changes** (`GEN-09`).
