# 2026-07-30 · Read-log — peril-typed jump events (`INT-25`, `HAZ-CENAPRED-11`)

Session scope: resolve `OQ-INT-11` (a)/(c)/(d) — type every climate jump event with a peril label so only susceptible sectors take the hit, extend the industrials' G layer with sourced state tables, and stress the ordinal S tiers — plus close the `GEN-27` inspección gap on the 2000–2015 CENAPRED base after importing the impactcal-mx QA findings. The readings below are what a reader needs to judge the label construction, the mean-preservation algebra, and the data caveats the sensitivities answer.

## Priority 1 — marked point processes: the peril label is a mark

**`[ContTankov2004]`, the marked-point-process and compound-Poisson chapters backing `INT-13` (thinning/marking of Poisson processes).** Phase B is textbook marking: the arrival process is unchanged, each arrival carries an i.i.d. categorical mark (the peril label) with distribution $\pi$, and the per-name impact is a function of the mark ($c_{ip}\times$ the base severity draw). Independent thinning explains why per-peril sub-streams are again Poisson with intensity $\pi_p\lambda$ — the fact that keeps the compound loss rate $\lambda\,\mathbb{E}[L]$ and every per-name mean exactly at their Phase A values while higher moments restructure. Without this reading the identity $\sum_p \pi_p c_{ip} = \gamma_i$ looks like a trick instead of the thinning theorem in config form.

## Priority 2 — why labels come from the frequency mix, not the damage mix

**`[Klugman2019]`, the frequency–severity decomposition chapters (collective risk model).** The user decision that $\pi$ is the trigger-set *frequency* mix is the collective-model discipline: arrival composition belongs to the frequency side (the same 270 rows the `INT-20` $\lambda$ counts), while size differences across perils belong to severity — which Phase B deliberately keeps pooled (per-peril severity is the logged `OQ-INT-11` (e) residual, with the ciclón subset's $\sigma\approx2.9$ vs the pooled $1.21$ as the known understatement). Read to defend the split and to see what upgrading (e) would entail.

## Priority 3 — the cause-vs-mechanism attribution caveat the sensitivities answer

**impactcal-mx canon, `CAL-BAYES-10` and `CAL-TARGET-06` (sibling project, `context/DECISIONS.md`).** The documented facts imported this session (`HAZ-CENAPRED-11`): a "Ciclón tropical" row is a *cause* label bundling wind + surge + rain damage; `INUND` disappears as a subtipo from 2016 (fluvial under `LLUV`); empty cells post-2016 are non-reports, not zeros. Our taxonomy is cause-level throughout, so the bundle is internally consistent — the residual risk is the fuzzy boundary *between* hydro labels, which is exactly what the `hidro_merged` and `fluvial_merged` variants bound (both within 0.4pp of base; fluvial identical). Read to see why the S matrix must be interpreted per cause, never per physical mechanism.

## Priority 4 — the asset-attribution template for the industrials G

**`[Bressan2024]`, the Methods section and the proxy-data experiment (already priority 1 of [[2026-07-26_sector_marks]]).** Re-read for (c): the 67–92% acute-risk understatement of HQ/coarse proxies is the citable reason the five sourced industrials improve on the population tier, and the reason HERDEZ (2 of 15 plants locatable) *stays* on the documented proxy rather than getting an invented table — `GEN-03`'s "excluded and documented" applied to G.

## Priority 5 — robust outlier triage behind the inspección annex

**`[Leys2013]` / `[Iglewicz1993]` (§99, the `GEN-27` basis).** The row-level `danio_mdp/danio_mdd` triage compares each row's ratio to its year median (the robust FIX proxy) on a $\log_{10}$ scale — the median/MAD philosophy of the standing inspección applied to a derived ratio. Read to defend the triage bands (one decade = `error_probable`) and why cell-level aggregation can mask offsetting row errors.

## Skim — the sensitivity-design precedents

**`[CEPAL2014]`** (the DaLA sector decomposition the S rows inherit) and **`[Kruttli2025]`** (exposure-share→return monotonicity; the Phase C event-window template, now sharpened by per-peril predictions: cyclone episodes should move high-$c_{\text{ciclón}}$ names specifically).

## Related

Decisions: [[DECISIONS]] (`INT-25`, `HAZ-CENAPRED-11`; re-bases `INT-23`) · explanation: [[2026-07-30_peril_typed_events_explained]] · contract: [[DATA_CONTRACTS]] (`DC-CCR-SIM-2` peril blocks) · predecessor: [[2026-07-26_sector_marks]] · gates: [[OPEN_QUESTIONS]] (`OQ-INT-11` b/e/f/g). Arm MOCs: [[CCR_MOC]] · [[HAZ_MOC]] · Home: [[_INDEX]]

#arm/ccr #arm/haz #arm/int #type/reading
