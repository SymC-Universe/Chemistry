from pathlib import Path
import json

from validate_family_depth_extension_v0_7 import validate

ROOT = Path(__file__).resolve().parent


def load(name: str):
    return json.loads((ROOT / name).read_text())


def test_family_depth_extension_v07():
    assert validate(
        load("FAMILY_DEPTH_EXTENSION_v0.7.json"),
        load("MC16_CH3_H2_CHAIN_PROPAGATION_SOURCE_AUDIT_v0.1.json"),
        load("FAMILY_INDEPENDENCE_CAMPAIGN_v0.1.json"),
        load("SIX_TRAIL_ADJUDICATION_v0.1.json"),
        load("FAMILY_DEPTH_EXTENSION_v0.6.json"),
        load("MC16_METHYLPEROXY_SCIENTIFIC_TOPOLOGY_AUDIT_v0.2.json"),
    ) == []


def test_v09_stays_immutable_and_unadmitted():
    ext = load("FAMILY_DEPTH_EXTENSION_v0.7.json")
    assert ext["parent_release"]["immutable"] is True
    assert ext["automatic_coordinate_admission"] is False
    assert ext["coordinates_admitted"] == 0
    assert ext["grades_changed"] == 0


def test_ch3_h2_ready_is_single_barrier_propagation_not_network_termination():
    ext = load("FAMILY_DEPTH_EXTENSION_v0.7.json")
    rec = ext["records"][0]
    assert rec["trail_id"] == "FI-MC16-CH3-H2-CHAIN-PROPAGATION"
    assert rec["classification_gate"] == "PASS_MC16_RADICAL_CHAIN_PROPAGATION"
    assert rec["representation_mode"] == "SINGLE_BARRIER_RADICAL_CHAIN_PROPAGATION_H_ATOM_TRANSFER"
    assert rec["ready_for_adjudication"] is True
    assert rec["automatic_admission"] is False


def test_classical_barrier_is_not_relabelled_as_free_energy_or_arrhenius_ea():
    ext = load("FAMILY_DEPTH_EXTENSION_v0.7.json")
    q = ext["records"][0]["barrier_quantity"]
    assert q["value"] == 11.9
    assert q["unit"] == "kcal/mol"
    assert q["free_energy_status"] == "NOT_A_GIBBS_FREE_ENERGY_BARRIER"
    assert q["arrhenius_activation_energy_status"] == "NOT_AN_EXPERIMENTAL_ARRHENIUS_ACTIVATION_ENERGY"


def test_comparator_window_and_firewall_are_frozen():
    ext = load("FAMILY_DEPTH_EXTENSION_v0.7.json")
    rec = ext["records"][0]
    comp = rec["observed_comparator"]
    assert comp["source_doi"] == "10.1039/F19817702271"
    assert comp["temperature_range_K"] == [584.0, 671.0]
    assert comp["pressure_range_Torr"] == [5.0, 26.0]
    for key in ["residual_may_select_candidate", "chi_may_select_candidate", "expected_chemsa_agreement_may_select_candidate", "same_target_fit_or_method_selection_may_validate_target"]:
        assert ext["selection_firewall"][key] is False


def test_methylperoxy_hold_is_preserved_separately():
    ext = load("FAMILY_DEPTH_EXTENSION_v0.7.json")
    methylperoxy = load("MC16_METHYLPEROXY_SCIENTIFIC_TOPOLOGY_AUDIT_v0.2.json")
    assert methylperoxy["terminal_state"] == "PES_TOPOLOGY_NETWORK_AND_MODEL_PROVENANCE_HOLD"
    assert methylperoxy["ready_for_adjudication"] is False
    assert ext["preserved_nonpromotion_states"]["FI-MC16-METHYLPEROXY-SELF-REACTION"] == "PES_TOPOLOGY_NETWORK_AND_MODEL_PROVENANCE_HOLD"


def test_family_depth_reaches_six_without_parent_mutation():
    ext = load("FAMILY_DEPTH_EXTENSION_v0.7.json")
    assert ext["aggregate"]["family_depth_classes_with_additive_ready_second_family"] == ["MC02", "MC04", "MC06", "MC11", "MC14", "MC16"]
    assert ext["aggregate"]["ready_second_family_count"] == 6
    assert ext["aggregate"]["target_class_count"] == 11
    assert ext["aggregate"]["coordinates_admitted"] == 0
    assert ext["aggregate"]["grades_changed"] == 0
