# 2026-08-01 · Read-log — per-peril severity + the Phase C null (`INT-26`, `INT-27`, `GEN-30`)

Session scope: close the last two analytical residuals of `OQ-INT-11` — (e) give each peril label its own severity distribution without moving any expected impact, and (b) test the adopted $c_{i,\text{ciclón}}$ ordering against realized equity returns under a pre-registered gate — plus the operational lesson of the wrong-environment incident the manifests caught. The readings below are what a reader needs to judge the mean-matching algebra, the truncation lesson behind $\sigma_{\text{ciclón}} = 1.33$, and what a FALLA verdict does and does not say.

## Priority 1 — conditional marks: severity typing is mark-dependent severity

**`[ContTankov2004]`, the marked-point-process chapters (marking + conditional mark distributions), continuing priority 1 of [[2026-07-30_peril_typed_events]].** Phase B′ upgrades the mark from (label, pooled size) to (label, size drawn from the label's own law $L_p$): the arrival process and the label draw are untouched, so the compound process stays a compound Poisson whose per-label sub-streams have intensity $\pi_p\lambda$ and severity $L_p$. The load-bearing identity is $\mathbb{E}[\text{mark}_i] = \sum_p \pi_p\,c_{ip}\,\mathbb{E}[L_p]/K_{\text{eff}}$ — with mean-matching ($\mathbb{E}[L_p] = \mathbb{E}[L]$) it collapses to the Phase A/B value $\gamma_i\,\mathbb{E}[L]/K_{\text{eff}}$ exactly, which is why the band barely moves while conditional tails restructure. Without this reading the mean-matched medians look like an arbitrary normalization instead of the moment condition that keeps `INT-17/20` intact.

## Priority 2 — the truncation lesson: fit after the threshold, never before

**`[Klugman2019]`, the chapters on truncated and censored data and on frequency–severity decomposition.** The session's key empirical surprise: the ciclón subset fits $\sigma = 1.33$ inside the $\geq 200$ MDP-2025 trigger set, not the $\approx 2.9$ of the unthresholded `INT-16` variant — left truncation removes the sub-threshold mass that carried most of the dispersion. Read to see why a lognormal fit on thresholded data estimates the *conditional* severity (the object the jump channel actually consumes, since only trigger events arrive at rate $\lambda$), why comparing $\sigma$ across different thresholds is a category error, and what a proper truncated-lognormal MLE would add if the untruncated law were ever needed. Also backs the `min_events` pooled fallback as a poor-man's credibility rule for thin labels (incendio, $n=2$).

## Priority 3 — event-study design under cross-sectional dependence

**`[MacKinlay1997]` (§99), the market-model event-study sections, re-read from the `INT-18` rate-leg design.** Phase C moves the same machinery from one yield series to a 26-name cross-section, which adds the dependence problem the rate leg never had: on any given episode all names share residual sector co-movement, so treating (name, episode) cells as independent overstates precision. The gate therefore bootstraps *episodes* (the panel's independent unit) and the exact Kendall $p$ is demoted to a diagnostic — the same pairs-bootstrap philosophy as `INT-18`, one level up. Read to defend the estimation window, the CAR construction on log AdjClose, and the choice of an ordering statistic (Kendall $\tau$) over a pooled regression when the prediction is monotonicity, not a slope.

## Priority 4 — interpreting the null: exposure ordering vs price discovery

**`[Kruttli2025]` (§99) and `[Bressan2024]`, the return-response sections.** The FALLA verdict ($\tau = +0.198$, wrong sign; $p_{\text{boot}} = .94$; drop-Otis jackknife agrees) says Mexican daily prices do not reprice cyclone events cross-sectionally — it does not say the physical-exposure ordering is wrong. `[Kruttli2025]` documents where and when disaster exposure *does* show in returns (and the horizons at which it fails to), and `[Bressan2024]` grounds the asset-footprint construction that now carries the ordering alone. Together they frame the manuscript sentence: the marks are exposure-based by construction and market-validation-bounded by design, the same epistemic status the rate channel earned in `INT-18/19`.

## Skim — the operational lesson

**`environment.yml` + `RunManifest` (`infra`), with `GEN-06`/`GEN-30`.** The wrong-env incident: the shell-default `thesis` env (numpy 2.4.3) moved the baseline book EPE $-0.036\%$ while every reported percentage held at 2 decimals; the July manifests' `packages` block is what identified the cause in minutes. The skim is the project's own manifest schema — knowing what it records is what makes byte-identity claims auditable.

## Related

Decisions: [[DECISIONS]] (`INT-26`, `INT-27`, `GEN-30`; re-bases `INT-23`) · explanation: [[2026-08-01_per_peril_severity_phase_c_explained]] · contract: [[DATA_CONTRACTS]] (`DC-CCR-SIM-2` per-label severity) · predecessor: [[2026-07-30_peril_typed_events]] · gates: [[OPEN_QUESTIONS]] (`OQ-INT-11` f/g remain). Arm MOCs: [[CCR_MOC]] · [[HAZ_MOC]] · Home: [[_INDEX]]

#arm/ccr #arm/haz #arm/int #type/reading
