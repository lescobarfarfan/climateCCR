#!/usr/bin/env python
"""Compare two artifact trees numerically — the cross-machine reproduction check (GEN-30/37).

    python tools/compare_results.py REF NEW [--tol 1e-6] [--skip manifests logs] [--details out.csv]
    python tools/compare_results.py --headlines tools/headlines.yaml NEW
    python tools/compare_results.py --manifests NEW/manifests

Byte identity is not expected across CPU architectures (ulp-level kernel differences, GEN-37),
so CSV / npz numbers are compared with a relative tolerance and the maximum relative difference
is reported; tied-row order is compared order-insensitively; text files verbatim; figures by
existence. "Relative" means relative to the column's (or array's) own scale, max |x|: a 1e-4
move in a cell near zero of a column that reaches 1e5 is 1e-9, not 1 — the reproducibility
question is whether the *artifact* moved, not whether a near-zero cell did. Classes: identical,
within_tol, order_only, differs, text_differs, exists, missing_new, missing_ref.
"""

from __future__ import annotations

import argparse
import filecmp
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

TEXT = {".md", ".txt", ".yaml", ".yml", ".json", ".html", ".tex"}
EXISTS = {".png", ".pdf", ".zip", ".log", ".svg"}


def _suffix(path: Path) -> str:
    name = path.name.lower()
    if name.endswith(".csv.gz"):
        return ".csv"
    return path.suffix.lower()


def _rel_diff(a: np.ndarray, b: np.ndarray) -> float:
    """Max |a - b| relative to the pair's scale max(|a|, |b|) over all cells, NaN-aware.

    Returns inf if the shapes or the NaN patterns disagree; 0 when both are all-NaN.
    """
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if a.shape != b.shape:
        return float("inf")
    na, nb = np.isnan(a), np.isnan(b)
    if (na != nb).any():
        return float("inf")
    both = ~na
    if not both.any():
        return 0.0
    scale = max(float(np.max(np.abs(a[both]))), float(np.max(np.abs(b[both]))), 1e-12)
    return float(np.max(np.abs(a[both] - b[both])) / scale)


def _frame_diff(ref: pd.DataFrame, new: pd.DataFrame) -> float:
    num = [c for c in ref.columns if pd.api.types.is_numeric_dtype(ref[c])]
    for c in ref.columns:
        if c in num:
            continue
        if not ref[c].astype(str).equals(new[c].astype(str)):
            return float("inf")
    return max((_rel_diff(ref[c].to_numpy(), new[c].to_numpy()) for c in num), default=0.0)


def _canonical(frame: pd.DataFrame) -> pd.DataFrame:
    """Round numerics and sort by every column so tied-row order stops mattering."""
    out = frame.copy()
    for c in out.columns:
        if pd.api.types.is_numeric_dtype(out[c]):
            out[c] = out[c].round(6)
        else:
            out[c] = out[c].astype(str)
    return out.sort_values(list(out.columns), kind="stable").reset_index(drop=True)


def compare_csv(ref: Path, new: Path, tol: float) -> tuple[str, float]:
    try:
        a = pd.read_csv(ref, low_memory=False)
        b = pd.read_csv(new, low_memory=False)
    except Exception:  # noqa: BLE001 — unparsable as a table: fall back to text
        return ("identical" if ref.read_bytes() == new.read_bytes() else "text_differs", np.nan)
    if list(a.columns) != list(b.columns) or a.shape != b.shape:
        return ("differs", float("inf"))
    d = _frame_diff(a, b)
    if d <= tol:
        return ("within_tol", d)
    d2 = _frame_diff(_canonical(a), _canonical(b))
    if d2 <= tol:
        return ("order_only", d2)
    return ("differs", min(d, d2))


def compare_npz(ref: Path, new: Path, tol: float) -> tuple[str, float]:
    with np.load(ref) as za, np.load(new) as zb:
        if sorted(za.files) != sorted(zb.files):
            return ("differs", float("inf"))
        worst = 0.0
        for k in za.files:
            x, y = za[k], zb[k]
            if x.dtype.kind in "USO" or y.dtype.kind in "USO":
                if not np.array_equal(x, y):
                    return ("differs", float("inf"))
                continue
            worst = max(worst, _rel_diff(x, y))
    return ("within_tol" if worst <= tol else "differs", worst)


def classify(ref: Path, new: Path, tol: float) -> tuple[str, float]:
    if filecmp.cmp(ref, new, shallow=False):
        return ("identical", 0.0)
    sfx = _suffix(ref)
    if sfx == ".csv":
        return compare_csv(ref, new, tol)
    if sfx == ".npz":
        return compare_npz(ref, new, tol)
    if sfx in TEXT:
        return ("text_differs", np.nan)
    if sfx in EXISTS:
        return ("exists", np.nan)
    return ("text_differs", np.nan)


def walk(root: Path, skip: set[str]) -> set[Path]:
    files = set()
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(root)
        if rel.parts[0] in skip or p.name.startswith("._") or p.name == ".DS_Store":
            continue
        files.add(rel)
    return files


