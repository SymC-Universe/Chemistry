#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED_CLASSES = ["MC01", "MC02", "MC04", "MC05", "MC06", "MC08", "MC11", "MC13", "MC14", "MC15", "MC16"]
EXPECTED_PARENT_READY = ["MC02", "MC04", "MC05", "MC06", "MC11", "MC14", "MC16"]
EXPECTED_READY = ["MC02", "MC04", "MC05", "MC06", "MC08", "MC11", "MC14", "MC16"]
WB = "1c287d2e8e82826e1353fabad09812efdb5147fb28a00c9cb398278942ea7a7e"
AR = "8ffd3319b968eb230552fc74269788f623ad76b2af9976504ec0341f8bf0ef6c"

def load(name): return json.loads((ROOT / name).read_text())

def validate(ext, audit, campaign, six, parent, held_identity, held_zeolite):
    e=[]
    if ext.get("schema") != "barrier-atlas-family-depth-extension-v0.9": e.append("wrong extension schema")
    if audit.get("schema") != "barrier-atlas-mc08-chloride-methyl-iodide-nonidentity-sn2-source-audit-v0.1": e.append("wrong source-audit schema")
    if ext.get("parent_family_depth_extension") != "barrier_atlas/family_independence/FAMILY_DEPTH_EXTENSION_v0.8.json": e.append("v0.9 must extend v0.8")
    for obj,label in [(ext,"extension"),(audit,"audit")]:
        pr=obj.get("parent_release",{})
        if pr.get("immutable") is not True or pr.get("workbook_sha256") != WB or pr.get("archive_sha256") != AR: e.append(f"{label}: frozen parent drift")
        if obj.get("automatic_coordinate_admission") is not False or obj.get("coordinates_admitted") != 0 or obj.get("grades_changed") != 0: e.append(f"{label}: parent mutation forbidden")
        fw=obj.get("selection_firewall",{})
        for k in ["residual_may_select_candidate","chi_may_select_candidate","expected_chemsa_agreement_may_select_candidate","same_target_fit_or_method_selection_may_validate_target"]:
            if fw.get(k) is not False: e.append(f"{label}: firewall violation {k}")
    if ext.get("frozen_target_classes") != EXPECTED_CLASSES: e.append("target classes drift")
    if [x.get("class_id") for x in campaign.get("target_classes",[])] != EXPECTED_CLASSES: e.append("campaign target classes drift")
    req={"FI-MC06-CYCLOPROPANE-PROPENE":"READY_FOR_ADJUDICATION_NETWORK_RESOLVED_NOT_ADMITTED","FI-MC02-CYCLOBUTENE-CLASSIFICATION-CHECK":"REFUSED_FOR_MC02_CLASSIFICATION","FI-MC01-TRYPSIN-BENZAMIDINE":"CONDITION_MISMATCH_HOLD","FI-ENZYME-DB-INVENTORY":"CONDITION_AND_EVENT_MAPPING_HOLD","FI-LIPRED-2026-SCREEN":"BARRIER_QUALIFIED_COMPARATOR_MISSING_POOL","FI-BARRIER-ONLY-REPOSITORY-SCREEN":"BARRIER_QUALIFIED_COMPARATOR_MISSING_POOL"}
    if ext.get("frozen_outcomes_reaffirmed") != req: e.append("frozen outcomes drift")
    by={r.get("trail_id"):r for r in six.get("trails",[])}
    if by.get("FI-MC06-CYCLOPROPANE-PROPENE",{}).get("representation_mode") != "NETWORK_RESOLVED": e.append("MC06 representation drift")
    if by.get("FI-MC02-CYCLOBUTENE-CLASSIFICATION-CHECK",{}).get("terminal_state") != "REFUSED_FOR_MC02_CLASSIFICATION": e.append("cyclobutene refusal drift")
    pa=parent.get("aggregate",{})
    if pa.get("family_depth_classes_with_additive_ready_second_family") != EXPECTED_PARENT_READY or pa.get("ready_second_family_count") != 7: e.append("parent ready state drift")
    rs=ext.get("records",[])
    if len(rs)!=1: e.append("v0.9 must add exactly one record"); return e
    r=rs[0]
    if r.get("trail_id") != "FI-MC08-CL-CH3I-NONIDENTITY-SN2": e.append("wrong trail")
    for g in ["classification_gate","source_gate","barrier_gate","comparator_gate","condition_gate","independence_gate","representation_gate"]:
        if not str(r.get(g,"")).startswith("PASS"): e.append(f"READY trail non-PASS {g}")
    if r.get("ready_for_adjudication") is not True or r.get("terminal_state") != "READY_FOR_ADJUDICATION" or r.get("automatic_admission") is not False: e.append("READY/admission state invalid")
    if r.get("representation_mode") != "NETWORK_RESOLVED_COMPLEX_FORMING_NONIDENTITY_SN2": e.append("representation drift")
    b=r.get("barrier_quantity",{})
    if b.get("classical_relative_energies_kcal_per_mol") != {"PreMIN":-11.56,"WaldenTS":-5.48,"PostMIN":-23.66,"products":-14.88}: e.append("classical PES drift")
    if b.get("adiabatic_relative_energies_kcal_per_mol") != {"PreMIN":-11.42,"WaldenTS":-5.54,"PostMIN":-22.72,"products":-14.07}: e.append("adiabatic PES drift")
    if b.get("gibbs_free_energy_status") != "NOT_A_GIBBS_FREE_ENERGY_BARRIER" or b.get("temperature_status") != "NOT_A_300_K_THERMAL_PROFILE": e.append("PES relabeling detected")
    c=r.get("observed_comparator",{})
    if c.get("primary_source_doi") != "10.1016/S1387-3806(01)00398-0" or c.get("temperature_K") != 300.0 or c.get("flow_tube_pressure_Torr") != 0.5: e.append("comparator provenance/conditions drift")
    if abs(float(c.get("value",0))-15.9e-11)>1e-20 or abs(float(c.get("uncertainty_one_sigma",0))-0.5e-11)>1e-21: e.append("comparator rate drift")
    if audit.get("ready_for_adjudication") is not True or audit.get("representation_mode") != r.get("representation_mode"): e.append("audit does not support READY representation")
    if held_identity.get("terminal_state") != "COMPARATOR_REGIME_CONFLICT_HOLD" or held_identity.get("ready_for_adjudication") is not False: e.append("identity SN2 hold altered")
    if held_zeolite.get("terminal_state") != "MECHANISM_AND_RAW_COMPARATOR_HOLD" or held_zeolite.get("ready_for_adjudication") is not False: e.append("zeolite hold altered")
    ag=ext.get("aggregate",{})
    if ag.get("family_depth_classes_with_additive_ready_second_family") != EXPECTED_READY or ag.get("ready_second_family_count") != 8: e.append("ready family-depth aggregate drift")
    if ag.get("coordinates_admitted") != 0 or ag.get("grades_changed") != 0: e.append("aggregate parent mutation")
    return e

def main():
    errors=validate(load("FAMILY_DEPTH_EXTENSION_v0.9.json"),load("MC08_CHLORIDE_METHYL_IODIDE_NONIDENTITY_SN2_SOURCE_AUDIT_v0.1.json"),load("FAMILY_INDEPENDENCE_CAMPAIGN_v0.1.json"),load("SIX_TRAIL_ADJUDICATION_v0.1.json"),load("FAMILY_DEPTH_EXTENSION_v0.8.json"),load("MC08_CHLORIDE_METHYL_CHLORIDE_IDENTITY_SN2_SOURCE_AUDIT_v0.2.json"),load("MC08_METHANE_ZEOLITE_EXCHANGE_SOURCE_AUDIT_v0.1.json"))
    if errors:
        print(json.dumps({"status":"FAIL","errors":errors},indent=2)); raise SystemExit(1)
    print(json.dumps({"status":"PASS","new_ready_class":"MC08","ready_second_family_count":8,"parent_mutated":False},indent=2))

if __name__ == "__main__": main()
