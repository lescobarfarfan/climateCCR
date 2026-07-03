"""Stochastic-process building blocks: diffusions (BM, GBM, HW1F) and climate jumps.

``diffusions`` holds the risk-factor evolution models promoted from PIMPA
(CCR-MIG-05); ``jumps`` holds the climate jump-injection channel superimposed on
them (DC-CCR-SIM-2, INT-10). Both live below all consumers (``simulation``,
``risk.ccr``) so the shared engine depends on them without a back-edge.
"""
