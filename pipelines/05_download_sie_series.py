"""Download Banxico SIE + FRED daily series (DC-MKT-SIE-1; seeds DC-XWALK-5).

The Python port of ``Actualiza_FTIIE.R``: Mexican policy/interbank rates
(TIIEs), Cetes 364, the six on-the-run Bonos M buckets, Bonos MS, plus the
FIX USD/MXN series and the FRED US Treasury controls the OQ-INT-09 event
study needs. Values land AS PUBLISHED under ``data/market_mx/`` with a
``_procedencia.json`` per directory (GEN-02: series ids, ranges, sha256 —
never the token). Idempotent per output file (GEN-05): existing files are
skipped, rerun with ``--forzar``.

    SIEBANXICO_TOKEN=<token> python pipelines/05_download_sie_series.py [--forzar]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
SERIES_CONFIG = REPO_ROOT / "configs" / "sie_series.yaml"
FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_provenance(directory: Path, meta: dict) -> None:
    files = {
        p.name: {"sha256": _sha256(p), "bytes": p.stat().st_size}
        for p in sorted(directory.glob("*.csv"))
    }
    payload = {
        "descargado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "archivos": files,
        **meta,
    }
    (directory / "_procedencia.json").write_text(json.dumps(payload, indent=2, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--forzar", "--force", action="store_true", help="re-download even if the output exists"
    )
    args = parser.parse_args()

    from climateCCR.data.market.sie import SIE_BASE, build_session, fetch_series
    from climateCCR.infra import get_logger, load_config

    config = load_config(SERIES_CONFIG)
    config.paths.ensure()
    logger = get_logger("climateCCR.download_sie", log_dir=config.paths.logs)

    start = str(config.extra["start"])
    end = str(config.extra["end"] or date.today().isoformat())
    sie_dir = config.paths.root / config.extra["sie_dir"]
    fred_dir = config.paths.root / config.extra["fred_dir"]
    sie_dir.mkdir(parents=True, exist_ok=True)
    fred_dir.mkdir(parents=True, exist_ok=True)
    session = build_session()
    downloaded = 0

    def skip(path: Path) -> bool:
        if path.exists() and not args.forzar:
            logger.info("Exists, skipping (rerun with --forzar): %s", path.name)
            return True
        return False

    for group, mapping in config.extra["sie"].items():
        out = sie_dir / f"{group}.csv"
        if skip(out):
            continue
        frame = fetch_series(mapping, start, end, session=session)
        frame.to_csv(out)
        logger.info(
            "%s: %d rows, %s..%s", out.name, len(frame), frame.index.min(), frame.index.max()
        )
        downloaded += 1

    out = sie_dir / "bonos_m.csv"
    if not skip(out):
        buckets = []
        for serie, mapping in config.extra["bonos_m"].items():
            frame = fetch_series(mapping, start, end, session=session).reset_index()
            frame.insert(1, "Serie", serie)
            buckets.append(frame)
        bonos = pd.concat(buckets, ignore_index=True)[["Fecha", "Serie", "Plazo", "Cupon", "Valor"]]
        bonos.to_csv(out, index=False)
        logger.info("bonos_m.csv: %d rows, %d buckets", len(bonos), len(buckets))
        downloaded += 1

    for sid in config.extra["fred"]:
        out = fred_dir / f"{sid}.csv"
        if skip(out):
            continue
        response = session.get(FRED_URL.format(sid=sid), timeout=60)
        if response.status_code != 200:
            raise RuntimeError(f"FRED request failed ({response.status_code}): {sid}")
        out.write_text(response.text)
        logger.info("%s.csv: %d bytes", sid, len(response.text))
        downloaded += 1

    if downloaded:
        _write_provenance(
            sie_dir,
            {
                "fuente": "Banco de Mexico, SIE API",
                "url_base": SIE_BASE,
                "series": {**config.extra["sie"], "bonos_m": config.extra["bonos_m"]},
                "rango": [start, end],
                "nota": "valores como los publica el SIE (tasas en %, precios por 100 nominal)",
            },
        )
        _write_provenance(
            fred_dir,
            {
                "fuente": "FRED, Federal Reserve Bank of St. Louis",
                "url_base": FRED_URL,
                "series": list(config.extra["fred"]),
                "rango": ["series completa", end],
            },
        )
        logger.info("Provenance written (%d files downloaded)", downloaded)
    print(f"Downloaded {downloaded} file(s) -> {sie_dir} / {fred_dir}")


if __name__ == "__main__":
    sys.path.insert(0, str(REPO_ROOT / "src"))
    main()
