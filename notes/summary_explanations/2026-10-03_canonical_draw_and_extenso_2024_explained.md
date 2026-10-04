# The canonical draw, the numerics pin, and the 2024 EXTENSO refresh, explained (2026-10-03)

Session decisions `GEN-37`, `CCR-SIM-02`, `HAZ-CENAPRED-13`, `HAZ-STOCH-07`, with the verbatim re-applications of the `INT-19` and `INT-27` gates and the two-stage re-base recorded in `INT-23`. This note explains what broke, what was changed and what was not, how to read the new numbers, and — at the user's request — what the Monte-Carlo precision caveat on tail quantiles means in practice and what the seemingly small post-2024 changes imply at institutional scale. Companion read-log: [[2026-10-03_numerics_pin_cenapred_2024]].

## What broke on 2026-09-24, and why it was not a bug in the results

The engine simulates correlated risk factors by drawing independent standard normals and mixing them with a square root of the correlation matrix. Any matrix $A$ with $AA^\top = C$ gives the same joint distribution, so the choice of $A$ is a convention, not a model assumption. Until this session the mixing came from SciPy's `multivariate_normal`, which uses numpy's SVD: $A = U\sqrt{S}$ with the singular values sorted in decreasing order.

The PIMPA fixture correlation matrix is not positive semidefinite and is repaired first (Rebonato–Jaeckel). After the macOS 27 update that repair, computed by Apple's Accelerate library, returned two diagonal entries one ulp apart ($0.9999999999999998$ and $0.9999999999999999$). For the two-factor netting sets whose factors are uncorrelated those two entries *are* the singular values, and their order decides which stream of normals drives the rate and which the share. The order flipped, the streams swapped, and the share path became the realization the rate had had before ($\mathrm{corr}(\Delta\log S_{\text{new}}, \Delta r_{\text{golden}}) = +1.000000$ at every step). Both outcomes are valid samples of the same law; the goldens simply lock one of them.

The fix replaces the SVD mixing by the Cholesky factor $L$ ($LL^\top = C$, lower-triangular with positive diagonal). $L$ is unique and depends continuously on $C$, so an ulp in $C$ gives an ulp in the increments and nothing can flip. The normals themselves are untouched (the `CCR-MIG-08` stream), which is why both goldens reproduce to $10^{-14}$ without regeneration: for uncorrelated factors $L$ is diagonal and assigns stream $i$ to factor $i$, the assignment the goldens were born with.

For the Mexican book the 28×28 correlation is dense and never degenerate, so the swap could not have happened there; but $L \neq U\sqrt{S}$, so the new draw is a different, equally valid set of 10,000 paths. That is why Stage 1 moved the baseline book EPE by +0.15 % with every config untouched.

## What the pin changes, and what it does not

The numerical libraries were PyPI wheels that, on macOS, use the operating system's BLAS (Accelerate). The OS is not a pinned package, so the environment was pinned in name only. The canonical env is now built from a lockfile of conda-forge packages on OpenBLAS, where the BLAS is a versioned package like any other; a GitHub Actions matrix runs the suite on Linux and macOS from the same lockfile; the run manifest records the BLAS backend, the environment prefix and whether the git tree was dirty.

The nuance recorded in `GEN-37`: the old SVD draw *also* fails the goldens under OpenBLAS, so the pin alone would not have restored them. The pin buys stability against future OS updates; the canonical draw is what makes the engine indifferent to the BLAS build.

## How to read the re-base (two stages, each against its own predecessor)

