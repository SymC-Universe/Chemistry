from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VALIDATOR_PATH = ROOT / "validate_mc08_methane_zeolite_exchange_v0_1.py"
AUDIT_PATH = ROOT / "MC08_METHANE_ZEOLITE_EXCHANGE_SOURCE_AUDIT_v0.1.json"

spec = importlib.util.spec_from_file_location("mc08_exchange_validator", VALIDATOR_PATH)
module = importlib.util.module_from_spec(spec)
assert spec is not None and spec.loader is not None
spec.loader.exec_module(module)


def test_mc08_exchange_audit_is_fail_closed_and_additive():
    record = json.loads(AUDIT_PATH.read_text())
    assert module.validate(record) == []


def test_mc08_exchange_cannot_silently_promote():
    record = json.loads(AUDIT_PATH.read_text())
    record["ready_for_adjudication"] = True
    assert module.validate(record) != []


def test_figure_only_rate_cannot_close_comparator_gate():
    record = json.loads(AUDIT_PATH.read_text())
    record["primary_experiment"]["comparator_gate"] = "PASS"
    assert module.validate(record) != []


def test_mechanism_hold_cannot_be_erased():
    record = json.loads(AUDIT_PATH.read_text())
    record["mechanism_audit"]["mechanism_gate"] = "PASS"
    assert module.validate(record) != []
