from __future__ import annotations
import copy, json
from pathlib import Path
from validate_family_depth_extension_v1_0 import validate
ROOT=Path(__file__).resolve().parent

def load(n): return json.loads((ROOT/n).read_text())
def inputs(): return (load("FAMILY_DEPTH_EXTENSION_v1.0.json"),load("MC01_BETA_CD_1_BUTANOL_ASSOCIATION_SOURCE_AUDIT_v0.1.json"),load("FAMILY_INDEPENDENCE_CAMPAIGN_v0.1.json"),load("SIX_TRAIL_ADJUDICATION_v0.1.json"),load("FAMILY_DEPTH_EXTENSION_v0.9.json"),load("TARGETED_HOLD_CLOSURE_UPDATE_v0.2.json"))

def test_v10_validates_cleanly(): assert validate(*inputs()) == []
def test_parent_immutable():
    ext,audit,*_=inputs()
    for o in [ext,audit]:
        assert o["parent_release"]["immutable"] is True
        assert o["coordinates_admitted"]==0 and o["grades_changed"]==0 and o["automatic_coordinate_admission"] is False
def test_pmf_cannot_be_relabelled_universal_standard_state_barrier():
    vals=list(inputs()); vals[0]=copy.deepcopy(vals[0]); b=vals[0]["records"][0]["barrier_quantity"]
    b["standard_state_activation_free_energy_status"]="STANDARD_STATE_DELTA_G_DAGGER"; b["universal_scalar_status"]="ALLOWED"
    errs=validate(*vals); assert any("scalar/relabeling" in x for x in errs)
def test_trypsin_hold_cannot_be_silently_promoted():
    vals=list(inputs()); vals[5]=copy.deepcopy(vals[5])
    for h in vals[5]["retained_holds"]:
        if h["trail_id"]=="FI-MC01-TRYPSIN-BENZAMIDINE": h["state"]="READY_FOR_ADJUDICATION"; h["ready_for_adjudication"]=True
    assert any("trypsin hold" in x for x in validate(*vals))
def test_ready_depth_is_exactly_nine_without_admission():
    ext,*_=inputs(); a=ext["aggregate"]
    assert a["ready_second_family_count"]==9
    assert a["family_depth_classes_with_additive_ready_second_family"]==["MC01","MC02","MC04","MC05","MC06","MC08","MC11","MC14","MC16"]
    assert a["remaining_classes"]==["MC13","MC15"]
    assert a["coordinates_admitted"]==0 and a["grades_changed"]==0
