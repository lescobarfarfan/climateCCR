# The fase matrix, the three-flavor table, and the spread leg, explained (2026-09-08)

Session decisions `INT-35` and `INT-36`, closing `OQ-INT-12`. This note explains what the full phased matrix says, what the new spread schedule is, how to read every number produced today against the other two application flavors, why the CVA sign flips under fase, and where the interpretation limits sit. Companion read-log: [[2026-09-08_fase_matrix_spread_leg]]; the operational recipe is [[ngfs_application_flavors]].

## What ran

Seven fase cells (HWTP and SWUC × the three λ bands, DAPS_NAM transition-only) on the **unshocked** Mexican book with the `pipelines/22` fragments injected into both legs, plus the CT-bridge λ(t) rider in the plain world — twice: once before the spread leg (the archived `_sin_spread` state) and once after it (the full-leg state, the numbers below). All on seed 233423, the `largo` grid and the canonical env, every artifact manifested. The readout is now the canon's own metric (`viz.epe_summary` book EPE, `INT-23`), not the proxy of the 2026-08-27 smoke, so these are manuscript numbers.

## The three-flavor table and how to read it

Transition-only book-EPE delta vs the unshocked jump-off book (255,278.60 MXN):

| Scenario | nivel (t=0 peak) | trayectoria (maturity-dated) | fase (in-simulation path) |
|---|---|---|---|
| HWTP | −5.73 % | −1.50 % | −4.57 % |
| SWUC | −8.18 % | −1.25 % | −6.63 % |
| DAPS_NAM | −20.03 % | +0.16 % | −7.37 % |

Read each column as an *application convention*, not a different scenario. Nivel applies the worst point of every path at once and holds it; trayectoria reprices each cashflow at the shock prevailing at its own maturity, which looks through transient peaks; fase applies the path as it arrives inside the simulation. Fase sits between the two for the three reasons recorded in `INT-34`: the phased path averages below its peak over the exposure-weighted horizon; the in-simulation rate leg carries the policy anchor only, propagated through the single-factor $B(t,T)/\alpha$ loading, with no sovereign long anchor; and — now closed — the credit-spread leg. The spread leg roughly doubled the fase transition cost on HWTP (−2.57 → −4.57 %) and tripled it on DAPS_NAM (−2.46 → −7.37 %), because DAPS_NAM's published transition is equity- and spread-led while its policy-rate path is economically nil. Nivel's DAPS_NAM −20 % is the signed-peak fiction the fase path recovers from: the −14 % equity shock is kept forever in nivel and mean-reverts by 2030 in fase.

**Ruling taken on these numbers (user, 2026-09-08):** nivel remains the headline transition convention, as `MKT-NGFS-09` already fixed for trayectoria — the peak-severity stress-test practice of the supervisory exercises — and fase is reported as the phased robustness flavor. The manuscript object is this table, not one column.

## The physical channel under fase: separability, again

