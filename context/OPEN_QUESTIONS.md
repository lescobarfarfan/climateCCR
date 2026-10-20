# OPEN_QUESTIONS — Integrated open items

Only what is genuinely open. When something is resolved, move it to `DECISIONS.md` (dated) and delete it here (or drop it to "Recently resolved" for brief traceability). IDs follow `OQ-<ARM>-NN`; integration questions `OQ-INT-NN` come first because they gate the others.

## Table of contents
- **Integration** — `OQ-INT-07` (c), `OQ-INT-10`, `OQ-INT-11` (residuals ruled low-priority or future work; everything else resolved — the trace lives in [[HISTORY]] §3)
- **Cross-cutting (GEN)** — none open (`OQ-GEN-03` deferred by ruling and `OQ-GEN-04` closed 2026-10-20)
- **CCR arm** — none open (`OQ-CCR-11`–`OQ-CCR-13` resolved 2026-10-20)
- **MKT arm** — `OQ-MKT-02`, `OQ-MKT-04`, `OQ-MKT-13`
- **HAZ arm** — `OQ-HAZ-17`, `OQ-HAZ-19`

---

## Integration — residuals

Every `OQ-INT` of the methodology gate is resolved (`OQ-INT-01`–`06`, `08`, `12`–`14`); the three lines below are the residuals ruled low-priority or future work, kept because they name the seams.

- `OQ-INT-07` **Jump-mark estimation — one residual (2026-09-14).** ✅ (a) the scale fixed (`INT-17`); ✅ (b) INPC deflation — closed 2026-09-14 as confirmed by cross-check (`HAZ-STOCH-05`); ✅ (d) leading variant `mayores_200mdp`. **Still open — (c) the step-aware `MarkSampler`** (`sample` is time-blind): kept as a desirable to-do by user ruling 2026-09-14, low priority — the severity trend is regime-specific (`HAZ-STOCH-06`) and arrivals trending already rides the λ(t) riders (`INT-34`); the exposure-vs-climate attribution caveat stands (`[PielkeLandsea1998]`).
- `OQ-INT-10` **Bond desk realism — residuals after `CCR-RISK-04`/`INT-32` (2026-08-08).** ✅ (b) **FRN pricer built** (`CCR-RISK-04`: TIIE28+sobretasa, single-curve simple-forward projection, static discount margin as the shocked credit column). ✅ (a) **partially — six issuers swapped to issuance-verified terms** (`INT-32`: OMA suplemento-primary; FIBRA_UNO/CEMEX/FEMSA/CFE press+IR-verified; provenance URLs in `configs/mexican_book.yaml`). Probe verdict on feasibility: BMV `docs-pub` prospectus PDFs are bot-blocked (302 → `no_disponible`) while issuer-IR/press pages work — **hand-collection viable, scraping not**; DataBursatil (`databursatil.com`) stays the untested API candidate, Valmer/PIP the quote-vendor route. **Still open:** the remaining representative rows stay `[eng]` — extend verification opportunistically, series by series; the PEMEX sobretasa confirmation (`[eng]`, no public doc found); UDI-linked (real-coupon) series excluded by scope — revisit only if an inflation leg ever enters; credit-spread *dynamics* (stochastic spreads) remain future work, coupling the built CVA's stochastic-WWR residual (`CCR-RISK-06`) and the phased-application question (`OQ-INT-12`). [eng] **2026-09-14 (`INT-38`): the residuals are future work — no further verification planned for the thesis.**
- `OQ-INT-11` **Sector/peril-differentiated marks — residuals after `INT-26`/`INT-27` (2026-08-01).** ✅ Phase A adopted (`INT-24`); ✅ Phase B peril-typed events adopted (`INT-25`, incl. industrials G + S-tier sensitivity); ✅ **(e) per-peril severity adopted** (`INT-26`: mean-matched per-label σ, ciclón 1.33 at trigger grain — the σ≈2.9 concern was sub-threshold dispersion; band −8.36/−5.05/−4.51%); ✅ **(b) Phase C executed under its pre-registered gate → FALLA** (`INT-27`: τ=+0.198, p_boot=.94 over 63 cyclone episodes × 26 names — the equity cross-section does not reprice cyclone events; the ordering rests on construction evidence, the `INT-18/19` pattern). ✅ **(f) storm-clustered refit executed 2026-08-01** (`INT-28`: band −7.85/−3.74/−4.63 vs adopted −8.36/−5.05/−4.51 — headline/floor within ±1pp, the CT anchor is the grain-sensitive leg, tails ease; the adopted band stands); ✅ **(g) MDD triage resolved 2026-08-01** (`HAZ-CENAPRED-12`: user rule — `danio_mdd` discarded, MDP dispositions 2/11/3/23/2, the two 2003 fire rows conservatively excluded from unthresholded diagnostics). **Residual (future work under the `[Bressan2024]` coarse-proxy caveat):** within-state asset resolution (LitPop/CLIMADA) and I-O indirect effects (`[Hallegatte2008]`). Couples `INT-23` (band numbers) and `DC-XWALK-4`. **2026-09-14 (`INT-38`): the residual is future work.**

