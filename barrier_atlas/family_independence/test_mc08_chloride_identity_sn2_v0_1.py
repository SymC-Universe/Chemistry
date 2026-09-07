from pathlib import Path
import importlib.util
import json

ROOT = Path(__file__).resolve().parent
VALIDATOR = ROOT / "validate_mc08_chloride_identity_sn2_v0_1.py"
AUDIT = ROOT / "MC08_CHLORIDE_METHYL_CHLORIDE_IDENTITY_SN2_SOURCE_AUDIT_v0.1.json"

spec = importlib.util.spec_from_file_location("validate_mc08_chloride_identity_sn2_v0_1", VALIDATOR)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def load_audit():
    return json.loads(AUDIT.read_text())


def test_mc08_identity_sn2_audit_passes_fail_closed_validator():
    assert module.validate(load_audit()) == []


def test_cross_section_cannot_be_promoted_to_rate_comparator():
    rec = load_audit()
    rec["direct_experimental_scattering_evidence"]["qualification"] = "OBSERVED_RATE_CONSTANT"
    assert any("cross-section-only" in e for e in module.validate(rec))


def test_aqueous_26_6_estimate_cannot_be_promoted_to_direct_experiment():
    rec = load_audit()
    rec["aqueous_candidate_quarantine"]["direct_measurement_audit"]["result"] = "DIRECT_EXPERIMENT"
    assert any("26.6" in e for e in module.validate(rec))


def test_candidate_cannot_be_marked_ready_without_observed_rate():
    rec = load_audit()
    rec["ready_for_adjudication"] = True
    assert any("must not become READY" in e for e in module.validate(rec))


def test_v09_hash_drift_is_detected():
    rec = load_audit()
    rec["parent_release"]["workbook_sha256"] = "drift"
    assert any("workbook hash drift" in e for e in module.validate(rec))
