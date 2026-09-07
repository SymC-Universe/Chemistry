#!/usr/bin/env python3
"""Fail-closed verifier for program governance and CO/Cu(111) execution contracts."""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GOV = ROOT / "governance" / "SCIENTIFIC_CHANGE_CONTROL_PROTOCOL_v1.0.json"
LEDGER = ROOT / "governance" / "PROGRAM_DECISION_LEDGER_v1.0.json"
QE_RESTART = ROOT / "systems" / "co_cu111" / "SYSTEM2_QE_NATIVE_CHECKPOINT_RESTART_PROTOCOL_v0.1.json"
L15 = ROOT / "systems" / "co_cu111" / "SYSTEM2_PBE_SURFACE_CONVERGENCE_EXTENSION_v0.1.json"


def load(path: Path) -> dict:
    obj = json.loads(path.read_text())
    if not isinstance(obj, dict):
        raise SystemExit(f"GOVERNANCE_HOLD: JSON root is not an object: {path}")
    return obj


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit("GOVERNANCE_HOLD: " + message)


def close(a: float, b: float, tol: float = 0.0) -> bool:
    return math.isclose(float(a), float(b), rel_tol=0.0, abs_tol=tol)


def main() -> None:
    gov = load(GOV)
    ledger = load(LEDGER)
    restart = load(QE_RESTART)
    l15 = load(L15)

    require(gov.get("schema") == "symc-scientific-change-control-protocol-v1.0", "wrong governance schema")
    require(gov.get("status") == "FROZEN_PROGRAM_GOVERNANCE", "governance is not frozen")
    rules = {row.get("id"): row for row in gov.get("hard_rules", [])}
    required_rules = {f"GOV-{i:03d}" for i in range(1, 18)}
    require(required_rules.issubset(rules), "one or more required hard rules are missing")
    for rid in required_rules:
        require(bool(rules[rid].get("requirement")), f"empty requirement for {rid}")

    authority = gov.get("authority", {})
    require(authority.get("scientific_change_requires_explicit_user_authorization_before_execution") is True,
            "scientific preauthorization firewall disabled")
    require(authority.get("safe_mechanical_repairs_may_proceed_without_reauthorization") is True,
            "mechanical autonomy rule missing")
    require(authority.get("mechanical_repairs_must_preserve_scientific_contract") is True,
            "mechanical firewall disabled")

    require(ledger.get("schema") == "symc-program-decision-ledger-v1.0", "wrong decision-ledger schema")
    require(ledger.get("status") == "ACTIVE_APPEND_ONLY_LEDGER", "decision ledger is not append-only active")
    lr = ledger.get("rules", {})
    require(lr.get("entries_may_not_be_deleted") is True, "ledger deletion protection disabled")
    require(lr.get("superseded_entries_remain_visible") is True, "ledger supersession history disabled")
    entries = {row.get("id"): row for row in ledger.get("entries", [])}
    required_decisions = {f"DEC-2026-08-30-{i:03d}" for i in range(1, 13)}
    require(required_decisions.issubset(entries), "one or more frozen 2026-08-30 decisions are missing")
    require(entries["DEC-2026-08-30-006"].get("evidence", {}).get("status") == "NUMERICAL_HOLD",
            "original L11-L13 HOLD was not preserved")
    require(entries["DEC-2026-08-30-009"].get("evidence", {}).get("authoritative_force_blocks") == 0,
            "L15 pre-BFGS timeout evidence drift")

    require(l15.get("schema") == "co-cu111-pbe-surface-convergence-extension-v0.1", "wrong L15 extension schema")
    require(l15.get("status") == "FROZEN_BEFORE_L15_RESULTS", "L15 extension is not prospectively frozen")
    method = l15["frozen_method"]
    audit = l15["extension_audit"]
    execution = l15["execution"]

    require(restart.get("schema") == "co-cu111-qe-native-checkpoint-restart-protocol-v0.1",
            "wrong QE restart schema")
    require(restart.get("status") == "FROZEN_BEFORE_CHECKPOINT_QUALIFICATION_RESULTS",
            "QE restart protocol is not prospectively frozen")
    require(restart.get("scope") == "MECHANICAL_EXECUTION_RECOVERY_ONLY", "restart scope became scientific")

    sc = restart["scientific_contract"]
    for flag in ("scientific_settings_changed", "thresholds_changed", "acceptance_rule_changed", "kinetic_inputs_used"):
        require(sc.get(flag) is False, f"restart scientific firewall changed: {flag}")
    require(sc.get("new_scientific_rung_authorized") is False, "restart protocol authorized a new scientific rung")

    require((int(sc["layers"]), float(sc["vacuum_angstrom"]), int(sc["kmesh"])) ==
            (int(audit["layers"]), float(audit["vacuum_angstrom"]), int(audit["kmesh"])),
            "restart L15/V32/K28 rung drift")
    compare = {
        "exchange_correlation": "exchange_correlation",
        "ecutwfc_ry": "ecutwfc_ry",
        "ecutrho_ry": "ecutrho_ry",
        "assume_isolated": "assume_isolated",
        "esm_bc": "esm_bc",
        "electron_conv_thr": "electron_conv_thr",
        "electron_maxstep": "electron_maxstep",
        "mixing_beta": "mixing_beta",
        "ion_dynamics": "ion_dynamics",
        "force_gate_ev_per_angstrom": "force_gate_ev_per_angstrom",
        "independent_scf_reproduction_gate_ev": "independent_scf_reproduction_gate_ev",
        "surface_excess_convergence_max_ev_per_surface_atom": "surface_excess_convergence_max_ev_per_surface_atom",
    }
    for restart_key, l15_key in compare.items():
        a, b = sc[restart_key], method[l15_key]
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            require(close(a, b, 0.0), f"scientific numeric drift: {restart_key}")
        else:
            require(a == b, f"scientific setting drift: {restart_key}")

    ex = restart["execution_invariants"]
    require(ex.get("execution_mode") == "DIRECT_ONE_RANK" and int(ex.get("mpi_ranks", -1)) == 1,
            "restart execution mode drift")
    require(ex.get("mpi_requalification_allowed") is False, "restart protocol reopened MPI")
    require(ex.get("same_processor_count_and_parallelization_required_for_restart") is True,
            "QE restart processor invariant disabled")
    require(ex.get("rank_selection_sha256") == l15["frozen_sources"]["rank_selection_sha256"],
            "rank-selection provenance drift")
    require(ex.get("pw_x_sha256") == l15["frozen_sources"]["pw_x_sha256"], "pw.x provenance drift")
    require(execution.get("execution_mode") == "DIRECT_ONE_RANK" and int(execution.get("mpi_ranks", -1)) == 1,
            "governing L15 protocol execution drift")

    native = restart["native_checkpoint"]
    require(native.get("clean_stop_mechanism") == "CONTROL.max_seconds", "native clean-stop mechanism changed")
    require(native.get("initial_restart_mode") == "from_scratch" and native.get("resume_restart_mode") == "restart",
            "QE restart modes changed")
    require(native.get("external_wrapper_kill_is_valid_checkpoint") is False,
            "external wrapper kill was incorrectly promoted to checkpoint")
    require(native.get("checkpoint_may_be_used_as_independent_reproduction") is False,
            "checkpoint contaminated independent reproduction")
    require(native.get("disk_io") not in {"nowf", "minimal", "none"}, "disk_io forbids restart")
    max_seconds = int(native["qe_max_seconds_per_chunk"])
    job_seconds = int(native["github_job_timeout_seconds"])
    reserve = int(native["minimum_clean_stop_and_persistence_reserve_seconds"])
    require(max_seconds + reserve <= job_seconds, "insufficient QE clean-stop/persistence reserve")

    persistence = restart["persistence"]
    require(persistence.get("exact_key_restore_only") is True and persistence.get("restore_key_fallback_forbidden") is True,
            "checkpoint cache may restore ambiguous state")
    require(int(persistence.get("checkpoint_entry_soft_max_bytes", 10**20)) < 10_000_000_000,
            "checkpoint soft size cap no longer protects default cache budget")

    qual = restart["qualification_before_production_restart"]
    require(qual.get("required") is True and qual.get("fixture_is_non_evidentiary") is True,
            "restart qualification requirement disabled")
    require(qual.get("must_cross_two_fresh_github_jobs") is True, "restart not tested across fresh runners")
    require(close(qual["energy_absolute_difference_max_ev"], 0.0001, 0.0), "restart energy parity threshold drift")
    require(close(qual["force_component_absolute_difference_max_ev_per_angstrom"], 0.0001, 0.0),
            "restart force parity threshold drift")

    repro = restart["independent_reproduction"]
    require(repro.get("required_after_relax_complete") is True, "final independent reproduction disabled")
    require(repro.get("restart_mode") == "from_scratch" and repro.get("electronic_checkpoint_reuse") is False,
            "final reproduction is no longer independent")
    require(close(repro["acceptance_gate_ev"], 0.001, 0.0), "reproduction acceptance gate drift")

    print("PROGRAM_GOVERNANCE_AUDIT_PASS")
    print(f"HARD_RULES_VERIFIED={len(required_rules)}")
    print(f"DECISIONS_VERIFIED={len(required_decisions)}")
    print("L15_SCIENTIFIC_CONTRACT_UNCHANGED=true")
    print("QE_NATIVE_CHECKPOINT_REQUIRED=true")
    print("EXTERNAL_KILL_IS_CHECKPOINT=false")
    print("FINAL_REPRODUCTION_FROM_SCRATCH=true")


if __name__ == "__main__":
    main()
