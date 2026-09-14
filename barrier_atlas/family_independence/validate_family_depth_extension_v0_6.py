#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED_CLASSES = ["MC01", "MC02", "MC04", "MC05", "MC06", "MC08", "MC11", "MC13", "MC14", "MC15", "MC16"]
EXPECTED_WORKBOOK_SHA = "1c287d2e8e82826e1353fabad09812efdb5147fb28a00c9cb398278942ea7a7e"
EXPECTED_ARCHIVE_SHA = "8ffd3319b968eb230552fc74269788f623ad76b2af9976504ec0341f8bf0ef6c"
EXPECTED_READY = ["MC02", "MC04", "MC06", "MC11", "MC14"]


def load(name: str):
    return json.loads((ROOT / name).read_text())


def validate(ext: dict, audit: dict, campaign: dict, six: dict) -> list[str]:
    errors: list[str] = []

    if ext.get("schema") != "barrier-atlas-family-depth-extension-v0.6":
        errors.append("wrong v0.6 extension schema")
    if audit.get("schema") != "barrier-atlas-mc02-n2o-dissociation-source-audit-v0.1":
        errors.append("wrong MC02 source-audit schema")

    for obj, label in [(ext, "extension"), (audit, "source audit")]:
        parent = obj.get("parent_release", {})
        if parent.get("immutable") is not True:
            errors.append(f"{label}: v0.9 must remain immutable")
        if parent.get("workbook_sha256") != EXPECTED_WORKBOOK_SHA:
            errors.append(f"{label}: v0.9 workbook hash drift")
        if parent.get("archive_sha256") != EXPECTED_ARCHIVE_SHA:
            errors.append(f"{label}: v0.9 archive hash drift")
        if obj.get("automatic_coordinate_admission") is not False:
            errors.append(f"{label}: automatic admission must be false")
        if obj.get("coordinates_admitted") != 0:
            errors.append(f"{label}: coordinates_admitted must remain zero")
        if obj.get("grades_changed") != 0:
            errors.append(f"{label}: grades_changed must remain zero")
        fw = obj.get("selection_firewall", {})
        for key in ["residual_may_select_candidate", "chi_may_select_candidate", "expected_chemsa_agreement_may_select_candidate", "same_target_fit_or_method_selection_may_validate_target"]:
            if fw.get(key) is not False:
                errors.append(f"{label}: firewall violated for {key}")

    if ext.get("frozen_target_classes") != EXPECTED_CLASSES:
        errors.append("frozen 11 target classes drift")
    campaign_classes = [x.get("class_id") for x in campaign.get("target_classes", [])]
    if campaign_classes != EXPECTED_CLASSES:
        errors.append("campaign target-class order/content drift")

    frozen = ext.get("frozen_outcomes_reaffirmed", {})
    required = {
        "FI-MC06-CYCLOPROPANE-PROPENE": "READY_FOR_ADJUDICATION_NETWORK_RESOLVED_NOT_ADMITTED",
        "FI-MC02-CYCLOBUTENE-CLASSIFICATION-CHECK": "REFUSED_FOR_MC02_CLASSIFICATION",
        "FI-MC01-TRYPSIN-BENZAMIDINE": "CONDITION_MISMATCH_HOLD",
        "FI-ENZYME-DB-INVENTORY": "CONDITION_AND_EVENT_MAPPING_HOLD",
        "FI-LIPRED-2026-SCREEN": "BARRIER_QUALIFIED_COMPARATOR_MISSING_POOL",
        "FI-BARRIER-ONLY-REPOSITORY-SCREEN": "BARRIER_QUALIFIED_COMPARATOR_MISSING_POOL",
    }
    if frozen != required:
        errors.append("frozen six-trail outcomes drift")

    six_by_id = {r.get("trail_id"): r for r in six.get("trails", [])}
    if six_by_id.get("FI-MC02-CYCLOBUTENE-CLASSIFICATION-CHECK", {}).get("terminal_state") != "REFUSED_FOR_MC02_CLASSIFICATION":
        errors.append("cyclobutene refusal was altered")
    cycprop = six_by_id.get("FI-MC06-CYCLOPROPANE-PROPENE", {})
    if cycprop.get("ready_for_adjudication") is not True or cycprop.get("representation_mode") != "NETWORK_RESOLVED":
        errors.append("MC06 frozen READY/NETWORK_RESOLVED outcome drift")

    records = ext.get("records", [])
    if len(records) != 1:
        errors.append("v0.6 must add exactly one record")
        return errors
    rec = records[0]
    if rec.get("trail_id") != "FI-MC02-N2O-SPIN-FORBIDDEN-DISSOCIATION":
        errors.append("wrong v0.6 trail id")
    for gate in ["classification_gate", "source_gate", "barrier_gate", "comparator_gate", "condition_gate", "independence_gate", "representation_gate"]:
        if not str(rec.get(gate, "")).startswith("PASS"):
            errors.append(f"MC02 READY trail has non-PASS {gate}: {rec.get(gate)}")
    if rec.get("ready_for_adjudication") is not True or rec.get("terminal_state") != "READY_FOR_ADJUDICATION":
        errors.append("MC02 trail must be READY_FOR_ADJUDICATION")
    if rec.get("automatic_admission") is not False:
        errors.append("MC02 READY may not auto-admit")
    if rec.get("representation_mode") != "NETWORK_RESOLVED_NONADIABATIC_SPIN_CROSSING_DISSOCIATION_HIGH_PRESSURE_LIMIT":
        errors.append("MC02 representation must retain nonadiabatic network/falloff semantics")
    barrier = rec.get("barrier_quantity", {})
    if barrier.get("value") != 60.1 or barrier.get("unit") != "kcal/mol" or "crossing-point" not in str(barrier.get("type", "")):
        errors.append("MC02 barrier quantity/type drift")
    comp = rec.get("observed_comparator", {})
    if comp.get("temperature_range_K") != [1570.0, 3100.0] or comp.get("pressure_range_atm") != [0.3, 450.0]:
        errors.append("MC02 comparator condition range drift")
    if "10^(12.1 +/- 0.4)" not in str(comp.get("high_pressure_limit_expression", "")):
        errors.append("MC02 high-pressure comparator expression drift")

    audit_rec_ready = audit.get("ready_for_adjudication") is True and audit.get("terminal_state") == "READY_FOR_ADJUDICATION"
    if not audit_rec_ready:
        errors.append("source audit no longer supports READY")
    if audit.get("representation_mode") != rec.get("representation_mode"):
        errors.append("source audit and extension representation mismatch")
    if audit.get("barrier_source", {}).get("reported_quantity", {}).get("free_energy_status") != "NOT_A_GIBBS_FREE_ENERGY_BARRIER":
        errors.append("MSX quantity may not be relabeled as Gibbs barrier")
    if audit.get("barrier_source", {}).get("source_theoretical_rate_expression_quarantine", {}).get("role") != "REPRESENTATION_AND_PROVENANCE_ONLY_NOT_SELECTION_OR_INDEPENDENT_COMPARATOR":
        errors.append("theory rate-agreement quarantine missing")

    agg = ext.get("aggregate", {})
    if agg.get("family_depth_classes_with_additive_ready_second_family") != EXPECTED_READY:
        errors.append("ready family-depth class list drift")
    if agg.get("ready_second_family_count") != 5 or agg.get("target_class_count") != 11:
        errors.append("family-depth aggregate count drift")
    if agg.get("new_ready_class") != "MC02" or agg.get("new_ready_for_adjudication") != 1:
        errors.append("new MC02 READY aggregate drift")

    return errors


def main() -> None:
    errors = validate(
        load("FAMILY_DEPTH_EXTENSION_v0.6.json"),
        load("MC02_N2O_DISSOCIATION_SOURCE_AUDIT_v0.1.json"),
        load("FAMILY_INDEPENDENCE_CAMPAIGN_v0.1.json"),
        load("SIX_TRAIL_ADJUDICATION_v0.1.json"),
    )
    if errors:
        print(json.dumps({"status": "FAIL", "errors": errors}, indent=2))
        raise SystemExit(1)
    print(json.dumps({"status": "PASS", "new_ready_class": "MC02", "ready_second_family_count": 5, "parent_mutated": False}, indent=2))


if __name__ == "__main__":
    main()
