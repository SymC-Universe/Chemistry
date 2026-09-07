#!/usr/bin/env python3
import argparse, json
from pathlib import Path
W="1c287d2e8e82826e1353fabad09812efdb5147fb28a00c9cb398278942ea7a7e"
A="8ffd3319b968eb230552fc74269788f623ad76b2af9976504ec0341f8bf0ef6c"
READY=["MC02","MC04","MC06","MC11","MC14","MC16"]
def load(p): return json.loads(Path(p).read_text())
def validate(r):
    e=[]
    if r.get("schema")!="barrier-atlas-mc08-chloride-methyl-chloride-identity-sn2-source-audit-v0.2": e.append("schema drift")
    p=r.get("parent_release",{})
    if p.get("immutable") is not True or p.get("workbook_sha256")!=W or p.get("archive_sha256")!=A: e.append("v0.9 parent drift")
    if r.get("coordinates_admitted")!=0 or r.get("grades_changed")!=0: e.append("parent mutation forbidden")
    fw=r.get("selection_firewall",{})
    for k in ["residual_may_select_candidate","chi_may_select_candidate","expected_chemsa_agreement_may_select_candidate","same_target_fitted_barrier_may_validate_observed_rate","drift_field_rate_may_be_silently_relabelled_as_zero_field_thermal_rate","conflicting_primary_experiments_may_be_resolved_by_expected_agreement"]:
        if fw.get(k) is not False: e.append("firewall violation: "+k)
    if r.get("barrier_evidence",{}).get("overall_barrier",{}).get("value_kJ_per_mol")!=9.8: e.append("298 K overall barrier drift")
    if r.get("primary_rate_evidence_A",{}).get("reported_rate_coefficient",{}).get("value")!=3.5e-14: e.append("1988 rate drift")
    if "immeasurably slow" not in r.get("primary_rate_evidence_B",{}).get("reported_result",""): e.append("1989 thermal conflict lost")
    if r.get("same_target_model_quarantine",{}).get("campaign_role")!="CALIBRATION_ONLY_NOT_INDEPENDENT_VALIDATION": e.append("same-target fit quarantine lost")
    if r.get("condition_gate")!="HOLD_DRIFT_FIELD_VS_ZERO_FIELD_THERMAL_REGIME_NOT_RECONSTRUCTED": e.append("condition hold drift")
    if r.get("comparator_gate")!="HOLD_CONFLICTING_PRIMARY_RATE_REGIMES": e.append("comparator conflict lost")
    if r.get("representation_mode")!="NETWORK_RESOLVED_COMPLEX_FORMING_IDENTITY_SN2": e.append("network representation drift")
    if r.get("highest_contiguous_promotion_state")!="BARRIER_QUALIFIED" or r.get("terminal_state")!="COMPARATOR_REGIME_CONFLICT_HOLD" or r.get("ready_for_adjudication") is not False: e.append("illegal promotion")
    ag=r.get("aggregate_effect",{})
    if ag.get("ready_second_family_count")!=6 or ag.get("ready_classes_unchanged")!=READY: e.append("family depth drift")
    return e
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--audit",required=True); a=ap.parse_args(); e=validate(load(a.audit))
    print(json.dumps({"status":"FAIL" if e else "PASS","errors":e},indent=2))
    if e: raise SystemExit(1)
if __name__=="__main__": main()
