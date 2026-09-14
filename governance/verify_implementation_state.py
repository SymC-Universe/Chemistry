#!/usr/bin/env python3
"""Fail-closed verifier for Chemistry deployment-state truth."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GOV11 = ROOT / "governance" / "SCIENTIFIC_CHANGE_CONTROL_PROTOCOL_v1.1.json"
STATUS_OLD = ROOT / "governance" / "IMPLEMENTATION_STATUS_v1.0.json"
STATUS = ROOT / "governance" / "IMPLEMENTATION_STATUS_v1.1.json"
DECISION = ROOT / "governance" / "decisions" / "DEC-2026-08-30-013.json"
RESTART = ROOT / "systems" / "co_cu111" / "SYSTEM2_QE_NATIVE_CHECKPOINT_RESTART_PROTOCOL_v0.1.json"

EXPECTED_GOM_SHA256 = "ee3d9955e19f280ad385488180800d1cdb2d5054823cfa2fa6a697ab3f51d396"


def load(path: Path) -> dict:
    obj = json.loads(path.read_text())
    if not isinstance(obj, dict):
        raise SystemExit(f"IMPLEMENTATION_HOLD: JSON root is not an object: {path}")
    return obj


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit("IMPLEMENTATION_HOLD: " + msg)


def main() -> None:
    gov = load(GOV11)
    old = load(STATUS_OLD)
    reg = load(STATUS)
    dec = load(DECISION)
    restart = load(RESTART)

    require(gov.get("schema") == "symc-scientific-change-control-protocol-v1.1", "wrong governance v1.1 schema")
    require(gov.get("status") == "FROZEN_PROGRAM_GOVERNANCE", "governance v1.1 is not frozen")
    rules = {r.get("id"): r for r in gov.get("hard_rules", [])}
    require({f"GOV-{i:03d}" for i in range(1, 19)}.issubset(rules), "governance v1.1 missing required rule")
    require(
        rules["GOV-018"].get("name") == "IMPLEMENTATION_CLAIM_REQUIRES_DEPLOYMENT_EVIDENCE",
        "deployment-evidence rule missing",
    )

    require(old.get("schema") == "symc-implementation-status-v1.0", "historical v1.0 registry schema drift")
    require(reg.get("schema") == "symc-implementation-status-v1.1", "wrong implementation registry schema")
    require(reg.get("status") == "ACTIVE_IMPLEMENTATION_REGISTRY", "implementation registry inactive")
    require(
        reg.get("supersedes") == "governance/IMPLEMENTATION_STATUS_v1.0.json",
        "v1.1 does not preserve v1.0 lineage",
    )
    require(
        reg.get("state_vocabulary") == ["FROZEN", "QUALIFIED", "WIRED", "ACTIVE"],
        "implementation registry vocabulary drift",
    )

    gom = reg.get("program_manual", {})
    require(gom.get("version") == "0.8.0", "current GOM version drift")
    require(gom.get("markdown_sha256") == EXPECTED_GOM_SHA256, "current GOM hash drift")

    comps = reg.get("components", {})

    pg = comps.get("program_governance", {})
    require(pg.get("protocol") == "governance/SCIENTIFIC_CHANGE_CONTROL_PROTOCOL_v1.1.json", "program governance pointer drift")
    require(pg.get("state") == "FROZEN", "program governance overclaims current deployment state")
    require(pg.get("production_active") is False, "program governance incorrectly claims active production")
    require(pg.get("latest_audit_run_id") == 34139049757, "latest governance audit identity drift")
    require(pg.get("latest_audit_conclusion") == "FAILURE_BEFORE_STEPS", "latest governance audit conclusion drift")
    require(pg.get("latest_audit_job_steps_observed") == 0, "latest governance failure was not pre-step")

    qe = comps.get("qe_native_checkpoint_restart", {})
    require(
        qe.get("protocol") == "systems/co_cu111/SYSTEM2_QE_NATIVE_CHECKPOINT_RESTART_PROTOCOL_v0.1.json",
        "QE checkpoint protocol pointer drift",
    )
    require(qe.get("state") == "WIRED", "QE checkpoint current state should be WIRED, not active execution")
    require(qe.get("qualification_required") is True, "QE checkpoint qualification requirement disabled")
    require(qe.get("qualification_status") == "PASS", "QE checkpoint qualification PASS lost")
    require(qe.get("qualification_run_id") == 33343734581, "QE checkpoint qualification run drift")
    require(qe.get("latest_production_run_id") == 33351747179, "QE production run identity drift")
    require(qe.get("latest_production_run_conclusion") == "success", "QE production workflow completion drift")
    require(qe.get("execution_state") == "COMPLETED", "QE production execution state drift")
    require(qe.get("production_active") is False, "completed QE production still claims active execution")
    require(qe.get("scientific_settings_changed") is False, "QE restart changed science")
    require(qe.get("thresholds_changed") is False, "QE restart changed thresholds")

    legacy = comps.get("legacy_l15_runtime_recovery_run_33329096616", {})
    require(legacy.get("run_id") == 33329096616, "legacy L15 run identity drift")
    require(
        legacy.get("architecture") == "LEGACY_EXTERNAL_WRAPPER_NO_NATIVE_ELECTRONIC_CHECKPOINT",
        "legacy L15 architecture was rewritten",
    )
    require(legacy.get("conclusion") == "FAILURE", "legacy L15 failure was rewritten")
    require(legacy.get("native_checkpoint_protected") is False, "legacy L15 run incorrectly claims native checkpoint protection")
    require(
        legacy.get("successor_identical_unsalvageable_retry_allowed") is False,
        "legacy L15 unsalvageable retry was reopened",
    )

    s3 = comps.get("system3_h_ru0001_pbe_bulk_recovery", {})
    require(s3.get("recovery_run_id") == 33351800093, "System 3 recovery run identity drift")
    require(s3.get("recovery_run_conclusion") == "success", "System 3 recovery completion drift")
    require(s3.get("recomputed_qe_cases") == 0, "System 3 zero-recompute recovery was rewritten")
    require(s3.get("execution_state") == "COMPLETED", "System 3 recovery still claims active execution")
    require(s3.get("production_active") is False, "completed System 3 recovery still claims active production")
    require(s3.get("kinetic_inputs_used") is False, "System 3 recovery imported kinetic inputs")
    require(s3.get("cross_system_inference_allowed") is False, "System 3 recovery permits cross-system inference")

    snap = reg.get("current_execution_snapshot", {})
    require(snap.get("checked_date") == "2026-09-14", "execution snapshot date drift")
    require(snap.get("in_progress_run_count") == 0, "registry claims an in-progress GitHub Actions run")
    require(snap.get("queued_run_count") == 0, "registry claims a queued GitHub Actions run")

    disp = reg.get("current_scientific_dispositions", {})
    s2d = disp.get("system2_co_cu111", {})
    s3d = disp.get("system3_h_ru0001", {})
    atlas = disp.get("barrier_height_rate_atlas", {})
    require(s2d.get("status") == "NUMERICAL_HOLD_EXTENSION_AUDIT", "System 2 HOLD was lost or relabeled")
    require(s2d.get("automatic_downstream_progression_allowed") is False, "System 2 HOLD permits automatic progression")
    require(s3d.get("status") == "CLEAN_SURFACE_NUMERICAL_HOLD", "System 3 HOLD was lost or relabeled")
    require(s3d.get("automatic_downstream_progression_allowed") is False, "System 3 HOLD permits automatic progression")
    require(atlas.get("status") == "CLOSED_REPRODUCIBLE_V0.9", "Barrier Atlas v0.9 closure status drift")
    require(atlas.get("depends_on_system2_or_system3_hold_resolution") is False, "Atlas incorrectly depends on surface HOLD resolution")

    flags = reg.get("synchronization_flags", {})
    require(flags.get("scientific_settings_changed") is False, "status synchronization changed scientific settings")
    require(flags.get("thresholds_changed") is False, "status synchronization changed thresholds")
    require(flags.get("acceptance_rule_changed") is False, "status synchronization changed acceptance rule")
    require(flags.get("kinetic_inputs_used") is False, "status synchronization used kinetic inputs")
    require(flags.get("prior_failure_preserved") is True, "status synchronization failed to preserve prior failure")
    require(flags.get("prospective_before_results") is True, "status synchronization is not prospective")

    require(dec.get("schema") == "symc-program-decision-v1.0", "wrong deployment correction decision schema")
    require(dec.get("id") == "DEC-2026-08-30-013" and dec.get("status") == "ACTIVE", "deployment correction decision missing")
    ev = dec.get("triggering_evidence", {})
    require(ev.get("run_id") == 33329096616, "deployment correction run identity drift")
    require(ev.get("native_checkpoint_protocol_was_wired_into_run") is False, "historical native-checkpoint wiring failure was rewritten")

    require(
        restart.get("status") == "FROZEN_BEFORE_CHECKPOINT_QUALIFICATION_RESULTS",
        "QE checkpoint protocol status drift",
    )

    print("IMPLEMENTATION_STATE_AUDIT_PASS")
    print("IMPLEMENTATION_REGISTRY_VERSION=1.1")
    print("GOM_VERSION=0.8.0")
    print("GITHUB_ACTIONS_IN_PROGRESS=0")
    print("GITHUB_ACTIONS_QUEUED=0")
    print("SYSTEM2_STATUS=NUMERICAL_HOLD_EXTENSION_AUDIT")
    print("SYSTEM3_STATUS=CLEAN_SURFACE_NUMERICAL_HOLD")
    print("QE_NATIVE_CHECKPOINT_STATE=WIRED")
    print("PROGRAM_GOVERNANCE_STATE=FROZEN")


if __name__ == "__main__":
    main()
