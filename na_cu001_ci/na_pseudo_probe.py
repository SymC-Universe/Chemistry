#!/usr/bin/env python3
"""Discover and audit the Na pseudopotential in the pinned SSSP archive.

No filename or cutoff is guessed. The probe selects only when exactly one Na UPF
exists and records every matching metadata object for later mixed-system cutoff
resolution. Selection ambiguity produces HOLD.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Iterable

UPF_ELEMENT_RE = re.compile(r"element\s*=\s*['\"]\s*Na\s*['\"]", re.I)
SUGGESTED_WFC_RE = re.compile(r"(?:Suggested minimum cutoff for wavefunctions|wfc_cutoff)\D+([0-9]+(?:\.[0-9]+)?)", re.I)
SUGGESTED_RHO_RE = re.compile(r"(?:Suggested minimum cutoff for charge density|rho_cutoff)\D+([0-9]+(?:\.[0-9]+)?)", re.I)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def walk_json(value: Any, trail: tuple[str, ...] = ()) -> Iterable[tuple[tuple[str, ...], Any]]:
    yield trail, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from walk_json(child, trail + (str(key),))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk_json(child, trail + (str(index),))


def metadata_hits(root: Path, filename: str) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*.json")):
        try:
            data = json.loads(path.read_text(errors="replace"))
        except Exception:
            continue
        for trail, value in walk_json(data):
            text = json.dumps(value, sort_keys=True) if isinstance(value, (dict, list)) else str(value)
            if filename in text or (trail and trail[-1].lower() == "na"):
                hits.append({
                    "metadata_path": str(path.relative_to(root)),
                    "json_trail": list(trail),
                    "value": value,
                })
    return hits


def numeric_candidates(value: Any, trail: tuple[str, ...] = ()) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        for key, child in value.items():
            key_lower = str(key).lower()
            next_trail = trail + (str(key),)
            if isinstance(child, (int, float)) and any(token in key_lower for token in ("cutoff", "ecut", "wfc", "rho")):
                yield {"trail": list(next_trail), "value": float(child)}
            yield from numeric_candidates(child, next_trail)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from numeric_candidates(child, trail + (str(index),))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive-root", required=True)
    parser.add_argument("--archive", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    root = Path(args.archive_root).resolve()
    archive = Path(args.archive).resolve()
    out = Path(args.out).resolve()
    upfs: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() != ".upf":
            continue
        head = path.read_text(errors="replace")[:20000]
        if UPF_ELEMENT_RE.search(head):
            upfs.append(path)

    candidates = []
    for path in upfs:
        text = path.read_text(errors="replace")[:50000]
        wfc = SUGGESTED_WFC_RE.search(text)
        rho = SUGGESTED_RHO_RE.search(text)
        hits = metadata_hits(root, path.name)
        cutoff_values = []
        for hit in hits:
            cutoff_values.extend(numeric_candidates(hit["value"]))
        candidates.append({
            "path": str(path.relative_to(root)),
            "filename": path.name,
            "sha256": sha256(path),
            "size_bytes": path.stat().st_size,
            "upf_header_suggested_wfc_ry": float(wfc.group(1)) if wfc else None,
            "upf_header_suggested_rho_ry": float(rho.group(1)) if rho else None,
            "metadata_hits": hits,
            "metadata_numeric_cutoff_candidates": cutoff_values,
        })

    selected = candidates[0] if len(candidates) == 1 else None
    status = "PASS" if selected is not None else "HOLD"
    result = {
        "schema": "na-cu001-na-pseudopotential-handoff-v0.1",
        "status": status,
        "selection_rule": "select the unique UPF whose parsed element attribute is Na from the pinned SSSP v2 PBE-efficiency archive",
        "archive": {
            "path": str(archive),
            "sha256": sha256(archive),
            "size_bytes": archive.stat().st_size,
        },
        "candidate_count": len(candidates),
        "candidates": candidates,
        "selected": selected,
        "mixed_cutoff_status": "UNRESOLVED_PENDING_BULK_HANDOFF_AND_UNAMBIGUOUS_SSSP_RECOMMENDATION",
        "next_gate": "resolve componentwise maximum Cu-Na cutoffs after bulk PASS",
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if status != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
