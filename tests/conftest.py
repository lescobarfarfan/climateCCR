"""Test harness setup.

Ensures the `climateCCR` package under `src/` is importable during tests even when
the project has not been installed editable (`pip install -e .`). The editable
install remains the documented standard (CCR-ARCH-01); this is a no-op once it is
in place, and a convenience for environments where the full `[dev]` extras are not
yet installed.

Also puts the CNSF pipeline-script directory on the path (resolves OQ-HAZ-15):
those modules are standalone CLI scripts at the bilingual boundary (INT-07), not a
package — no `__init__.py`, and they import each other by bare name (e.g.
`import consolidar_cnsf` inside `scraper_cnsf._despachar`), so their tests under
`tests/data/hazard_mx/cnsf/` keep the same bare imports. Packaging them instead
would change how they are invoked as CLIs.
"""

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

_CNSF_DIR = _SRC / "climateCCR" / "data" / "hazard_mx" / "cnsf"
if _CNSF_DIR.is_dir() and str(_CNSF_DIR) not in sys.path:
    sys.path.append(str(_CNSF_DIR))

# The CNSF scripts need the `haz` extra (pip install -e ".[dev,haz]"). In an env
# without it, drop their tests from collection instead of erroring the whole run:
# the core suite (infra, PIMPA baseline) must stay runnable from the plain [dev] env.
try:
    import bs4  # noqa: F401
    import openpyxl  # noqa: F401
    import requests  # noqa: F401
except ImportError:
    collect_ignore_glob = ["data/hazard_mx/cnsf/test_*.py"]
