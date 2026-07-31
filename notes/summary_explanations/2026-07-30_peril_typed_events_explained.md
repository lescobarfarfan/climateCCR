# 2026-07-30 · Explained — peril-typed jump events, the industrials G, and the S-tier stress (`INT-25`)

Plain-language companion to the `INT-25` decision (`GEN-26`): what the new quantities mean, how to read the re-based numbers, and why the construction is defensible.

## What changed, in one paragraph

Until yesterday, every simulated climate event hit **all 26 equity names at once**, each scaled by its static sensitivity $\gamma_i$ (`INT-24`). That overstates how synchronized the book is: in reality a drought does not damage an airport, and a Chihuahua cement plant barely notices a Caribbean hurricane. Now each event first draws a **peril label** (cyclone, rain, flood, drought, wildfire, other) and only the names whose sector is susceptible to that peril move — by their per-peril sensitivity $c_{ip}$. The average hit each name takes is *unchanged by construction*; what changes is **which events carry it**: concentrated, peril-coherent shocks instead of a uniform drizzle.

## The quantities

**$\pi_p$ (peril mix)** — the probability that an arriving event carries label $p$. Estimated as the *frequency* shares of the same 270 trigger-set rows the headline $\lambda = 19.2857$/yr counts (2002–2015 registry, ≥ 200 MDP-2025): lluvia 34.8%, ciclón 34.1%, sequía 13.3%, inundación 8.5%, otros 8.5%, incendio 0.7%. Frequency — not damage — because $\pi$ describes *arrivals* (the frequency side of the collective model, `[Klugman2019]`); how much damage a peril does is already inside the $\gamma$ components.

**$c_{ip}$ (per-peril scale)** — name $i$'s mark multiplier on a $p$-event: $c_{ip} = \gamma_i^p / \pi_p$, where $\gamma_i^p$ is the peril-$p$ slice of the same G×S×H composition ($\sum_p \gamma_i^p = \gamma_i$ exactly). The division by $\pi_p$ makes the mean come out right: $\sum_p \pi_p c_{ip} = \gamma_i$ to machine precision, so per-name expected impact is exactly the Phase A value — peril typing *redistributes*, never re-estimates (the `INT-24` principle, one level deeper). A zero is structural: ASUR's $c$ on sequía and incendio is exactly $0$ because the S matrix says airports have no drought/wildfire channel. A rare label inflates its $c$ (small $\pi_p$ in the denominator): wildfire events are 0.7% of arrivals, so wildfire-exposed names take large-but-rare hits there, mean unchanged.

**Reading the extremes** — a cyclone event hits ASUR at $c = 11.08$ and HOTEL at $11.44$ (versus their flat $\gamma \approx 4$): all of their climate risk now arrives through the ~34% of events that are cyclones, which is the economically correct picture for Cancún-concentrated assets. GCC's cyclone $c = 0.037$ says a Chihuahua cement maker is almost cyclone-inert; PEÑOLES concentrates on droughts ($c = 2.02$) through mining water risk.

## How to read the re-based band

Book EPE delta (headline / CT-anchor / floor $\lambda$), baseline book EPE 272,314.21 MXN identical to the digit in every generation (the diffusion is untouched — the jump substream isolation doing its job):

| generation | headline | ct_anchor | floor |
|---|---|---|---|
| sector-$\gamma$ (`INT-24`) | −8.74% | −5.35% | −4.68% |
| + industrials G (A′) | −8.68% | −5.33% | −4.66% |
| **+ peril typing (`INT-25`)** | **−8.44%** | **−5.12%** | **−4.50%** |

Two readings. First, the industrials-G step barely moves the book (−0.06pp): the re-tiered names are small book weights and the anchor renormalizes — its real effect is per-name (GRUMA deepens to $\gamma = 0.93$ from its coastal mills; CEMEX/GCC/GMEXICO ease toward their inland asset reality). Second, peril typing eases the book EPE delta ~0.3pp for the same per-name means — the same Jensen/concentration direction as `INT-24`: EE is a mean of *floored* path values, and concentrating a fixed expected shock into fewer, larger, sector-coherent events slightly reduces its bite on a time-averaged floored mean, while making any *single* event far more concentrated (ASUR's cyclone-day loss is ~2.8× its old uniform-event loss).

## Why you can trust it (the robustness answers)

**Ordering robustness** — jittering every nonzero S tier by ±1 ladder step 500 times leaves the $\gamma$ ordering essentially intact (Kendall $\tau$ median 0.899, minimum 0.818; ASUR/HOTEL stay top, VISTA/GCC/CEMEX stay bottom).

**Attribution robustness** — the two documented CENAPRED label caveats (`HAZ-CENAPRED-11`, imported from impactcal-mx): cyclone rows bundle wind+surge+rain (cause-level labels), and from 2016 `INUND` reports under `LLUV`. Merging the fluvial labels (`fluvial_merged`) reproduces the base band to two decimals — the 2016 relabeling is **immaterial**; merging all three hydro labels (`hidro_merged`) moves the headline only to −8.86%. The label-boundary noise cannot overturn the result.

**Concentration robustness** — Nuevo León's cyclone history is ~74% one event (Hurricane Alex 2010, real, ≈ 41.1k MDP-2025). Deleting it (`drop_alex`) moves the book only to −8.31%.

**Level bounds** — wholesale contrast transforms of the ordinal tiers ($S^{1/2}$ / $S^2$) bound the headline at −9.26% / −7.22%: the honest uncertainty of the author-judgment tier levels is about ±1pp around −8.44%, sign and ordering never in doubt.

**Data hygiene** — the 2000–2015 base finally went through the `GEN-27` inspección (new `pipelines/12`): 41 rows with anomalous `danio_mdp/danio_mdd` ratios (Chiapas-concentrated), but the anomaly sits in the *unused* MDD column; the only two rows reaching the trigger set (the Grijalva landslide 2007, TS Larry 2003) carry historically corroborated MDP values, so $\lambda$, the severity fit, and $K_{\text{eff}}$ are uncontaminated.

## Honest limits (logged, not hidden)

Pooled severity understates cyclone event sizes conditional on the label (ciclón subset $\sigma \approx 2.9$ vs pooled $1.21$) — book mean unaffected, tails and the Phase C event-study power affected (`OQ-INT-11` e). State×peril rows enter the fits as independent events though 8 named storms contribute 2–6 rows each — $\lambda\,\mathbb{E}[L]$ invariant, tails not (`OQ-INT-11` f). The same $\pi$ is carried across the three band members ([eng]; the floor regime cannot yield an event-grain mix for non-cyclone perils). And the G layer remains count-weighted public disclosure — the `[Bressan2024]` coarse-proxy caveat still applies to every proxy-tier name.

## Related

Decision: [[DECISIONS]] (`INT-25`, `HAZ-CENAPRED-11`) · read-log: [[2026-07-30_peril_typed_events]] · predecessor: [[2026-07-26_sector_marks_explained]] · contract: [[DATA_CONTRACTS]] (`DC-CCR-SIM-2`) · open: [[OPEN_QUESTIONS]] (`OQ-INT-11`). Arm MOCs: [[CCR_MOC]] · [[HAZ_MOC]] · Home: [[_INDEX]]

#arm/ccr #arm/haz #arm/int #type/explanation
