"""HAZ estimation of the climate jump-channel inputs (DC-XWALK-4, OQ-INT-07)."""

from .hazard_jump import (
    ANNUAL_AGGREGATE_MIN_DAYS,
    IntensityTrendFit,
    LognormalSeverityFit,
    PoissonIntensityFit,
    annual_event_counts,
    estimate_intensity,
    fit_intensity_trend,
    fit_severity,
    load_climate_events,
)

__all__ = [
    "ANNUAL_AGGREGATE_MIN_DAYS",
    "IntensityTrendFit",
    "LognormalSeverityFit",
    "PoissonIntensityFit",
    "annual_event_counts",
    "estimate_intensity",
    "fit_intensity_trend",
    "fit_severity",
    "load_climate_events",
]
