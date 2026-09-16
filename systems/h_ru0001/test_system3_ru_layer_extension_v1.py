#!/usr/bin/env python3
import unittest

from system3_ru_layer_extension_v1 import source_layer_rows, suffix_decision


class TestRuLayerExtension(unittest.TestCase):
    def test_suffix_pass_requires_complete_larger_suffix(self):
        rows = [
            {"layers": 5, "surface_excess_ev_per_surface_atom": 0.4700},
            {"layers": 7, "surface_excess_ev_per_surface_atom": 0.4760},
            {"layers": 9, "surface_excess_ev_per_surface_atom": 0.4782},
            {"layers": 11, "surface_excess_ev_per_surface_atom": 0.4786},
            {"layers": 13, "surface_excess_ev_per_surface_atom": 0.4791},
            {"layers": 15, "surface_excess_ev_per_surface_atom": 0.4792},
            {"layers": 17, "surface_excess_ev_per_surface_atom": 0.4793},
            {"layers": 19, "surface_excess_ev_per_surface_atom": 0.4794},
        ]
        selected, _ = suffix_decision(rows, 0.001, 7)
        self.assertEqual(selected, 11)

    def test_isolated_in_tolerance_rung_does_not_pass(self):
        rows = [
            {"layers": 5, "surface_excess_ev_per_surface_atom": 0.4700},
            {"layers": 7, "surface_excess_ev_per_surface_atom": 0.4800},
            {"layers": 9, "surface_excess_ev_per_surface_atom": 0.4770},
            {"layers": 11, "surface_excess_ev_per_surface_atom": 0.4801},
            {"layers": 13, "surface_excess_ev_per_surface_atom": 0.4772},
            {"layers": 15, "surface_excess_ev_per_surface_atom": 0.4802},
            {"layers": 17, "surface_excess_ev_per_surface_atom": 0.4774},
            {"layers": 19, "surface_excess_ev_per_surface_atom": 0.4803},
        ]
        selected, _ = suffix_decision(rows, 0.001, 7)
        self.assertIsNone(selected)

    def test_terminal_alone_is_not_a_pass(self):
        rows = [
            {"layers": 7, "surface_excess_ev_per_surface_atom": 0.470},
            {"layers": 9, "surface_excess_ev_per_surface_atom": 0.472},
            {"layers": 11, "surface_excess_ev_per_surface_atom": 0.474},
            {"layers": 13, "surface_excess_ev_per_surface_atom": 0.476},
            {"layers": 15, "surface_excess_ev_per_surface_atom": 0.478},
            {"layers": 17, "surface_excess_ev_per_surface_atom": 0.480},
            {"layers": 19, "surface_excess_ev_per_surface_atom": 0.482},
        ]
        selected, _ = suffix_decision(rows, 0.001, 7)
        self.assertIsNone(selected)

    def test_source_ladder_reuses_selected_l7_baseline(self):
        src = {
            "selected_kmesh": [16, 16, 1],
            "selected_total_vacuum_angstrom": 15.0,
            "raw_records": [
                {
                    "kind": "slab_scf",
                    "first_stage_requested": "layers",
                    "layers": 5,
                    "kmesh": [16, 16, 1],
                    "total_vacuum_angstrom": 15.0,
                    "surface_excess_ev_per_surface_atom": 1.0987778170992897,
                },
                {
                    "kind": "slab_scf",
                    "first_stage_requested": "vacuum",
                    "layers": 7,
                    "kmesh": [16, 16, 1],
                    "total_vacuum_angstrom": 15.0,
                    "surface_excess_ev_per_surface_atom": 1.0929096816544188,
                },
                {
                    "kind": "slab_scf",
                    "first_stage_requested": "layers",
                    "layers": 9,
                    "kmesh": [16, 16, 1],
                    "total_vacuum_angstrom": 15.0,
                    "surface_excess_ev_per_surface_atom": 1.0954157142714394,
                },
                {
                    "kind": "slab_scf",
                    "first_stage_requested": "layers",
                    "layers": 11,
                    "kmesh": [16, 16, 1],
                    "total_vacuum_angstrom": 15.0,
                    "surface_excess_ev_per_surface_atom": 1.0895499598245806,
                },
                {
                    "kind": "slab_scf",
                    "first_stage_requested": "layers",
                    "layers": 13,
                    "kmesh": [16, 16, 1],
                    "total_vacuum_angstrom": 15.0,
                    "surface_excess_ev_per_surface_atom": 1.0926721942851145,
                },
            ],
        }
        rows = source_layer_rows(src)
        self.assertEqual([r["layers"] for r in rows], [5, 7, 9, 11, 13])
        self.assertEqual(rows[1]["origin"], "source_selected_baseline")
        self.assertAlmostEqual(rows[1]["surface_excess_ev_per_surface_atom"], 1.0929096816544188)


if __name__ == "__main__":
    unittest.main()
