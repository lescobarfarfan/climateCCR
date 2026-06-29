"""Financial calibration: building market objects from calibrated parameters.

Promoted from PIMPA's ``MarketDataBuilder`` (CCR-MIG-05). Today it implements the
``calibration_method='direct_input'`` loader (reads pre-calibrated CSVs); new
estimators (GBM, HW1F) will emit ``'direct_input'``-compatible objects through this
same seam (DC-CCR-CAL-1, CCR-CAL-01).
"""
