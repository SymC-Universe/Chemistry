#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from pathlib import Path

TARGETS = {"MC01","MC02","MC04","MC05","MC06","MC08","MC11","MC13","MC14","MC15","MC16"}
ALLOWED_STATES = {
    "CANDIDATE", "SOURCE_QUALIFIED", "BARRIER_QUALIFIED", "COMPARATOR_QUALIFIED",
    "CONDITION_MATCHED", "INDEPENDENCE_PASS", "READY_FOR_ADJUDICATION",
    "HOLD", "REFUSED", "CLASSIFICATION_HOLD", "BARRIER_HALF_TRAIL",
    "COMPARATOR_MISSING", "COMPUTATIONAL_TRAIL_PINNED", "EXISTING_HOLD_REOPENABLE"
}
SHA40 = re.compile(r"^[0-9a-f]{40}$")


def load(path: str):
    return json.loads(Path(path).read_text())


def validate(campaign, trails):
    failures=[]
    def req(cond,msg):
        if not cond: failures.append(msg)

    req(campaign.get("status") == "FROZEN_BEFORE_SECOND_FAMILY_ADMISSION_RESULTS", "campaign status not prospectively frozen")
    parent=campaign.get("parent_release",{})
    req(parent.get("name") == "Barrier_Height_Rate_Atlas_v0.9", "wrong parent release")
    req(parent.get("immutable") is True, "v0.9 must be immutable")
    scope=campaign.get("scope",{})
    req(scope.get("campaign_is_additive") is True, "campaign must be additive")
    req(scope.get("automatic_parent_mutation") is False, "automatic parent mutation forbidden")
    req(scope.get("automatic_coordinate_admission") is False, "automatic coordinate admission forbidden")
    req(scope.get("automatic_grade_promotion") is False, "automatic grade promotion forbidden")
    req(scope.get("residual_may_select_candidate") is False, "residual-based candidate selection forbidden")
    req(scope.get("chi_or_expected_chemsa_result_may_select_candidate") is False, "ChemSA outcome selection forbidden")

    classes=campaign.get("target_classes",[])
    ids=[x.get("class_id") for x in classes]
    req(len(classes)==11, f"expected 11 target classes, got {len(classes)}")
    req(set(ids)==TARGETS, f"target-class set mismatch: {set(ids)^TARGETS}")
    req(len(ids)==len(set(ids)), "duplicate target class")
    for row in classes:
        req(row.get("current_independent_family_count")==1, f"{row.get('class_id')} baseline must be one family")
        req(row.get("target_minimum")==2, f"{row.get('class_id')} minimum target must be two")
        req(len(row.get("current_families",[]))==1, f"{row.get('class_id')} must preserve exact one-family baseline")

    adjud=campaign.get("adjudication",{})
    req(adjud.get("ready_for_adjudication_is_not_admission") is True, "READY_FOR_ADJUDICATION must not mean admitted")
    req(adjud.get("new_coordinates_require_new_release_version") is True, "new coordinates must require new version")
    req(adjud.get("v0_9_rows_and_grades_may_not_change") is True, "v0.9 mutation fence missing")

    req(trails.get("status")=="CANDIDATE_GENERATION_ONLY", "trail registry must be candidate-generation only")
    tids=[]
    for t in trails.get("trails",[]):
        tid=t.get("trail_id"); tids.append(tid)
        req(t.get("state") in ALLOWED_STATES, f"{tid}: invalid state {t.get('state')}")
        req(t.get("automatic_admission") is False, f"{tid}: automatic admission must be false")
        for c in t.get("provisional_target_classes",[]):
            req(c in TARGETS, f"{tid}: provisional class {c} is not a current target")
        if "repository" in t:
            req(SHA40.match(t.get("commit", "")) is not None, f"{tid}: pinned GitHub trail requires exact 40-char commit")
    req(len(tids)==len(set(tids)), "duplicate trail_id")
    return failures


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--campaign",required=True)
    ap.add_argument("--trails",required=True)
    args=ap.parse_args()
    failures=validate(load(args.campaign),load(args.trails))
    if failures:
        for f in failures: print("FAIL",f)
        raise SystemExit(1)
    print("FAMILY_INDEPENDENCE_CAMPAIGN_VALID")
    print("TARGET_SINGLE_FAMILY_CLASSES=11")
    print("AUTOMATIC_ADMISSION=FALSE")
    print("PARENT_V0_9_MUTATION=FORBIDDEN")

if __name__=="__main__": main()
