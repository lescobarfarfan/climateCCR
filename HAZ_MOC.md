# HAZ_MOC — Physical hazard & insurance loss (the estimation engine)

> Map of content for the **HAZ arm**: Mexican hazard/loss pipelines (CNSF, IBTrACS, CENAPRED,
> drought), CLIMADA subnational impact-function calibration, and the compound-Poisson/Cox loss
> models. Hub note. Home: [[_INDEX]].

**Role in the machine (`INT-11`):** the **estimation engine for the climate↔price link** — it produces
the intensity `λ` and the per-event **impact/jump-mark** that drive the climate shock. Those feed
`processes.jumps`, which injects the shock into the [[MKT_MOC|MKT]] diffusions inside the
[[CCR_MOC|CCR]] framework (the climate jump channel, `INT-10`).

## Decisions → [[DECISIONS]]
- CNSF cleaning: `HAZ-CLEAN-CNSF-01..11` (`NU`→No Disponible; `MONTO PAGADO`; 32 states; peril taxonomy).
- CNSF pipeline: `HAZ-SCRAPER-CNSF-01..08` (orchestrator; year regex; autos `.mdb`→3 CSVs).
- IBTrACS: `HAZ-IBTRACS-01..11` (Vmax-anchored Holland; K&D decay; wind-field > buffer; covariates).
- CENAPRED: `HAZ-CENAPRED-01..09` (A/B/A′ structures; multi-state kept as one record).
- CLIMADA: `HAZ-CLIMADA-01..12` (subnational impf; `v_thresh=25.7`, `v_half=74.7`; LitPop; PyMC; multi-peril union).
- Drought: `HAZ-DROUGHT-01..07` (SPEI primary; idempotent CDS downloads).
- Source tiers: `HAZ-SOURCES-01..03` · stochastic loss/pricing: `HAZ-STOCH-01..03`.

## Data contracts → [[DATA_CONTRACTS]]
- `DC-HAZ-CNSF-1..5` consolidation+cleaning · `DC-HAZ-IBTRACS-1..4` cyclone panels.
- `DC-HAZ-CENAPRED-1..3` (the four outputs) · `DC-HAZ-CLIMADA-1..5` calibration unit.
- `DC-HAZ-DROUGHT-1..4` drought pipeline.
- Crosswalks: `DC-XWALK-1` state↔storm (`nombre_evento`→`SID`) · **`DC-XWALK-4` the jump channel** · `DC-XWALK-2` CNSF↔CENAPRED penetration.

## Open questions → [[OPEN_QUESTIONS]]
- `OQ-HAZ-01` CDMX discretization · `OQ-HAZ-03` `MONEDA`/FX (closable via MKT) · `OQ-HAZ-06` validate covariates (Odile/Otis).
- `OQ-HAZ-07/08/09` references & source access · `OQ-HAZ-10` timestep convergence.
- `OQ-HAZ-12` stochastic-model calibration · `OQ-HAZ-13` parametric pricing · `OQ-HAZ-14` remaining CNSF sectors.
- Estimation core (shared): `OQ-INT-07` jump-mark / impact estimation.

## Notes (import under `notes/`)
- Theory (`notes/theory/`): [[referencias_riesgo_catastrofico]] (master), [[diseno_calibracion_funciones_impacto_mexico]] (CLIMADA design).
- Sources (`notes/sources/`): [[cenapred]], [[ibtracs]].
- Pipelines (`notes/pipelines/`): [[README_scraper_cnsf]], [[README_sequia]], [[DISENO_pipeline_autos_CNSF]], [[Guia_MDB_Automoviles_CNSF]].

## Wires to the other arms
- Sends **`λ` + impact** to [[CCR_MOC]]/`processes.jumps` (`DC-CCR-SIM-2`, `DC-XWALK-4`) — the climate shock.
- Loss panels → `risk.loss`; shares `clave_mpio` hazard-source questions with [[MKT_MOC]] (`OQ-MKT-09`).

#arm/haz #type/workflow
