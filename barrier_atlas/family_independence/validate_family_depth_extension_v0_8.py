#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED_CLASSES = ["MC01", "MC02", "MC04", "MC05", "MC06", "MC08", "MC11", "MC13", "MC14", "MC15", "MC16"]
EXPECTED_WORKBOOK_SHA = "1c287d2e8e82826e1353fabad09812efdb5147fb28a00c9cb398278942ea7a7e"
EXPECTED_ARCHIVE_SHA = "8ffd3319b968eb230552fc74269788f623ad76b2af9976504ec0341f8bf0ef6c"
EXPECTED_PARENT_READY = ["MC02", "MC04", "MC06", "MC11", "MC14", "MC16"]
EXPECTED_READY = ["MC02", "MC04", "MC05", "MC06", "MC11", "MC14", "MC16"]


def load(name: str):
    return json.loads((ROOT / name).read_text())


def validate(ext: dict, audit: dict, campaign: dict, six: dict, parent: dict, held_mc05: dict) -> list[str]:
    errors: list[str] = []

    if ext.get("schema") != "barrier-atlas-family-depth-extension-v0.8":
        errors.append("wrong v0.8 extension schema")
    if audit.get("schema") != "barrier-atlas-mc05-ethyl-acetate-beta-elimination-source-audit-v0.1":
        errors.append("wrong MC05 ethyl-acetate source-audit schema")
    if ext.get("parent_family_depth_extension") != "barrier_atlas/family_independence/FAMILY_DEPTH_EXTENSION_v0.7.json":
        errors.append("v0.8 must extend v0.7")

    for obj, label in [(ext, "extension"), (audit, "source audit")]:
        parent_release = obj.get("parent_release", {})
        if parent_release.get("immutable") is not True:
            errors.append(f"{label}: v0.9 must remain immutable")
        if parent_release.get("workbook_sha256") != EXPECTED_WORKBOOK_SHA:
            errors.append(f"{label}: v0.9 workbook hash drift")
        if parent_release.get("archive_sha256") != EXPECTED_ARCHIVE_SHA:
            errors.append(f"{label}: v0.9 archive hash drift")
        if obj.get("automatic_coordinate_admission") is not False:
            errors.append(f"{label}: automatic admission must be false")
        if obj.get("coordinates_admitted") != 0:
            errors.append(f"{label}: coordinates_admitted must remain zero")
        if obj.get("grades_changed") != 0:
            errors.append(f"{label}: grades_changed must remain zero")
        firewall = obj.get("selection_firewall", {})
        for key in ["residual_may_select_candidate", "chi_may_select_candidate", "expected_chemsa_agreement_may_select_candidate", "same_target_fit_or_method_selection_may_validate_target"]:
            if firewall.get(key) is not False:
                errors.append(f"{label}: firewall violated for {key}")

    if ext.get("frozen_target_classes") != EXPECTED_CLASSES:
        errors.append("frozen 11 target classes drift")
    campaign_classes = [x.get("class_id") for x in campaign.get("target_classes", [])]
    if campaign_classes != EXPECTED_CLASSES:
        errors.append("campaign target-class order/content drift")

    required_frozen = {
        "FI-MC06-CYCLOPROPANE-PROPENE": "READY_FOR_ADJUDICATION_NETWORK_RESOLVED_NOT_ADMITTED",
        "FI-MC02-CYCLOBUTENE-CLASSIFICATION-CHECK": "REFUSED_FOR_MC02_CLASSIFICATION",
        "FI-MC01-TRYPSIN-BENZAMIDINE": "CONDITION_MISMATCH_HOLD",
        "FI-ENZYME-DB-INVENTORY": "CONDITION_AND_EVENT_MAPPING_HOLD",
        "FI-LIPRED-2026-SCREEN": "BARRIER_QUALIFIED_COMPARATOR_MISSING_POOL",
        "FI-BARRIER-ONLY-REPOSITORY-SCREEN": "BARRIER_QUALIFIED_COMPARATOR_MISSING_POOL",
    }
    if ext.get("frozen_outcomes_reaffirmed") != required_frozen:
        errors.append("frozen six-trail outcomes drift")

    six_by_id = {r.get("trail_id"): r for r in six.get("trails", [])}
    cycprop = six_by_id.get("FI-MC06-CYCLOPROPANE-PROPENE", {})
    if cycprop.get("ready_for_adjudication") is not True or cycprop.get("representation_mode") != "NETWORK_RESOLVED":
        errors.append("MC06 frozen READY/NETWORK_RESOLVED outcome drift")
    if six_by_id.get("FI-MC02-CYCLOBUTENE-CLASSIFICATION-CHECK", {}).get("terminal_state") != "REFUSED_FOR_MC02_CLASSIFICATION":
        errors.append("cyclobutene refusal was altered")

    parent_agg = parent.get("aggregate", {})
    if parent_agg.get("family_depth_classes_with_additive_ready_second_family") != EXPECTED_PARENT_READY or parent_agg.get("ready_second_family_count") != 6:
        errors.append("v0.7 parent family-depth state drift")

    records = ext.get("records", [])
    if len(records) != 1:
        errors.append("v0.8 must add exactly one record")
        return errors
    rec = records[0]
    if rec.get("trail_id") != "FI-MC05-ETHYL-ACETATE-BETA-ELIMINATION":
        errors.append("wrong v0.8 trail id")
    for gate in ["classification_gate", "source_gate", "barrier_gate", "comparator_gate", "condition_gate", "independence_gate", "representation_gate"]:
        if not str(rec.get(gate, "")).startswith("PASS"):
            errors.append(f"MC05 READY trail has non-PASS {gate}: {rec.get(gate)}")
    if rec.get("ready_for_adjudication") is not True or rec.get("terminal_state") != "READY_FOR_ADJUDICATION":
        errors.append("MC05 ethyl-acetate trail must be READY_FOR_ADJUDICATION")
    if rec.get("automatic_admission") is not False:
        errors.append("MC05 READY may not auto-admit")
    if rec.get("representation_mode") != "SINGLE_BARRIER_CONCERTED_SIX_MEMBERED_BETA_ELIMINATION_HIGH_PRESSURE_LIMIT":
        errors.append("MC05 ethyl-acetate representation drift")

    barrier = rec.get("barrier_quantity", {})
    if abs(float(barrier.get("value", -1)) - 199.5416732268) > 1e-6 or barrier.get("unit") != "kJ/mol":
        errors.append("MC05 activation-enthalpy value/unit drift")
    if barrier.get("temperature_K") != 773.15:
        errors.append("MC05 barrier temperature drift")
    if barrier.get("quantity_origin") != "REPRODUCIBLY_CALCULATED_FROM_SOURCE_SUPPLIED_QUANTITY_AND_EQUATION":
        errors.append("MC05 barrier origin must remain explicit")
    if barrier.get("gibbs_free_energy_status") != "NOT_A_GIBBS_FREE_ENERGY_BARRIER":
        errors.append("MC05 activation enthalpy may not be relabeled as Gibbs barrier")
    if barrier.get("experimental_arrhenius_activation_energy_status") != "NOT_AN_EXPERIMENTAL_ARRHENIUS_ACTIVATION_ENERGY":
        errors.append("MC05 activation enthalpy may not be relabeled as experimental Arrhenius Ea")

    supplied = audit.get("supplied_theory_quantity", {})
    if supplied.get("value") != 205.97 or supplied.get("temperature_K") != 773.15:
        errors.append("MC05 source-supplied theoretical Ea drift")
    aq = audit.get("barrier_quantity", {})
    if abs(float(aq.get("value", -1)) - 199.5416732268) > 1e-6:
        errors.append("MC05 source-audit activation enthalpy drift")

    comp = rec.get("observed_comparator", {})
    if comp.get("primary_source_doi") != "10.1139/v60-196":
        errors.append("MC05 comparator source drift")
    if comp.get("temperature_range_K") != [773.15, 876.15] or comp.get("matched_temperature_K") != 773.15:
        errors.append("MC05 comparator condition window drift")
    if abs(float(comp.get("reproducibly_evaluated_k_inf_s_inverse", -1)) - 0.1057637437) > 1e-9:
        errors.append("MC05 evaluated comparator rate drift")
    if comp.get("rate_derived_arrhenius_activation_energy_role") != "QUARANTINED_NOT_AN_INDEPENDENT_BARRIER_VALIDATOR":
        errors.append("rate-derived experimental activation energy must stay quarantined")

    if audit.get("ready_for_adjudication") is not True or audit.get("terminal_state") != "READY_FOR_ADJUDICATION":
        errors.append("MC05 source audit no longer supports READY")
    if audit.get("representation_mode") != rec.get("representation_mode"):
        errors.append("MC05 source audit and extension representation mismatch")
    if audit.get("observed_comparator", {}).get("matched_temperature_K") != 773.15:
        errors.append("MC05 source-audit exact temperature overlap drift")

    if held_mc05.get("trail_id") != "FI-MC05-ETHYL-CHLORIDE-HCL-ELIMINATION":
        errors.append("held ethyl-chloride MC05 audit missing")
    if held_mc05.get("terminal_state") != "METHOD_SELECTION_AND_PROVENANCE_HOLD" or held_mc05.get("ready_for_adjudication") is not False:
        errors.append("held ethyl-chloride MC05 trail was altered or promoted")
    if ext.get("preserved_nonpromotion_states", {}).get("FI-MC05-ETHYL-CHLORIDE-HCL-ELIMINATION") != "METHOD_SELECTION_AND_PROVENANCE_HOLD":
        errors.append("v0.8 must preserve ethyl-chloride MC05 hold")

    agg = ext.get("aggregate", {})
    if agg.get("family_depth_classes_with_additive_ready_second_family") != EXPECTED_READY:
        errors.append("ready family-depth class list drift")
    if agg.get("ready_second_family_count") != 7 or agg.get("target_class_count") != 11:
        errors.append("family-depth aggregate count drift")
    if agg.get("new_ready_class") != "MC05" or agg.get("new_ready_for_adjudication") != 1:
        errors.append("new MC05 READY aggregate drift")
    if agg.get("coordinates_admitted") != 0 or agg.get("grades_changed") != 0:
        errors.append("v0.8 may not mutate parent coordinates or grades")

    return errors


def main() -> None:
    errors = validate(
        load("FAMILY_DEPTH_EXTENSION_v0.8.json"),
        load("MC05_ETHYL_ACETATE_BETA_ELIMINATION_SOURCE_AUDIT_v0.1.json"),
        load("FAMILY_INDEPENDENCE_CAMPAIGN_v0.1.json"),
        load("SIX_TRAIL_ADJUDICATION_v0.1.json"),
        load("FAMILY_DEPTH_EXTENSION_v0.7.json"),
        load("MC05_ETHYL_CHLORIDE_SOURCE_AUDIT_v0.1.json"),
    )
    if errors:
        print(json.dumps({"status": "FAIL", "errors": errors}, indent=2))
        raise SystemExit(1)
    print(json.dumps({"status": "PASS", "new_ready_class": "MC05", "ready_second_family_count": 7, "parent_mutated": False}, indent=2))


if __name__ == "__main__":
    main()
