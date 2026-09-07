#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

EXPECTED_WORKBOOK_SHA = "1c287d2e8e82826e1353fabad09812efdb5147fb28a00c9cb398278942ea7a7e"
EXPECTED_ARCHIVE_SHA = "8ffd3319b968eb230552fc74269788f623ad76b2af9976504ec0341f8bf0ef6c"
EXPECTED_READY = ["MC02", "MC04", "MC06", "MC11", "MC14", "MC16"]


def load(path: str | Path) -> dict:
    return json.loads(Path(path).read_text())


def validate(rec: dict) -> list[str]:
    errors: list[str] = []
    if rec.get("schema") != "barrier-atlas-mc08-chloride-methyl-chloride-identity-sn2-source-audit-v0.1":
        errors.append("wrong schema")
    if rec.get("frozen_baseline_commit") != "7fcedacf5ae485eb11cae2ace51610210ecd2ab6":
        errors.append("frozen baseline drift")
    if rec.get("validated_six_trail_run") != 33359415026:
        errors.append("six-trail audit run drift")

    parent = rec.get("parent_release", {})
    if parent.get("name") != "Barrier_Height_Rate_Atlas_v0.9" or parent.get("immutable") is not True:
        errors.append("v0.9 parent must remain immutable")
    if parent.get("workbook_sha256") != EXPECTED_WORKBOOK_SHA:
        errors.append("v0.9 workbook hash drift")
    if parent.get("archive_sha256") != EXPECTED_ARCHIVE_SHA:
        errors.append("v0.9 archive hash drift")
    if rec.get("coordinates_admitted") != 0 or rec.get("grades_changed") != 0:
        errors.append("audit may not admit coordinates or change grades")
    if rec.get("automatic_coordinate_admission") is not False or rec.get("automatic_admission") is not False:
        errors.append("automatic admission must remain false")

    fw = rec.get("selection_firewall", {})
    for key in [
        "residual_may_select_candidate",
        "chi_may_select_candidate",
        "expected_chemsa_agreement_may_select_candidate",
        "cross_section_may_be_silently_relabelled_as_rate_constant",
        "estimated_activation_free_energy_may_be_silently_relabelled_as_direct_experiment",
    ]:
        if fw.get(key) is not False:
            errors.append(f"selection/type firewall violated: {key}")

    if rec.get("trail_id") != "FI-MC08-CL-CH3CL-IDENTITY-SN2" or rec.get("target_class") != "MC08":
        errors.append("wrong trail identity or target class")
    if not str(rec.get("classification_gate", "")).startswith("PASS_PROVISIONAL_MC08"):
        errors.append("MC08 classification must remain provisional-pass only")
    if not str(rec.get("barrier_gate", "")).startswith("PASS_TYPED"):
        errors.append("typed barrier gate must pass")

    barrier = rec.get("barrier_evidence", {}).get("quantity", {})
    if barrier.get("value_kJ_per_mol") != 11.5:
        errors.append("registered gas-phase back-side barrier drift")
    if "overall gas-phase barrier" not in str(barrier.get("type", "")):
        errors.append("barrier quantity typing lost")

    scattering = rec.get("direct_experimental_scattering_evidence", {})
    if scattering.get("qualification") != "DIRECT_EXPERIMENT_BUT_NOT_AN_OBSERVED_THERMAL_RATE_CONSTANT":
        errors.append("guided-ion-beam evidence must remain cross-section-only")
    if scattering.get("promotion_role") != "MECHANISM_AND_SCATTERING_SUPPORT_ONLY":
        errors.append("guided-ion-beam evidence may not become the rate comparator")

    aq = rec.get("aqueous_candidate_quarantine", {}).get("direct_measurement_audit", {})
    if aq.get("result") != "NO_DIRECT_EXPERIMENTAL_MEASUREMENT_REPORTED_FOR_THE_26_6_KCAL_PER_MOL_ESTIMATE":
        errors.append("aqueous 26.6 kcal/mol direct-measurement quarantine drift")

    if rec.get("comparator_gate") != "FAIL_NO_QUALIFYING_INDEPENDENT_OBSERVED_RATE_CONSTANT_PINNED":
        errors.append("qualifying observed-rate comparator must remain missing")
    if rec.get("highest_contiguous_promotion_state") != "BARRIER_QUALIFIED":
        errors.append("trail must stop at BARRIER_QUALIFIED")
    if rec.get("terminal_state") != "COMPARATOR_MISSING":
        errors.append("trail must remain COMPARATOR_MISSING")
    if rec.get("ready_for_adjudication") is not False:
        errors.append("trail must not become READY")

    agg = rec.get("aggregate_effect", {})
    if agg.get("ready_second_family_count") != 6 or agg.get("ready_classes_unchanged") != EXPECTED_READY:
        errors.append("ready family-depth set drift")
    if agg.get("new_ready_for_adjudication") != 0:
        errors.append("audit may not register a new READY candidate")
    return errors


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--audit", required=True)
    args = ap.parse_args()
    errors = validate(load(args.audit))
    if errors:
        print(json.dumps({"status": "FAIL", "errors": errors}, indent=2))
        raise SystemExit(1)
    print(json.dumps({"status": "PASS", "trail": "FI-MC08-CL-CH3CL-IDENTITY-SN2", "state": "COMPARATOR_MISSING", "parent_mutated": False}, indent=2))


if __name__ == "__main__":
    main()
