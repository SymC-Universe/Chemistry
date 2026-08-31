from pathlib import Path
import json
from validate_targeted_hold_closure_v0_2 import validate

ROOT=Path(__file__).resolve().parent

def load(name): return json.loads((ROOT/name).read_text())

def test_targeted_hold_closure_v02():
    errors=validate(load("TARGETED_HOLD_CLOSURE_UPDATE_v0.2.json"),load("FAMILY_INDEPENDENCE_CAMPAIGN_v0.1.json"),load("SIX_TRAIL_ADJUDICATION_v0.1.json"))
    assert errors==[]
