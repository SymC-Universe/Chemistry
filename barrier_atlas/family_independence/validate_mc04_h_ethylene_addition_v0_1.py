#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AUDIT = ROOT / "MC04_H_ETHYLENE_ADDITION_SOURCE_AUDIT_v0.1.json"
EXPECTED_WORKBOOK_SHA = "1c287d2e8e82826e1353fabad09812efdb5147fb28a00c9cb398278942ea7a7e"
EXPECTED_ARCHIVE_SHA = "8ffd3319b968eb230552fc74269788f623ad76b2af9976504ec0341f8bf0ef6c"


def validate(record: dict) -> list[str]:
    errors: list[str] = []
    parent = record.get("parent_release", {})
    if record.get("trail_id") != "FI-MC04-H-ETHYLENE-ADDITION":
        errors.append("trail id drift")
    if record.get("target_class") != "MC04":
        errors.append("target class drift")
    if parent.get("immutable") is not True:
        errors.append("v0.9 parent must remain immutable")
    if parent.get("workbook_sha256") != EXPECTED_WORKBOOK_SHA:
        errors.append("v0.9 workbook hash drift")
    if parent.get("archive_sha256") != EXPECTED_ARCHIVE_SHA:
        errors.append("v0.9 archive hash drift")
    if record.get("coordinates_admitted") != 0 or record.get("grades_changed") != 0:
        errors.append("audit may not mutate v0.9 coordinates or grades")

    firewall = record.get("selection_firewall", {})
    for key in (
        "residual_may_select_candidate",
        "chi_may_select_candidate",
        "expected_chemsa_agreement_may_select_candidate",
        "same_target_agreement_may_select_theory_method",
        "garbled_or_inferred_numeric_comparator_may_close_gate",
        "rate_derived_activation_quantity_may_validate_same_rate",
    ):
        if firewall.get(key) is not False:
            errors.append(f"selection firewall violated: {key}")

    barrier = record.get("theory_source", {}).get("barrier_quantity", {})
    if barrier.get("value") != 11.18 or barrier.get("unit") != "kJ/mol":
        errors.append("exact MC04 barrier quantity drift")
    if "activation enthalpy at 0 K" not in str(barrier.get("type", "")):
        errors.append("barrier must retain Delta-dagger H_0K typing")
    if barrier.get("free_energy") is not False or barrier.get("arrhenius_activation_energy") is not False:
        errors.append("0 K activation enthalpy may not be relabeled")

    comparator = record.get("experimental_comparator_trail", {}).get("primary_source", {})
    if comparator.get("doi") != "10.1021/j100296a054":
        errors.append("primary comparator source drift")
    if comparator.get("high_pressure_expression_transcription_status") != "HOLD_SOURCE_RENDERING_LOSES_SUPERSCRIPT_EXPONENTS_AND_UNIT_EXPONENTS":
        errors.append("garbled comparator expression must remain explicitly held")
    if record.get("experimental_comparator_trail", {}).get("comparator_gate") != "HOLD_EXACT_NUMERIC_PRIMARY_OR_AUTHORITATIVE_TRANSCRIPTION":
        errors.append("comparator may not close without exact numeric transcription")

    if record.get("representation_mode") != "PRESSURE_DEPENDENT_ASSOCIATION_WITH_SINGLE_ENTRANCE_BARRIER_AND_MASTER_EQUATION_STABILIZATION":
        errors.append("pressure-dependent association representation drift")
    if record.get("barrier_gate") != "PASS_EXACTLY_TYPED_DELTA_H_DAGGER_0K":
        errors.append("barrier gate drift")
    if record.get("highest_contiguous_promotion_state") != "BARRIER_QUALIFIED":
        errors.append("MC04 trail may not promote past BARRIER_QUALIFIED")
    if record.get("ready_for_adjudication") is not False:
        errors.append("MC04 audit is not READY_FOR_ADJUDICATION")
    if record.get("automatic_admission") is not False:
        errors.append("automatic admission must remain false")
    return errors


def main() -> None:
    record = json.loads(AUDIT.read_text())
    errors = validate(record)
    if errors:
        print(json.dumps({"status": "FAIL", "errors": errors}, indent=2))
        raise SystemExit(1)
    print(json.dumps({
        "status": "PASS",
        "trail_id": record["trail_id"],
        "highest_contiguous_promotion_state": record["highest_contiguous_promotion_state"],
        "ready_for_adjudication": False,
        "parent_mutated": False
    }, indent=2))


if __name__ == "__main__":
    main()
