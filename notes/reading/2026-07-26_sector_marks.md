# 2026-07-26 · Read-log — sector-differentiated equity marks (`INT-24`)

Session scope: resolve the core of `OQ-INT-11` — replace the uniform `INT-17` book-level equity mark with per-name sector/geography-differentiated scales `γ_i`, anchored so the book-level shock is redistributed rather than re-estimated, and re-base the `INT-23` EPE band. The readings below are what a reader needs to judge each layer of the composition and its caveats.

## Priority 1 — the asset-level attribution template (and its fallback caveat)

**`[Bressan2024]`, the Methods section (database model → CLIMADA acute risk → business-line aggregation → CDDM valuation) and the Mexico application + the proxy-data comparison.** This is the paper `INT-24`'s G layer imitates at thesis scale: physical-asset locations aggregated to listed firms, applied to *Mexico* (1,820 assets, 177 firms, tropical-cyclone damages). Read the proxy-data experiment closely — replacing asset locations with headquarters understates acute-risk portfolio VaR by 67–92% — because that number is the citable caveat carried by every name we left on the population-share national-proxy tier (HCITY, FIHO12, FUNO, all industrials until their G blocks are collected). Without this reading, the tiering in `configs/equity_mark_scales.yaml` looks like an arbitrary shortcut instead of a documented, bounded approximation.

## Priority 2 — the sector decomposition behind the damage data

**`[CEPAL2014]`, the DaLA sector chapters (social/housing, productive sectors — agriculture, industry, commerce, tourism — and infrastructure).** CENAPRED's *Impacto Socioeconómico* series follows this methodology, so the sector rows of the S matrix inherit their meaning from it: when the S matrix says "hoteles are highly susceptible to ciclón", the defensible basis is the DaLA notion of sectoral damage + business interruption. Needed to argue the S rows are a recognized decomposition, not an invented taxonomy.

## Priority 3 — exposure shares drive return responses (and the validation design)

**`[Kruttli2025]`, the construction of the firm-level hurricane-exposure measure and the return/volatility response results.** Two uses: (i) it is the empirical justification for *weighting* climate marks by exposed-asset shares — firms with more assets in the storm's path move more, monotonically; (ii) its event-window design is the template for the deferred Phase C validation (sector-portfolio CARs around CENAPRED episodes vs the `γ` ordering, `OQ-INT-11` b). Also note its finding of *positive* disaster sensitivities for materials/reconstruction — the reason the S matrix deliberately zeroes upsides (cemento) rather than modelling them in an adverse-marks channel.

## Priority 4 — the supervisory frame for sector × geography disaggregation

**`[ECB2021EconomyWide]`, the physical-risk methodology sections (firm-level location × sector vulnerability; agriculture/construction/tourism results).** Backs the *shape* of the whole exercise — supervisors quantify physical climate risk exactly by crossing geographic exposure with sectoral vulnerability — so `INT-24` can be presented as the book-scale version of standard supervisory practice rather than an ad-hoc construction.

## Priority 5 — the mechanism the seam relies on

**`[ContTankov2004]`, the marked-point-process / compound-Poisson chapters already backing `INT-13`.** The one fact this session leaned on: for a lognormal mark, scaling the median by `γ` is identical in distribution to multiplying every draw by `γ` — which is why `target_scales` rescales marks *exactly* (same draws, same events) and the uniform run remains nested as `γ ≡ 1`. The regression test `marks_scaled == γ · marks_uniform` is this algebra, executable.

## Deferred-scope readings (skim only)

**`[Hallegatte2008]`** — the ARIO model and the ≈30%-of-direct indirect-loss figure for Katrina: why the direct-damage marks are a lower bound on economic impact and why I-O propagation stays future work. **`[INEGICenso2020]`** — the population tabulado used for per-capita damage intensity and the national-proxy shares; verify a few state values when confirming the §99 entry.

## Related

Decisions: [[DECISIONS]] (`INT-24`; re-bases `INT-23`, resolves the `INT-21` caveat) · explanation: [[2026-07-26_sector_marks_explained]] · contract: [[DATA_CONTRACTS]] (`DC-CCR-SIM-2` `target_scales` extension, `DC-XWALK-4`) · predecessors: [[2026-07-25_mexican_book_swap]] · [[2026-07-25_headline_metric_explained]] (the EPE band this session re-bases) · gates: [[OPEN_QUESTIONS]] (`OQ-INT-11` residuals). Arm MOCs: [[CCR_MOC]] · [[HAZ_MOC]] · Home: [[_INDEX]]

#arm/ccr #arm/haz #arm/int #type/reading
