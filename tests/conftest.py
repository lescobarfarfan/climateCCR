"""Test harness setup.

Ensures the `climateCCR` package under `src/` is importable during tests even when
the project has not been installed editable (`pip install -e .`). The editable
install remains the documented standard (CCR-ARCH-01); this is a no-op once it is
in place, and a convenience for environments where the full `[dev]` extras are not
yet installed.
"""
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
