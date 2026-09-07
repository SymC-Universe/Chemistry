from __future__ import annotations
import copy, json
from pathlib import Path
from validate_family_depth_extension_v0_9 import validate
ROOT=Path(__file__).resolve().parent

def load(n): return json.loads((ROOT/n).read_text())
def inputs(): return (load("FAMILY_DEPTH_EXTENSION_v0.9.json"),load("MC08_CHLORIDE_METHYL_IODIDE_NONIDENTITY_SN2_SOURCE_AUDIT_v0.1.json"),load("FAMILY_INDEPENDENCE_CAMPAIGN_v0.1.json"),load("SIX_TRAIL_ADJUDICATION_v0.1.json"),load("FAMILY_DEPTH_EXTENSION_v0.8.json"),load("MC08_CHLORIDE_METHYL_CHLORIDE_IDENTITY_SN2_SOURCE_AUDIT_v0.2.json"),load("MC08_METHANE_ZEOLITE_EXCHANGE_SOURCE_AUDIT_v0.1.json"))

def test_v09_validates_cleanly(): assert validate(*inputs()) == []
def test_parent_immutable():
    ext,audit,*_=inputs()
    for o in [ext,audit]:
        assert o["parent_release"]["immutable"] is True
        assert o["coordinates_admitted"]==0 and o["grades_changed"]==0 and o["automatic_coordinate_admission"] is False
def test_intrinsic_pes_cannot_be_relabelled_thermal_gibbs():
    vals=list(inputs()); vals[0]=copy.deepcopy(vals[0]); b=vals[0]["records"][0]["barrier_quantity"]; b["gibbs_free_energy_status"]="GIBBS_FREE_ENERGY"; b["temperature_status"]="300_K_THERMAL_PROFILE"
    errs=validate(*vals); assert any("relabeling" in x for x in errs)
def test_prior_mc08_holds_cannot_be_silently_promoted():
    vals=list(inputs()); vals[5]=copy.deepcopy(vals[5]); vals[5]["terminal_state"]="READY_FOR_ADJUDICATION"; vals[5]["ready_for_adjudication"]=True
    assert any("identity SN2" in x for x in validate(*vals))
def test_ready_depth_is_exactly_eight_without_admission():
    ext,*_=inputs(); a=ext["aggregate"]
    assert a["ready_second_family_count"]==8
    assert a["family_depth_classes_with_additive_ready_second_family"]==["MC02","MC04","MC05","MC06","MC08","MC11","MC14","MC16"]
    assert a["coordinates_admitted"]==0 and a["grades_changed"]==0
