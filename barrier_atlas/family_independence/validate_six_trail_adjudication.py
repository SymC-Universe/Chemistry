#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

EXPECTED_TRAILS = {
    "FI-MC01-TRYPSIN-BENZAMIDINE",
    "FI-MC02-CYCLOBUTENE-CLASSIFICATION-CHECK",
    "FI-MC06-CYCLOPROPANE-PROPENE",
    "FI-ENZYME-DB-INVENTORY",
    "FI-LIPRED-2026-SCREEN",
    "FI-BARRIER-ONLY-REPOSITORY-SCREEN",
}
EXPECTED_TARGET_CLASSES = {
    "MC01", "MC02", "MC04", "MC05", "MC06", "MC08",
    "MC11", "MC13", "MC14", "MC15", "MC16",
}
EXPECTED_WORKBOOK_SHA = "1c287d2e8e82826e1353fabad09812efdb5147fb28a00c9cb398278942ea7a7e"
EXPECTED_ARCHIVE_SHA = "8ffd3319b968eb230552fc74269788f623ad76b2af9976504ec0341f8bf0ef6c"
LADDER_GATES = ["source_gate", "barrier_gate", "comparator_gate", "condition_gate", "independence_gate"]


def load_json(path: str | Path):
    return json.loads(Path(path).read_text())


def validate(adjudication: dict, campaign: dict, readout_text: str) -> list[str]:
    errors: list[str] = []

    if adjudication.get("schema") != "barrier-atlas-six-trail-adjudication-v0.1":
        errors.append("wrong adjudication schema")
    if adjudication.get("trail_count") != 6:
        errors.append("trail_count must equal 6")
    ids = [x.get("trail_id") for x in adjudication.get("trails", [])]
    if set(ids) != EXPECTED_TRAILS or len(ids) != 6:
        errors.append("exact six registered trail IDs are required")

    parent = adjudication.get("parent_release", {})
    if not parent.get("immutable"):
        errors.append("v0.9 parent must remain immutable")
    if parent.get("workbook_sha256") != EXPECTED_WORKBOOK_SHA:
        errors.append("v0.9 workbook hash drift")
    if parent.get("archive_sha256") != EXPECTED_ARCHIVE_SHA:
        errors.append("v0.9 archive hash drift")
    if adjudication.get("automatic_coordinate_admission") is not False:
        errors.append("automatic coordinate admission must be false")
    if adjudication.get("coordinates_admitted") != 0:
        errors.append("six-trail audit may not admit coordinates")
    if adjudication.get("grades_changed") != 0:
        errors.append("six-trail audit may not change grades")

    firewall = adjudication.get("selection_firewall", {})
    for key in ["residual_may_select_candidate", "chi_may_select_candidate", "expected_chemsa_agreement_may_select_candidate"]:
        if firewall.get(key) is not False:
            errors.append(f"selection firewall violated: {key}")
    if firewall.get("ready_for_adjudication_is_not_admission") is not True:
        errors.append("READY_FOR_ADJUDICATION must remain distinct from admission")

    target_ids = {x.get("class_id") for x in campaign.get("target_classes", [])}
    if target_ids != EXPECTED_TARGET_CLASSES:
        errors.append("frozen 11-class target set drift")
    cp = campaign.get("parent_release", {})
    if cp.get("workbook_sha256") != EXPECTED_WORKBOOK_SHA or cp.get("archive_sha256") != EXPECTED_ARCHIVE_SHA:
        errors.append("campaign parent hashes do not match frozen v0.9")

    ready = []
    for rec in adjudication.get("trails", []):
        tid = rec.get("trail_id", "UNKNOWN")
        is_ready = rec.get("ready_for_adjudication") is True
        if is_ready:
            ready.append(tid)
            if rec.get("terminal_state") != "READY_FOR_ADJUDICATION":
                errors.append(f"{tid}: ready flag requires READY_FOR_ADJUDICATION terminal state")
            for gate in LADDER_GATES:
                value = str(rec.get(gate, ""))
                if not value.startswith("PASS"):
                    errors.append(f"{tid}: ready candidate has non-PASS {gate}={value}")
        elif rec.get("terminal_state") == "READY_FOR_ADJUDICATION":
            errors.append(f"{tid}: READY terminal state without ready flag")

    if ready != ["FI-MC06-CYCLOPROPANE-PROPENE"]:
        errors.append("v0.1 adjudication must contain exactly the registered MC06 ready candidate")

    by_id = {x["trail_id"]: x for x in adjudication.get("trails", []) if "trail_id" in x}
    cycbut = by_id.get("FI-MC02-CYCLOBUTENE-CLASSIFICATION-CHECK", {})
    if cycbut.get("terminal_state") != "REFUSED_FOR_MC02_CLASSIFICATION":
        errors.append("cyclobutene may not be reassigned into MC02")
    cycprop = by_id.get("FI-MC06-CYCLOPROPANE-PROPENE", {})
    if cycprop.get("representation_mode") != "NETWORK_RESOLVED":
        errors.append("cyclopropane ready state must retain NETWORK_RESOLVED representation")

    counts = adjudication.get("aggregate_gate_counts", {})
    expected_counts = {
        "source_gate_pass": 6,
        "candidate_or_pool_barrier_evidence_pass": 6,
        "independent_kinetic_comparator_pass": 3,
        "condition_match_pass": 1,
        "ready_for_adjudication": 1,
        "target_class_refusals": 1,
        "comparator_missing_half_trails": 2,
        "condition_or_event_mapping_holds": 2,
    }
    if counts != expected_counts:
        errors.append("aggregate gate counts drift from six individual adjudications")

    required_readout_phrases = [
        "non-voting conglomerate analysis",
        "Barrier availability is not the primary bottleneck",
        "NETWORK_RESOLVED",
        "REFUSED_FOR_MC02_CLASSIFICATION",
        "does not adjudicate universality",
    ]
    for phrase in required_readout_phrases:
        if phrase not in readout_text:
            errors.append(f"conglomerate readout missing required phrase: {phrase}")

    return errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--adjudication", required=True)
    ap.add_argument("--campaign", required=True)
    ap.add_argument("--readout", required=True)
    args = ap.parse_args()

    errors = validate(
        load_json(args.adjudication),
        load_json(args.campaign),
        Path(args.readout).read_text(),
    )
    if errors:
        print(json.dumps({"status": "FAIL", "errors": errors}, indent=2))
        raise SystemExit(1)
    print(json.dumps({"status": "PASS", "trail_count": 6, "ready_for_adjudication": 1, "parent_mutated": False}, indent=2))


if __name__ == "__main__":
    main()