## Cross-cutting (GEN)

- None open. `OQ-GEN-03` (the CNSF 2025 hidro vintage) was deferred by ruling and `OQ-GEN-04` (the landing backlog) closed on 2026-10-20 (`GEN-41`, `GEN-42`); the earlier `OQ-GEN-01/02` closed in August (`GEN-32`, `GEN-33/34`).

## CCR arm

- None open. `OQ-CCR-11/12/13` (the engine details found 2026-10-08) resolved 2026-10-20 (`CCR-RISK-09`, `CCR-SIM-04`); `OQ-CCR-01`–`10` closed between June and September (`CCR-MIG-05/08`, `CCR-ARCH-06`, `MKT-NGFS-04`, `CCR-RISK-03/05/06/07`, `CCR-SIG-05`).

## MKT arm

- `OQ-MKT-02` **λ, the market price of interest-rate risk — kept open as a P-measure appendix hook (re-scoped 2026-09-14).** No P-measure stress output enters the results (pricing rides θ(t) under Q, scenarios are exogenous NGFS paths, the only P-measure object is the `GEN-33` backtest cone), so λ is estimated only if a real-world stress-path appendix is written — historical excess-return regression vs Yasuoka's forward-rate approach; confirm the `[Yasuoka2018]`/`[JamesWebber2000]` editions then (`[JamesWebber2000]` pinned 2026-09-14). (← `MKT-MEAS-01`)
- `OQ-MKT-04` **NGFS scenario-vintage mix — deferred until the long-term vintage joins** (`MKT-NGFS-04`: the ST-only first build needs no splice). When the Phase-V/VI LT build starts: confirm the splice point (ST quarterly 2025–2030 → LT annual beyond) and how to blend the two rate paths without a kink — two different model worlds (GEM-E3/EIRIN vs NiGEM+IAM), no official NGFS splice guidance. (← `MKT-NGFS-03`)
- `OQ-MKT-13` **NGFS connector extensions (post-`MKT-NGFS-04..08`/`INT-29/30/31`).** ✅ (c) equity/corporate leg, (d) `[BanxicoREF]` pin, (e) inner-band reordering — **all resolved 2026-08-03** (`MKT-NGFS-08`/`INT-31`: sector-grain S0 + excl-policy spread overlays with sign-flipping full-leg deltas; REF dic-2024 Recuadro 6 pinned; the "reordering" was an `INT-30` (b) transcription artifact, corrected in place). ✅ (a) **trajectory flavor resolved 2026-08-08** (`MKT-NGFS-09`: maturity-dated anchor deltas, flat-path reduction invariant, hold-constant beyond the window; rates-only — the phased equity/spread application re-homed to `OQ-INT-12`; nivel stays headline, trajectory = robustness flavor). **Still open:** (b) the **long-term vintage join** (Phase V now / Phase VI on release per `GEN-31`) — reopens the `OQ-MKT-04` splice and brings Current-Policies baselining and NiGEM country-grain rate variables.

