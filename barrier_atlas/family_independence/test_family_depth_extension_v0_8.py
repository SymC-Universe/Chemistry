from __future__ import annotations

import json
from pathlib import Path

from validate_family_depth_extension_v0_8 import validate

ROOT = Path(__file__).resolve().parent


def load(name: str):
    return json.loads((ROOT / name).read_text())


def inputs():
    return (
        load("FAMILY_DEPTH_EXTENSION_v0.8.json"),
        load("MC05_ETHYL_ACETATE_BETA_ELIMINATION_SOURCE_AUDIT_v0.1.json"),
        load("FAMILY_INDEPENDENCE_CAMPAIGN_v0.1.json"),
        load("SIX_TRAIL_ADJUDICATION_v0.1.json"),
        load("FAMILY_DEPTH_EXTENSION_v0.7.json"),
        load("MC05_ETHYL_CHLORIDE_SOURCE_AUDIT_v0.1.json"),
    )


def test_v08_validates_cleanly():
    assert validate(*inputs()) == []


def test_v09_parent_is_still_immutable_and_unmodified():
    ext, audit, *_ = inputs()
    for obj in [ext, audit]:
        assert obj["parent_release"]["immutable"] is True
        assert obj["coordinates_admitted"] == 0
        assert obj["grades_changed"] == 0
        assert obj["automatic_coordinate_admission"] is False


def test_mc05_barrier_typing_and_rate_derived_ea_quarantine_are_fail_closed():
    ext, audit, campaign, six, parent, held = inputs()
    ext["records"][0]["barrier_quantity"]["gibbs_free_energy_status"] = "GIBBS_FREE_ENERGY"
    ext["records"][0]["observed_comparator"]["rate_derived_arrhenius_activation_energy_role"] = "BARRIER_VALIDATOR"
    errors = validate(ext, audit, campaign, six, parent, held)
    assert any("Gibbs" in e for e in errors)
    assert any("quarantined" in e for e in errors)


def test_held_ethyl_chloride_cannot_be_silently_promoted():
    ext, audit, campaign, six, parent, held = inputs()
    held["ready_for_adjudication"] = True
    held["terminal_state"] = "READY_FOR_ADJUDICATION"
    errors = validate(ext, audit, campaign, six, parent, held)
    assert any("ethyl-chloride" in e for e in errors)


def test_family_depth_count_is_exactly_seven_without_admission():
    ext, *_ = inputs()
    assert ext["aggregate"]["ready_second_family_count"] == 7
    assert ext["aggregate"]["family_depth_classes_with_additive_ready_second_family"] == ["MC02", "MC04", "MC05", "MC06", "MC11", "MC14", "MC16"]
    assert ext["aggregate"]["coordinates_admitted"] == 0
    assert ext["aggregate"]["grades_changed"] == 0
