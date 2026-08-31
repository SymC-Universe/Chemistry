from pathlib import Path
import importlib.util
import json

ROOT=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location("targeted_hold_validator",ROOT/"validate_targeted_hold_closure_v0.2.py")
MOD=importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MOD)

def load(name): return json.loads((ROOT/name).read_text())

def test_targeted_hold_closure_v02():
    errors=MOD.validate(load("TARGETED_HOLD_CLOSURE_UPDATE_v0.2.json"),load("FAMILY_INDEPENDENCE_CAMPAIGN_v0.1.json"),load("SIX_TRAIL_ADJUDICATION_v0.1.json"))
    assert errors==[]
