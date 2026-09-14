#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

EXPECTED_TARGET_CLASSES = {
    "MC01", "MC02", "MC04", "MC05", "MC06", "MC08",
    "MC11", "MC13", "MC14", "MC15", "MC16",
}
EXPECTED_WORKBOOK_SHA = "1c287d2e8e82826e1353fabad09812efdb5147fb28a00c9cb398278942ea7a7e"
EXPECTED_ARCHIVE_SHA = "8ffd3319b968eb230552fc74269788f623ad76b2af9976504ec0341f8bf0ef6c"
EXPECTED_BASELINE_COMMIT = "7fcedacf5ae485eb11cae2ace51610210ecd2ab6"
EXPECTED_SIX_TRAIL_RUN = 33359415026


def load_json(name: str) -> dict:
    return json.loads((ROOT / name).read_text())


def validate(extension: dict, campaign: dict, six_trail: dict) -> list[str]:
    errors: list[str] = []

    if extension.get("schema") != "barrier-atlas-family-depth-extension-v0.3":
        errors.append("wrong extension schema")
    if extension.get("frozen_baseline_commit") != EXPECTED_BASELINE_COMMIT:
        errors.append("frozen baseline commit drift")
    if extension.get("validated_six_trail_run") != EXPECTED_SIX_TRAIL_RUN:
        errors.append("validated six-trail run drift")

    parent = extension.get("parent_release", {})
    if parent.get("name") != "Barrier_Height_Rate_Atlas_v0.9":
        errors.append("wrong parent release")
    if parent.get("immutable") is not True:
        errors.append("v0.9 parent must remain immutable")
    if parent.get("workbook_sha256") != EXPECTED_WORKBOOK_SHA:
        errors.append("v0.9 workbook hash drift")
    if parent.get("archive_sha256") != EXPECTED_ARCHIVE_SHA:
        errors.append("v0.9 archive hash drift")
    if extension.get("automatic_coordinate_admission") is not False:
        errors.append("automatic coordinate admission must be false")
    if extension.get("coordinates_admitted") != 0:
        errors.append("extension may not admit coordinates")
    if extension.get("grades_changed") != 0:
        errors.append("extension may not change grades")

    firewall = extension.get("selection_firewall", {})
    for key in (
        "residual_may_select_candidate",
        "chi_may_select_candidate",
        "expected_chemsa_agreement_may_select_candidate",
        "same_target_fit_or_method_selection_may_validate_target",
    ):
        if firewall.get(key) is not False:
            errors.append(f"selection firewall violated: {key}")

    target_ids = {x.get("class_id") for x in campaign.get("target_classes", [])}
    if target_ids != EXPECTED_TARGET_CLASSES:
        errors.append("frozen 11-class target set drift")
    cp = campaign.get("parent_release", {})
    if cp.get("workbook_sha256") != EXPECTED_WORKBOOK_SHA:
        errors.append("campaign workbook hash drift")
    if cp.get("archive_sha256") != EXPECTED_ARCHIVE_SHA:
        errors.append("campaign archive hash drift")

    six_by_id = {
        x.get("trail_id"): x for x in six_trail.get("trails", [])
        if x.get("trail_id")
    }
    if len(six_by_id) != 6 or six_trail.get("trail_count") != 6:
        errors.append("six-trail baseline must remain exactly six trails")

    mc06 = six_by_id.get("FI-MC06-CYCLOPROPANE-PROPENE", {})
    if mc06.get("terminal_state") != "READY_FOR_ADJUDICATION":
        errors.append("MC06 baseline READY state drift")
    if mc06.get("ready_for_adjudication") is not True:
        errors.append("MC06 baseline ready flag drift")
    if mc06.get("representation_mode") != "NETWORK_RESOLVED":
        errors.append("MC06 baseline representation must remain NETWORK_RESOLVED")

    mc02_refused = six_by_id.get("FI-MC02-CYCLOBUTENE-CLASSIFICATION-CHECK", {})
    if mc02_refused.get("terminal_state") != "REFUSED_FOR_MC02_CLASSIFICATION":
        errors.append("cyclobutene refusal state drift")
    if mc02_refused.get("ready_for_adjudication") is not False:
        errors.append("cyclobutene refusal cannot become ready")

    trypsin = six_by_id.get("FI-MC01-TRYPSIN-BENZAMIDINE", {})
    if trypsin.get("highest_contiguous_promotion_state") != "COMPARATOR_QUALIFIED":
        errors.append("trypsin baseline promotion state drift")
    if trypsin.get("ready_for_adjudication") is not False:
        errors.append("trypsin baseline cannot become ready in extension")

    mc13 = six_by_id.get("FI-ENZYME-DB-INVENTORY", {})
    if mc13.get("terminal_state") != "CONDITION_AND_EVENT_MAPPING_HOLD":
        errors.append("MC13 1B25 baseline hold drift")
    if mc13.get("ready_for_adjudication") is not False:
        errors.append("MC13 1B25 baseline cannot become ready in extension")

    for pool_id in ("FI-LIPRED-2026-SCREEN", "FI-BARRIER-ONLY-REPOSITORY-SCREEN"):
        pool = six_by_id.get(pool_id, {})
        if pool.get("highest_contiguous_promotion_state") != "BARRIER_QUALIFIED":
            errors.append(f"{pool_id}: barrier-qualified pool state drift")
        if pool.get("ready_for_adjudication") is not False:
            errors.append(f"{pool_id}: candidate pool cannot become ready wholesale")

    records = extension.get("records", [])
    if len(records) != 1:
        errors.append("v0.3 extension must contain exactly one new trail")
        return errors

    rec = records[0]
    if rec.get("trail_id") != "FI-MC14-CL-CH4-HAT":
        errors.append("unexpected v0.3 trail ID")
    if rec.get("target_class") != "MC14":
        errors.append("new trail must target MC14")
    if rec.get("classification_gate") != "PASS_MC14_HYDROGEN_ATOM_TRANSFER":
        errors.append("MC14 classification gate drift")
    if not str(rec.get("source_gate", "")).startswith("PASS"):
        errors.append("MC14 source gate must pass")
    if rec.get("barrier_gate") != "PASS_EXACTLY_TYPED_ZERO_POINT_CORRECTED_AB_INITIO_BARRIER":
        errors.append("MC14 exact barrier typing gate drift")

    barrier = rec.get("barrier_quantity", {})
    if barrier.get("value") != 4.87 or barrier.get("unit") != "kcal/mol":
        errors.append("MC14 registered ZPE-corrected barrier drift")
    if "zero-point-energy-corrected" not in str(barrier.get("type", "")).lower():
        errors.append("MC14 barrier must retain ZPE-corrected typing")
    if "free energy" in str(barrier.get("type", "")).lower():
        errors.append("MC14 barrier may not be relabeled as free energy")
    source = barrier.get("source", {})
    if source.get("doi") != "10.1021/j100099a021" or source.get("year") != 1994:
        errors.append("MC14 barrier source provenance drift")

    if rec.get("comparator_gate") != "PASS_INDEPENDENT_PRIMARY_DIRECT_KINETICS":
        errors.append("MC14 comparator gate drift")
    comparator = rec.get("observed_comparator", {})
    comp_source = comparator.get("source", {})
    if comp_source.get("doi") != "10.1021/jp0257909" or comp_source.get("year") != 2002:
        errors.append("MC14 comparator provenance drift")
    if comparator.get("measured_temperature_range_K") != [295.0, 1104.0]:
        errors.append("MC14 measured temperature range drift")
    if comparator.get("measured_pressure_range_Torr") != [1.4, 8.8]:
        errors.append("MC14 measured pressure range drift")
    expected_expr = "k(T)=1.30e-19*T^2.69*exp(-497 K/T) cm^3 molecule^-1 s^-1"
    if comparator.get("rate_expression") != expected_expr:
        errors.append("MC14 primary experimental rate expression drift")
    if source.get("year", 9999) >= comp_source.get("year", 0):
        errors.append("MC14 chronology no longer blocks comparator fitting")

    if rec.get("condition_gate") != "PASS_GAS_PHASE_ELEMENTARY_BIMOLECULAR_MAPPING":
        errors.append("MC14 condition gate drift")
    if rec.get("independence_gate") != "PASS_DISTINCT_FAMILY_AND_TARGET_RATE_NOT_USED_TO_FIT_BARRIER":
        errors.append("MC14 independence gate drift")
    if rec.get("representation_mode") != "SINGLE_BARRIER_ATOM_TRANSFER":
        errors.append("MC14 representation mode drift")
    if rec.get("highest_contiguous_promotion_state") != "READY_FOR_ADJUDICATION":
        errors.append("MC14 promotion state drift")
    if rec.get("terminal_state") != "READY_FOR_ADJUDICATION":
        errors.append("MC14 terminal state drift")
    if rec.get("ready_for_adjudication") is not True:
        errors.append("MC14 ready flag drift")
    if rec.get("automatic_admission") is not False:
        errors.append("MC14 READY may not auto-admit")

    diag = rec.get("post_gate_diagnostic", {})
    if diag.get("selection_role") != "NONE":
        errors.append("MC14 post-gate diagnostic must be non-voting")
    for key in (
        "residual_calculation_required_for_promotion",
        "chi_calculation_required_for_promotion",
        "expected_chemsa_agreement_required_for_promotion",
    ):
        if diag.get(key) is not False:
            errors.append(f"MC14 forbidden promotion dependency: {key}")

    aggregate = extension.get("aggregate", {})
    if aggregate.get("new_ready_for_adjudication") != 1:
        errors.append("v0.3 aggregate new READY count drift")
    if aggregate.get("new_ready_class") != "MC14":
        errors.append("v0.3 aggregate ready class drift")
    if aggregate.get("family_depth_classes_with_additive_ready_second_family") != ["MC06", "MC11", "MC14"]:
        errors.append("additive READY family-depth list drift")
    if aggregate.get("ready_second_family_count") != 3:
        errors.append("additive READY family-depth count drift")
    if aggregate.get("target_class_count") != 11:
        errors.append("target class count drift")
    if aggregate.get("coordinates_admitted") != 0 or aggregate.get("grades_changed") != 0:
        errors.append("aggregate reports forbidden v0.9 mutation")

    return errors


def main() -> None:
    errors = validate(
        load_json("FAMILY_DEPTH_EXTENSION_v0.3.json"),
        load_json("FAMILY_INDEPENDENCE_CAMPAIGN_v0.1.json"),
        load_json("SIX_TRAIL_ADJUDICATION_v0.1.json"),
    )
    if errors:
        print(json.dumps({"status": "FAIL", "errors": errors}, indent=2))
        raise SystemExit(1)
    print(json.dumps({
        "status": "PASS",
        "new_ready_for_adjudication": "FI-MC14-CL-CH4-HAT",
        "ready_second_family_count": 3,
        "parent_mutated": False,
        "coordinates_admitted": 0,
        "grades_changed": 0,
    }, indent=2))


if __name__ == "__main__":
    main()
