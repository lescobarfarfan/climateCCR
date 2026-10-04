"""Correlated Monte Carlo engine (promoted from PIMPA, CCR-MIG-05).

``MultiRiskFactorSimulation`` draws the correlated Gaussian increments for a set of
``RiskFactor`` models (BM / GBM / HW1F in ``processes.diffusions``) and superimposes
the optional climate-jump and scheduled-shock overlays (DC-CCR-SIM-1/2). The draw
is seeded through ``infra.get_legacy_rng`` and coloured with the Cholesky factor of
the ``CorrelationMatrix`` (CCR-SIM-02); ``SimulatedHW1FCurve`` reconstructs the
discount curve from a simulated short-rate path.
"""
