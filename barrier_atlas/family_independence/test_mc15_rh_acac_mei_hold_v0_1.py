from pathlib import Path
import importlib.util
import json

ROOT = Path(__file__).resolve().parent
VALIDATOR = ROOT / "validate_mc15_rh_acac_mei_hold_v0_1.py"
AUDIT = ROOT / "MC15_RH_ACAC_MEI_OXIDATIVE_ADDITION_SOURCE_AUDIT_v0.1.json"

spec = importlib.util.spec_from_file_location("mc15_hold_validator", VALIDATOR)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def load_audit():
    return json.loads(AUDIT.read_text())


def test_registered_mc15_hold_passes():
    assert module.validate(load_audit()) == []


def test_solvent_mismatch_cannot_silently_promote():
    doc = load_audit()
    doc["trail"]["condition_gate"] = "PASS"
    doc["trail"]["ready_for_adjudication"] = True
    errors = module.validate(doc)
    assert errors
    assert any("silently closed" in e or "may not be READY" in e for e in errors)


def test_rate_derived_activation_quantity_cannot_validate_rate():
    doc = load_audit()
    doc["trail"]["rate_derived_activation_quantities"]["validation_role"] = "INDEPENDENT_BARRIER_COMPARATOR"
    errors = module.validate(doc)
    assert any("rate-derived activation quantities" in e for e in errors)


def test_vaska_hold_cannot_be_superseded():
    doc = load_audit()
    doc["existing_mc15_hold_preserved"]["superseded"] = True
    errors = module.validate(doc)
    assert any("Vaska" in e for e in errors)
