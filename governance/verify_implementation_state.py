#!/usr/bin/env python3
"""Fail-closed verifier for protocol deployment-state truth."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GOV11 = ROOT / "governance" / "SCIENTIFIC_CHANGE_CONTROL_PROTOCOL_v1.1.json"
STATUS = ROOT / "governance" / "IMPLEMENTATION_STATUS_v1.0.json"
DECISION = ROOT / "governance" / "decisions" / "DEC-2026-08-30-013.json"
RESTART = ROOT / "systems" / "co_cu111" / "SYSTEM2_QE_NATIVE_CHECKPOINT_RESTART_PROTOCOL_v0.1.json"


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
    reg = load(STATUS)
    dec = load(DECISION)
    restart = load(RESTART)

    require(gov.get("schema") == "symc-scientific-change-control-protocol-v1.1", "wrong governance v1.1 schema")
    require(gov.get("status") == "FROZEN_PROGRAM_GOVERNANCE", "governance v1.1 is not frozen")
    rules = {r.get("id"): r for r in gov.get("hard_rules", [])}
    require({f"GOV-{i:03d}" for i in range(1, 19)}.issubset(rules), "governance v1.1 missing required rule")
    require(rules["GOV-018"].get("name") == "IMPLEMENTATION_CLAIM_REQUIRES_DEPLOYMENT_EVIDENCE",
            "deployment-evidence rule missing")

    vocab = gov.get("implementation_state_vocabulary", {})
    require(set(vocab) == {"FROZEN", "QUALIFIED", "WIRED", "ACTIVE"}, "deployment state vocabulary drift")

    require(reg.get("schema") == "symc-implementation-status-v1.0", "wrong implementation registry schema")
    require(reg.get("status") == "ACTIVE_IMPLEMENTATION_REGISTRY", "implementation registry inactive")
    require(reg.get("state_vocabulary") == ["FROZEN", "QUALIFIED", "WIRED", "ACTIVE"], "implementation registry vocabulary drift")
    comps = reg.get("components", {})

    pg = comps.get("program_governance", {})
    require(pg.get("protocol") == "governance/SCIENTIFIC_CHANGE_CONTROL_PROTOCOL_v1.1.json", "program governance protocol pointer drift")
    require(pg.get("state") in {"FROZEN", "QUALIFIED", "WIRED", "ACTIVE"}, "invalid program governance state")
    if pg.get("state") == "ACTIVE":
        require(pg.get("qualification_or_audit_run_id") is not None, "ACTIVE governance lacks audit run")
        require(bool(pg.get("production_commit")), "ACTIVE governance lacks production commit")
        require(pg.get("production_workflow") == ".github/workflows/program-governance-audit.yml", "ACTIVE governance workflow drift")
        require(pg.get("production_active") is True, "ACTIVE governance registry flag false")
    else:
        require(pg.get("production_active") is False, "non-ACTIVE governance cannot claim production active")

    qe = comps.get("qe_native_checkpoint_restart", {})
    require(qe.get("protocol") == "systems/co_cu111/SYSTEM2_QE_NATIVE_CHECKPOINT_RESTART_PROTOCOL_v0.1.json",
            "QE checkpoint protocol pointer drift")
    require(qe.get("state") in {"FROZEN", "QUALIFIED", "WIRED", "ACTIVE"}, "invalid QE checkpoint state")
    require(qe.get("qualification_required") is True, "QE checkpoint qualification requirement disabled")
    if qe.get("state") == "ACTIVE":
        require(qe.get("qualification_run_id") is not None, "ACTIVE QE checkpoint lacks qualification run")
        require(bool(qe.get("production_commit")), "ACTIVE QE checkpoint lacks production commit")
        require(bool(qe.get("production_workflow")), "ACTIVE QE checkpoint lacks production workflow")
        require(qe.get("production_active") is True, "ACTIVE QE checkpoint registry flag false")
    else:
        require(qe.get("production_active") is False, "non-ACTIVE QE checkpoint cannot claim production protection")

    legacy = comps.get("l15_runtime_recovery_run_33329096616", {})
    require(legacy.get("run_id") == 33329096616, "legacy L15 run identity drift")
    require(legacy.get("architecture") == "LEGACY_EXTERNAL_WRAPPER_NO_NATIVE_ELECTRONIC_CHECKPOINT",
            "legacy L15 architecture was rewritten")
    require(legacy.get("native_checkpoint_protected") is False,
            "legacy L15 run incorrectly claims native checkpoint protection")
    require(legacy.get("successor_identical_unsalvageable_retry_allowed") is False,
            "legacy L15 run reopened unsalvageable retry")

    require(dec.get("schema") == "symc-program-decision-v1.0", "wrong deployment correction decision schema")
    require(dec.get("id") == "DEC-2026-08-30-013" and dec.get("status") == "ACTIVE",
            "deployment correction decision missing")
    ev = dec.get("triggering_evidence", {})
    require(ev.get("run_id") == 33329096616, "deployment correction run identity drift")
    require(ev.get("native_checkpoint_protocol_was_wired_into_run") is False,
            "historical native-checkpoint wiring failure was rewritten")

    require(restart.get("status") == "FROZEN_BEFORE_CHECKPOINT_QUALIFICATION_RESULTS",
            "QE checkpoint protocol status drift")

    print("IMPLEMENTATION_STATE_AUDIT_PASS")
    print("DEPLOYMENT_STATE_VOCABULARY=FROZEN,QUALIFIED,WIRED,ACTIVE")
    print("LEGACY_RUN_33329096616_NATIVE_CHECKPOINT_PROTECTED=false")
    print("QE_NATIVE_CHECKPOINT_STATE=" + str(qe.get("state")))
    print("PROGRAM_GOVERNANCE_STATE=" + str(pg.get("state")))


if __name__ == "__main__":
    main()
