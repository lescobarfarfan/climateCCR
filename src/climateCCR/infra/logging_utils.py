"""Project logging.

A single configured logger (console + optional rotating file) so that runs are
auditable. Replaces ad-hoc ``print`` / notebook output in PIMPA.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

_FORMAT = "%(asctime)s | %(name)s | %(levelname)-7s | %(message)s"
_CONFIGURED: set[str] = set()


def get_logger(
    name: str = "climateCCR",
    level: int = logging.INFO,
    log_dir: str | Path | None = None,
) -> logging.Logger:
    """Return a configured logger.

    Idempotent: repeated calls with the same ``name`` do not add duplicate
    handlers. If ``log_dir`` is given, a rotating file handler is attached.
    """
    logger = logging.getLogger(name)
    if name in _CONFIGURED:
        return logger

    logger.setLevel(level)
    logger.propagate = False
    formatter = logging.Formatter(_FORMAT)

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    if log_dir is not None:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_dir / f"{name}.log", maxBytes=2_000_000, backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    _CONFIGURED.add(name)
    return logger
