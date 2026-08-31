from pathlib import Path
import json
import importlib.util

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("validate_family_depth_extension_v0_4", ROOT / "validate_family_depth_extension_v0_4.py")
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MOD)


def load(name):
    return json.loads((ROOT / name).read_text())


def test_family_depth_extension_v04():
    errors = MOD.validate(
        load("FAMILY_DEPTH_EXTENSION_v0.4.json"),
        load("FAMILY_INDEPENDENCE_CAMPAIGN_v0.1.json"),
        load("SIX_TRAIL_ADJUDICATION_v0.1.json"),
        load("FAMILY_DEPTH_EXTENSION_v0.3.json"),
    )
    assert errors == []


def test_v04_adds_no_ready_candidate_and_no_parent_mutation():
    data = load("FAMILY_DEPTH_EXTENSION_v0.4.json")
    assert data["aggregate"]["new_ready_for_adjudication"] == 0
    assert data["aggregate"]["family_depth_classes_with_additive_ready_second_family"] == ["MC06", "MC11", "MC14"]
    assert data["coordinates_admitted"] == 0
    assert data["grades_changed"] == 0
    assert all(r["ready_for_adjudication"] is False for r in data["records"])


def test_vaska_and_ethyl_chloride_fail_closed_at_open_gates():
    data = load("FAMILY_DEPTH_EXTENSION_v0.4.json")
    by_id = {r["trail_id"]: r for r in data["records"]}
    assert by_id["FI-MC15-VASKA-H2-OXIDATIVE-ADDITION"]["condition_gate"].startswith("HOLD_")
    assert by_id["FI-MC15-VASKA-H2-OXIDATIVE-ADDITION"]["highest_contiguous_promotion_state"] == "COMPARATOR_QUALIFIED"
    assert by_id["FI-MC05-ETHYL-CHLORIDE-HCL-ELIMINATION"]["barrier_gate"].startswith("HOLD_")
    assert by_id["FI-MC05-ETHYL-CHLORIDE-HCL-ELIMINATION"]["highest_contiguous_promotion_state"] == "SOURCE_QUALIFIED"
