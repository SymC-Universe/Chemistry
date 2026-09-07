#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
import pbe_surface_timeout_recovery_v1 as rec
import pbe_surface_site_ordering_v1 as base

RECOVERY = HERE / "SYSTEM2_PBE_SURFACE_TIMEOUT_RECOVERY_v0.1.json"
SURFACE = HERE / "SYSTEM2_PBE_SURFACE_SITE_ORDERING_PROTOCOL_v0.1.json"


class RecoveryContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.p = rec.recovery_protocol(RECOVERY)
        self.p["_sha256"] = rec.sha256(RECOVERY)
        self.surface = base.load_json(SURFACE)
        base.verify_protocol(self.surface)

    def test_frozen_repo_sources_and_exact_targets(self) -> None:
        rec.verify_frozen_repo_sources(self.p)
        self.assertEqual(set(self.p["recovery_targets"]), {"reference", "audit"})
        for key in ("reference", "audit"):
            rec.verify_target_against_surface(self.surface, rec.get_target(self.p, key))

    def test_no_science_or_kinetic_change(self) -> None:
        self.assertFalse(self.p["provenance"]["scientific_settings_changed"])
        self.assertFalse(self.p["provenance"]["kinetic_inputs_used"])
        self.assertEqual(self.p["unchanged_science"]["mpi_rank_count"], 1)
        self.assertEqual(self.p["unchanged_science"]["ecutwfc_ry"], 90)
        self.assertEqual(self.p["unchanged_science"]["ecutrho_ry"], 900)
        self.assertEqual(self.p["continuation_contract"]["restart_claim"], "NOT_EXACT_QE_RESTART")
        self.assertFalse(self.p["continuation_contract"]["qe_restart_mode_added"])
        self.assertFalse(self.p["continuation_contract"]["qe_max_seconds_added"])
        self.assertEqual(self.p["continuation_contract"]["segment_runtime_cap_seconds"], 16200)
        self.assertEqual(self.p["continuation_contract"]["maximum_relax_segments"], 4)
        self.assertEqual(self.p["continuation_contract"]["continuation_mode"], "FROM_SCRATCH_FROM_LAST_EVALUATED_GEOMETRY")

    def test_generated_recovery_input_uses_frozen_qe_science(self) -> None:
        t = rec.get_target(self.p, "reference")
        cell, atoms = rec.cell_and_template(self.surface, t)
        bundle = {"pseudopotentials": {"Cu": {"filename": "Cu.UPF"}, "C": {"filename": "C.UPF"}, "O": {"filename": "O.UPF"}}}
        text = base.qe_input(
            calculation="relax", prefix="co_cu111_clean", cell=cell, atoms=atoms,
            kmesh=int(t["kmesh"]), protocol=self.surface, bundle=bundle,
            pseudo_dir=Path("/tmp/pseudo"), outdir=Path("/tmp/out"),
        )
        required = [
            "ecutwfc=90,", "ecutrho=900,", "input_dft='PBE',",
            "occupations='smearing',", "smearing='mv',", "degauss=0.02,",
            "conv_thr=1e-10,", "mixing_beta=0.3,", "electron_maxstep=200,",
            "assume_isolated='esm',", "esm_bc='bc1',", "20 20 1 0 0 0",
            "ion_dynamics='bfgs',",
        ]
        for token in required:
            self.assertIn(token, text)
        lower = text.lower()
        self.assertNotIn("restart_mode", lower)
        self.assertNotIn("max_seconds", lower)
        self.assertNotIn("nstep", lower)

    def test_last_evaluated_geometry_is_used_not_partial_tail(self) -> None:
        t = rec.get_target(self.p, "reference")
        _, template = rec.cell_and_template(self.surface, t)
        block1 = ["ATOMIC_POSITIONS (angstrom)"]
        block2 = ["ATOMIC_POSITIONS (angstrom)"]
        for i, atom in enumerate(template):
            x, y, z = atom["position_angstrom"]
            block1.append(f"Cu {x:.10f} {y:.10f} {z:.10f}")
            block2.append(f"Cu {x:.10f} {y:.10f} {z + 0.01:.10f}")
        # Each evaluated geometry must be followed by a completed energy and force record.
        complete1 = ["!    total energy              =   -1.00000000 Ry", "     Total force =     0.010000"]
        complete2 = ["!    total energy              =   -1.10000000 Ry", "     Total force =     0.009000"]
        block3 = ["ATOMIC_POSITIONS (angstrom)"]
        for atom in template:
            x, y, z = atom["position_angstrom"]
            block3.append(f"Cu {x:.10f} {y:.10f} {z + 0.02:.10f}")
        # block3 is followed only by the start of an SCF and must not be admitted.
        text = "\n".join(block1 + complete1 + block2 + complete2 + block3 + ["Self-consistent Calculation", "iteration # 1"]) + "\n"
        atoms = rec.last_evaluated_positions(text, len(template), template)
        self.assertIsNotNone(atoms)
        self.assertAlmostEqual(atoms[0]["position_angstrom"][2], template[0]["position_angstrom"][2] + 0.01, places=8)

    def test_optional_real_source_fixtures(self) -> None:
        fixtures = {
            "reference": os.environ.get("CO_CU111_REFERENCE_SOURCE"),
            "audit": os.environ.get("CO_CU111_AUDIT_SOURCE"),
        }
        if not all(fixtures.values()):
            self.skipTest("real source artifacts not supplied")
        for key, root in fixtures.items():
            t = rec.get_target(self.p, key)
            rec.verify_source_artifact(Path(root), t)
            atoms = rec.positions_from_source(Path(root), self.surface, t)
            self.assertEqual(len(atoms), int(t["layers"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
