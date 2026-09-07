from pathlib import Path
import json

from validate_family_depth_extension_v0_6 import validate

ROOT = Path(__file__).resolve().parent


def load(name: str):
    return json.loads((ROOT / name).read_text())


def test_family_depth_extension_v06():
    ext = load("FAMILY_DEPTH_EXTENSION_v0.6.json")
    audit = load("MC02_N2O_DISSOCIATION_SOURCE_AUDIT_v0.1.json")
    campaign = load("FAMILY_INDEPENDENCE_CAMPAIGN_v0.1.json")
    six = load("SIX_TRAIL_ADJUDICATION_v0.1.json")
    assert validate(ext, audit, campaign, six) == []


def test_v09_stays_immutable_and_unadmitted():
    ext = load("FAMILY_DEPTH_EXTENSION_v0.6.json")
    assert ext["parent_release"]["immutable"] is True
    assert ext["automatic_coordinate_admission"] is False
    assert ext["coordinates_admitted"] == 0
    assert ext["grades_changed"] == 0


def test_cyclobutene_refusal_is_preserved():
    ext = load("FAMILY_DEPTH_EXTENSION_v0.6.json")
    six = load("SIX_TRAIL_ADJUDICATION_v0.1.json")
    assert ext["frozen_outcomes_reaffirmed"]["FI-MC02-CYCLOBUTENE-CLASSIFICATION-CHECK"] == "REFUSED_FOR_MC02_CLASSIFICATION"
    by_id = {r["trail_id"]: r for r in six["trails"]}
    assert by_id["FI-MC02-CYCLOBUTENE-CLASSIFICATION-CHECK"]["terminal_state"] == "REFUSED_FOR_MC02_CLASSIFICATION"


def test_n2o_ready_requires_network_resolved_spin_crossing_representation():
    ext = load("FAMILY_DEPTH_EXTENSION_v0.6.json")
    rec = ext["records"][0]
    assert rec["ready_for_adjudication"] is True
    assert rec["terminal_state"] == "READY_FOR_ADJUDICATION"
    assert rec["representation_mode"] == "NETWORK_RESOLVED_NONADIABATIC_SPIN_CROSSING_DISSOCIATION_HIGH_PRESSURE_LIMIT"
    assert rec["automatic_admission"] is False


def test_theory_rate_agreement_is_quarantined_from_selection():
    audit = load("MC02_N2O_DISSOCIATION_SOURCE_AUDIT_v0.1.json")
    quarantine = audit["barrier_source"]["source_theoretical_rate_expression_quarantine"]
    assert quarantine["role"] == "REPRESENTATION_AND_PROVENANCE_ONLY_NOT_SELECTION_OR_INDEPENDENT_COMPARATOR"
    assert audit["selection_firewall"]["residual_may_select_candidate"] is False
    assert audit["selection_firewall"]["chi_may_select_candidate"] is False
    assert audit["selection_firewall"]["expected_chemsa_agreement_may_select_candidate"] is False


def test_crossing_energy_is_not_relabelled_as_free_energy_or_arrhenius_ea():
    audit = load("MC02_N2O_DISSOCIATION_SOURCE_AUDIT_v0.1.json")
    q = audit["barrier_source"]["reported_quantity"]
    assert q["value"] == 60.1
    assert q["unit"] == "kcal/mol"
    assert q["free_energy_status"] == "NOT_A_GIBBS_FREE_ENERGY_BARRIER"
    assert q["arrhenius_activation_energy_status"] == "NOT_AN_EXPERIMENTAL_ARRHENIUS_ACTIVATION_ENERGY"
