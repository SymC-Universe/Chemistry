#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("depth_ext", HERE / "pbe_surface_depth_stack_v1.py")
mod = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(mod)


class StubBase:
    @staticmethod
    def clean_geometry(a0, layers, vacuum):
        dz = 2.0
        center = (layers - 1) / 2.0
        atoms = []
        for i in range(layers):
            atoms.append({
                "symbol": "Cu",
                "position_angstrom": [0.0, 0.0, (i-center)*dz],
                "flags": [0, 0, 0],
                "layer": i,
            })
        return [[1.0,0.0,0.0],[0.0,1.0,0.0],[0.0,0.0,float(vacuum)]], atoms


class TestSurfaceDepthExtension(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol_path = HERE / "SYSTEM2_PBE_SURFACE_CONVERGENCE_L19_v0.1.json"
        cls.policy_path = HERE / "SYSTEM2_PBE_SURFACE_DEPTH_STACKING_POLICY_v0.1.json"
        cls.raw = json.loads(cls.protocol_path.read_text())
        cls.policy = json.loads(cls.policy_path.read_text())

    def test_full_protocol_validation_passes_fail_closed_contract(self):
        p = mod.protocol(self.protocol_path)
        self.assertEqual(p["scientific_scope"], "PROSPECTIVE_ODD_LAYER_DEPTH_EXTENSION_UNDER_FROZEN_STACKING_POLICY")
        self.assertEqual(p["extension_audit"]["case_id"], "L19-V40-K36-extension-audit")

    def test_l19_target_and_predefined_rung_rule(self):
        p = self.raw
        self.assertEqual((p["source_reference"]["layers"], p["source_reference"]["vacuum_angstrom"], p["source_reference"]["kmesh"]), (17,36.0,32))
        self.assertEqual((p["extension_audit"]["layers"], p["extension_audit"]["vacuum_angstrom"], p["extension_audit"]["kmesh"]), (19,40.0,36))
        self.assertEqual(p["extension_audit"]["layers"]-p["source_reference"]["layers"], 2)
        self.assertEqual(p["extension_audit"]["vacuum_angstrom"]-p["source_reference"]["vacuum_angstrom"], 4.0)
        self.assertEqual(p["extension_audit"]["kmesh"]-p["source_reference"]["kmesh"], 4)

    def test_old_l17_hold_is_preserved_not_reclassified(self):
        s = self.raw["source_reference"]
        self.assertEqual(s["required_result_status"], "NUMERICAL_HOLD_L17_TERMINAL_UNDER_CURRENT_CONTRACT")
        self.assertTrue(s["force_pass"])
        self.assertTrue(s["energy_reproduction_pass"])
        self.assertFalse(s["surface_excess_pass"])
        self.assertTrue(s["prior_failure_preserved"])
        self.assertTrue(self.raw["provenance"]["original_l17_failure_preserved_as_failure"])

    def test_thresholds_unchanged_and_match_stacking_policy(self):
        m = self.raw["frozen_method"]
        g = self.policy["unchanged_scientific_gates"]
        self.assertEqual(m["force_gate_ev_per_angstrom"], 0.02)
        self.assertEqual(m["independent_scf_reproduction_gate_ev"], 0.001)
        self.assertEqual(m["surface_excess_convergence_max_ev_per_surface_atom"], 0.001)
        self.assertEqual(g["max_movable_force_ev_per_angstrom"], m["force_gate_ev_per_angstrom"])
        self.assertEqual(g["independent_scf_reproduction_delta_ev"], m["independent_scf_reproduction_gate_ev"])
        self.assertEqual(g["adjacent_rung_surface_excess_delta_ev_per_surface_atom"], m["surface_excess_convergence_max_ev_per_surface_atom"])
        self.assertFalse(self.raw["provenance"]["thresholds_changed"])

    def test_checkpoint_contract_and_meter_rule(self):
        ex = self.raw["execution"]
        self.assertEqual(ex["checkpoint_mode"], "QE_CLEAN_MAX_SECONDS_EXACT_RESTART")
        self.assertEqual(ex["qe_max_seconds_per_segment"], 16200)
        self.assertEqual(ex["shutdown_and_artifact_reserve_seconds"], 5400)
        self.assertEqual(ex["github_job_timeout_minutes"]*60, 21600)
        self.assertEqual(ex["qe_max_seconds_per_segment"]+ex["shutdown_and_artifact_reserve_seconds"], 21600)
        self.assertEqual(ex["runner_label"], "ubuntu-24.04")
        self.assertTrue(self.policy["execution"]["larger_runner_only_after_demonstrated_resource_failure"])
        self.assertTrue(self.policy["execution"]["duplicate_paid_compute_forbidden_when_valid_checkpoint_survives"])

    def test_restart_input_changes_only_restart_mode(self):
        base = "&CONTROL\n calculation='relax',\n/\n&SYSTEM\n/\n"
        first = mod.add_control_fields(base, "from_scratch", 16200)
        rest = mod.add_control_fields(base, "restart", 16200)
        self.assertIn("restart_mode='from_scratch'", first)
        self.assertIn("restart_mode='restart'", rest)
        self.assertIn("max_seconds=16200", first)
        self.assertIn("max_seconds=16200", rest)
        self.assertEqual(first.replace("from_scratch", "restart"), rest)

    def test_complete_prior_rejects_protocol_hash_drift(self):
        p = mod.protocol(self.protocol_path)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            state = {
                "schema": mod.STATE_SCHEMA, "stage": "relax", "segment": 1,
                "case_id": p["extension_audit"]["case_id"], "layers": 19,
                "status": "COMPLETE", "scientific_settings_changed": False,
                "thresholds_changed": False, "protocol_sha256": "0"*64,
            }
            mod.write_json(mod.state_output_path(root), state)
            with self.assertRaises(SystemExit):
                mod.load_prior(root, "relax", 1, p)

    def test_checkpoint_manifest_detects_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            f = root / "qe_checkpoint" / "prefix.save" / "data-file-schema.xml"
            f.parent.mkdir(parents=True)
            f.write_text("state-a")
            h = mod.write_checkpoint_manifest(root)
            self.assertEqual(mod.verify_checkpoint_manifest(root, h), h)
            f.write_text("state-b")
            with self.assertRaises(SystemExit):
                mod.verify_checkpoint_manifest(root, h)

    def test_surface_offset_seed_uses_geometry_only_and_preserves_symmetry(self):
        p = self.raw
        _, ideal = StubBase.clean_geometry(p["frozen_method"]["bulk_lattice_constant_angstrom"], 17, 36.0)
        source = {"final_atoms": json.loads(json.dumps(ideal))}
        offsets = [0.02, 0.003, -0.003, -0.02]
        for i,d in zip(p["initialization"]["source_layers"], offsets):
            source["final_atoms"][i]["position_angstrom"][2] += d
        cell, seed, evidence = mod.seed_target(source, p, StubBase)
        self.assertEqual(len(seed), 19)
        for a,b in zip(evidence["z_offsets_angstrom"], offsets):
            self.assertAlmostEqual(a,b,places=12)
        self.assertFalse(evidence["energy_or_surface_excess_used_to_seed"])
        self.assertTrue(evidence["initialization_only"])
        _, ideal19 = StubBase.clean_geometry(p["frozen_method"]["bulk_lattice_constant_angstrom"], 19, 40.0)
        got = [seed[i]["position_angstrom"][2]-ideal19[i]["position_angstrom"][2] for i in p["initialization"]["target_layers"]]
        for a,b in zip(got, offsets):
            self.assertAlmostEqual(a,b,places=12)
        self.assertEqual(cell[2][2], 40.0)

    def test_continuation_policy_is_not_deadline_tuned(self):
        d = self.policy["deadline_policy"]
        self.assertTrue(d["publication_deadline_is_operational_not_scientific"])
        self.assertTrue(d["deadline_may_not_change_method_thresholds_or_interpretation"])
        c = self.policy["continuation_logic"]
        self.assertTrue(c["no_outcome_dependent_threshold_retuning"])
        self.assertTrue(c["no_retroactive_reclassification_of_prior_rungs"])
        self.assertTrue(c["next_rung_requires_new_hash_binding_before_compute"])

    def test_pinned_source_and_policy_hashes_present(self):
        s = self.raw["source_reference"]
        for key in ("relax_state_sha256","result_json_sha256"):
            self.assertRegex(s[key], r"^[0-9a-f]{64}$")
        self.assertRegex(self.raw["stacking_policy"]["sha256"], r"^[0-9a-f]{64}$")


if __name__ == "__main__":
    unittest.main(verbosity=2)
