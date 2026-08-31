#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

EXPECTED_TARGETS = {"MC01", "MC02", "MC04", "MC05", "MC06", "MC08", "MC11", "MC13", "MC14", "MC15", "MC16"}
EXPECTED_WORKBOOK_SHA = "1c287d2e8e82826e1353fabad09812efdb5147fb28a00c9cb398278942ea7a7e"
EXPECTED_ARCHIVE_SHA = "8ffd3319b968eb230552fc74269788f623ad76b2af9976504ec0341f8bf0ef6c"
EXPECTED_FROZEN = {
    "FI-MC06-CYCLOPROPANE-PROPENE": "READY_FOR_ADJUDICATION_NETWORK_RESOLVED_NOT_ADMITTED",
    "FI-MC02-CYCLOBUTENE-CLASSIFICATION-CHECK": "REFUSED_FOR_MC02_CLASSIFICATION",
    "FI-MC01-TRYPSIN-BENZAMIDINE": "CONDITION_MISMATCH_HOLD",
    "FI-ENZYME-DB-INVENTORY": "CONDITION_AND_EVENT_MAPPING_HOLD",
    "FI-LIPRED-2026-SCREEN": "BARRIER_QUALIFIED_COMPARATOR_MISSING_POOL",
    "FI-BARRIER-ONLY-REPOSITORY-SCREEN": "BARRIER_QUALIFIED_COMPARATOR_MISSING_POOL",
}


def load(path: str | Path) -> dict:
    return json.loads(Path(path).read_text())


def validate(rec: dict) -> list[str]:
    errors: list[str] = []
    if rec.get("schema") != "barrier-atlas-mc16-methylperoxy-scientific-topology-audit-v0.2":
        errors.append("wrong schema")
    parent = rec.get("parent_release", {})
    if parent.get("immutable") is not True:
        errors.append("v0.9 must remain immutable")
    if parent.get("workbook_sha256") != EXPECTED_WORKBOOK_SHA:
        errors.append("v0.9 workbook hash drift")
    if parent.get("archive_sha256") != EXPECTED_ARCHIVE_SHA:
        errors.append("v0.9 archive hash drift")
    if set(rec.get("frozen_target_classes", [])) != EXPECTED_TARGETS:
        errors.append("frozen 11-class target set drift")
    if rec.get("frozen_outcomes_reaffirmed") != EXPECTED_FROZEN:
        errors.append("six-trail frozen outcomes drift")
    if rec.get("automatic_coordinate_admission") is not False or rec.get("coordinates_admitted") != 0:
        errors.append("coordinate admission firewall violated")
    if rec.get("grades_changed") != 0:
        errors.append("v0.9 grade mutation detected")
    firewall = rec.get("selection_firewall", {})
    for key in ("residual_may_select_candidate", "chi_may_select_candidate", "expected_chemsa_agreement_may_select_candidate", "same_target_fit_or_method_selection_may_validate_target"):
        if firewall.get(key) is not False:
            errors.append(f"selection firewall violated: {key}")
    if rec.get("trail_id") != "FI-MC16-METHYLPEROXY-SELF-REACTION":
        errors.append("wrong trail")
    if rec.get("representation_mode") != "NETWORK_RESOLVED_TETROXIDE_SELF_REACTION_REQUIRED":
        errors.append("MC16 network representation drift")
    if rec.get("barrier_gate") != "HOLD_NO_ROBUST_SINGLE_SADDLE_POINT_BARRIER_AT_PREFERRED_HIGHER_LEVEL_PES":
        errors.append("higher-level PES topology hold missing")
    if rec.get("highest_contiguous_promotion_state") != "COMPARATOR_QUALIFIED":
        errors.append("MC16 promotion state must remain COMPARATOR_QUALIFIED")
    if rec.get("ready_for_adjudication") is not False:
        errors.append("MC16 must not be READY")
    if rec.get("terminal_state") != "PES_TOPOLOGY_NETWORK_AND_MODEL_PROVENANCE_HOLD":
        errors.append("MC16 terminal hold drift")
    agg = rec.get("aggregate_effect", {})
    if agg.get("ready_second_family_count") != 4 or agg.get("ready_classes_unchanged") != ["MC04", "MC06", "MC11", "MC14"]:
        errors.append("ready family-depth count drift")
    if agg.get("new_ready_for_adjudication") != 0:
        errors.append("audit may not create a ready candidate")
    return errors


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--audit", required=True)
    args = ap.parse_args()
    errors = validate(load(args.audit))
    if errors:
        print(json.dumps({"status": "FAIL", "errors": errors}, indent=2))
        raise SystemExit(1)
    print(json.dumps({"status": "PASS", "trail": "FI-MC16-METHYLPEROXY-SELF-REACTION", "ready": False, "v0_9_mutated": False}, indent=2))


if __name__ == "__main__":
    main()
