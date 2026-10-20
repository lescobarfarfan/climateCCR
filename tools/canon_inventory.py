"""Inventory of the context canon: IDs, citation keys, wikilinks and numeric tokens.

    python tools/canon_inventory.py snapshot <out.json> [--root DIR]
    python tools/canon_inventory.py compare <before.json> <after.json>

``snapshot`` records, per canon file, every decision / contract / open-question ID
(``GEN-01``, ``DC-CCR-SIM-2``, ``OQ-INT-13``), citation key (``[Klugman2019]``), wikilink
(``[[DECISIONS]]``) and numeric token (``255,735.47``, ``-8.9965``, ``1e-13``, ``19.2857/yr``
→ ``19.2857``). ``compare`` reports what the later snapshot lost: an ID, key or link gone
from the canon as a whole, and every numeric token that no longer appears anywhere in it
(HISTORY.md included) — the lossless gate of a compaction (00_README_CONTEXT §4e). Exit 1
on any loss.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ID_RE = re.compile(r"\b(?:GEN|INT|CCR|MKT|HAZ|DC|OQ)-[A-Z][A-Z-]*-?\d+\b")
KEY_RE = re.compile(r"\[([A-Za-z][A-Za-z0-9_]+)(?: ref\?)?\]")
LINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")
NUMBER_RE = re.compile(r"(?<![A-Za-z_/])[-−+]?\d(?:[\d,]*\d)?(?:\.\d+)?(?:[eE][-+]?\d+)?")


def inventory(root: Path) -> dict:
    out: dict[str, dict] = {}
    for path in sorted((root / "context").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        numbers = Counter(tok.replace("−", "-").strip("+") for tok in NUMBER_RE.findall(text))
        out[path.name] = {
            "ids": sorted(set(ID_RE.findall(text))),
            "keys": sorted(set(KEY_RE.findall(text))),
            "links": sorted(set(LINK_RE.findall(text))),
            "numbers": dict(numbers),
            "lines": text.count("\n"),
            "bytes": len(text.encode("utf-8")),
        }
    return out


def union(inv: dict, field: str) -> set[str]:
    return {x for f in inv.values() for x in f[field]}


def compare(before: dict, after: dict) -> int:
    lost = 0
    for field in ("ids", "keys", "links"):
        gone = sorted(union(before, field) - union(after, field))
        if gone:
            lost += len(gone)
            print(f"LOST {field} ({len(gone)}): {', '.join(gone)}")
    before_numbers = Counter()
    after_numbers = Counter()
    for f in before.values():
        before_numbers.update(f["numbers"])
    for f in after.values():
        after_numbers.update(f["numbers"])
    gone_numbers = sorted(tok for tok in before_numbers if tok not in after_numbers)
    if gone_numbers:
        lost += len(gone_numbers)
        print(f"LOST numeric tokens ({len(gone_numbers)}): {', '.join(gone_numbers[:60])}")
        if len(gone_numbers) > 60:
            print(f"  ... and {len(gone_numbers) - 60} more")
    for name in sorted(set(before) | set(after)):
        b, a = before.get(name), after.get(name)
        if b and a:
            lines = f"{b['lines']:5d} -> {a['lines']:5d} lines"
            print(f"{name:24s} {lines}  {b['bytes']:8d} -> {a['bytes']:8d} bytes")
        else:
            print(f"{name:24s} {'added' if a else 'removed'}")
    print("no losses" if not lost else f"{lost} losses")
    return 1 if lost else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    snap = sub.add_parser("snapshot")
    snap.add_argument("out", type=Path)
    snap.add_argument("--root", type=Path, default=REPO_ROOT)
    comp = sub.add_parser("compare")
    comp.add_argument("before", type=Path)
    comp.add_argument("after", type=Path)
    args = parser.parse_args()
    if args.command == "snapshot":
        args.out.write_text(json.dumps(inventory(args.root), indent=1), encoding="utf-8")
        print("snapshot:", args.out)
        return 0
    return compare(
        json.loads(args.before.read_text(encoding="utf-8")),
        json.loads(args.after.read_text(encoding="utf-8")),
    )


if __name__ == "__main__":
    sys.exit(main())
