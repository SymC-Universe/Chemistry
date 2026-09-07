#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXTENSION = ROOT / "FAMILY_DEPTH_EXTENSION_v0.4.json"
CAMPAIGN = ROOT / "FAMILY_INDEPENDENCE_CAMPAIGN_v0.1.json"
BASELINE = ROOT / "SIX_TRAIL_ADJUDICATION_v0.1.json"
PARENT = ROOT / "FAMILY_DEPTH_EXTENSION_v0.3.json"

EXPECTED_CLASSES = ["MC01", "MC02", "MC04", "MC05", "MC06", "MC08", "MC11", "MC13", "MC14", "MC15", "MC16"]
EXPECTED_WORKBOOK_SHA = "1c287d2e8e82826e1353fabad09812efdb5147fb28a00c9cb398278942ea7a7e"
EXPECTED_ARCHIVE_SHA = "8ffd3319b968eb230552fc74269788f623ad76b2af9976504ec0341f8bf0ef6c"
EXPECTED_BASELINE_COMMIT = "7fcedacf5ae485eb11cae2ace51610210ecd2ab6"


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def validate(extension: dict, campaign: dict, baseline: dict, parent: dict) -> list[str]:
    errors: list[str] = []

    if extension.get("schema") != "barrier-atlas-family-depth-extension-v0.4":
        errors.append("wrong v0.4 schema")
    if extension.get("frozen_baseline_commit") != EXPECTED_BASELINE_COMMIT:
        errors.append("frozen baseline commit drift")
    if extension.get("validated_six_trail_run") != 33359415026:
        errors.append("six-trail audit run drift")

    parent_release = extension.get("parent_release", {})
    if parent_release.get("immutable") is not True:
        errors.append("v0.9 parent must remain immutable")
    if parent_release.get("workbook_sha256") != EXPECTED_WORKBOOK_SHA:
        errors.append("v0.9 workbook hash drift")
    if parent_release.get("archive_sha256") != EXPECTED_ARCHIVE_SHA:
        errors.append("v0.9 archive hash drift")
    if extension.get("automatic_coordinate_admission") is not False:
        errors.append("automatic admission must remain false")
    if extension.get("coordinates_admitted") != 0:
        errors.append("v0.4 may not admit coordinates")
    if extension.get("grades_changed") != 0:
        errors.append("v0.4 may not change grades")

    campaign_classes = [x.get("class_id") for x in campaign.get("target_classes", [])]
    if campaign_classes != EXPECTED_CLASSES:
        errors.append("campaign target-class order/content drift")
    if extension.get("frozen_target_classes") != EXPECTED_CLASSES:
        errors.append("v0.4 frozen target classes drift")

    firewall = extension.get("selection_firewall", {})
    for key in [
        "residual_may_select_candidate",
        "chi_may_select_candidate",
        "expected_chemsa_agreement_may_select_candidate",
        "same_target_fit_or_method_selection_may_validate_target",
    ]:
        if firewall.get(key) is not False:
            errors.append(f"selection firewall violated: {key}")

    frozen = extension.get("frozen_outcomes_reaffirmed", {})
    expected_frozen = {
        "FI-MC06-CYCLOPROPANE-PROPENE": "READY_FOR_ADJUDICATION_NETWORK_RESOLVED_NOT_ADMITTED",
        "FI-MC02-CYCLOBUTENE-CLASSIFICATION-CHECK": "REFUSED_FOR_MC02_CLASSIFICATION",
        "FI-MC01-TRYPSIN-BENZAMIDINE": "CONDITION_MISMATCH_HOLD",
        "FI-ENZYME-DB-INVENTORY": "CONDITION_AND_EVENT_MAPPING_HOLD",
        "FI-LIPRED-2026-SCREEN": "BARRIER_QUALIFIED_COMPARATOR_MISSING_POOL",
        "FI-BARRIER-ONLY-REPOSITORY-SCREEN": "BARRIER_QUALIFIED_COMPARATOR_MISSING_POOL",
    }
    if frozen != expected_frozen:
        errors.append("frozen six-trail outcomes drift")

    by_id = {r.get("trail_id"): r for r in extension.get("records", [])}
    if set(by_id) != {"FI-MC15-VASKA-H2-OXIDATIVE-ADDITION", "FI-MC05-ETHYL-CHLORIDE-HCL-ELIMINATION"}:
        errors.append("v0.4 must contain exactly the two registered hold trails")

    vaska = by_id.get("FI-MC15-VASKA-H2-OXIDATIVE-ADDITION", {})
    if vaska.get("target_class") != "MC15":
        errors.append("Vaska trail must remain MC15")
    if vaska.get("barrier_quantity", {}).get("value") != 5.1:
        errors.append("Vaska pinned barrier drift")
    if vaska.get("barrier_quantity", {}).get("type") != "PBE-D3/def2-SVP gas-phase electronic potential-energy activation barrier for H2 activation, evaluated as E(TS)-E(isolated Ir(I) complex)-E(H2)":
        errors.append("Vaska barrier typing drift")
    if vaska.get("observed_comparator", {}).get("source", {}).get("doi") != "10.1021/ja00967a009":
        errors.append("Vaska primary comparator DOI drift")
    if vaska.get("condition_gate") != "HOLD_GAS_PHASE_ELECTRONIC_BARRIER_VS_BENZENE_SOLUTION_RATE":
        errors.append("Vaska condition hold may not be bypassed")
    if vaska.get("highest_contiguous_promotion_state") != "COMPARATOR_QUALIFIED":
        errors.append("Vaska promotion state must stop at COMPARATOR_QUALIFIED")
    if vaska.get("ready_for_adjudication") is not False:
        errors.append("Vaska may not be READY in v0.4")

    ethyl = by_id.get("FI-MC05-ETHYL-CHLORIDE-HCL-ELIMINATION", {})
    if ethyl.get("target_class") != "MC05":
        errors.append("ethyl-chloride trail must remain MC05")
    if ethyl.get("kinetics_first_comparator", {}).get("source", {}).get("doi") != "10.1039/TF9676300643":
        errors.append("ethyl-chloride primary kinetic DOI drift")
    if ethyl.get("barrier_gate") != "HOLD_EXACT_NUMERIC_PARENT_BARRIER_AND_METHOD_SELECTION_AUDIT_INCOMPLETE":
        errors.append("ethyl-chloride barrier hold may not be bypassed")
    if ethyl.get("highest_contiguous_promotion_state") != "SOURCE_QUALIFIED":
        errors.append("ethyl-chloride promotion state must stop at SOURCE_QUALIFIED")
    if ethyl.get("ready_for_adjudication") is not False:
        errors.append("ethyl-chloride may not be READY in v0.4")

    aggregate = extension.get("aggregate", {})
    if aggregate.get("new_ready_for_adjudication") != 0:
        errors.append("v0.4 must add no READY candidates")
    if aggregate.get("family_depth_classes_with_additive_ready_second_family") != ["MC06", "MC11", "MC14"]:
        errors.append("existing READY family-depth set drift")
    if aggregate.get("ready_second_family_count") != 3:
        errors.append("existing READY family-depth count drift")
    if aggregate.get("coordinates_admitted") != 0 or aggregate.get("grades_changed") != 0:
        errors.append("aggregate parent mutation detected")

    parent_ready = parent.get("aggregate", {}).get("family_depth_classes_with_additive_ready_second_family")
    if parent_ready != ["MC06", "MC11", "MC14"]:
        errors.append("v0.3 parent READY set unexpected")
    baseline_by_id = {r.get("trail_id"): r for r in baseline.get("trails", [])}
    if baseline_by_id.get("FI-MC06-CYCLOPROPANE-PROPENE", {}).get("representation_mode") != "NETWORK_RESOLVED":
        errors.append("baseline MC06 network representation drift")
    if baseline_by_id.get("FI-MC02-CYCLOBUTENE-CLASSIFICATION-CHECK", {}).get("terminal_state") != "REFUSED_FOR_MC02_CLASSIFICATION":
        errors.append("baseline MC02 refusal drift")

    return errors


def main() -> None:
    errors = validate(load(EXTENSION), load(CAMPAIGN), load(BASELINE), load(PARENT))
    if errors:
        print(json.dumps({"status": "FAIL", "errors": errors}, indent=2))
        raise SystemExit(1)
    print(json.dumps({
        "status": "PASS",
        "new_ready_for_adjudication": 0,
        "ready_second_family_count": 3,
        "coordinates_admitted": 0,
        "grades_changed": 0,
    }, indent=2))


if __name__ == "__main__":
    main()
