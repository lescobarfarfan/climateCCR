# 2026-07-18 — CNSF agro data-quality corrections & the inspection step, explained (`HAZ-CLEAN-CNSF-12/13` / `GEN-27`)

> Summary-explanation note (`GEN-26`): what was corrected in the agro consolidado, what the new inspection step measures, how to interpret the corrected series and the findings tables, and the justification behind each threshold. Reading list: [[2026-07-18_cnsf_agro_dq_inspeccion]].

## 1. What was wrong, in plain terms

The CNSF agro consolidado carries two magnitude errors that come **from the source files** (the raw SESA deliveries — verified against `2015 Agricola Bases.xlsx`; the consolidation did not introduce them):

**(a) Surfaces ×1000.** Some rows report hectares a thousand times too large — Michoacán-aguacate 2015 claims 13.9 M ha insured, about $2.4\times$ the state's entire territory — while the money columns are correct. The tell: the implied insured value $\text{suma}/\text{superficie}$ collapses to under 100 MXN/ha (you cannot insure a hectare of anything for the price of a coffee), and dividing the surface by 1000 puts the cell exactly back on its own historical value range. This is a clean unit error: the factor is exact.

**(b) `SUMA ASEGURADA` ×FIX, systemic 2022–2024.** From 2022 the insured sums of many rows (≥12 states, concentrated in "Seguro agrícola a la inversión (por planta)") are inflated by roughly that year's MXN/USD exchange rate, with surfaces and premium untouched — consistent with a **double currency conversion** (amounts already in MXN treated as USD and converted again). The tell: the implied premium rate $100 \cdot \text{prima}/\text{suma}$ collapses below 0.5% when the historical median is 2.7–7.5% — insurers do not suddenly charge a tenth of the going rate. The signature count jumps from ≤26 rows/yr before 2022 to 224/211/196 in 2022/23/24.

## 2. What each introduced quantity means

**The corrections are in copy, never in place.** `corregir_consolidados_agricola.py` writes `emision_corregida.csv` / `siniestros_corregida.csv`; the originals remain the CNSF "as published" record. Every touched row carries `dq_correccion` (which rule fired: `superficie_div1000` or `suma_div_fix`) and `dq_valor_original` (the pre-correction value), and `_correcciones_dq.csv` lists every correction row by row — you can always reconstruct exactly what changed and undo it.

**The thresholds** (all in `limpieza_cnsf.py` §6): the plausible implied-value band is $[10^3, 2\times 10^5]$ MXN/ha — a ÷1000 correction is only applied when the raw implied value is below 100 MXN/ha *and* the corrected one lands inside the band; the ×FIX signature requires implied value $> 2\times10^5$ MXN/ha *plus* a collapsed premium rate ($< 0.5\%$); rows with $\text{prima} \leq 0$ (no rate to betray them) are corrected only when their implied value is at least $5\times$ their **own** pre-2022 median (`FACTOR_HISTORIA`) — a cell is only ever judged against its own history, never against other crops or states.

**The ÷FIX factors** are the Banxico annual averages (2022 = 20.1274, 2023 = 17.7587, 2024 = 18.3049) — a *documented approximation*: the true factor per row is the FIX of its intra-year issue date, so corrected 2022–2024 levels carry ±5–10% uncertainty (`OQ-HAZ-17` c).

**The inspector's robust $z$** (`GEN-27`): $z = (x - \mathrm{med})/(\mathrm{MAD}/0.6745)$, computed per group across time, and on $\log_{10}(\text{num}/\text{den})$ for derived ratios — unit errors are multiplicative, so they appear as clean $\pm 3$-decade offsets in log space. Median/MAD instead of mean/SD because the outlier being hunted would otherwise inflate the yardstick used to flag it `[Leys2013]`.

**The triage labels** (deterministic rules, `[Iglewicz1993]` detect-then-triage): `error_probable` = capture/unit-error signature (fix); `atipico_a_revisar` = extreme but possibly real — a hurricane year is *supposed* to be an outlier (domain review before touching); `inconsistencia_estructural` = structural defect (duplicates, near-duplicate labels, systematic missingness — fixed in pipeline, not cell by cell).

## 3. How to interpret the results obtained

915 corrections were applied: 122 surfaces ÷1000 (25 emisión + 97 siniestros) and 793 sumas ÷FIX. After correction the median implied premium rate returns to **3.1%** (inside the 2.7–7.5% historical band) and 89% of corrected rows fall in the plausible value band — the corrected series is the one to use for **per-hectare rates and suma-asegurada levels** in the agro ramo; frequency and `MONTO PAGADO` series were never affected.

The inspector doubles as the verification: on the original `emision.csv` it flags 372 `error_probable` findings including the flagship Maíz dulce/Sinaloa 2015 cell; on `emision_corregida.csv` that signature is gone and the count drops to 323. The residual 323 are the standing triage queue (`OQ-HAZ-17` d): the 132 deliberately-uncorrected weak-signature rows (prima ≤ 0 with no confirming history — still inflated in the copies, listed on every corrector run) plus candidates that need domain judgment.

**Honest caveats before using the agro series:** 2022–2024 levels are ±5–10% (annual-average FIX); the 132 weak rows are still wrong in the copies; insurer attribution is impossible from these files; external confirmation (CNSF fe de erratas / INAI) is pending (`OQ-HAZ-17` a–b).

## 4. Why this is the right design

Correct-don't-delete, with a full audit trail, preserves both reproducibility (`GEN-05`: re-runs always start from the untouched originals, so the pipeline is idempotent) and the evidentiary record (the as-published files remain citable as what the CNSF actually released). Detection is statistical but **correction is only ever rule-based**: the inspector proposes, a documented rule with a physical or accounting rationale disposes — no cell is changed because a $z$-score alone said so. That is the same discipline the canon already applies to entities (`HAZ-CLEAN-CNSF-04`: unrecognized labels go to manual review, never blind-assigned).

## Related

Backs: [[DECISIONS]] (`HAZ-CLEAN-CNSF-12/13`, `GEN-27`) · contracts: [[DATA_CONTRACTS]] (`DC-HAZ-CNSF-6`, `DC-CONV-11`) · open: [[OPEN_QUESTIONS]] (`OQ-HAZ-17`) · evidence: [[referencias_riesgo_catastrofico]] §4 (recuadro agrícola) · pipeline: [[README_scraper_cnsf]] · read-log: [[2026-07-18_cnsf_agro_dq_inspeccion]]. Arm MOC: [[HAZ_MOC]] · Home: [[_INDEX]]

#arm/haz #type/explanation