## HAZ arm

- `OQ-HAZ-17` **Agro magnitude-correction residuals — a documented approximation (slimmed 2026-09-14, `HAZ-SOURCES-05`).** The corrected copies are wired into the `K` scale (`configs/loss_to_mark_scale.yaml`) and agro is ≈ 7 % of `K`, so (a) the 132 weak-signature rows, (b) the external ×FIX confirmation, (c) the intra-year FIX refinement and (d) the 323-finding triage queue bound `K` at the percent level — a manuscript caveat, no further work planned.
- `OQ-HAZ-19` **Post-extension residuals (2026-07-21; successor of `OQ-HAZ-18` after `HAZ-CENAPRED-10`/`HAZ-STOCH-06`/`INT-19`).** ✅ (a) **the headline arrival intensity — resolved 2026-07-25** (`INT-20`): registry λ=19.2857/yr headline (measurement-consistent with the `INT-17` scale window) + a regime-consistent scenario band as robustness (report floor 7.2222, CT anchor 9.9565; `configs/climate_jump_real_{floor,ct_anchor}.yaml`). ✅ (b) **done 2026-10-03** (`HAZ-CENAPRED-13`, `HAZ-STOCH-07`): the EXTENSO 2024 replaced the preliminary rows (12 → 138) and the refits were adopted — floor λ unchanged at 7.2222 with severity 1,287.13 / 1.0555, CT bridge λ 10.0870; both null gates re-applied verbatim (FALLA). **Still open:** (d) the EXTENSO 2024 portal URL — provenance carries `url` null with the sha256; add it to `EXTENSOS_CONOCIDOS` when found. (c) The non-CT stream post-2016 is censored (LLUV/sequía as state-annual aggregates) — if a future CENAPRED product restores event grain, refit; until then cross-regime statements ride on the ciclón bridge. [eng]

---

## Recently resolved (traceability)

The closures of the last session; the full trace — every closed question and the decision that closed it, plus the verbatim closing lines of the resolved `OQ-INT`/`OQ-GEN`/`OQ-CCR` entries — lives in [[HISTORY]] §3.

- ~~The CNSF 2025 hidro vintage (`OQ-GEN-03`)~~ → **deferred by ruling 2026-10-20** (`GEN-41`): 2024 stays the closed data year.
- ~~The landing backlog (`OQ-GEN-04` a–h)~~ → **closed 2026-10-20** (`GEN-42`): substreams per sector name, the book builder's prune and provenance stamp, the CLI defaults, the encoding sweep, the archived cache.
- ~~Control-sector S-tier references and the tier-jitter band on the control book (`OQ-INT-13`)~~ → **resolved 2026-10-20** (`INT-41`): the control band spans −5.91 … −1.22 % on the headline leg across the variants, the heterogeneity gap never below 4 pp; the rows keep their author tiers (no sector score vector exists in the two verified sources).
- ~~Tier-E back-pricing caveats (`OQ-INT-14`)~~ → **resolved 2026-10-20** (`INT-42`): the annual grid read on non-overlapping dates and the realised-curve reprice built and scored; the implied-vol history closed as infeasible.
- ~~Close-out collateral pairing, option curve by position, GBM endpoint tenor (`OQ-CCR-11/12/13`)~~ → **resolved 2026-10-20** (`CCR-RISK-09`, `CCR-SIM-04`): the pairing fixed and the goldens re-based; the two details closed with zero results change.

## Related
Reads with: [[DECISIONS]] (resolved items move there) · [[DATA_CONTRACTS]] (the contracts they gate) · [[WORKFLOW]] (the ritual that closes them). By arm: [[CCR_MOC]] · [[MKT_MOC]] · [[HAZ_MOC]] · Home: [[_INDEX]]
#arm/int #type/open #status/open
