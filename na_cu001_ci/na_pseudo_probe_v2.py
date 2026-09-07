#!/usr/bin/env python3
"""Fail-closed Na pseudopotential and cutoff audit for the pinned SSSP archive."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any

UPF_ELEMENT_RE = re.compile(r"element\s*=\s*['\"]\s*Na\s*['\"]", re.I)
HEADER_WFC_RE = re.compile(r"(?:Suggested minimum cutoff for wavefunctions|wfc_cutoff)\D+([0-9]+(?:\.[0-9]+)?)", re.I)
HEADER_RHO_RE = re.compile(r"(?:Suggested minimum cutoff for charge density|rho_cutoff)\D+([0-9]+(?:\.[0-9]+)?)", re.I)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise SystemExit(f"HOLD: JSON root is not an object: {path}")
    return data


def json_pointer(data: Any, pointer: str) -> Any:
    if pointer == "":
        return data
    if not pointer.startswith("/"):
        raise ValueError("JSON pointer must begin with /")
    current = data
    for token in pointer[1:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict) and token in current:
            current = current[token]
        elif isinstance(current, list) and token.isdigit() and int(token) < len(current):
            current = current[int(token)]
        else:
            raise KeyError(pointer)
    return current


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--archive-root", required=True)
    p.add_argument("--archive", required=True)
    p.add_argument("--protocol", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    root = Path(args.archive_root).resolve(); archive = Path(args.archive).resolve()
    protocol = read_json(Path(args.protocol).resolve())
    if protocol.get("schema") != "na-cu001-method-protocol-v0.2" or protocol.get("status") != "FROZEN_BEFORE_DOWNSTREAM_RESULTS":
        raise SystemExit("HOLD: unsupported or unfrozen method protocol")
    source = protocol["immutable_sources"]
    errors: list[str] = []
    archive_hash = sha256(archive)
    if archive_hash != source["sssp_pbe_efficiency_v2_archive_sha256"]:
        errors.append("archive SHA-256 differs from frozen protocol")

    upfs: list[Path] = []
    for path in sorted(root.rglob("*.upf")):
        head = path.read_text(errors="replace")[:50000]
        if UPF_ELEMENT_RE.search(head):
            upfs.append(path)
    if len(upfs) != 1:
        errors.append(f"expected exactly one Na UPF, found {len(upfs)}")
    selected_path = upfs[0] if len(upfs) == 1 else None
    selected: dict[str, Any] | None = None

    metadata_spec = source["na_authoritative_cutoff_metadata"]
    metadata_path = root / metadata_spec["relative_path"]
    metadata_record = None
    if not metadata_path.is_file():
        errors.append(f"authoritative cutoff metadata absent: {metadata_spec['relative_path']}")
    else:
        metadata = read_json(metadata_path)
        try:
            metadata_record = json_pointer(metadata, metadata_spec["json_pointer"])
        except (KeyError, ValueError, TypeError):
            metadata_record = None
        if not isinstance(metadata_record, dict):
            errors.append(f"authoritative {metadata_spec['json_pointer']} metadata record absent or malformed")
        else:
            if set(metadata_record) < {"cutoff_wfc", "cutoff_rho"}:
                errors.append("authoritative Na metadata lacks cutoff_wfc/cutoff_rho")

    if selected_path is not None:
        text = selected_path.read_text(errors="replace")[:50000]
        wfc_match = HEADER_WFC_RE.search(text); rho_match = HEADER_RHO_RE.search(text)
        selected = {
            "path": str(selected_path.relative_to(root)),
            "filename": selected_path.name,
            "sha256": sha256(selected_path),
            "size_bytes": selected_path.stat().st_size,
            "upf_header_suggested_wfc_ry": float(wfc_match.group(1)) if wfc_match else None,
            "upf_header_suggested_rho_ry": float(rho_match.group(1)) if rho_match else None,
        }
        if selected["filename"] != source["na_upf_filename"]:
            errors.append("Na filename differs from frozen protocol")
        if selected["sha256"] != source["na_upf_sha256"]:
            errors.append("Na UPF SHA-256 differs from frozen protocol")

    authoritative = None
    if isinstance(metadata_record, dict):
        authoritative = {
            "recommended_ecutwfc_ry": float(metadata_record["cutoff_wfc"]),
            "recommended_ecutrho_ry": float(metadata_record["cutoff_rho"]),
            "source_metadata_file": metadata_spec["relative_path"],
            "source_json_pointer": metadata_spec["json_pointer"],
            "raw_values": metadata_record,
            "units": "Ry"
        }
        if authoritative["recommended_ecutwfc_ry"] != float(metadata_spec["ecutwfc_ry"]):
            errors.append("authoritative Na wavefunction cutoff differs from frozen expectation")
        if authoritative["recommended_ecutrho_ry"] != float(metadata_spec["ecutrho_ry"]):
            errors.append("authoritative Na density cutoff differs from frozen expectation")

    result = {
        "schema": "na-cu001-na-pseudo-probe-v0.2",
        "status": "PASS" if not errors else "HOLD",
        "selection_rule": "unique UPF with parsed element Na plus exact archive, metadata, filename, and UPF hash agreement",
        "archive": {"path": str(archive), "sha256": archive_hash, "size_bytes": archive.stat().st_size},
        "selected": selected,
        "authoritative_cutoffs": authoritative,
        "header_cutoffs_are_diagnostic_only": True,
        "errors": errors,
        "next_gate": "resolve mixed Cu-Na cutoffs from authoritative metadata and bulk PASS"
    }
    out = Path(args.out).resolve(); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n"); print(json.dumps(result, indent=2))
    if errors:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
