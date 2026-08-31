from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VALIDATOR_PATH = ROOT / "validate_mc04_h_ethylene_addition_v0_1.py"
AUDIT_PATH = ROOT / "MC04_H_ETHYLENE_ADDITION_SOURCE_AUDIT_v0.1.json"

spec = importlib.util.spec_from_file_location("mc04_h_ethylene_validator", VALIDATOR_PATH)
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(validator)


def load_record() -> dict:
    return json.loads(AUDIT_PATH.read_text())


def test_registered_record_passes() -> None:
    assert validator.validate(load_record()) == []


def test_garbled_comparator_cannot_be_silently_promoted() -> None:
    record = load_record()
    record["experimental_comparator_trail"]["comparator_gate"] = "PASS"
    record["highest_contiguous_promotion_state"] = "COMPARATOR_QUALIFIED"
    record["ready_for_adjudication"] = True
    errors = validator.validate(record)
    assert errors
    assert any("comparator" in error.lower() or "promote" in error.lower() for error in errors)


def test_barrier_typing_cannot_drift_to_free_energy() -> None:
    record = load_record()
    record["theory_source"]["barrier_quantity"]["type"] = "activation free energy at 298 K"
    record["theory_source"]["barrier_quantity"]["free_energy"] = True
    errors = validator.validate(record)
    assert errors
    assert any("barrier" in error.lower() or "relabeled" in error.lower() for error in errors)


def test_parent_hash_mutation_fails() -> None:
    record = load_record()
    record["parent_release"]["workbook_sha256"] = "0" * 64
    errors = validator.validate(record)
    assert "v0.9 workbook hash drift" in errors
