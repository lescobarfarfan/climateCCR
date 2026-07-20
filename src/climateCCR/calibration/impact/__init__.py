"""HAZ estimation of the climate jump-channel inputs (DC-XWALK-4, OQ-INT-07)."""

from .hazard_jump import (
    ANNUAL_AGGREGATE_MIN_DAYS,
    IntensityTrendFit,
    LognormalSeverityFit,
    LossToMarkScale,
    PoissonIntensityFit,
    annual_event_counts,
    annual_real_amounts,
    derive_loss_to_mark_scale,
    estimate_intensity,
    fit_intensity_trend,
    fit_severity,
    load_climate_events,
)
from .rate_response import (
    EventStudyResult,
    build_episodes,
    event_study,
    rate_scale_from_beta,
)

__all__ = [
    "ANNUAL_AGGREGATE_MIN_DAYS",
    "EventStudyResult",
    "IntensityTrendFit",
    "LognormalSeverityFit",
    "LossToMarkScale",
    "PoissonIntensityFit",
    "annual_event_counts",
    "annual_real_amounts",
    "build_episodes",
    "derive_loss_to_mark_scale",
    "estimate_intensity",
    "event_study",
    "fit_intensity_trend",
    "fit_severity",
    "load_climate_events",
    "rate_scale_from_beta",
]
