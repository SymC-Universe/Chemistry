#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("ext", HERE / "pbe_surface_convergence_extension_v1.py")
ext = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(ext)
PROTOCOL = HERE / "SYSTEM2_PBE_SURFACE_CONVERGENCE_EXTENSION_v0.1.json"


class ExtensionTests(unittest.TestCase):
    def load_protocol(self):
        p = ext.protocol(PROTOCOL)
        p["_protocol_path"] = str(PROTOCOL)
        return p

    def test_frozen_scientific_contract(self):
        p = self.load_protocol()
        self.assertEqual(p["extension_audit"]["case_id"], "L15-V32-K28-extension-audit")
        self.assertEqual((p["extension_audit"]["layers"], p["extension_audit"]["vacuum_angstrom"], p["extension_audit"]["kmesh"]), (15, 32.0, 28))
        self.assertEqual(p["frozen_method"]["force_gate_ev_per_angstrom"], 0.02)
        self.assertEqual(p["frozen_method"]["independent_scf_reproduction_gate_ev"], 0.001)
        self.assertEqual(p["frozen_method"]["surface_excess_convergence_max_ev_per_surface_atom"], 0.001)
        self.assertTrue(p["decision"]["no_threshold_retuning_after_results"])
        self.assertTrue(p["decision"]["no_additional_scientific_rung_authorized"])
        self.assertFalse(p["decision"]["automatic_site_ordering_dispatch"])

    def test_mechanical_runway_is_bounded_and_direct_one_rank(self):
        p = self.load_protocol()
        ex = p["execution"]
        self.assertEqual(ex["execution_mode"], "DIRECT_ONE_RANK")
        self.assertEqual(ex["mpi_ranks"], 1)
        self.assertEqual(ex["maximum_continuation_segments"], 36)
        self.assertEqual(ex["logical_segment_numbers"], list(range(1, 37)))
        self.assertEqual(ex["continuation_segment_runtime_cap_seconds"], 19800)
        self.assertEqual(ex["reproduction_runtime_cap_seconds"], 19200)
        self.assertTrue(ex["four_rank_reselection_forbidden"])
        self.assertTrue(ex["new_rank_qualification_forbidden"])

    def synthetic_l13(self):
        p = self.load_protocol()
        _, atoms = ext.ideal_geometry(p["frozen_method"]["bulk_lattice_constant_angstrom"], 13, 28.0)
        offsets = p["initialization"]["l13_offsets_angstrom"]
        for layer, delta in ((0, offsets["bottom_outermost"]), (1, offsets["bottom_subsurface"]), (11, offsets["top_subsurface"]), (12, offsets["top_outermost"])):
            atoms[layer]["position_angstrom"][2] += delta
        return {
            "case_id": "L13-V28-K24-audit",
            "final_atoms": atoms,
        }

    def test_seed_uses_only_surface_z_offsets(self):
        p = self.load_protocol()
        l13 = self.synthetic_l13()
        _, ideal15 = ext.ideal_geometry(p["frozen_method"]["bulk_lattice_constant_angstrom"], 15, 32.0)
        cell, seed, evidence = ext.seed_from_l13(l13, p)
        self.assertAlmostEqual(cell[2][2], 61.359982358301025, places=12)
        self.assertFalse(evidence["energy_or_surface_excess_used_to_seed"])
        self.assertTrue(evidence["initialization_only"])
        changed = []
        for i, (a, b) in enumerate(zip(seed, ideal15)):
            for j in (0, 1):
                self.assertAlmostEqual(a["position_angstrom"][j], b["position_angstrom"][j], places=12)
            if abs(a["position_angstrom"][2] - b["position_angstrom"][2]) > 1e-14:
                changed.append(i)
        self.assertEqual(changed, [0, 1, 13, 14])

    def test_prior_segment_manifest_and_carry_state(self):
        p = self.load_protocol()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            record = {
                "schema": ext.SEG_SCHEMA,
                "status": "RELAX_COMPLETE",
                "segment": 4,
                "case_id": "L15-V32-K28-extension-audit",
                "layers": 15,
                "vacuum_angstrom": 32.0,
                "kmesh": 28,
                "mpi_ranks": 1,
                "execution_mode": "DIRECT_ONE_RANK",
                "scientific_settings_changed": False,
                "kinetic_inputs_used": False,
                "surface_convergence_extension_protocol_sha256": ext.sha256(PROTOCOL),
                "final_atoms": [{}] * 15,
            }
            rp = root / "SURFACE_CONVERGENCE_EXTENSION_SEGMENT.json"
            rp.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
            (root / "STAGE_TIME_MANIFEST.sha256").write_text(f"{ext.sha256(rp)}  {rp.name}\n")
            got, _ = ext.verify_prior_segment(root, p, 4)
            self.assertEqual(got["status"], "RELAX_COMPLETE")

    def test_actual_source_fixtures_when_available(self):
        hold = os.environ.get("CO_CU111_HOLD_FIXTURE")
        l13 = os.environ.get("CO_CU111_L13_FIXTURE")
        if not hold or not l13:
            self.skipTest("source fixtures not provided")
        p = self.load_protocol()
        h, hp = ext.verify_source_hold(Path(hold), p)
        r, rp = ext.verify_l13_reference(Path(l13), p)
        self.assertEqual(ext.sha256(hp), p["source_hold"]["gate_sha256"])
        self.assertEqual(ext.sha256(rp), p["extension_reference"]["summary_sha256"])
        self.assertFalse(h["reference_audit_pass"])
        self.assertTrue(r["mechanical_pass"])
        self.assertEqual(r["energy_reproduction_delta_ev"], 0.0)


if __name__ == "__main__":
    unittest.main()
