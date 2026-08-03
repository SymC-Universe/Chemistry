#!/usr/bin/env python3
from __future__ import annotations

import argparse
import contextlib
import io
import json
import math
from pathlib import Path
import tempfile
import unittest

import numpy as np

import closure_engine as ce


class ClosureEngineTests(unittest.TestCase):
    def test_geometry_replication_and_site_classification(self) -> None:
        cell, atoms = ce.primitive_clean_geometry(3.60, 7, 16.0)
        self.assertEqual(len(atoms), 7)
        self.assertEqual(sum(a["flags"] == [0, 0, 1] for a in atoms), 4)
        supercell, replicated = ce.replicate_surface(cell, atoms, 4)
        self.assertEqual(len(replicated), 112)
        for site in ("top", "bridge", "hollow"):
            fx, fy = ce.surface_site_fraction(site)
            pos = ce.frac_to_cart([fx, fy, 0.5], supercell)
            classified = ce.classify_surface_site(pos, supercell)
            self.assertEqual(classified["site"], site)
            self.assertLess(classified["distance_angstrom"], 1e-10)

    def test_registered_flags_are_restored(self) -> None:
        parsed = [{"symbol": "Cu", "position_angstrom": [0.0, 0.0, 0.0], "flags": [1, 1, 1]}]
        template = [{"symbol": "Cu", "position_angstrom": [0.0, 0.0, 0.0], "flags": [0, 0, 1]}]
        restored = ce.restore_flags(parsed, template)
        self.assertEqual(restored[0]["flags"], [0, 0, 1])

    def test_neb_parser(self) -> None:
        text = """
 activation energy (->) = 0.051 eV
 activation energy (<-) = 0.050 eV
 1 -100.000 0.000 T
 2 -99.980 0.021 F
 3 -99.949 0.017 F
 4 -99.979 0.018 F
 5 -100.001 0.000 T
 NEB: convergence achieved
 JOB DONE.
 """
        result = ce.parse_neb_output(text, 5)
        self.assertTrue(result["converged"])
        self.assertTrue(result["job_done"])
        self.assertAlmostEqual(result["forward_barrier_ev"], 0.051)
        self.assertEqual(len(result["images"]), 5)
        self.assertAlmostEqual(result["max_internal_error_ev_per_angstrom"], 0.021)

    def test_hessian_reconstruction(self) -> None:
        target = np.diag([0.8, 1.2, 2.0])
        delta = 0.02
        records = {}
        for axis in range(3):
            e = np.zeros(3)
            e[axis] = delta
            records[(axis, 1)] = (-target @ e).tolist()
            records[(axis, -1)] = (target @ e).tolist()
        recovered = ce.hessian_from_force_records(records, delta)
        self.assertTrue(np.allclose(recovered, target, atol=1e-12))
        frequencies = ce.frequencies_from_eigenvalues(np.array([-0.5, 0.8, 1.2]))
        self.assertLess(frequencies[0], 0.0)
        self.assertGreater(frequencies[1], 0.0)

    def test_barrier_and_computational_atlas_remain_separate(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "PATH_CONVERGENCE_HANDOFF.json"
            ci = root / "CI_NEB_HANDOFF.json"
            saddle = root / "SADDLE_HANDOFF.json"
            evidence = root / "public_evidence_candidates.json"
            barrier = root / "BARRIER_COORDINATE.json"
            atlas = root / "ATLAS_ADMISSION_RECORD.json"
            path.write_text(json.dumps({
                "schema": "na-cu001-path-convergence-handoff-v0.1",
                "status": "PASS",
                "selected_record": {"forward_barrier_ev": 0.052},
                "barrier_range_ev": 0.004,
            }))
            ci.write_text(json.dumps({
                "schema": "na-cu001-ci-neb-handoff-v0.1",
                "status": "PASS",
                "forward_barrier_ev": 0.051,
                "reverse_barrier_ev": 0.050,
            }))
            saddle.write_text(json.dumps({
                "schema": "na-cu001-saddle-handoff-v0.1",
                "status": "PASS",
                "partial_vineyard_prefactor_hz": 5.0e11,
                "partial_vineyard_prefactor_delta_check_hz": 5.1e11,
                "partial_vineyard_prefactor_relative_difference": 0.02,
            }))
            evidence.write_text(json.dumps({
                "schema": "na-cu001-public-evidence-candidates-v0.1",
                "status": "HOLD",
                "reported_barrier_ev": 0.051,
                "reported_attempt_frequency_hz": 5.3e11,
            }))
            with contextlib.redirect_stdout(io.StringIO()):
                ce.command_barrier(argparse.Namespace(
                    path_handoff=str(path), ci_handoff=str(ci),
                    saddle_handoff=str(saddle), out=str(barrier),
                ))
            coordinate = json.loads(barrier.read_text())
            self.assertEqual(coordinate["status"], "PASS")
            self.assertIsNone(coordinate["friction_or_linewidth"])
            self.assertEqual(len(coordinate["computed_rate_coordinates"]), 5)
            expected = 5.0e11 * math.exp(-0.051 / (ce.KB_EV_K * 300.0))
            self.assertAlmostEqual(coordinate["computed_rate_coordinates"][-1]["rate_s_minus_1"], expected)
            with contextlib.redirect_stdout(io.StringIO()):
                ce.command_atlas(argparse.Namespace(
                    barrier_coordinate=str(barrier), public_evidence=str(evidence), out=str(atlas),
                ))
            admission = json.loads(atlas.read_text())
            self.assertEqual(admission["status"], "PASS")
            self.assertEqual(admission["experimental_admission_status"], "HOLD_PENDING_EXACT_STATE_POINT_TABLE")
            self.assertTrue(all(row["experimental_rate"] is None for row in admission["computational_rows"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
