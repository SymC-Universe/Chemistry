#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AUDIT = ROOT / "MC08_METHANE_ZEOLITE_EXCHANGE_SOURCE_AUDIT_v0.1.json"
EXPECTED_WORKBOOK_SHA = "1c287d2e8e82826e1353fabad09812efdb5147fb28a00c9cb398278942ea7a7e"
EXPECTED_ARCHIVE_SHA = "8ffd3319b968eb230552fc74269788f623ad76b2af9976504ec0341f8bf0ef6c"


def validate(record: dict) -> list[str]:
    errors: list[str] = []
    parent = record.get("parent_release", {})
    if record.get("target_class") != "MC08":
        errors.append("target class drift")
    if record.get("trail_id") != "FI-MC08-METHANE-ZEOLITE-HD-EXCHANGE":
        errors.append("trail id drift")
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
        "rate_derived_activation_energy_may_validate_same_rate",
        "figure_only_rate_may_close_comparator_gate",
    ):
        if firewall.get(key) is not False:
            errors.append(f"selection firewall violated: {key}")
    barrier = record.get("theory_source", {}).get("barrier_quantity", {})
    if barrier.get("value") != 159.71 or barrier.get("unit") != "kJ/mol":
        errors.append("exact MC08 barrier quantity drift")
    if "zero-point-energy" not in str(barrier.get("type", "")):
        errors.append("barrier must retain ZPE-corrected typing")
    experiment = record.get("primary_experiment", {})
    if not str(experiment.get("comparator_gate", "")).startswith("FAIL_NO_TEXT_OR_TABLE_NUMERIC_RAW_RATE"):
        errors.append("figure-only raw rate may not close comparator gate")
    mechanism = record.get("mechanism_audit", {})
    if not str(mechanism.get("mechanism_gate", "")).startswith("HARD_HOLD"):
        errors.append("experimental KIE mechanism hold must remain explicit")
    if record.get("highest_contiguous_promotion_state") != "BARRIER_QUALIFIED":
        errors.append("MC08 may not promote past BARRIER_QUALIFIED")
    if record.get("ready_for_adjudication") is not False:
        errors.append("MC08 audit is not READY_FOR_ADJUDICATION")
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
