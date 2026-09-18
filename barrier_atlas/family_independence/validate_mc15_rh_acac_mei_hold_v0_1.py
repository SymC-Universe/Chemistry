#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

EXPECTED_CLASSES = {"MC01", "MC02", "MC04", "MC05", "MC06", "MC08", "MC11", "MC13", "MC14", "MC15", "MC16"}
EXPECTED_WORKBOOK_SHA = "1c287d2e8e82826e1353fabad09812efdb5147fb28a00c9cb398278942ea7a7e"
EXPECTED_ARCHIVE_SHA = "8ffd3319b968eb230552fc74269788f623ad76b2af9976504ec0341f8bf0ef6c"


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    if doc.get("schema") != "barrier-atlas-mc15-rh-acac-mei-source-audit-v0.1":
        errors.append("wrong schema")
    parent = doc.get("parent_release", {})
    if parent.get("immutable") is not True:
        errors.append("v0.9 must remain immutable")
    if parent.get("workbook_sha256") != EXPECTED_WORKBOOK_SHA:
        errors.append("v0.9 workbook hash drift")
    if parent.get("archive_sha256") != EXPECTED_ARCHIVE_SHA:
        errors.append("v0.9 archive hash drift")
    if set(doc.get("frozen_target_classes", [])) != EXPECTED_CLASSES:
        errors.append("frozen 11-class set drift")
    if doc.get("automatic_coordinate_admission") is not False or doc.get("coordinates_admitted") != 0:
        errors.append("coordinate admission firewall violated")
    if doc.get("grades_changed") != 0:
        errors.append("v0.9 grade mutation detected")

    fw = doc.get("selection_firewall", {})
    for key in (
        "residual_may_select_candidate",
        "chi_may_select_candidate",
        "expected_chemsa_agreement_may_select_candidate",
        "same_target_fit_or_method_selection_may_validate_target",
        "experimental_eyring_quantity_from_selected_rate_may_validate_rate",
    ):
        if fw.get(key) is not False:
            errors.append(f"selection firewall violated: {key}")

    trail = doc.get("trail", {})
    if trail.get("trail_id") != "FI-MC15-RH-ACAC-MEI-OXIDATIVE-ADDITION":
        errors.append("unexpected MC15 trail id")
    if trail.get("target_class") != "MC15":
        errors.append("trail must remain MC15")
    if trail.get("barrier_quantity", {}).get("type", "").find("Gibbs free energy of activation") < 0:
        errors.append("barrier must remain explicitly typed as computational Gibbs activation free energy")
    if trail.get("barrier_quantity", {}).get("solvent") != "methanol":
        errors.append("theory solvent must remain methanol")
    if trail.get("observed_comparator", {}).get("solvent") != "dichloromethane":
        errors.append("experimental solvent must remain dichloromethane")
    if trail.get("condition_gate") != "FAIL_SOLVENT_AND_STANDARD_STATE_MAPPING_NOT_CLOSED":
        errors.append("solvent/standard-state mismatch may not be silently closed")
    if trail.get("independence_gate") != "HOLD_METHOD_SELECTION_LINEAGE_REQUIRES_AUDIT":
        errors.append("method-selection independence may not be presumed")
    if trail.get("terminal_state") != "CONDITION_AND_MODEL_SELECTION_PROVENANCE_HOLD":
        errors.append("MC15 trail must remain on hard hold")
    if trail.get("ready_for_adjudication") is not False:
        errors.append("MC15 trail may not be READY while hold remains")
    if trail.get("representation_mode") != "SINGLE_BARRIER_ASSOCIATIVE_SN2_OXIDATIVE_ADDITION":
        errors.append("representation drift")

    q = trail.get("rate_derived_activation_quantities", {})
    if q.get("validation_role") != "QUARANTINED_RATE_DERIVED_NOT_AN_INDEPENDENT_BARRIER_COMPARATOR":
        errors.append("rate-derived activation quantities must stay quarantined")

    old = doc.get("existing_mc15_hold_preserved", {})
    if old.get("trail_id") != "FI-MC15-VASKA-H2-OXIDATIVE-ADDITION" or old.get("superseded") is not False:
        errors.append("existing Vaska MC15 hold must remain preserved")

    agg = doc.get("campaign_aggregate_unchanged", {})
    if agg.get("ready_second_family_count") != 6:
        errors.append("hard hold must not increase READY-family count")
    if agg.get("coordinates_admitted") != 0 or agg.get("grades_changed") != 0:
        errors.append("aggregate parent mutation detected")
    return errors


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--audit", required=True)
    args = ap.parse_args()
    doc = json.loads(Path(args.audit).read_text())
    errors = validate(doc)
    if errors:
        print(json.dumps({"status": "FAIL", "errors": errors}, indent=2))
        raise SystemExit(1)
    print(json.dumps({"status": "PASS", "trail": doc["trail"]["trail_id"], "terminal_state": doc["trail"]["terminal_state"], "parent_mutated": False}, indent=2))


if __name__ == "__main__":
    main()
