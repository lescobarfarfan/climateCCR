"""Climate jump-injection channel (DC-CCR-SIM-2, INT-10).

The integrating mechanism of the project: HAZ-estimated intensity + impact ->
compound-Poisson shocks with shared event times -> superimposed on the GBM/HW1F
diffusions by ``MultiRiskFactorSimulation`` -> Monte Carlo reads out the
climate-vs-baseline change in risk (INT-09).
"""

from .climate_jump_process import CLIMATE_JUMP_STREAM, ClimateJumpProcess, ClimateJumpScenario
from .marks import DeterministicMark, GaussianMark, LognormalMark, MarkSampler

__all__ = [
    "CLIMATE_JUMP_STREAM",
    "ClimateJumpProcess",
    "ClimateJumpScenario",
    "MarkSampler",
    "DeterministicMark",
    "GaussianMark",
    "LognormalMark",
]