Jump-within (the scenario run's own jump-on vs jump-off) reads HWTP −9.06 / −5.53 / −4.95 % and SWUC −9.18 / −5.61 / −5.02 % (headline / CT anchor / floor) against the unshocked band −8.93 / −5.44 / −4.86 %. The physical channel's marginal effect barely depends on the transition state, even with the full spread leg in — the `INT-31` overlay-invariance now demonstrated on the canon metric in-simulation. Reporting consequence: physical and transition channels stay approximately additive on this book, so the headline physical band (`INT-23`) does not need a per-flavor restatement.

## The per-pillar profile and the 0D rule

Under HWTP the whole-book EE delta is −4.52 % at 1D (the raw-basing catch-up: the delta already accumulated by the valuation date lands at the first step), deepens to −6.72 % at 2Y as the path climbs, and shrinks to −0.77 % at 5Y as the book runs off. The 0D pillar is zero-delta by construction — the `INT-33` pin — and the readout now *asserts* it per netting set: any 0D delta in a fase readout is a bug signal, not a result. The book-EPE metric is unchanged by this rule because the 0D pillar carries about $2.7 \times 10^{-5}$ of the 50-year trapezoid weight; the rule bites only in per-pillar tables and figures, which start at the first post-0D pillar.

## The spread schedule: what the new quantity is

The fragment now carries, per issuer, a path $\Delta s(t)$ of credit-spread deltas in decimal — the excl-policy `corporate_bond_spread_adjustment` of the issuer's GEM-E3 sector, pp/100, on the same Act/365 axis, raw basing and 2031.0 clip as the other channels (5 points, held beyond). At each reporting date the bond pricers discount all remaining cashflows with $s_{\text{eff}}(t) = \max(s_0 + \Delta s(t), 0)$, where $s_0$ is the book's issuance sobretasa or discount margin: a flat spread term structure per date, exactly the semantics of the nivel `spread + delta` rewrite, only time-indexed. Three properties make it a clean extension rather than a new pricing convention: at t=0 and for issuers the fragment does not name the pricer receives the original spread object, so absent or zero schedules price byte-identically; a constant path reproduces the nivel spread state at every post-0D date; and the floor at 0 matches the nivel leg (CFE's two bonds floor under HWTP in both flavors, because the Power Supply spread adjustment is negative). What it is *not*: a forward-integrated spread (rejected — it would mix path timing with a different discounting convention) and not a stochastic spread (per-path credit dynamics would need a credit risk factor; the `ponytail:` note in both pricers records that ceiling).

Magnitudes for orientation: HWTP moves PEMEX's sector (Crude Oil) from +4.34 pp at valuation to +9.59 pp by 2030 and CFE's (Power Supply) from −2.46 to −3.00 pp; SWUC starts at 0 and reaches +12.09 pp on its worst sector; DAPS_NAM starts at +6.30 pp and recovers to +0.18 pp.

## The CVA sign reversal

CVA with LGD 0.60 (BOOK): base 514,270 MXN; fase HWTP 532,528, SWUC 557,535, DAPS_NAM 539,319 — every fase transition leg *raises* CVA, where the nivel legs netted to −6.6k / −1.5k / −64.5k. The decomposition explains it exactly: the credit channel (the CLIMACRED PD path) is the same in both flavors, +57.0k for HWTP; the exposure channel is −26.8k under fase against −48.9k under nivel; the interaction is −11.9k. A phased exposure fall a little more than half of nivel's cannot offset the PD path, so the net turns positive (+18.3k). This is the `INT-23`/`INT-31` wrong-way caveat with the opposite sign: under nivel the bank's shrinking claims almost exactly cancel the rising default probability, under fase they do not. The spread channel's own CVA contribution is read by subtraction of the archived pre-spread legs: −19.1k / −28.3k / −49.3k (wider cebur spreads lower bond values, hence exposure, hence CVA).

## The λ(t) riders

In the plain world the registry rider moves the book-EPE climate shift from −8.93 % to −9.31 % and the CT bridge to −8.97 % — a 43 % terminal intensity rise buys 0.4 pp because the exposure integral feels the *time-averaged* intensity over the first years, which the new `intensity_paths` figure shows directly. Arrivals trending, the `HAZ-STOCH-06` ambiguity, is a quantified footnote to the physical band; the riders were deliberately not crossed with the fase scenarios (jump-within is transition-invariant, so the crossing would only replicate the separability result).

## Limits to state when citing these numbers

The fase rate leg has no sovereign long anchor (single-factor propagation, `INT-33`), so fase transition deltas are model-consistent rather than anchor-blended and structurally milder than nivel on the rate side. The spread schedule is deterministic and applied as a level per date. The PD paths in the CVA legs are flavor-invariant by construction (CLIMACRED publishes one path per scenario), so the CVA comparison isolates the exposure side. The raw-basing catch-up means HWTP's and DAPS_NAM's "phase-in" opens with a one-step jump of the already-accumulated delta, reported alongside every fase result. Two housekeeping notes from the session, not results: six pre-existing files fail `black --check` under the env's black and were left untouched, and the env's ruff and the pre-commit ruff disagree on first-party import grouping — the hook is the gate the committed files follow.

## Related
Decisions: [[DECISIONS]] (`INT-35`, `INT-36`, `INT-33`, `INT-34`, `INT-31`, `INT-23`, `MKT-NGFS-09`, `CCR-RISK-06`) · Read-log: [[2026-09-08_fase_matrix_spread_leg]] · Pipeline recipe: [[ngfs_application_flavors]] · Prior explanation: [[2026-08-27_fase_producer_results_explained]] · Arms: [[CCR_MOC]] · [[MKT_MOC]] · Home: [[_INDEX]]
#arm/int #type/explanation
