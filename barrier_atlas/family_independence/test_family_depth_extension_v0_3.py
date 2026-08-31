from pathlib import Path
import importlib.util
import json

ROOT = Path(__file__).resolve().parent
VALIDATOR_PATH = ROOT / "validate_family_depth_extension_v0_3.py"
SPEC = importlib.util.spec_from_file_location("family_depth_v03_validator", VALIDATOR_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def load(name: str) -> dict:
    return json.loads((ROOT / name).read_text())


def test_family_depth_extension_v03() -> None:
    errors = MODULE.validate(
        load("FAMILY_DEPTH_EXTENSION_v0.3.json"),
        load("FAMILY_INDEPENDENCE_CAMPAIGN_v0.1.json"),
        load("SIX_TRAIL_ADJUDICATION_v0.1.json"),
    )
    assert errors == []


def test_mc14_ready_is_not_admission() -> None:
    extension = load("FAMILY_DEPTH_EXTENSION_v0.3.json")
    rec = extension["records"][0]
    assert rec["ready_for_adjudication"] is True
    assert rec["automatic_admission"] is False
    assert extension["coordinates_admitted"] == 0
    assert extension["grades_changed"] == 0


def test_mc14_barrier_is_not_free_energy() -> None:
    extension = load("FAMILY_DEPTH_EXTENSION_v0.3.json")
    barrier_type = extension["records"][0]["barrier_quantity"]["type"].lower()
    assert "zero-point-energy-corrected" in barrier_type
    assert "free energy" not in barrier_type
