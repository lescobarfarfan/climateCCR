# 2026-07-26 · Explained — the sector-differentiated equity marks (`INT-24`)

Plain-language companion to `INT-24` (`GEN-26`): what `γ_i` is, how each layer is built, what the re-based numbers mean, and where the construction's honest limits are.

## What `γ_i` means

`γ_i` is name `i`'s climate sensitivity *relative to the book*: on every climate event, name `i`'s jump-mark median is the book median times `γ_i` ($0.686\% \cdot \gamma_i$ at the headline calibration), with the severity shape $\sigma$, the adverse sign, the arrival intensity $\lambda$, and the shared event times all unchanged. `γ_i` ranges from $0.127$ (VISTA — its producing assets are in Argentina's Vaca Muerta, so Mexican physical events barely touch it) to $3.985$ (ASUR — three quarters of its 2024 traffic passes through Quintana Roo, the most hurricane-damaged state per capita). A `γ` of 1 means "exactly the old uniform treatment".

## How it is composed — three layers, one number

$\gamma_i \propto \sum_{s,p} G[i,s] \cdot S[\text{sector}_i, p] \cdot D[s,p] / \text{pob}[s]$

**G — where the assets are.** For the geo-resolvable names, hand-collected shares with provenance URLs in `configs/equity_mark_scales.yaml`: 2024 passenger traffic by state for ASUR/GAP (per-airport, from their own disclosures), OMA's published traffic composition, property enumerations for Santa Fe and RLH, POSADAS's four sourced state counts with the undisclosed remainder spread over population shares (`resto_nacional`). Every other name gets population shares — the national proxy tier, whose understatement of concentrated exposure is quantified by `[Bressan2024]` (67–92% of acute-risk VaR in their Mexico study).

**S — what the sector is susceptible to.** An ordinal tier matrix in $[0,1]$ over sector × peril group (ciclón, lluvia, inundación, sequía, incendio forestal, otros). The *ordering* of building sectors in the hydro column is empirical — CNSF hidrometeorológico paid losses by property use put HOTEL as the largest identified commercial use (≈9.4bn MXN, `results/equity_mark_scales/cnsf_uso_peril_shares.csv`) — while the *levels* are literature-tier judgment (`[CEPAL2014]` DaLA sectors, `[ECB2021EconomyWide]`, `[Kruttli2025]`), flagged `[eng]` where judgment dominates. Upsides are deliberately zeroed: reconstruction demand for cement and drought-driven demand for Rotoplas exist but do not belong in an adverse-marks channel.

**D/pob — where climate damage actually lands.** CENAPRED 2000–2024 state × peril damage, deflated to MDP-2025 with the same INPC series as the `INT-17`/`INT-20` calibration (measurement consistency), divided by state population (`[INEGICenso2020]`) so a small, frequently-hit state (BCS) counts as more hazardous *per asset* than a large state with equal total damage.

## The anchor: redistribution, not re-estimation

The scales are renormalized on book equity notionals so that $\sum_i w_i \gamma_i = 1$ exactly. This is the load-bearing design choice: the `INT-17` loss→price scale ($\beta$, $K_{\text{eff}}$) — the only *estimated* link between peso damage and price moves — is untouched. Sector differentiation only decides *which names* carry the book-level shock, in proportions a reviewer can audit cell by cell.

## How to read the re-based numbers

The book-EPE delta band moves from $-11.0/-6.5/-5.6\%$ (uniform) to $-8.74/-5.35/-4.68\%$ (headline / CT anchor / floor), on a baseline book EPE identical to the digit (272,314 MXN — the diffusion draws are bit-for-bit unchanged). Two things happened at once:

**The book-level hit attenuates ≈26% relative.** This is Jensen's inequality, not a lost shock: the anchor fixes the value-weighted *log-mark scale*, but the dollar loss $1 - e^{-\gamma m}$ is concave in that scale, so dispersing $\gamma$ around 1 produces a smaller aggregate expected loss than concentrating everything at $\gamma = 1$. The uniform treatment was the aggressive upper bound `OQ-INT-11` said it was; the sector treatment quantifies exactly how much of it was the uniformity assumption.

**The cross-section reorders the way economics says it should.** Hotel and airport counterparties concentrate the damage (NAID 107's mean EE shift more than doubles, $-5{,}471 \to -12{,}863$ MXN), while diversifier NAIDs relax by multiples (NAID 124: $-3{,}711 \to -527$). For the manuscript: the climate shock to a Mexican book is not a uniform haircut but a concentrated hit on coastal-tourism and airport exposure — which is also why the wrong-way-risk caveat logged in `INT-23` bites hardest exactly there.

## Honest limits (the `OQ-INT-11` residuals)

Every name still moves on every event — only by $\gamma$-scaled amounts — so cross-name correlation is still overstated until events are peril-typed (Phase B). The S-matrix levels are ordinal judgment awaiting a tier-perturbation sensitivity. The industrials still sit on the national proxy tier until their plant/mine states are collected (config-only). And the derived $\gamma$ ordering has not yet been confronted with market data (the Phase C sector event study; a null would itself be reportable, per the `INT-19` precedent).

## Related

Decision: [[DECISIONS]] (`INT-24`) · read-log: [[2026-07-26_sector_marks]] · re-bases: [[2026-07-25_headline_metric_explained]] (the EPE band) · book: [[2026-07-25_mexican_book_swap_explained]] · contracts: [[DATA_CONTRACTS]] (`DC-CCR-SIM-2`, `DC-XWALK-4`) · gates: [[OPEN_QUESTIONS]] (`OQ-INT-11`). Arm MOCs: [[CCR_MOC]] · [[HAZ_MOC]] · Home: [[_INDEX]]

#arm/ccr #arm/haz #arm/int #type/explanation
