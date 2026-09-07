from pathlib import Path
import json

from validate_family_depth_extension_v0_5 import validate

ROOT = Path(__file__).resolve().parent


def load(name):
    return json.loads((ROOT / name).read_text())


def test_family_depth_extension_v05():
    errors = validate(
        load("FAMILY_DEPTH_EXTENSION_v0.5.json"),
        load("MC04_H_PROPENE_ADDITION_SOURCE_AUDIT_v0.1.json"),
        load("FAMILY_INDEPENDENCE_CAMPAIGN_v0.1.json"),
        load("SIX_TRAIL_ADJUDICATION_v0.1.json"),
        load("MC04_H_ETHYLENE_ADDITION_SOURCE_AUDIT_v0.1.json"),
    )
    assert errors == []


def test_mc04_propene_ready_is_network_resolved_not_admitted():
    audit = load("MC04_H_PROPENE_ADDITION_SOURCE_AUDIT_v0.1.json")
    assert audit["ready_for_adjudication"] is True
    assert audit["representation_mode"] == "NETWORK_RESOLVED_PARALLEL_ADDITION_HIGH_PRESSURE"
    assert audit["automatic_admission"] is False
    assert audit["coordinates_admitted"] == 0
    assert audit["grades_changed"] == 0


def test_held_mc04_ethylene_is_unchanged():
    ethylene = load("MC04_H_ETHYLENE_ADDITION_SOURCE_AUDIT_v0.1.json")
    assert ethylene["ready_for_adjudication"] is False
    assert ethylene["highest_contiguous_promotion_state"] == "BARRIER_QUALIFIED"
    assert ethylene["terminal_state"] == "COMPARATOR_NUMERIC_PROVENANCE_HOLD"


def test_propene_barrier_profile_cannot_collapse_to_single_barrier():
    audit = load("MC04_H_PROPENE_ADDITION_SOURCE_AUDIT_v0.1.json")
    profile = audit["theory_source"]["barrier_profile"]
    assert len(profile) == 2
    assert {x["value"] for x in profile} == {15.61, 8.39}
    assert all("activation enthalpy at 0 K" in x["type"] for x in profile)
