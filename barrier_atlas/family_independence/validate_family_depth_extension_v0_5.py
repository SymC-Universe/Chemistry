#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

EXPECTED_TARGET_CLASSES = {
    "MC01", "MC02", "MC04", "MC05", "MC06", "MC08",
    "MC11", "MC13", "MC14", "MC15", "MC16",
}
EXPECTED_WORKBOOK_SHA = "1c287d2e8e82826e1353fabad09812efdb5147fb28a00c9cb398278942ea7a7e"
EXPECTED_ARCHIVE_SHA = "8ffd3319b968eb230552fc74269788f623ad76b2af9976504ec0341f8bf0ef6c"
EXPECTED_READY_CLASSES = {"MC04", "MC06", "MC11", "MC14"}
EXPECTED_FROZEN_OUTCOMES = {
    "FI-MC06-CYCLOPROPANE-PROPENE": "READY_FOR_ADJUDICATION_NETWORK_RESOLVED_NOT_ADMITTED",
    "FI-MC02-CYCLOBUTENE-CLASSIFICATION-CHECK": "REFUSED_FOR_MC02_CLASSIFICATION",
    "FI-MC01-TRYPSIN-BENZAMIDINE": "CONDITION_MISMATCH_HOLD",
    "FI-ENZYME-DB-INVENTORY": "CONDITION_AND_EVENT_MAPPING_HOLD",
    "FI-LIPRED-2026-SCREEN": "BARRIER_QUALIFIED_COMPARATOR_MISSING_POOL",
    "FI-BARRIER-ONLY-REPOSITORY-SCREEN": "BARRIER_QUALIFIED_COMPARATOR_MISSING_POOL",
}
PASS_GATES = [
    "classification_gate", "source_gate", "barrier_gate", "comparator_gate",
    "condition_gate", "independence_gate", "representation_gate",
]


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text())


