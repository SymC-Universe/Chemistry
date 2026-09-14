from pathlib import Path
import importlib.util
import json

ROOT = Path(__file__).resolve().parent
VALIDATOR = ROOT / "validate_mc16_methylperoxy_scientific_topology_v0_2.py"
SPEC = importlib.util.spec_from_file_location("mc16_topology_validator", VALIDATOR)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def test_mc16_topology_hold_v02():
    record = json.loads((ROOT / "MC16_METHYLPEROXY_SCIENTIFIC_TOPOLOGY_AUDIT_v0.2.json").read_text())
    assert MODULE.validate(record) == []


def test_no_single_barrier_promotion():
    record = json.loads((ROOT / "MC16_METHYLPEROXY_SCIENTIFIC_TOPOLOGY_AUDIT_v0.2.json").read_text())
    assert record["ready_for_adjudication"] is False
    assert record["highest_contiguous_promotion_state"] == "COMPARATOR_QUALIFIED"
    assert record["representation_mode"] == "NETWORK_RESOLVED_TETROXIDE_SELF_REACTION_REQUIRED"
    assert record["barrier_gate"].startswith("HOLD_NO_ROBUST_SINGLE_SADDLE_POINT")
