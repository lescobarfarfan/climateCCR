# The CVA extension, explained (OQ-CCR-04 → built)

**Session 2026-08-12.** Two coupled changes landed together: the `OQ-CCR-06` audit **corrected the
IRS pricer** (see [[PRICING_INTERNALS_AUDIT_2026-08-12]]) — which re-based every EE number — and the
CCR arm gained its **unilateral CVA** on top of the re-based EE trajectories. Read the numbers below
as the post-audit state.

## What was built

`risk/ccr/xva.py` (the reporting seam — the engine is untouched, the `viz.epe_summary` /
`with_supervisory_pfe` pattern) + `pipelines/21_cva_readout.py` + `configs/cva.yaml`:

$$\mathrm{CVA} = \mathrm{LGD}\sum_i \tfrac12\big(EE_{i-1}DF_{i-1} + EE_i DF_i\big)\,\big(S_{i-1}-S_i\big)$$

- **EE** — the stored uncollateralised profiles (`ee_pe_climate_shift.csv`, per NAID, 12-point B3
  grid), already floored path-wise (`CCR-RISK-03`). `[Gregory_xVA]` `[PykhtinZhu2007]`
- **DF** — deterministic, off **each leg's own** pricing curve (base book vs the NGFS-shocked
  overlay curves), year fractions at the `viz.epe_summary` 365.25 convention.
- **S(t)** — piecewise-exponential survival from annual hazards `λ_y = −ln(1 − PD_y)`;
  `PD_y` = CLIMACRED `baseline_pd` (+ `pd_adjustment|sector` on scenario legs), calendar-year
  segments, flat beyond 2030. `[Battiston2025CLIMACRED]`
- **LGD** — 0.60 headline; 0.45 / 0.75 sensitivity columns (CVA is exactly linear in LGD).

## The headline numbers (book v2, corrected pricer, LGD 0.60)

| leg | BOOK CVA (MXN) | ΔCVA vs base | exposure ch. | credit ch. | interaction |
|---|---|---|---|---|---|
| base | 514,191 | — | — | — | — |
| jump headline / CT / floor | 465,369 / 484,638 / 487,787 | −48.8k / −29.6k / −26.4k | = ΔCVA | 0 | 0 |
| NGFS HWTP (jump-off) | 507,433 | **−6.8k** | −49.0k | **+57.0k** | −14.7k |
| NGFS SWUC (jump-off) | 512,327 | **−1.9k** | −75.0k | **+98.4k** | −25.3k |
| NGFS DAPS_NAM (jump-off) | 449,274 | −64.9k | −131.9k | +97.2k | −30.2k |

**How to read it.** Base CVA ≈ 2× book EPE (255,217 MXN) because the country-level CLIMACRED PD
(11.55%/yr at t0) accumulates ~30–40% default mass over the exposure-heavy first years. The
**physical (jump) legs** move CVA through exposure alone — ΔPD ≡ 0 there, honestly stated: the HAZ
channel carries no PD response in scope. The **transition legs are the thesis punchline**: book
EPE *falls* under every NGFS scenario (the bank is net long equity optionality and cebur credit,
`INT-31`), so an exposure-only reading says climate transition *reduces* counterparty risk — but
the same states raise counterparty PDs, and the credit channel (+57k / +98k) almost exactly offsets
the exposure channel (−49k / −75k): **net transition CVA is nearly flat (−1.3% / −0.4% of base)
where the EPE delta reads −5.8% / −8.3%.** That is the `INT-23`/`INT-31` wrong-way caveat,
quantified. The **interaction term** (−14.7k / −25.3k / −30.2k) is the exact bilinear cross term —
negative because exposure shrinks precisely in the states where default mass grows.

## The credit-triangle cross-check (`pd_crosscheck.csv`)

Cebur discount margins (65–430 bp) imply 1y PDs of ~1.1–7.0% via `λ = s/(1−R)`, R = 0.40 — i.e.
**0.13–0.45× the CLIMACRED country PD**. That is the P-vs-Q wedge in one table: CLIMACRED PDs are
physical-measure structural-model outputs; market-implied (issuance-spread) default intensities are
several times smaller. The headline CVA is therefore a **scenario/real-world CVA**, defensible
under proxy-data supervision practice (`[ECB2020Guide]`), not a market-implied price — the
manuscript must say so, and the LGD/PD-level uncertainty dwarfs the LGD sensitivity band
(385,643 / 514,191 / 642,739 MXN at LGD 0.45/0.60/0.75).

## Known limits (deliberate)

- **Country-level BAU PD**: the BAU cross-section of CVA is EE-driven; sector differentiation
  enters only through scenario `pd_adjustment` (the `[Bressan2024]` coarse-proxy honesty note).
- **Deterministic discounting** off today's (or the scenario's) curve — the rate–exposure
  covariance and any path-level wrong-way coupling (jump-linked default intensity) are the
  documented **stochastic-WWR future work**; `sector_overrides` in `configs/cva.yaml` assigns PD
  sectors to book names outside the NGFS shock crosswalks (BACHOCO) without touching shock scope.
- **Unilateral only** — the hypothetical Mexican bank has no credit identity for a DVA leg.
- Channel separation per `INT-29` holds: DAPS_NAM appears jump-off only.

## Related

Producers: `pipelines/21_cva_readout.py` (`results/cva/`: `cva_summary.csv`,
`cva_decomposition.csv`, `pd_crosscheck.csv`) · module `risk/ccr/xva.py` · tests
`tests/risk_ccr/test_xva.py`. Session read-log: [[2026-08-12_ccr_audit_cva]] (digest).
Reads with: [[PRICING_INTERNALS_AUDIT_2026-08-12]] · [[2026-07-25_headline_metric_explained]] ·
[[DECISIONS]] · [[DATA_CONTRACTS]] · [[CCR_MOC]] · Home: [[_INDEX]]
#arm/ccr #type/explanation