def validate(extension: dict, audit: dict, campaign: dict, baseline: dict, ethylene: dict) -> list[str]:
    errors: list[str] = []

    if extension.get("schema") != "barrier-atlas-family-depth-extension-v0.5":
        errors.append("wrong v0.5 extension schema")
    if audit.get("schema") != "barrier-atlas-mc04-h-propene-addition-source-audit-v0.1":
        errors.append("wrong MC04 propene audit schema")

    for name, doc in [("extension", extension), ("audit", audit), ("campaign", campaign), ("baseline", baseline), ("ethylene", ethylene)]:
        parent = doc.get("parent_release", {})
        if parent:
            if parent.get("immutable") is not True:
                errors.append(f"{name}: parent release must remain immutable")
            if parent.get("workbook_sha256") != EXPECTED_WORKBOOK_SHA:
                errors.append(f"{name}: v0.9 workbook hash drift")
            if parent.get("archive_sha256") != EXPECTED_ARCHIVE_SHA:
                errors.append(f"{name}: v0.9 archive hash drift")

    for name, doc in [("extension", extension), ("audit", audit)]:
        if doc.get("automatic_coordinate_admission") is not False:
            errors.append(f"{name}: automatic coordinate admission must be false")
        if doc.get("coordinates_admitted") != 0:
            errors.append(f"{name}: coordinates_admitted must remain zero")
        if doc.get("grades_changed") != 0:
            errors.append(f"{name}: grades_changed must remain zero")
        firewall = doc.get("selection_firewall", {})
        for key in ["residual_may_select_candidate", "chi_may_select_candidate", "expected_chemsa_agreement_may_select_candidate"]:
            if firewall.get(key) is not False:
                errors.append(f"{name}: selection firewall violated for {key}")

    campaign_targets = {x.get("class_id") for x in campaign.get("target_classes", [])}
    if campaign_targets != EXPECTED_TARGET_CLASSES:
        errors.append("campaign exact 11-class target set drift")
    if set(extension.get("frozen_target_classes", [])) != EXPECTED_TARGET_CLASSES:
        errors.append("v0.5 exact 11-class target set drift")
    if extension.get("frozen_outcomes_reaffirmed") != EXPECTED_FROZEN_OUTCOMES:
        errors.append("v0.5 frozen six-trail outcome map drift")

    by_id = {x.get("trail_id"): x for x in baseline.get("trails", [])}
    cycprop = by_id.get("FI-MC06-CYCLOPROPANE-PROPENE", {})
    if cycprop.get("ready_for_adjudication") is not True or cycprop.get("representation_mode") != "NETWORK_RESOLVED":
        errors.append("baseline MC06 must remain READY only with NETWORK_RESOLVED representation")
    cycbut = by_id.get("FI-MC02-CYCLOBUTENE-CLASSIFICATION-CHECK", {})
    if cycbut.get("terminal_state") != "REFUSED_FOR_MC02_CLASSIFICATION":
        errors.append("baseline cyclobutene must remain refused for MC02")
    for tid, terminal in [
        ("FI-MC01-TRYPSIN-BENZAMIDINE", "CONDITION_MATCH_HOLD"),
        ("FI-ENZYME-DB-INVENTORY", "CONDITION_AND_EVENT_MAPPING_HOLD"),
        ("FI-LIPRED-2026-SCREEN", "COMPARATOR_MISSING"),
        ("FI-BARRIER-ONLY-REPOSITORY-SCREEN", "BARRIER_HALF_TRAIL_COMPARATOR_MISSING"),
    ]:
        if by_id.get(tid, {}).get("terminal_state") != terminal:
            errors.append(f"baseline frozen trail drift: {tid}")

    if ethylene.get("trail_id") != "FI-MC04-H-ETHYLENE-ADDITION":
        errors.append("held ethylene trail identity drift")
    if ethylene.get("ready_for_adjudication") is not False:
        errors.append("held ethylene trail may not be silently promoted")
    if ethylene.get("highest_contiguous_promotion_state") != "BARRIER_QUALIFIED":
        errors.append("held ethylene trail promotion state drift")
    if ethylene.get("terminal_state") != "COMPARATOR_NUMERIC_PROVENANCE_HOLD":
        errors.append("held ethylene trail terminal state drift")

    if audit.get("trail_id") != "FI-MC04-H-PROPENE-ADDITION" or audit.get("target_class") != "MC04":
        errors.append("MC04 propene trail identity/class mismatch")
    for gate in PASS_GATES:
        if not str(audit.get(gate, "")).startswith("PASS"):
            errors.append(f"MC04 propene READY trail has non-PASS {gate}={audit.get(gate)}")
    if audit.get("representation_mode") != "NETWORK_RESOLVED_PARALLEL_ADDITION_HIGH_PRESSURE":
        errors.append("MC04 propene must remain network-resolved parallel addition")
    if audit.get("ready_for_adjudication") is not True or audit.get("terminal_state") != "READY_FOR_ADJUDICATION":
        errors.append("MC04 propene ready/terminal state mismatch")
    if audit.get("automatic_admission") is not False:
        errors.append("MC04 propene READY may not auto-admit")

    profile = audit.get("theory_source", {}).get("barrier_profile", [])
    values = {x.get("channel"): x for x in profile}
    expected = {
        "internal H addition forming n-C3H7": 15.61,
        "terminal H addition forming i-C3H7": 8.39,
    }
    if set(values) != set(expected):
        errors.append("MC04 propene barrier profile must contain exactly the two registered entry channels")
    for channel, value in expected.items():
        rec = values.get(channel, {})
        if rec.get("value") != value or rec.get("unit") != "kJ/mol":
            errors.append(f"MC04 propene barrier value drift for {channel}")
        if "activation enthalpy at 0 K" not in str(rec.get("type", "")):
            errors.append(f"MC04 propene barrier typing drift for {channel}")
        if rec.get("free_energy") is not False or rec.get("arrhenius_activation_energy") is not False:
            errors.append(f"MC04 propene barrier was relabeled for {channel}")

    comp = audit.get("experimental_comparator", {})
    if comp.get("temperature_K") != 298.0:
        errors.append("MC04 propene comparator temperature drift")
    if comp.get("rate_constant") != 1.61e-12 or comp.get("uncertainty") != 0.04e-12:
        errors.append("MC04 propene comparator value/uncertainty drift")
    if comp.get("unit") != "cm^3 molecule^-1 s^-1":
        errors.append("MC04 propene comparator unit drift")
    if "high-pressure" not in str(comp.get("observable", "")):
        errors.append("MC04 propene comparator must remain explicitly high-pressure limiting")

    aggregate = extension.get("aggregate", {})
    if aggregate.get("new_ready_for_adjudication") != 1 or aggregate.get("new_ready_class") != "MC04":
        errors.append("v0.5 new READY aggregate mismatch")
    if aggregate.get("new_ready_trail") != "FI-MC04-H-PROPENE-ADDITION":
        errors.append("v0.5 new READY trail mismatch")
    if set(aggregate.get("family_depth_classes_with_additive_ready_second_family", [])) != EXPECTED_READY_CLASSES:
        errors.append("v0.5 READY class set mismatch")
    if aggregate.get("ready_second_family_count") != 4 or aggregate.get("target_class_count") != 11:
        errors.append("v0.5 family-depth counts mismatch")
    if aggregate.get("coordinates_admitted") != 0 or aggregate.get("grades_changed") != 0:
        errors.append("v0.5 aggregate may not mutate v0.9")

    preserved = extension.get("preserved_nonpromotion_states", {})
    if preserved.get("FI-MC04-H-ETHYLENE-ADDITION") != "COMPARATOR_NUMERIC_PROVENANCE_HOLD":
        errors.append("v0.5 must preserve ethylene comparator provenance hold")

    return errors


def main() -> None:
    root = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser()
    ap.add_argument("--extension", default=root / "FAMILY_DEPTH_EXTENSION_v0.5.json")
    ap.add_argument("--audit", default=root / "MC04_H_PROPENE_ADDITION_SOURCE_AUDIT_v0.1.json")
    ap.add_argument("--campaign", default=root / "FAMILY_INDEPENDENCE_CAMPAIGN_v0.1.json")
    ap.add_argument("--baseline", default=root / "SIX_TRAIL_ADJUDICATION_v0.1.json")
    ap.add_argument("--ethylene", default=root / "MC04_H_ETHYLENE_ADDITION_SOURCE_AUDIT_v0.1.json")
    args = ap.parse_args()

    errors = validate(
        load_json(args.extension),
        load_json(args.audit),
        load_json(args.campaign),
        load_json(args.baseline),
        load_json(args.ethylene),
    )
    if errors:
        print(json.dumps({"status": "FAIL", "errors": errors}, indent=2))
        raise SystemExit(1)
    print(json.dumps({
        "status": "PASS",
        "new_ready_trail": "FI-MC04-H-PROPENE-ADDITION",
        "representation": "NETWORK_RESOLVED_PARALLEL_ADDITION_HIGH_PRESSURE",
        "ready_second_family_count": 4,
        "target_class_count": 11,
        "parent_mutated": False,
    }, indent=2))


if __name__ == "__main__":
    main()
