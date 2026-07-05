"""Thesis-wide plotting style: palette, matplotlib defaults, figure saving.

The palette is a validated instance of the dataviz color method (CVD-safe hue
pairing, >= 3:1 contrast on a white surface). Scenario semantics are fixed
project-wide: baseline = deep green, climate/jump-on = warm orange, and the
same two hues serve as the diverging poles for shift (climate - baseline)
encodings around zero. The pair was chosen by validator, not by eye: green
vs *red* is the classic deutan/protan confusion (adjacent-pair Delta-E 13.3,
barely at the >= 12 floor); the teal-leaning green vs orange pair clears it
at Delta-E 36.5 with both hues >= 3:1 on white.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
from matplotlib.figure import Figure

# Scenario colors (categorical pair; also the diverging poles for shifts).
COLOR_BASELINE = "#00745e"  # jump-off / baseline (deep green)
COLOR_CLIMATE = "#eb6834"  # jump-on / climate-stressed (warm orange)
COLOR_SHIFT_UP = COLOR_CLIMATE  # shift > 0: risk metric increases under climate
COLOR_SHIFT_DOWN = COLOR_BASELINE  # shift < 0: risk metric decreases

# Fixed-order categorical palette for multi-series plots (never cycled/reordered).
SERIES_COLORS = [
    "#2a78d6",  # blue
    "#1baf7a",  # aqua
    "#eda100",  # yellow
    "#008300",  # green
    "#4a3aa7",  # violet
    "#e34948",  # red
    "#e87ba4",  # magenta
    "#eb6834",  # orange
]

TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
GRID_COLOR = "#e7e6e2"


def apply_style() -> None:
    """Set the thesis matplotlib defaults (idempotent; call once per process).

    Recessive grid and spines, fixed categorical cycle, constrained layout, and
    print-quality savefig defaults, so every figure module inherits one look.
    """
    mpl.rcParams.update(
        {
            "figure.constrained_layout.use": True,
            "figure.dpi": 120,
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
            "font.size": 10,
            "axes.titlesize": 10,
            "axes.titleweight": "bold",
            "axes.titlelocation": "left",
            "axes.labelsize": 9,
            "axes.labelcolor": TEXT_SECONDARY,
            "axes.edgecolor": TEXT_SECONDARY,
            "axes.linewidth": 0.8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "axes.axisbelow": True,
            "grid.color": GRID_COLOR,
            "grid.linewidth": 0.8,
            "xtick.color": TEXT_SECONDARY,
            "ytick.color": TEXT_SECONDARY,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.frameon": False,
            "legend.fontsize": 8,
            "lines.linewidth": 2.0,
            "axes.prop_cycle": mpl.cycler(color=SERIES_COLORS),
        }
    )


def save_figure(
    fig: Figure,
    path: Path | str,
    formats: tuple[str, ...] = ("png", "pdf"),
    dpi: int | None = None,
) -> list[Path]:
    """Save ``fig`` under ``path`` (extension ignored) once per format.

    PNG for notes/review, PDF for the LaTeX manuscript. ``dpi`` overrides the
    300-dpi default — use it for raster-only figures (e.g. an all-paths
    envelope skips the unwieldy vector PDF and compensates with higher dpi).
    Returns the written paths; parents are created as needed.
    """
    base = Path(path)
    base.parent.mkdir(parents=True, exist_ok=True)
    written = []
    for fmt in formats:
        target = base.with_suffix(f".{fmt}")
        fig.savefig(target, **({"dpi": dpi} if dpi is not None else {}))
        written.append(target)
    return written
