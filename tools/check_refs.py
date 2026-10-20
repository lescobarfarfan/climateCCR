"""Resolve every DOI and URL in literature/refs.bib — the reference-verification record.

    python tools/check_refs.py [--bib literature/refs.bib] [--out literature/refs_check.csv]

Each ``doi`` field is looked up on the DOI handle API (``responseCode`` 1 = registered)
and each ``url`` field is fetched with a browser user agent (a redirect that lands on a
page counts; publishers that block scripted clients answer 403/429 and are reported as
``blocked``, not as failures). The CSV lists one row per field checked —
``key, entry_type, field, value, status, http_status, checked_on`` — and the exit code is
non-zero when a DOI does not resolve or a URL is unreachable (GEN-01: a citation the
manuscript compiles against must be checkable).
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[1]
HANDLE_API = "https://doi.org/api/handles/{doi}"
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) climateCCR/check_refs (+https://github.com/lescobarfarfan)"
)
ENTRY_RE = re.compile(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", re.MULTILINE)
FIELD_RE = re.compile(r"^\s*(doi|url)\s*=\s*\{(.*?)\}\s*,?\s*$", re.MULTILINE | re.IGNORECASE)


def parse_entries(text: str) -> list[tuple[str, str, dict[str, str]]]:
    """``(key, entry_type, {field: value})`` for the doi / url fields of every entry."""
    starts = list(ENTRY_RE.finditer(text))
    entries = []
    for i, match in enumerate(starts):
        body = text[match.end() : starts[i + 1].start() if i + 1 < len(starts) else len(text)]
        fields = {m.group(1).lower(): m.group(2).strip() for m in FIELD_RE.finditer(body)}
        entries.append((match.group(2), match.group(1).lower(), fields))
    return entries


def check_doi(session: requests.Session, doi: str) -> tuple[str, int | None]:
    try:
        response = session.get(HANDLE_API.format(doi=doi), timeout=30)
    except requests.RequestException as error:
        return f"error: {type(error).__name__}", None
    if response.status_code == 200 and response.json().get("responseCode") == 1:
        return "ok", 200
    return "unresolved", response.status_code


def check_url(session: requests.Session, url: str) -> tuple[str, int | None]:
    try:
        response = session.get(url, timeout=30, allow_redirects=True, stream=True)
        response.close()
    except requests.RequestException as error:
        return f"error: {type(error).__name__}", None
    if response.status_code < 400:
        return "ok", response.status_code
    if response.status_code in (401, 403, 429):
        return "blocked", response.status_code
    return "unreachable", response.status_code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--bib", type=Path, default=REPO_ROOT / "literature" / "refs.bib")
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "literature" / "refs_check.csv")
    parser.add_argument("--pause", type=float, default=0.5, help="seconds between requests")
    args = parser.parse_args()

    entries = parse_entries(args.bib.read_text(encoding="utf-8"))
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    checked_on = datetime.now(UTC).strftime("%Y-%m-%d")
    rows, failures, blocked = [], 0, 0
    for key, entry_type, fields in entries:
        for field in ("doi", "url"):
            value = fields.get(field)
            if not value:
                continue
            status, http = (check_doi if field == "doi" else check_url)(session, value)
            failures += status not in ("ok", "blocked")
            blocked += status == "blocked"
            rows.append(
                {
                    "key": key,
                    "entry_type": entry_type,
                    "field": field,
                    "value": value,
                    "status": status,
                    "http_status": http if http is not None else "",
                    "checked_on": checked_on,
                }
            )
            print(f"{key:36s} {field:4s} {status:12s} {value}")
            time.sleep(args.pause)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    n_entries = len(entries)
    print(
        f"\n{n_entries} entries, {len(rows)} fields checked: {len(rows) - failures - blocked} ok, "
        f"{blocked} blocked, {failures} failed -> {args.out}"
    )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
