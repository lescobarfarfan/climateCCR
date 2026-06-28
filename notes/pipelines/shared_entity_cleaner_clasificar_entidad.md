# Shared entity cleaner — `limpieza_cnsf.clasificar_entidad`

> The single canonical normaliser for Mexican federal-entity names across the HAZ pipelines.
> One source of truth for geography (`DC-CONV-5`); imported by more than one source, never re-implemented.

## What it is

`clasificar_entidad(x) -> (categoría, canónico)` lives in
`src/climateCCR/data/hazard_mx/cnsf/limpieza_cnsf.py`. It maps any raw entity label to a
`(categoría, canónico)` pair where `categoría ∈ {estado, extranjero, no_localizado, desconocido}`:

- typos auto-remapped (`Quitana Roo` → Quintana Roo; `Distrito Federal` → Ciudad de México) — `HAZ-CLEAN-CNSF-02`;
- `NU` / unlocated → `No Disponible`, **not** assigned to any state — `HAZ-CLEAN-CNSF-01`;
- `Extranjero` / `No aplica (exportación)` excluded from the state panel — `HAZ-CLEAN-CNSF-03`;
- unrecognised labels → `desconocido`, flagged for manual review, **never blind-assigned** — `HAZ-CLEAN-CNSF-04`.

**Guarantee:** 32 federal entities per year after correction (`DC-HAZ-CNSF-5`, `HAZ-CLEAN-CNSF-05`).

## Who consumes it (shared by design — `DC-CONV-5`)

- **CNSF** value-level cleaning (`consolidar_cnsf.py`, `procesar_autos_cnsf.py`) — the home module.
- **CENAPRED** processing (`cenapred/procesar_cenapred.py`) — uses the *same* CNSF standard so the
  insured (CNSF) and total-loss (CENAPRED) panels share one `estado × peril × año` grain
  (`HAZ-CENAPRED-04`, `DC-XWALK-2`). Entity normalisation must be identical or the penetration join
  (insured ÷ total) is corrupted.

Keeping one implementation importable by both is the rule; duplicating the table in `cenapred/`
would let the two panels drift apart silently.

## Open wiring follow-up (HAZ port — migration step 4, not yet done)

`cenapred/procesar_cenapred.py:42-49` currently reaches the cleaner via a `sys.path.extend([...])`
hack plus a `try/except ImportError` that falls back to a **stub** returning `("estado", x)` for every
input. That stub silently mis-classifies (assigns foreign/unlocated labels to states with no warning)
— the same failure mode `HAZ-SCRAPER-CNSF-06` warns against. When `hazard_mx` is wired as a proper
package (the HAZ `PORT` step: add `__init__.py`, editable install), replace the hack with a package
import `from ..cnsf.limpieza_cnsf import clasificar_entidad, CAT_ESTADO` and drop the silent stub (fail
loudly instead). Tracked as part of the HAZ pipeline port; do not refactor in isolation
(behaviour-sensitive — lock the cleaning output first, per `CCR-MIG-01` discipline).

## Related
[[HAZ_MOC]] · [[README_scraper_cnsf]] · [[cenapred]] · Home: [[_INDEX]]

#arm/haz #type/pipeline