def compare_trees(ref: Path, new: Path, tol: float, skip: set[str], details: Path | None) -> int:
    fr, fn = walk(ref, skip), walk(new, skip)
    rows = []
    for rel in sorted(fr | fn):
        if rel not in fn:
            rows.append((rel, "missing_new", np.nan))
        elif rel not in fr:
            rows.append((rel, "missing_ref", np.nan))
        else:
            rows.append((rel, *classify(ref / rel, new / rel, tol)))
    table = pd.DataFrame(rows, columns=["path", "class", "max_rel_diff"])
    table["group"] = [p.parts[0] if len(p.parts) > 1 else "." for p in table["path"]]
    classes = [
        "identical",
        "within_tol",
        "order_only",
        "differs",
        "text_differs",
        "exists",
        "missing_new",
        "missing_ref",
    ]
    summary = defaultdict(Counter)
    worst: dict[str, float] = defaultdict(float)
    for _, r in table.iterrows():
        summary[r["group"]][r["class"]] += 1
        if r["class"] in {"within_tol", "order_only", "differs"} and np.isfinite(r["max_rel_diff"]):
            worst[r["group"]] = max(worst[r["group"]], r["max_rel_diff"])
    head = f"{'group':44s}" + "".join(f"{c[:9]:>10s}" for c in classes) + f"{'max_rel':>10s}"
    print(head)
    total = Counter()
    for g in sorted(summary):
        cnt = summary[g]
        total.update(cnt)
        line = f"{g[:44]:44s}" + "".join(f"{cnt.get(c, 0):>10d}" for c in classes)
        print(line + (f"{worst[g]:>10.1e}" if g in worst else f"{'-':>10s}"))
    print(f"{'TOTAL':44s}" + "".join(f"{total.get(c, 0):>10d}" for c in classes))
    bad = table[table["class"].isin(["differs", "text_differs", "missing_new", "missing_ref"])]
    if len(bad):
        print(f"\n-- {len(bad)} files to look at (first 120):")
        for _, r in bad.head(120).iterrows():
            extra = f"  max_rel={r['max_rel_diff']:.2e}" if np.isfinite(r["max_rel_diff"]) else ""
            print(f"  {r['class']:13s} {r['path']}{extra}")
    if details is not None:
        details.parent.mkdir(parents=True, exist_ok=True)
        table.assign(path=table["path"].astype(str)).to_csv(details, index=False)
        print(f"\nper-file table: {details}")
    return 0


def check_headlines(spec: Path, new: Path) -> int:
    """Each entry: label, file, column, expected, decimals, optional where {col: value}."""
    entries = yaml.safe_load(spec.read_text(encoding="utf-8"))
    n_bad = 0
    print(f"{'headline':58s}{'expected':>16s}{'regenerated':>16s}  verdict")
    for e in entries:
        path = new / e["file"]
        label = e["label"][:58]
        if not path.exists():
            print(f"{label:58s}{e['expected']:>16}{'(missing)':>16s}  MISSING")
            n_bad += 1
            continue
        frame = pd.read_csv(path, low_memory=False)
        for col, val in (e.get("where") or {}).items():
            frame = frame[frame[col].astype(str) == str(val)]
        values = frame[e["column"]].dropna().unique() if len(frame) else []
        if len(values) != 1:  # one row, or a stream-level cell repeated on every row
            print(f"{label:58s}{e['expected']:>16}{f'({len(frame)} rows)':>16s}  AMBIGUOUS")
            n_bad += 1
            continue
        actual = float(values[0])
        if "scale" in e:
            actual *= float(e["scale"])
        dec = int(e.get("decimals", 2))
        ok = round(actual, dec) == round(float(e["expected"]), dec)
        n_bad += not ok
        print(f"{label:58s}{e['expected']:>16}{actual:>16.{dec}f}  {'ok' if ok else 'DIFFERS'}")
    print(f"\n{len(entries) - n_bad}/{len(entries)} headline cells reproduce at reported precision")
    return 1 if n_bad else 0


def check_manifests(folder: Path) -> int:
    """Distinct (platform, blas, python, numpy, pandas, commit) tuples — the GEN-30/37 tripwire."""
    seen: Counter = Counter()
    for p in sorted(folder.glob("*.json")):
        m = json.loads(p.read_text(encoding="utf-8"))
        pk = m.get("packages") or {}
        key = (
            str(m.get("platform", "?")).split("-")[0],
            str(m.get("blas")),
            str(m.get("python_version")),
            str(pk.get("numpy")),
            str(pk.get("pandas")),
            str(m.get("git_commit"))[:7],
            str(m.get("git_dirty")),
        )
        seen[key] += 1
    print(f"{'n':>5s}  platform  blas / python / numpy / pandas / commit / dirty")
    for key, n in seen.most_common():
        print(f"{n:>5d}  {key[0]:9s} {' / '.join(key[1:])}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("ref", nargs="?", type=Path)
    ap.add_argument("new", nargs="?", type=Path)
    ap.add_argument("--tol", type=float, default=1e-6)
    ap.add_argument("--skip", nargs="*", default=["manifests", "logs"])
    ap.add_argument("--details", type=Path)
    ap.add_argument("--headlines", type=Path, help="YAML of headline cells to check against NEW")
    ap.add_argument("--manifests", type=Path, help="manifest folder to summarise")
    args = ap.parse_args(argv)
    if args.manifests:
        return check_manifests(args.manifests)
    if args.headlines:
        target = args.new or args.ref
        if target is None:
            ap.error("--headlines needs the results root to check")
        return check_headlines(args.headlines, target)
    if args.ref is None or args.new is None:
        ap.error("REF and NEW are required")
    return compare_trees(args.ref, args.new, args.tol, set(args.skip), args.details)


if __name__ == "__main__":
    sys.exit(main())
