#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

EXPECTED_WORKBOOK = "1c287d2e8e82826e1353fabad09812efdb5147fb28a00c9cb398278942ea7a7e"
EXPECTED_ARCHIVE = "8ffd3319b968eb230552fc74269788f623ad76b2af9976504ec0341f8bf0ef6c"
EXPECTED_TARGETS = {"MC01","MC02","MC04","MC05","MC06","MC08","MC11","MC13","MC14","MC15","MC16"}


def load(p): return json.loads(Path(p).read_text())

def validate(update, campaign, baseline):
    e=[]
    p=update.get("parent_release",{})
    if not p.get("immutable"): e.append("parent not immutable")
    if p.get("workbook_sha256")!=EXPECTED_WORKBOOK: e.append("workbook hash drift")
    if p.get("archive_sha256")!=EXPECTED_ARCHIVE: e.append("archive hash drift")
    if update.get("coordinates_admitted")!=0: e.append("coordinate admission forbidden")
    if update.get("grades_changed")!=0: e.append("grade mutation forbidden")
    fw=update.get("selection_firewall",{})
    for k in ("residual_may_select_candidate","chi_may_select_candidate","expected_chemsa_agreement_may_select_candidate","agreement_quality_may_select_method_variant"):
        if fw.get(k) is not False: e.append(f"firewall violation: {k}")
    if fw.get("ready_for_adjudication_is_not_admission") is not True: e.append("ready/admission firewall lost")
    targets={x.get("class_id") for x in campaign.get("target_classes",[])}
    if targets!=EXPECTED_TARGETS: e.append("11-class target set drift")
    ready=update.get("new_ready_for_adjudication",[])
    if len(ready)!=1 or ready[0].get("trail_id")!="FI-MC11-ECDHFR-HYDRIDE": e.append("exact new MC11 ready trail required")
    if ready:
        r=ready[0]
        if r.get("target_class")!="MC11": e.append("MC11 class drift")
        if r.get("terminal_state")!="READY_FOR_ADJUDICATION" or r.get("ready_for_adjudication") is not True: e.append("MC11 ready-state inconsistency")
        for g in ("classification_gate","source_gate","barrier_gate","comparator_gate","condition_gate","independence_gate"):
            if not str(r.get(g,"")).startswith("PASS"): e.append(f"MC11 non-pass gate: {g}")
        if r.get("automatic_admission") is not False: e.append("MC11 automatic admission forbidden")
        if "phenomenological" not in r.get("barrier_quantity",{}).get("type",""): e.append("MC11 barrier typing weakened")
    base={x.get("trail_id"):x for x in baseline.get("trails",[])}
    if base.get("FI-MC06-CYCLOPROPANE-PROPENE",{}).get("representation_mode")!="NETWORK_RESOLVED": e.append("MC06 network-resolved baseline drift")
    if base.get("FI-MC06-CYCLOPROPANE-PROPENE",{}).get("ready_for_adjudication") is not True: e.append("MC06 ready baseline drift")
    if base.get("FI-MC02-CYCLOBUTENE-CLASSIFICATION-CHECK",{}).get("terminal_state")!="REFUSED_FOR_MC02_CLASSIFICATION": e.append("cyclobutene refusal drift")
    preserved=update.get("baseline_outcomes_preserved",{})
    if preserved.get("FI-MC02-CYCLOBUTENE-CLASSIFICATION-CHECK")!="REFUSED_FOR_MC02_CLASSIFICATION": e.append("cyclobutene relabel attempted")
    if "NETWORK_RESOLVED" not in preserved.get("FI-MC06-CYCLOPROPANE-PROPENE",""): e.append("MC06 representation lost in update")
    return e

if __name__=="__main__":
    root=Path(__file__).resolve().parent
    errors=validate(load(root/"TARGETED_HOLD_CLOSURE_UPDATE_v0.2.json"),load(root/"FAMILY_INDEPENDENCE_CAMPAIGN_v0.1.json"),load(root/"SIX_TRAIL_ADJUDICATION_v0.1.json"))
    print(json.dumps({"status":"PASS" if not errors else "FAIL","errors":errors},indent=2))
    raise SystemExit(1 if errors else 0)
