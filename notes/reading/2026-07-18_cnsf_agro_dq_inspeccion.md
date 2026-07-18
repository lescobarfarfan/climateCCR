# 2026-07-18 — CNSF agro data quality & the inspection step (read-log)

Session decisions: `HAZ-CLEAN-CNSF-12/13` (agro magnitude corrections ÷1000 and ÷FIX, in copy) and `GEN-27` (`climateCCR.data.inspeccion` as the standing sanity-check step). Readings, by priority:

1. **`[Leys2013]` — Leys, Ley, Klein, Bernard & Licata (2013), *Detecting outliers: do not use standard deviation around the mean, use absolute deviation around the median*, J. Exp. Soc. Psychology 49(4), 764–766 — short paper, read whole.** **Why:** the case for the median/MAD robust $z$ the inspector uses everywhere (`GEN-27`): mean/SD detection self-masks (the outlier inflates the very SD meant to flag it), and the consistency constant $0.6745$ (MAD $\to \sigma$ under normality) is what makes the $|z|$ threshold interpretable. Without it the default umbral $|z| > 5$ looks arbitrary.
2. **`[Iglewicz1993]` — Iglewicz & Hoaglin (1993), *How to Detect and Handle Outliers*, ASQC Quality Press — ch. 2–3 (labeling rules, the modified z-score).** **Why:** the operational rulebook behind flag-don't-delete: detection and treatment are separate steps, which is exactly the inspector's triage (`error_probable` / `atipico_a_revisar` / `inconsistencia_estructural`) and the corrections-in-copy discipline of `HAZ-CLEAN-CNSF-12/13` — nothing is silently dropped or overwritten.
3. **`[BanxicoFIX2024]` — Banco de México, FIX MXN/USD representative rate, annual averages 2022–2024 (Informe Anual compilation; SIE SF43718).** **Why:** the ÷FIX factors (20.1274 / 17.7587 / 18.3049) that undo the double MXN→"USD"→MXN conversion in `HAZ-CLEAN-CNSF-13`; also the upgrade path to per-issue-date FIX if the ±5–10% intra-year approximation ever matters (`OQ-HAZ-17` c).

## Related

Backs: [[DECISIONS]] (`HAZ-CLEAN-CNSF-12/13`, `GEN-27`) · contracts: [[DATA_CONTRACTS]] (`DC-HAZ-CNSF-6`, `DC-CONV-11`) · open: [[OPEN_QUESTIONS]] (`OQ-HAZ-17`) · evidence: [[referencias_riesgo_catastrofico]] §4 · pipeline: [[README_scraper_cnsf]] · explained in [[2026-07-18_cnsf_agro_dq_inspeccion_explained]]. Arm MOC: [[HAZ_MOC]] · Home: [[_INDEX]]

#arm/haz #type/reading
