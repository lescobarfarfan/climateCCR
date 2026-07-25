# 2026-07-25 — The Mexican book, the bond desk, and the inverse sensitivity, explained

> Companion to [[2026-07-25_mexican_book_swap]] (the read-log). Decisions: `INT-21`, `INT-22`, `CCR-RISK-02` — resolving `OQ-INT-04` and `OQ-MKT-12` (c).

## What was decided

The PIMPA engine's Swiss stand-in book (CS/UBS shares, EUR/GBP/USD curves) was replaced by a **Mexican climate-exposed book** (`data/ccr_book_mx/`, rebuilt deterministically by `pipelines/09_build_mexican_book.py` from `configs/mexican_book.yaml`): 26 BMV equities, 30 counterparties (one per issuer plus PEMEX and CFE as debt-only cebures issuers), 28 TIIE swaps, 52 equity options, and 21 fixed-coupon cebures priced by a **new additive bond desk** (`CCR-RISK-02`). The rate-channel scale was re-inverted with the Mexican mean reversion (`INT-22`), and the `INT-20` λ band was re-run on the book.

## $S_{\text{rate,eff}}$ is an inverse sensitivity, not a loss

The rate-mark equation is $\text{mark} = L / S_{\text{rate,eff}}$: an event with real damage $L$ (MDP-2025) jumps the simulated short rate by $L/S_{\text{rate,eff}}$ (decimal). So $S_{\text{rate,eff}}$ answers: *how much national damage would move the Mexican short rate by a full 1.0 — i.e. 10,000 bp?* It is a **denominator with damage units**, not an exposure, a loss, or money at risk — which is why its magnitude (144.3M MDP-2025 ≈ $1.44\times10^{14}$ MXN ≈ 4–5× Mexican GDP) is *correct, not alarming*: moving sovereign yields by a hundred percentage points via climate damage should require a counterfactually absurd loss. A **median event (905.53 MDP-2025) maps to a 0.063 bp jump**.

The chain (`[Anyfantaki2025]`, Figure 8 → `INT-18` gate → `INT-22`): the scenario slope is $\beta = 4\times10^{-6}$ of 10Y yield per **bn** MDP; a short-rate jump decays through the HW1F mean reversion before reaching the 10y yield, so the inversion divides by the loading $\bar B(T) = (1-e^{-aT})/(aT)$: $j = (\beta/10^3)/\bar B(T)$ per MDP and $S_{\text{rate,eff}} = 1/j$. With the engine-fixture $a = 0.05$: $\bar B = 0.787$, $S = 196{,}734{,}670$; with the Mexican $a = 0.1221$ (`MKT-CALIB-05`): $\bar B = 0.577$, $S_{\text{rate,eff}}^{MX} = 144{,}343{,}565$ MDP-2025 (**−26.6%**). Faster mean reversion ⇒ the jump dies sooner ⇒ a *bigger* initial jump is needed for the same 10y move ⇒ smaller $S$, larger marks (medians $4.6028\times10^{-6} \to 6.2734\times10^{-6}$ registry, $8.8267\times10^{-6}$ floor-severity).

Two standing flags travel with the number: it is an `INT-12` **Path-B scenario, not a Mexican estimate** — the pre-registered event studies (`INT-18`, reconfirmed with Otis in sample, `INT-19`) bound Mexico's own per-event response near zero, and the `[Anyfantaki2025]` slope is **~12× that estimated upper bound**; and the name `s_rate_eff_mdp` invites misreading as a peso amount (hence this note and the GLOSSARY entry).

## What the book's calibrated quantities mean

**Per-name GBM ($\mu$, $\sigma$, $S_0$):** closed-form MLE on daily log-returns per ticker (Yahoo, crisis windows excluded per `MKT-CALIB-03`), $S_0$ = last close at the 2026-07-17 valuation anchor — each share diffuses with its own drift/vol instead of one IPC proxy. **`MXN_USD_FX_RATE`:** a GBM on Banxico FIX (MXN per USD), required mechanically by the engine's settlement conversion; for this all-MXN book the conversion cancels per path, so it adds no net FX risk. **Correlation (28×28):** pairwise-complete sample correlation of daily log-returns plus the F-TIIE rate factor, eigenvalue-clipped to PSD (`[Higham2002]` §99; min eigenvalue 0.067 — no repair actually fired). **IV surfaces:** flat at each name's fitted $\sigma$ — a documented `[eng]` proxy, since no free MXN single-name surfaces exist. **Bond desk:** each cebur is $\pm(\text{face}/100)\sum_i cf_i\,P(t,T_i)\,e^{-s\,\tau_i}$ with $P(t,T_i)$ from the simulated HW1F curve and $s$ the **static** issuance sobretasa — rate risk flows through discounting, credit-spread risk is deliberately absent (`OQ-INT-10`); the 21 coupon/maturity/spread triples are representative-by-tier `[eng]` pending prospectus verification.

## How to read the EE/PE results

Mean EE shift over 30 NAIDs × the largo grid (jump-ON − baseline, seed 233423, byte-identical re-runs): **−2,968 MXN headline** ($\lambda=19.29$), **−1,705 CT anchor** ($9.96$), **−1,469 floor** ($7.22$) — the `INT-20` compound-rate ordering, now on the real book. Sign anchors that validate the plumbing: the one NAID holding only a **payer** IRS gains (+73) when rate-up jumps arrive (pays fixed, receives floating); the debt-only PEMEX/CFE NAIDs lose on long bonds (−39/−57, small because the rate marks are 0.06–0.09 bp medians). The equity legs dominate the magnitudes: the `INT-17` book-level mark (median −0.69%/event, and $\mathbb{E}[\text{mark}] \approx -1.4\%$ given $\sigma=1.21$) hits **all 26 names on every shared event**, compounding to a ≈28%/yr expected drag per equity path at the headline $\lambda$ — faithful to the canon's book-level interpretation but an aggressive upper bound at single-name grain, which is exactly `OQ-INT-11`.

## Justification

Hull–White bond reconstruction and the yield loading: `[BrigoMercurio2006]` ch. 3. GBM MLE and path generation: `[Glasserman2003]` ch. 3. The scenario slope and its EMDE provenance: `[Anyfantaki2025]`. Compound-Poisson scaling of the band: `[ContTankov2004]` ch. 3. PSD repair: `[Higham2002]` (§99).

## Related

Decisions: [[DECISIONS]] (`INT-21`, `INT-22`, `CCR-RISK-02`) · read-log: [[2026-07-25_mexican_book_swap]] · contract: [[DATA_CONTRACTS]] (`DC-CCR-RISK-4`) · predecessors: [[2026-07-25_lambda_band_readout_explained]] (the λ band and the deferral this session executes) · [[2026-07-19_rate_leg_event_study_explained]] (what $S_{\text{rate,eff}}$ came from) · gates: [[OPEN_QUESTIONS]] (`OQ-INT-10`, `OQ-INT-11`, `OQ-INT-02`). Arm MOCs: [[CCR_MOC]] · [[MKT_MOC]] · Home: [[_INDEX]]

#arm/ccr #arm/mkt #arm/int #type/explanation
