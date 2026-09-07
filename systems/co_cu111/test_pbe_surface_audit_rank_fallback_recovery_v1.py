#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
MOD = HERE / "pbe_surface_audit_rank_fallback_recovery_v1.py"
spec = importlib.util.spec_from_file_location("rank_fallback_recovery", MOD)
m = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(m)


class TestRankFallbackRecovery(unittest.TestCase):
    def test_authoritative_parser_ignores_decomposition(self):
        text = """Forces acting on atoms (cartesian axes, Ry/au):\n\n atom 1 type 1 force = 0 0 0.002\n atom 2 type 1 force = 0 0 -0.002\n The non-local contrib. to forces\n atom 1 type 1 force = 0 0 9.0\n atom 2 type 1 force = 0 0 -9.0\n Total force = 0.003\n"""
        blocks = m.authoritative_force_blocks(text, 2)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0][0][2], 0.002)
        self.assertEqual(blocks[0][1][2], -0.002)

    def test_command_builder_preserves_direct_one_rank(self):
        pw = Path("/tmp/pw.x")
        self.assertEqual(m.command_for_rank(pw, 1), [str(pw)])
        self.assertEqual(m.command_for_rank(pw, 2), ["mpirun", "-np", "2", str(pw)])
        self.assertEqual(m.command_for_rank(pw, 3), ["mpirun", "-np", "3", str(pw)])

    def test_highest_passing_rank_is_selected(self):
        records = [
            {"test_mpi_ranks": 3, "status": "NUMERICAL_PARITY_REJECTED"},
            {"test_mpi_ranks": 2, "status": "PASS"},
        ]
        self.assertEqual(m.select_highest_passing(records, [3, 2], 1), 2)

    def test_three_rank_short_circuits_higher_choice(self):
        records = [
            {"test_mpi_ranks": 3, "status": "PASS"},
            {"test_mpi_ranks": 2, "status": "PASS"},
        ]
        self.assertEqual(m.select_highest_passing(records, [3, 2], 1), 3)

    def test_original_one_rank_is_fail_closed_fallback(self):
        records = [
            {"test_mpi_ranks": 3, "status": "NUMERICAL_PARITY_REJECTED"},
            {"test_mpi_ranks": 2, "status": "MECHANICAL_CANDIDATE_EXECUTION_REJECTED"},
        ]
        self.assertEqual(m.select_highest_passing(records, [3, 2], 1), 1)

    def test_protocol_freezes_science_parity_and_budget(self):
        p = m.protocol(HERE / "SYSTEM2_PBE_SURFACE_AUDIT_RANK_FALLBACK_RECOVERY_v0.1.json")
        self.assertEqual(p["rank_qualification"]["candidate_mpi_ranks_descending"], [3, 2])
        self.assertEqual(p["rank_qualification"]["fallback_mpi_ranks"], 1)
        self.assertEqual(p["rank_qualification"]["energy_absolute_difference_max_ev"], 0.0001)
        self.assertEqual(p["rank_qualification"]["force_component_absolute_difference_max_ev_per_angstrom"], 0.0001)
        self.assertEqual(p["execution"]["maximum_new_continuation_segments"], 4)
        self.assertEqual(p["execution"]["logical_segment_numbers"], [9, 10, 11, 12])
        self.assertEqual(p["unchanged_science"]["force_gate_ev_per_angstrom"], 0.02)
        self.assertEqual(p["unchanged_science"]["independent_scf_reproduction_gate_ev"], 0.001)
        self.assertFalse(p["provenance"]["scientific_settings_changed"])
        self.assertFalse(p["provenance"]["kinetic_inputs_used"])

    def test_force_component_parity_math(self):
        a = [(0.0, 0.0, 0.001)]
        b = [(0.0, 0.0, 0.001001)]
        got = m.max_force_component_difference_ev_a(a, b)
        self.assertAlmostEqual(got, 0.000001 * m.RY_BOHR_TO_EV_ANG, places=12)


if __name__ == "__main__":
    unittest.main()
