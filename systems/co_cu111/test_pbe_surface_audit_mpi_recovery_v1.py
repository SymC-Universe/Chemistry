#!/usr/bin/env python3
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
MOD = HERE / "pbe_surface_audit_mpi_recovery_v1.py"
spec = importlib.util.spec_from_file_location("mpi_recovery", MOD)
m = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(m)


class TestMPIRecovery(unittest.TestCase):
    def test_authoritative_parser_ignores_decomposition(self):
        text = """Forces acting on atoms (cartesian axes, Ry/au):\n\n atom 1 type 1 force = 0 0 0.002\n atom 2 type 1 force = 0 0 -0.002\n The non-local contrib. to forces\n atom 1 type 1 force = 0 0 9.0\n atom 2 type 1 force = 0 0 -9.0\n Total force = 0.003\n"""
        blocks = m.authoritative_force_blocks(text, 2)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0][0][2], 0.002)
        self.assertEqual(blocks[0][1][2], -0.002)

    def test_movable_force_uses_flags(self):
        atoms = [
            {"flags": [0, 0, 1]},
            {"flags": [0, 0, 0]},
            {"flags": [0, 0, 1]},
        ]
        forces = [(0.0, 0.0, 0.001), (0.0, 0.0, 9.0), (0.0, 0.0, -0.002)]
        got = m.max_movable_force_ev_a(forces, atoms)
        self.assertAlmostEqual(got, 0.002 * m.RY_BOHR_TO_EV_ANG, places=12)

    def test_force_component_parity(self):
        a = [(0.0, 0.0, 0.001)]
        b = [(0.0, 0.0, 0.001001)]
        got = m.max_force_component_difference_ev_a(a, b)
        self.assertAlmostEqual(got, 0.000001 * m.RY_BOHR_TO_EV_ANG, places=12)

    def test_protocol_is_frozen_and_bounded(self):
        p = m.protocol(HERE / "SYSTEM2_PBE_SURFACE_AUDIT_MPI_RECOVERY_v0.1.json")
        self.assertEqual(p["execution_amendment"]["mpi_rank_count_proposed"], 4)
        self.assertEqual(p["execution_amendment"]["maximum_new_continuation_segments"], 2)
        self.assertFalse(p["provenance"]["scientific_settings_changed"])
        self.assertFalse(p["provenance"]["kinetic_inputs_used"])

    def test_segment8_fixture_when_supplied(self):
        import os
        root = os.environ.get("CO_CU111_SEG8_FIXTURE")
        if not root:
            self.skipTest("fixture not supplied")
        p = m.protocol(HERE / "SYSTEM2_PBE_SURFACE_AUDIT_MPI_RECOVERY_v0.1.json")
        row, _, text = m.verify_segment8(Path(root), p)
        blocks = m.authoritative_force_blocks(text, int(row["layers"]))
        self.assertGreaterEqual(len(blocks), 2)
        f0 = m.max_movable_force_ev_a(blocks[0], row["input_atoms"])
        f1 = m.max_movable_force_ev_a(blocks[1], row["input_atoms"])
        self.assertAlmostEqual(f0, p["parser_correction"]["segment8_true_input_max_movable_force_ev_per_angstrom"], places=10)
        self.assertAlmostEqual(f1, p["parser_correction"]["segment8_true_second_evaluated_max_movable_force_ev_per_angstrom"], places=10)


if __name__ == "__main__":
    unittest.main()
