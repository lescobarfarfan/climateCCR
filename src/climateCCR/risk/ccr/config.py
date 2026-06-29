"""Assemble PIMPA's legacy ``global_parameters`` dict from a YAML Config (Step 1b).

CCR-MIG-05 / GEN-08 / CCR-ARCH-04: replaces PIMPA's mutable ``global_parameters.py``
module with a typed :class:`climateCCR.infra.Config` (``configs/*.yaml``) plus
central path resolution (:class:`climateCCR.infra.ProjectPaths`). The engine still
consumes the same dict shape, so the EE/PE regression baseline (CCR-MIG-03) is
unaffected — only where the values come from changes.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from climateCCR.infra import Config


def build_global_parameters(config: Config, data_root: str | Path) -> dict[str, Any]:
    """Build the legacy ``global_parameters`` dict from a Config and a data root.

    ``data_root`` is the directory PIMPA's old ``GLOBAL_DATA_PATH`` pointed at (the
    fixture tree for the regression, or a real data root resolved via
    ``ProjectPaths`` in production). Every data path is anchored to it, so no
    CWD-relative paths remain.

    Args:
        config: Typed configuration loaded from ``configs/pimpa_fixture.yaml``
            (or an equivalent); leaf layout values live in ``config.extra``.
        data_root: Root directory the relative data layout is joined onto.

    Returns:
        The ``global_parameters`` dict in PIMPA's original shape and key names.
    """
    extra = config.extra
    root = os.path.join(str(data_root), "")  # exactly one trailing separator

    # prototype_data_paths (data_paths): simple subdirs + the nested trades dict.
    data_paths: dict[str, Any] = {key: root + sub for key, sub in extra["data_subdirs"].items()}
    data_paths["trades"] = {k: root + v for k, v in extra["trades_subdirs"].items()}

    file_names = extra["file_names"]

    # market_data_by_service (market_data_folders): data_paths[dir] + file name.
    market_data_by_service: dict[str, str] = {}
    for e in extra["market_data_services"]:
        market_data_by_service[e["service"]] = (
            data_paths[e["dir"]] + file_names[e["group"]][e["file"]]
        )

    return {
        "B3_grid": extra["b3_grid"],
        "date_format": config.date_format,
        "IR_curves_tenors": extra["ir_curves_tenors"],
        "n_paths": config.n_paths,
        "prototype_data_files": file_names,
        "prototype_data_paths": data_paths,
        "random_state": config.seed,
        "settlement_currency": config.settlement_currency,
        "calibration_parameters": extra["calibration_parameters"],
        "market_data_by_service": market_data_by_service,
        "pricer_mapping": extra["pricer_mapping"],
    }
