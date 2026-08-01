# 2026-08-01 · Explained — per-peril severity, the Phase C null, and the environment lesson

Plain-language companion to `INT-26` / `INT-27` / `GEN-30` (`GEN-26` series). What was calibrated, what the numbers mean, and why the choices are justified.

## What per-peril severity is (`INT-26`)

Until today every climate event, whatever its peril label, drew its size from one pooled lognormal (median 905.53 MDP-2025, $\sigma = 1.2106$). Now a cyclone-labeled event draws from a cyclone lognormal, a drought event from a drought lognormal, and so on: per label $p$ we fit the dispersion $\sigma_p$ on the label's own rows of the trigger set and set its median to $m_p = m\,e^{(\sigma^2 - \sigma_p^2)/2}$.

That median formula is the whole trick. A lognormal's mean is $m\,e^{\sigma^2/2}$, so this choice makes **every label's mean equal to the pooled mean** — cyclone events get fatter tails (higher $\sigma_p$ → occasional huge draws) but not a bigger average, drought events get thinner tails but not a smaller average. Because all the `INT-24/25` identities ($\Sigma w\gamma = 1$, $\Sigma_p \pi_p c_{ip} = \gamma_i$) are statements about means, they all keep holding *exactly*: only the shape of the severity distribution conditional on the label changes.

Why pin the means at all? Because the cross-peril *mean* differential is already in the model: $c_{ip} = \gamma_i^p/\pi_p$ divides a damage share by a frequency share, so rare-but-big perils already hit harder per event. Letting the label also choose a bigger mean severity would count the same fact twice.

## The parameters obtained, and the surprise

Registry trigger set ($\geq 200$ MDP-2025 real, 2002–2015): ciclón $\sigma = 1.3317$ ($n = 92$), inundación $1.2249$ ($23$), lluvia $1.0470$ ($94$), otros $0.8682$ ($23$), sequía $0.8102$ ($36$), incendio pooled ($n = 2$ — too thin to fit, kept at $1.2106$ by the `min_events` rule). Report regime (floor config): ciclón $1.0284$ ($51$), lluvia $0.9616$ ($11$), everything else pooled because the post-2016 non-cyclone stream is censored.

The surprise: `INT-16` had fit ciclón at $\sigma \approx 2.9$ and the open question warned cyclone sizes were understated. That $2.9$ came from *all* cyclone events, most of them tiny; once the real-terms threshold removes the sub-threshold mass, the surviving cyclone events are far more homogeneous. The lesson (a `[Klugman2019]` staple): severity fitted after a threshold is the *conditional* severity, and that is the right object here — the jump channel only ever draws events that cleared the trigger.

## How to read the re-based numbers

Book EPE delta band: $-8.36\,/\,-5.05\,/\,-4.51\%$ (headline / CT anchor / floor), versus $-8.44\,/\,-5.12\,/\,-4.50$ with pooled severity. The move is second-order by design — means are preserved, and EPE is close to linear in the mark mean; what remains is a small convexity effect through the exposure floor $\max(V, 0)$. Per name it redistributes exactly as the $\sigma_p$ table says: cyclone-concentrated names ease a little (ASUR's EPE shift by $+65$ MXN — its label now has a *lower median* with the same mean), thin-$\sigma$ drought-takers deepen a little (sequía's mean-matched median is $1.499\times$ pooled), and headline PE99 tails ease $\approx 2\%$. If a future reader sees a large band move attributed to severity typing, something is wrong — the construction forbids it.

## What Phase C tested and what FALLA means (`INT-27`)

The claim under test: on cyclone events, high-$c_{\text{ciclón}}$ names (ASUR, HOTEL) should lose more than low-$c$ names (GCC, VISTA). We measured each name's abnormal return (market model against the IPC on log adjusted closes) over the five business days after each of 63 cyclone episodes (2002–2024, Otis included), averaged per name, and asked whether that average *orders* by $c_{\text{ciclón}}$ (Kendall $\tau$, one-sided $H_1{:}\ \tau < 0$). The gate — fixed and committed before running, so the verdict could not be steered — required the episode-bootstrap $P(\tau^* \geq 0) < .05$.

Result: $\tau = +0.198$ — the *wrong sign*, weakly — with $p_{\text{boot}} = .94$; every window agrees, the top-vs-bottom tercile spread is $+0.43\%$, and dropping Otis (the largest episode, 91,540 MDP-2025) changes nothing. **FALLA.**

Interpretation, carefully: this does **not** say ASUR is not more cyclone-exposed than GCC — the footprints, the CENAPRED damage record, and the CNSF paid-loss shares say it is. It says Mexican *daily equity prices* do not express that differential around events, exactly as `INT-18/19` found for sovereign yields over 23 years. The marks therefore keep their exposure-based justification, and the manuscript reports the validation attempt as a bounded null rather than a confirmation — which is what a pre-registered design is for. The mildly positive $\tau$ at longer windows (reconstruction demand? insured-recovery pricing?) is noted as a diagnostic curiosity only.

## The environment lesson (`GEN-30`)

A re-run reproduced every percentage but not the bytes: the session had run under the machine's default `thesis` conda env (numpy 2.4.3) instead of the project's canonical `climateCCR` env (numpy 2.4.6 — the one every July manifest records). No package had changed anywhere; the *selection* had. Effect: baseline book EPE $272{,}314.21 \to 272{,}215.61$ ($-0.036\%$) from floating-point kernel differences, while every reported EPE delta held to 2 decimals. Everything was re-materialized under the canonical env (baselines byte-identical again). Two takeaways: byte-identity claims are meaningful only *within* a pinned environment, and the `GEN-06` manifests — which record `packages` and `python_version` per run — are what turned a mystery into a five-minute diagnosis.

## Related

Decisions: [[DECISIONS]] (`INT-26`, `INT-27`, `GEN-30`) · read-log: [[2026-08-01_per_peril_severity_phase_c]] · contract: [[DATA_CONTRACTS]] (`DC-CCR-SIM-2`) · predecessors: [[2026-07-30_peril_typed_events_explained]] · [[2026-07-26_sector_marks_explained]]. Arm MOCs: [[CCR_MOC]] · [[HAZ_MOC]] · Home: [[_INDEX]]

#arm/ccr #arm/haz #arm/int #type/explanation
