# 2026-07-25 · Read-log — rendering the Mexican book (viz layer)

Session scope: bring the visualization layer up to the post-swap state — make `pipelines/02` book-agnostic, add the λ-band figure, and make the CCR figures survive a 30-counterparty book (`INT-15`, `GEN-28`; renders `INT-20`/`INT-21`/`INT-22`).

This session made **no methodological decisions** — no parameter was estimated and no model changed; the numbers rendered are the ones `INT-20`/`INT-21` already fixed. Per `GEN-26` the summary-explanation note is therefore skipped, and the readings below are about *how to present* those results defensibly, plus the one substantive correction the session produced (the `INT-21` band figures).

## Priority 1 — how a counterparty-credit exposure profile is meant to be read

**`[Gregory_xVA]`, the exposure-quantification chapter — the EE / PFE / EPE definitions and, above all, its worked exposure-profile plots; then the netting-set aggregation chapter.** Read the *figures* as much as the text: the published convention is a profile over a tenor ladder, and the grid our engine calls the "B3 default grid" (an engine/PIMPA name, see [[GLOSSARY]] — not a regulatory citation) is exactly such a ladder. This is the justification for `GEN-28`: a calendar x-axis is not a neutral rendering of a tenor object, and on the Mexican book (grid to 2077) it hid the entire 2026–2037 exposure ramp in ~15% of the frame. The same chapters back the two companion rules — why a per-counterparty panel grid stops informing past a handful of netting sets (hence a *disclosed* cut, never a silent one) while the book-level view stays exhaustive — and give the vocabulary for reading the `+73` payer-IRS sign anchor against the 29 losing NAIDs. *(Edition/year still to pin down — `REFERENCES.md` §99.)*

## Priority 2 — the sensitivity being drawn

**`[ContTankov2004]`, Ch. 3 (compound Poisson) — specifically the compound-loss rate $\lambda\,\mathbb{E}[L]$.** Re-read the single identity that the band figure is a picture of: the three scenario lines order themselves by $\lambda\,\mathbb{E}[L]$, which is why the headline (λ = 19.2857/yr) sits at roughly twice the CT anchor (9.9565) and the floor (7.2222) — and why pairing a λ from one regime with a severity fit from another would make the figure lie (the `INT-20` regime-consistency rule). Without this the band reads as three arbitrary lines instead of one sensitivity.

**`[PielkeLandsea1998]` — the normalization argument.** Background for the caption/manuscript text accompanying the band: the λ spread across scenarios is a *measurement-regime* spread (registry vs report-era CENAPRED granularity), not a climate-trend spread. The figure must not be captioned as "climate intensifies risk by X" when what varies is the counting rule.

## Priority 3 — reproducibility discipline for figures

**`context/WORKFLOW.md` §3 (`GEN-05`/`GEN-06`) and `GEN-22`.** Re-read before touching any figure code: the standard requires a figure run to be reconstructible from one command plus config and seed, with a manifest. The practical test used this session — regenerate the demo set and md5-diff every PNG against the committed originals (all 10 bit-for-bit identical) — is the cheapest possible proof that a refactor of a figure pipeline changed nothing, and is worth repeating on any future `viz` change.

**Anything on categorical palettes is *not* needed here.** `GEN-22` already fixes the scenario colors by validator (deep green baseline / warm orange climate, ΔE 36.5, CVD-safe) and `SERIES_COLORS` fixes the categorical order; the band figure reuses them rather than choosing new hues. Recorded so a future session does not re-litigate a settled, tested decision.

## Note on the corrected numbers

The `INT-21` band means are now `−2,970.83 / −1,705.59 / −1,470.74` MXN, edited in place in [[DECISIONS]]. Nothing to read for this — it is a transcription correction against the stored `DC-CCR-RISK-3` frames — but it is the reason to prefer reading the *artifact* over the digest line when quoting a number into the manuscript.

## Related

Decisions: [[DECISIONS]] (`INT-15`, `GEN-28`, `GEN-22`, `INT-20`, `INT-21`) · contracts: [[DATA_CONTRACTS]] (`DC-CCR-RISK-3`, `DC-CCR-RISK-4`) · gates: [[OPEN_QUESTIONS]] (`OQ-INT-02`, `OQ-INT-11`) · predecessors: [[2026-07-25_mexican_book_swap]] · [[2026-07-05_viz_layer_horizons]]. Arm MOCs: [[CCR_MOC]] · Home: [[_INDEX]]

#arm/ccr #arm/int #type/reading
