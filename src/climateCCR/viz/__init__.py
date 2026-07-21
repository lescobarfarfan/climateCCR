"""Cross-cutting visualization layer: contract-shaped inputs → thesis figures.

``viz`` sits at the top of the dependency stack, mirroring ``infra`` at the
bottom: it may import from anywhere, nothing imports from it. The load-bearing
rule: **public functions accept contract-shaped data — path-major arrays
(DC-CONV-10), tidy/result DataFrames (DC-CONV-9, DC-CCR-RISK-2), manifests —
never model objects.** Any model, in any arm, that emits a conforming artifact
is plottable with no change here.

Modules: ``style`` (palette + matplotlib defaults + saving), ``ccr`` (EE/PE
profiles and climate shifts), ``processes`` (simulated paths, fans, jump
diagnostics), ``market`` (rate-path fans, calibration diagnostics). Planned:
``hazard`` (λ panels, impact functions) as that arm produces artifacts
(Phase 5, PROJECT_PLAN).
"""

from .ccr import plot_exposure_profiles, plot_exposure_shift, plot_mean_shift_summary
from .market import plot_estimator_fan_comparison, plot_jump_decay, plot_rate_path_fan
from .processes import plot_event_arrivals, plot_fan_comparison, plot_sample_paths
from .style import apply_style, save_figure

__all__ = [
    "apply_style",
    "save_figure",
    "plot_exposure_profiles",
    "plot_exposure_shift",
    "plot_mean_shift_summary",
    "plot_sample_paths",
    "plot_fan_comparison",
    "plot_event_arrivals",
    "plot_rate_path_fan",
    "plot_estimator_fan_comparison",
    "plot_jump_decay",
]
