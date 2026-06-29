"""Shared low-level utilities (date/tenor math) imported across all layers.

``calendar_utils`` was PIMPA-local; promoted here (CCR-MIG-05) because diffusions,
simulation, market primitives, pricers, and trade models all depend on it. It sits
below every consumer so there is no circular dependency.
"""