| Readout | `CCR-RISK-07` state | Stage 1 — numerics only | Stage 2 — data refresh (final) |
|---|---|---|---|
| Baseline BOOK EPE (MXN) | 255,278.60 | 255,670.01 (+0.15 %) | 255,670.01 (jump-off legs byte-identical to Stage 1) |
| Band EPE shift (headline / CT / floor) | −8.93 / −5.44 / −4.86 % | −8.97 / −5.47 / −4.89 % | −8.97 / −5.54 / −4.99 % |
| BOOK EEPE shift | −2.13 / −1.53 / −1.39 % | −2.20 / −1.57 / −1.43 % | −2.20 / −1.59 / −1.46 % |
| Riders (registry / CT bridge) | −9.31 / −8.97 % | — | −9.36 / −9.03 % |
| Nivel transition HWTP / SWUC / DAPS_NAM | −5.73 / −8.18 / −20.03 % | — | −5.72 / −8.16 / −20.01 % |
| Trayectoria transition | −1.50 / −1.25 / +0.16 % | — | −1.49 / −1.23 / +0.16 % |
| Fase transition | −4.57 / −6.63 / −7.37 % | — | −4.57 / −6.62 / −7.37 % |
| CVA base BOOK (LGD 0.60) | 514,270 | — | 515,139 |
| 1-year book-exposure q99 (MXN) | 3,113,482 → 2,773,089 (−10.9 %) | — | 3,433,541 → 2,999,986 (−12.6 %) |
| Compound-Poisson annual S q99 (MDP-2025) | 93,588 / 60,877 / 48,569 | — | 93,588 / 61,905 / 50,653 |

Stage 1 isolates the numerics: a new realization of the same model moves the band by at most 0.04 pp. Stage 2 adds the data. The headline leg does not move at two decimals because its λ and severity are the 2002–2015 registry, untouched by a 2024 report, and the sector scales γ moved by at most 0.6 %. The CT anchor deepens from −5.47 to −5.54 % because three 2024 cyclone rows (Ileana/Sonora, Alberto/Veracruz, Nadine/Chiapas) lift the bridge λ from 9.9565 to 10.0870, a 1.3 % increase in arrivals with the registry marks unchanged. The floor deepens from −4.89 to −4.99 % because John's revised Guerrero damage (6,659 → 12,910 MDP) lifts the report-regime severity (median 1,274 → 1,287 MDP-2025, σ 1.036 → 1.056) with the same 65 events, so λ is unchanged. The transition legs are jump-off and cannot see the data refresh; they moved only in Stage 1, by at most 0.02 pp. The CVA base moved +0.17 % through exposure alone, since PDs are scenario inputs and unchanged. Both null gates (`INT-19` rates, `INT-27` equities) returned FALLA with essentially the same statistics, so H1 stands as written.

## The Monte-Carlo precision caveat on tail quantiles — what it means and what it entails

Every metric the engine reports is a sample statistic of $n = 10{,}000$ simulated paths. EPE is a time-average of means, $\mathrm{EE}(t) = \tfrac{1}{n}\sum_i \max(V_i(t), 0)$, and the standard error of a mean is $\sigma_V/\sqrt{n}$ — a fraction of a percent of the level. That is why a new realization moved EPE by 0.15 %.

A 99 % quantile is an order statistic. On 10,000 paths it sits between the 100th and 101st largest values, so it is decided by the roughly one hundred most extreme paths. Its standard error is approximately $\sqrt{p(1-p)/n}\,/\,f(q_p)$, where $f(q_p)$ is the density of the exposure distribution at the quantile; for a heavy right tail that density is small and the relative error is several percent even when the mean is tight. The observed move of the 1-year book-exposure q99 between two equally valid realizations was +10 % (3.11 M → 3.43 M MXN) with the same seed structure and the same model. Nothing economic happened; the hundred largest paths were different paths.

What this entails for the manuscript and for anyone using the numbers: (i) report tail *levels* (PFE99, the aggregate-loss q99) with a Monte-Carlo uncertainty — a bootstrap or order-statistic interval, or the spread across a few seeds — and never with three significant figures or as byte-identical across environments; (ii) report climate *deltas* of tail quantiles as paired, same-seed differences — the jump-on and jump-off legs share the diffusion stream, so the delta is far more precise than either level, and the −12.6 % now against −10.9 % before is one such delta moving within its own precision, same sign and same order; (iii) conclusions that rest on means and paired deltas — the EPE band, EEPE, the CVA decomposition, the H2 and H3 claims — are robust at reported precision, while a conclusion resting on a tail *level* is robust in sign and order of magnitude only; (iv) if a tighter tail is needed, increase the number of paths (the error falls like $1/\sqrt{n}$, so ten times the paths buys one extra digit) or use the variance-reduction toolkit already listed in `MKT-MC-01`; (v) `GEN-30`'s rule that "conclusions hold at reported precision" is now stated as applying to means and paired deltas, not to tail levels.

