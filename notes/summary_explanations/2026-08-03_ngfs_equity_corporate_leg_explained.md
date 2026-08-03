# The NGFS ST equity/corporate leg, explained (2026-08-03)

What was built and decided on 2026-08-03 — the `OQ-MKT-13` (c) extension of the transition channel to the book's equity and cebur legs, the (e) inner-band resolution, and the (d) `[BanxicoREF]` pin — in plain language, with the reasoning and the numbers.

## 1. What the extension is

The 2026-08-02 connector moved only the rate curve, so a transition scenario repriced the IRS and bond desks through discounting but left the 26 equities and every cebur spread untouched — transition risk was understated exactly where a Mexican book holds it (a fossil NOC's debt, carbon-intensive cement/mining equities). The ST database publishes what closes the gap: CLIMACRED's 50-sector families at Mexico country grain, `equity_relative_adjustment|<sector>` (% vs BAU) and `corporate_bond_spread_adjustment{,_incl_policy}|<sector>` (pp vs BAU), annual to 2030. The pull config now takes every variable at the Mexico grain (`variables: []` — the REST filter matches exact names only, so the region *is* the scope; the PD/WACC families land alongside for the future CVA build), same run ids and version as the first build: a scope extension, not a data revision.

## 2. How the shocks enter (and why not through the jump)

Both new legs ride the existing fixed flavor — the signed peak over 2025–2030 — as **overlays on initial conditions**: each equity's S0 becomes S0·(1 + Δ%/100) in the spot file and both GBM `initial_value` columns (drift/vol, option strikes and notionals, FX untouched — an instantaneous revaluation of current values, the CBES/Fed-CSA practice); each issuer's sobretasa becomes spread + Δpp/100, floored at 0. The **excl-policy** spread variant is deliberate: the shocked curve already carries the policy + sovereign move at both anchors, so the bond leg takes only the corporate credit component — incl-policy would count the curve twice. Nothing enters the jump process or the GBM dynamics: CLIMACRED adjustments are model-implied *expectations repricing* under a narrative, while the jump marks are *empirically estimated realized-loss transmission* (`INT-17`), and summing the two would double-count both channels (`INT-29`) while averaging a counterfactual with an estimate. The jump channel's γ/c/severity blocks keep their unshocked-book values across scenarios — the physical-exposure composition must not depend on the transition state.

## 3. The numbers

Transition-only book-EPE deltas (vs base jump-off 269,655.35 MXN): **HWTP −3.78 %, SWUC −3.65 %, DAPS_NAM −13.35 %** — against the rate-only −0.36 / +1.50 / +4.28 %. The equity and spread legs dominate the curve leg and **flip the sign** of the adverse narratives: rate-only, higher rates *raised* EPE through the exposure kink; with VISTA at −21.7/−25.7 %, CEMEX·GCC at −15.5/−19.5 %, and PEMEX's sobretasa widening +959/+1,209 bp (380/430 → up to 1,639 bp), every scenario is now a net book loss. Approximate decomposition (additivity is only approximate under the kink): HWTP −3.78 ≈ −0.36 (curve) − 3.42 (equity+spread); SWUC −3.65 ≈ +1.50 − 5.15; DAPS −13.35 ≈ +4.28 − 17.63.

The `INT-30` non-monotonicity survives one level up: HWTP ≈ SWUC at the book level despite SWUC's uniformly larger shocks, because SWUC's larger rates-up gain nearly offsets its larger equity/spread losses — the netting-set kink, not shock size, still sets the book number. At name level the alternated IRS directions spread both signs: GRUMA +7.4k, FIBRA UNO +6.0k, GAP +4.2k MXN off-leg EPE under SWUC where higher rates dominate; PEÑOLES −7.2k, OMA −5.5k, FIBRAHOTEL −5.4k, PEMEX −5.3k (debt-only: curve + 1,209 bp spread) where repricing dominates; GCC's netting set nearly extinguishes (4.3k → 0.4k).

Combined cells (transition overlay × HAZ jump-on, HWTP/SWUC only per `INT-29`): −12.00/−12.01 % headline. Jump-within — the physical band re-read inside each shocked book — matches the rate-only build to ~0.02 pp (headline −8.54 vs −8.56 under HWTP): equity marks are multiplicative in log-price, so revaluing S0 rescales both legs nearly proportionally. The physical-channel conclusion is again robust to the transition state.

## 4. The counterpoint, equity edition

DAPS_NAM embeds physical risk via expectations repricing and moves the book **−13.35 %**; the HAZ empirically-calibrated physical jump moves it **−8.40 %** (headline); and `INT-27` measured the realized per-event equity repricing of the same peril class as **≈ 0** (63 cyclone episodes × 26 names, τ = +0.198, p_boot = .94). Same direction, same order of magnitude, entirely different epistemics — the `INT-18/19` ↔ DAPS-sovereign pattern one asset class over, and the manuscript's strongest argument for the `INT-29` split: a scenario-based transition channel and an empirically-estimated physical channel, compared and combined through separate seams, never summed.

## 5. The (e) resolution — there was no reordering

Computed from the artifacts, the unshocked inner legs are CT −5.074 / floor −4.527 (the `INT-23/25/26` ordering; the stored rate-only readout agrees), and under shocked curves each deepens by ~0.15 pp with ordering preserved (CT −5.22/−5.31, floor −4.68/−4.77). The `INT-30` (b) sentence "floor −5.07 → −4.68, CT −4.53 → −5.23, drift ±0.4 pp and swap order" wrote the shocked triple in headline/floor/CT order but quoted the unshocked band in headline/CT/floor order — each leg was compared against the other's baseline, manufacturing a swap out of two benign drifts. Per-NAID decomposition caps any single netting set's contribution to the floor-vs-CT gap at 0.017 pp: smooth, second-order, no λ-config × curve interaction worth further study. Canon consequence: correct `INT-30` (b) in place at digest and close `OQ-MKT-13` (e).

## 6. Caveats to carry

PEMEX rides `Crude Oil` (upstream-dominant mix); the refining alternative `Oil` is *more* adverse (+1,680 vs +959 bp under HWTP), so the reported hit is the conservative of the two defensible mappings — GEM-E3 has no integrated-oil sector. Hotels, airports, retail, and insurance ride the `Market Services` aggregate (airports `Warehousing`, the ISIC H52 home of air-transport support activities) — their transition sensitivity is likely understated, but these are precisely the names the physical channel prices (ASUR's γ ≈ 4), so the combined cell carries their risk through the estimated channel. The CFE floor (sobretasa at 0 under HWTP's −3.04 pp `Power Supply` tightening) binds on 2 trades and nowhere else. The curve's short anchor still rides the `EIRIN 1.0|North America` region proxy.

## 7. The `[BanxicoREF]` pin (d)

The supervisory-practice sentence now has its exact source: Banco de México, *Reporte de Estabilidad Financiera*, **diciembre 2024, Recuadro 6 — "Piloto de análisis de escenarios climáticos del Comité de Finanzas Sostenibles"** (the CFS climate-scenario-analysis pilot), with Recuadro 5 of the June-2023 REF ("Aumento en la ocurrencia de ciclones tropicales y crédito expuesto en México") as the physical-risk companion; located via the REF recuadros index on banxico.org.mx. To move from §99 to verified at digest.

## 8. What comes next

The trajectory flavor (a) and the long-term vintage join (b) remain the open `OQ-MKT-13` items (both deliberately deferred 2026-08-03); the PD/WACC families now sit in the pulled data ready for the CVA future-work hook (`OQ-CCR-04`); the `OQ-CCR-06` pricer audit was queued as this session's if-time item.

## Related
Explanation of: [[DECISIONS]] (`MKT-NGFS-04..07` extended, `INT-29`, `INT-30`) · contracts: [[DATA_CONTRACTS]] (`DC-MKT-NGFS-2`) · prior: [[2026-08-02_ngfs_transition_channel_explained]] (the rate-only build this extends), [[2026-07-25_mexican_book_swap_explained]] (the book), [[2026-08-01_per_peril_severity_phase_c_explained]] (the `INT-27` null of §4) · Home: [[_INDEX]] · MOC: [[MKT_MOC]]
#arm/mkt #arm/int #type/explanation
