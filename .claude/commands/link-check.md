---
description: Audit the Obsidian vault — broken links, orphans, MOC coverage, tags (read-only)
argument-hint: [optional folder to scope, e.g. notes/theory]
allowed-tools: Read, Grep, Glob
---

Audit the Obsidian vault for link and structure integrity. Scope: `context/`,
`notes/`, `literature/`, and the root hubs (`_INDEX.md`, `*_MOC.md`,
`OBSIDIAN_SETUP.md`, `README.md`, `REPO_STRUCTURE.md`, `ASSET_MAP.md`,
`CONSOLIDATION_PLAN.md`). If I passed a folder ($ARGUMENTS), scope to it.

Conventions are in `OBSIDIAN_SETUP.md`. Build the set of note basenames, then
report (do **not** modify files):

1. **Broken wikilinks** — every `[[Note]]`, `[[Note#Heading]]`, `[[Note#^anchor]]`
   whose target basename (and heading/anchor, when given) does not resolve to an
   existing note. List each with its source file and line.
2. **Orphan notes** — notes under `notes/` not linked from any MOC or `_INDEX`
   (i.e. unreachable from the home note).
3. **MOC coverage gaps** — `notes/{theory,sources,pipelines,plan,reviews}/` notes
   not listed in their arm MOC's "Notes" section.
4. **Missing footers/tags** — notes lacking a `## Related` footer, or missing an
   `#arm/…` or `#type/…` tag.
5. **Hollow hub links** — links in the MOCs / `_INDEX` to notes not yet imported
   (expected during migration; list them as "pending import", not errors).

End with a prioritized fix list. If I then ask, apply the safe fixes (add the
missing MOC backlink, add a `## Related` footer, add tags, fix an obvious typo in
a link target) — showing the diff first — but never invent a note or a reference.
