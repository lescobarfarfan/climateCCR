# OBSIDIAN_SETUP — Turning this canon into a linked vault

This explains how the consolidated material is wired as an [Obsidian](https://obsidian.md) vault: a
network of notes connected by `[[wikilinks]]`, with a home index and per-arm maps of content (MOCs)
so the graph actually means something. It also covers how your **existing theory notes** join the
network when you import them.

---

## 1. Open the vault

Point Obsidian at the **repository root** (the folder holding `README.md`, `context/`, `notes/`,
`literature/`). Obsidian indexes `.md`/`.canvas` and ignores code, so `src/`, `data/`, `results/`
won't clutter the graph. (If you prefer a leaner vault, open a folder containing just `context/`,
`notes/`, `literature/`, and the `*_MOC.md` / `_INDEX.md` files.)

## 2. Link convention (already applied here)

- **Wikilinks by note name:** `[[DECISIONS]]`, `[[GLOSSARY]]`, `[[CCR_MOC]]`. Obsidian resolves them
  across folders by filename, so links survive moving a note between `notes/theory/` and elsewhere.
- **Heading links** where a specific section matters: `[[OPEN_QUESTIONS#Integration — decide first]]`.
- **The ID scheme is the fine-grained anchor.** Decisions/contracts/questions carry stable IDs
  (`CCR-MIG-02`, `DC-CCR-SIM-2`, `OQ-INT-07`). Obsidian's full-text search (`Ctrl/Cmd-Shift-F`)
  jumps to any ID instantly — lighter than block links. If you want hard links to a single line, add
  a block anchor `^ccr-mig-02` and link `[[DECISIONS#^ccr-mig-02]]`.

Recommended **Settings → Files and links**: *Use `[[Wikilinks]]`* ON · *New link format* = "Shortest
path when possible" · *Automatically update internal links* ON · *Default location for new notes* =
`notes/` (or vault root).

## 3. Recommended tags

Tags give the graph a second, type-based structure that complements the arm folders. Add them to a
note's top as needed:

- **Arm:** `#arm/ccr` · `#arm/mkt` · `#arm/haz` · `#arm/int` · `#cross/gen`
- **Type:** `#type/decision` · `#type/contract` · `#type/glossary` · `#type/reference` ·
  `#type/open` · `#type/workflow` · `#type/theory` · `#type/source` · `#type/pipeline` ·
  `#type/review` · `#type/plan`
- **Status:** `#status/built` · `#status/todo` · `#status/open` · `#status/resolved`

The canon files are intentionally left mostly untagged so you can adopt whatever subset you actually
use — start with `#arm/*` on the theory notes and `#status/open` on the live open questions.

## 4. How your existing theory notes join the network

The MOCs (`CCR_MOC`, `MKT_MOC`, `HAZ_MOC`) already link to your theory/source/pipeline notes **by the
filenames in `ASSET_MAP.md`** (e.g. `[[Hull_White_Comprehensive]]`,
`[[referencias_riesgo_catastrofico]]`, `[[diseno_calibracion_funciones_impacto_mexico]]`). Until you
import those files they appear as **hollow nodes** (unresolved links) in the graph — that's expected.
When you drop the real notes into `notes/` with those names, the links light up automatically. So:

1. Import each theory note under `notes/{theory,sources,pipelines,plan,reviews}/` keeping the
   filename from `ASSET_MAP.md`.
2. The matching MOC link resolves; the note is now in the graph.
3. Optionally add `#arm/*` + `#type/theory` and a one-line backlink to its MOC at the top.

> If you rename a note, use Obsidian's rename (not the OS) so links update. If a filename here
> doesn't match what you actually have, just fix the link target in the MOC — it's one edit.

## 5. Working with the graph

- **Start at `[[_INDEX]]`** — the home note. It branches to the three MOCs and the canon.
- **Each MOC** is a hub for one arm: its decisions, contracts, open questions, and theory notes.
- **Local graph** (on any note) shows immediate neighbours — good for "what connects to this decision".
- **Backlinks pane** shows what points *at* the current note — e.g. open `GLOSSARY` to see every MOC
  and note that references it.
- **Global graph** with the tag/arm colours set gives you the "network of documents" at a glance.

## 6. Keeping it alive

The vault and the git canon are the same files, so the **end-of-chat ritual** (`[[WORKFLOW]]` §2)
maintains both at once: fold each chat's digest into `[[DECISIONS]]`, update the contract/term/
reference/open-question note if needed, and add a wikilink from any new note to its MOC. The graph
stays current for free.

> **Note on GitHub:** GitHub doesn't render `[[wikilinks]]` (they show as literal text). If you need
> the canon to be clickable on GitHub too, switch *New link format* off wikilinks (Obsidian will
> write `[text](path.md)` instead) — but you lose some of the graph fluidity. For an Obsidian-first
> knowledge vault, keep wikilinks.