## What the seemingly small post-2024 changes imply at institutional scale

The numbers are small because the book is small. The hypothetical book has an EPE of 255,670 MXN and a CVA of 515,139 MXN; the engine is linear in notionals, so the portable results are the percentages, not the pesos. A +0.17 % CVA move on a CVA reserve of MXN 10 bn is MXN 17 M; the floor leg's extra −0.10 pp on a book carrying MXN 50 bn of expected positive exposure is MXN 50 M of exposure that the preliminary report did not show. The thesis book cannot say what any real institution would lose; it says by what fraction a book of this composition moves, and that fraction is what an institution would apply to its own notionals.

Thresholds turn continuous moves into discrete outcomes. Regulatory capital is $\alpha \cdot \mathrm{EEPE}$; counterparty limits are set on PFE; collateral calls and rating triggers fire at fixed levels. A change of 0.1 pp in an input that sits near a limit or a trigger produces a jump in the outcome — a breach, a call, a downgrade — not a 0.1 pp change in the outcome. At institutional scale the question is how many counterparties sit near a threshold, not what the average move is; the per-counterparty grid matters more than the book total.

Data vintage is parameter risk. The preliminary 2024 report understated the year's losses by 43 % (14,434.9 against 20,679.95 MDP) and John/Guerrero by half. A calibration refreshed on the latest preliminary year therefore runs low until the final report lands, and systematically so: preliminary disaster totals are revised upward far more often than down. Under a living calibration (`GEN-31`) this is a reporting-lag bias to disclose and to backtest, exactly as a model-risk item, and the two-stage re-base is the discipline that keeps data moves separable from numerics moves so each can be attributed.

The moves are concentrated. The book-level γ moved by at most 0.6 %, but it moved up for the hotel and airport names on the Guerrero–Oaxaca–Veracruz coast (HOTEL +0.6 %) and down for inland industrials (ASUR, GAP and the cement names −0.5 %). An institutional book concentrated in the affected states would see a larger move on those counterparties than the book average suggests; the per-counterparty grid (`GEN-28`) is where the effect lives, and concentration limits are where it would bind first.

Wrong-way risk scales with it. The CVA moved through exposure alone here because PDs are scenario inputs; at institutional scale the credit channel (the CLIMACRED PD paths) dominates, and the fase results already show the sign of the transition CVA flips with the application convention. A small exposure move is dwarfed by convention choices, which is the argument for reporting all three NGFS flavors rather than one.

Tail statistics at scale inherit the sampling error of the previous section. A 10 % swing of a PFE-type level on a MXN 50 bn limit book is MXN 5 bn of apparent headroom appearing or vanishing with the seed. Production systems resolve this with more paths and variance reduction; the thesis must present tail levels with their uncertainty and lean on means and paired deltas for its claims.

## Limits to state when citing this session

The precision caveat is estimated from one realization change, not from a seed study; a short multi-seed run would give the actual interval. The institutional-scale readings are mechanisms — linearity, thresholds, vintage bias, concentration, sampling error — not estimates for any real portfolio. The sensitivities `pipelines/11` and `14` still sit on the 2026-08-01 state. The EXTENSO 2024 portal URL is unconfirmed in provenance (`url` null, sha256 recorded).

## Related
Decisions: [[DECISIONS]] (`GEN-37`, `CCR-SIM-02`, `HAZ-CENAPRED-13`, `HAZ-STOCH-07`) · Read-log: [[2026-10-03_numerics_pin_cenapred_2024]] · Prior explanation: [[2026-09-14_hypotheses_and_scope_explained]] · Arms: [[CCR_MOC]] · [[HAZ_MOC]] · [[MKT_MOC]] · Home: [[_INDEX]]
#arm/int #type/explanation
