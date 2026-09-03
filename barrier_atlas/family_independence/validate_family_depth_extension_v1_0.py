#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED_CLASSES = ["MC01","MC02","MC04","MC05","MC06","MC08","MC11","MC13","MC14","MC15","MC16"]
EXPECTED_PARENT_READY = ["MC02","MC04","MC05","MC06","MC08","MC11","MC14","MC16"]
EXPECTED_READY = ["MC01","MC02","MC04","MC05","MC06","MC08","MC11","MC14","MC16"]
WB = "1c287d2e8e82826e1353fabad09812efdb5147fb28a00c9cb398278942ea7a7e"
AR = "8ffd3319b968eb230552fc74269788f623ad76b2af9976504ec0341f8bf0ef6c"

def load(name): return json.loads((ROOT / name).read_text())

def validate(ext, audit, campaign, six, parent, hold_update):
    e=[]
    if ext.get("schema") != "barrier-atlas-family-depth-extension-v1.0": e.append("wrong extension schema")
    if audit.get("schema") != "barrier-atlas-mc01-beta-cyclodextrin-1-butanol-association-source-audit-v0.1": e.append("wrong source-audit schema")
    if ext.get("parent_family_depth_extension") != "barrier_atlas/family_independence/FAMILY_DEPTH_EXTENSION_v0.9.json": e.append("v1.0 must extend v0.9")
    for obj,label in [(ext,"extension"),(audit,"audit")]:
        pr=obj.get("parent_release",{})
        if pr.get("immutable") is not True or pr.get("workbook_sha256") != WB or pr.get("archive_sha256") != AR: e.append(f"{label}: frozen parent drift")
        if obj.get("automatic_coordinate_admission") is not False or obj.get("coordinates_admitted") != 0 or obj.get("grades_changed") != 0: e.append(f"{label}: parent mutation forbidden")
        fw=obj.get("selection_firewall",{})
        for k in ["residual_may_select_candidate","chi_may_select_candidate","expected_chemsa_agreement_may_select_candidate","same_target_fit_or_method_selection_may_validate_target","rate_derived_activation_quantity_may_validate_same_observed_rate","single_scalar_barrier_may_replace_required_network_representation"]:
            if fw.get(k) is not False: e.append(f"{label}: firewall violation {k}")
    if ext.get("frozen_target_classes") != EXPECTED_CLASSES: e.append("target classes drift")
    if [x.get("class_id") for x in campaign.get("target_classes",[])] != EXPECTED_CLASSES: e.append("campaign target classes drift")
    req={"FI-MC06-CYCLOPROPANE-PROPENE":"READY_FOR_ADJUDICATION_NETWORK_RESOLVED_NOT_ADMITTED","FI-MC02-CYCLOBUTENE-CLASSIFICATION-CHECK":"REFUSED_FOR_MC02_CLASSIFICATION","FI-MC01-TRYPSIN-BENZAMIDINE":"CONDITION_MISMATCH_HOLD","FI-ENZYME-DB-INVENTORY":"CONDITION_AND_EVENT_MAPPING_HOLD","FI-LIPRED-2026-SCREEN":"BARRIER_QUALIFIED_COMPARATOR_MISSING_POOL","FI-BARRIER-ONLY-REPOSITORY-SCREEN":"BARRIER_QUALIFIED_COMPARATOR_MISSING_POOL"}
    if ext.get("frozen_outcomes_reaffirmed") != req: e.append("frozen outcomes drift")
    by={r.get("trail_id"):r for r in six.get("trails",[])}
    if by.get("FI-MC06-CYCLOPROPANE-PROPENE",{}).get("representation_mode") != "NETWORK_RESOLVED": e.append("MC06 representation drift")
    if by.get("FI-MC02-CYCLOBUTENE-CLASSIFICATION-CHECK",{}).get("terminal_state") != "REFUSED_FOR_MC02_CLASSIFICATION": e.append("cyclobutene refusal drift")
    pa=parent.get("aggregate",{})
    if pa.get("family_depth_classes_with_additive_ready_second_family") != EXPECTED_PARENT_READY or pa.get("ready_second_family_count") != 8: e.append("parent ready state drift")
    rs=ext.get("records",[])
    if len(rs)!=1: e.append("v1.0 must add exactly one record"); return e
    r=rs[0]
    if r.get("trail_id") != "FI-MC01-BETA-CD-1-BUTANOL-ASSOCIATION": e.append("wrong trail")
    for g in ["classification_gate","source_gate","barrier_gate","comparator_gate","condition_gate","independence_gate","representation_gate"]:
        if not str(r.get(g,"")).startswith("PASS"): e.append(f"READY trail non-PASS {g}")
    if r.get("ready_for_adjudication") is not True or r.get("terminal_state") != "READY_FOR_ADJUDICATION" or r.get("automatic_admission") is not False: e.append("READY/admission state invalid")
    if r.get("representation_mode") != "CONFORMATION_AND_PATH_RESOLVED_PMF_ASSOCIATION": e.append("representation drift")
    b=r.get("barrier_quantity",{})
    if b.get("value_kcal_per_mol") != 1.1 or b.get("temperature_K") != 298.0 or b.get("host_conformation") != "conf1": e.append("PMF barrier drift")
    if b.get("standard_state_activation_free_energy_status") != "NOT_CLAIMED_AS_STANDARD_STATE_DELTA_G_DAGGER" or b.get("universal_scalar_status") != "FORBIDDEN": e.append("PMF scalar/relabeling violation")
    c=r.get("observed_comparator",{})
    if c.get("primary_system_doi") != "10.1246/bcsj.70.1003" or c.get("experimental_series_doi") != "10.1021/jp010535u": e.append("comparator source drift")
    if c.get("temperature_K") != 298.15 or c.get("unit") != "M^-1 s^-1" or abs(float(c.get("value",0))-2.8e8)>1 or abs(float(c.get("uncertainty",0))-0.8e8)>1: e.append("comparator rate/condition drift")
    if audit.get("ready_for_adjudication") is not True or audit.get("representation_mode") != r.get("representation_mode"): e.append("audit does not support READY representation")
    holds={x.get("trail_id"):x for x in hold_update.get("retained_holds",[])}
    h=holds.get("FI-MC01-TRYPSIN-BENZAMIDINE",{})
    if h.get("state") != "CONDITION_MISMATCH_HOLD" or h.get("ready_for_adjudication") is not False: e.append("trypsin hold altered")
    ag=ext.get("aggregate",{})
    if ag.get("family_depth_classes_with_additive_ready_second_family") != EXPECTED_READY or ag.get("ready_second_family_count") != 9 or ag.get("remaining_classes") != ["MC13","MC15"]: e.append("ready family-depth aggregate drift")
    if ag.get("coordinates_admitted") != 0 or ag.get("grades_changed") != 0: e.append("aggregate parent mutation")
    return e

def main():
    errors=validate(load("FAMILY_DEPTH_EXTENSION_v1.0.json"),load("MC01_BETA_CD_1_BUTANOL_ASSOCIATION_SOURCE_AUDIT_v0.1.json"),load("FAMILY_INDEPENDENCE_CAMPAIGN_v0.1.json"),load("SIX_TRAIL_ADJUDICATION_v0.1.json"),load("FAMILY_DEPTH_EXTENSION_v0.9.json"),load("TARGETED_HOLD_CLOSURE_UPDATE_v0.2.json"))
    if errors:
        print(json.dumps({"status":"FAIL","errors":errors},indent=2)); raise SystemExit(1)
    print(json.dumps({"status":"PASS","new_ready_class":"MC01","ready_second_family_count":9,"parent_mutated":False},indent=2))

if __name__ == "__main__": main()
