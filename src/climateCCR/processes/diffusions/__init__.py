"""Stochastic-process definitions (BM, GBM, HW1F) and their shared base.

Promoted from PIMPA's ``scenario_generation`` (CCR-MIG-05). These are the
diffusion building blocks the climate jump injects into (INT-10); they live below
all consumers (``simulation``, ``risk.ccr``) so the shared simulation engine can
depend on them without a back-edge.
"""
