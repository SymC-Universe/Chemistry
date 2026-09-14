from pathlib import Path
import importlib.util,json
R=Path(__file__).resolve().parent
P=R/"validate_mc08_chloride_identity_sn2_v0_2.py"
s=importlib.util.spec_from_file_location("v",P); v=importlib.util.module_from_spec(s); s.loader.exec_module(v)
def load(): return json.loads((R/"MC08_CHLORIDE_METHYL_CHLORIDE_IDENTITY_SN2_SOURCE_AUDIT_v0.2.json").read_text())
def test_pass(): assert v.validate(load())==[]
def test_no_drift_to_thermal_rate():
 r=load(); r["selection_firewall"]["drift_field_rate_may_be_silently_relabelled_as_zero_field_thermal_rate"]=True; assert v.validate(r)
def test_no_same_target_fit_validation():
 r=load(); r["same_target_model_quarantine"]["campaign_role"]="INDEPENDENT_VALIDATION"; assert v.validate(r)
def test_no_ready_during_conflict():
 r=load(); r["ready_for_adjudication"]=True; assert v.validate(r)
def test_network_representation_frozen():
 r=load(); r["representation_mode"]="SINGLE_BARRIER"; assert v.validate(r)
