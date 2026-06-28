---
description: Scaffold a new vault note, born linked to its MOC and _INDEX
argument-hint: <Note_Name> [arm: ccr|mkt|haz|int] [type: theory|source|pipeline|plan|review]
disable-model-invocation: true
---

Create a new Obsidian-vault note from $ARGUMENTS. Parse the note name, arm, and
type; if any are missing or ambiguous, ask me one short question rather than
guessing.

1. **Place it** in the right folder by type: `theory`→`notes/theory/` (or
   `notes/theory/hull_white/` for HW notes), `source`→`notes/sources/`,
   `pipeline`→`notes/pipelines/`, `plan`→`notes/plan/`, `review`→`notes/reviews/`.
   Keep the filename verbatim (Spanish names stay Spanish, `INT-07`).
2. **Scaffold the content:** an H1 title, a one-line purpose, a placeholder body,
   and a footer:
   ```
   ## Related
   Reads with: [[<arm>_MOC]] · [[relevant sibling notes]]. Home: [[_INDEX]]
   #arm/<arm> #type/<type>
   ```
3. **Wire it into the graph:** add a wikilink to the new note under the "Notes"
   section of the matching MOC (`[[CCR_MOC]]`/`[[MKT_MOC]]`/`[[HAZ_MOC]]`), so it
   is reachable from the home note and is not an orphan.
4. Show me the new file and the MOC edit as a diff before writing. After I
   confirm, write both. Do not commit (I'll fold it into the next `/digest`),
   unless I ask.

If the note corresponds to an analytical decision, remind me it also needs a
`DECISIONS.md` entry with a reference (or `[eng]`) at the next `/digest`.
