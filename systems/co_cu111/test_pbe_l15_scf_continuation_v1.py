#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("continuation", HERE / "pbe_l15_scf_continuation_v1.py")
continuation = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(continuation)


class L15ScfContinuationTests(unittest.TestCase):
    def make_save(self, root: Path, *, include_paw: bool = True) -> Path:
        save = root / f"{continuation.PREFIX}.save"
        save.mkdir(parents=True)
        (save / "data-file-schema.xml").write_text("<xml/>\n")
        (save / "charge-density.dat").write_bytes(b"density")
        if include_paw:
            (save / "paw.txt").write_text("paw-becsum\n")
        (save / "wfc1.dat").write_bytes(b"excluded-wavefunction")
        return save

    def test_preserve_and_restore_complete_paw_density_state(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            tmp = root / "tmp"
            self.make_save(tmp)
            state = root / "state"
            preserved = continuation.preserve_density_state(tmp, state)
            self.assertEqual(preserved, ["data-file-schema.xml", "paw.txt", "charge-density.dat"])
            stored = state / "density_state" / f"{continuation.PREFIX}.save"
            self.assertTrue((stored / "paw.txt").is_file())
            self.assertFalse((stored / "wfc1.dat").exists())

            restored_tmp = root / "restored"
            copied = continuation.copy_density_state(state, restored_tmp)
            self.assertEqual(copied, preserved)
            restored = restored_tmp / f"{continuation.PREFIX}.save"
            self.assertEqual((restored / "paw.txt").read_text(), "paw-becsum\n")
            self.assertEqual((restored / "charge-density.dat").read_bytes(), b"density")

    def test_missing_paw_state_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            tmp = root / "tmp"
            self.make_save(tmp, include_paw=False)
            with self.assertRaisesRegex(SystemExit, "paw.txt"):
                continuation.preserve_density_state(tmp, root / "state")

    def make_preserved_seed(self, root: Path, protocol: Path) -> Path:
        state = {
            "schema": continuation.LEGACY_STATE_SCHEMA,
            "status": "CONTINUE",
            "cell": 1,
            "total_cells_provisioned": 5,
            "case_id": "L15-V32-K28-extension-audit",
            "layers": 15,
            "vacuum_angstrom": 32.0,
            "kmesh": 28,
            "final_atoms": [{}] * 15,
            "relax_energy_ev": -10.0,
            "max_movable_force_ev_per_angstrom": 0.01,
            "completion_segment": 2,
            "surface_convergence_extension_protocol_sha256": continuation.sha256(protocol),
            "scientific_settings_changed": False,
            "thresholds_changed": False,
            "geometry_changed": False,
            "method_changed": False,
            "rank_changed": False,
            "kinetic_inputs_used": False,
            "warm_started_from_prior_charge_density": False,
            "continuation_semantics": "FROZEN_GEOMETRY_FRESH_START",
            "pw_returncode": 0,
            "wrapper_timeout": False,
        }
        path = root / "SCF_CONTINUATION_STATE.json"
        path.write_text(json.dumps(state))
        return path

    def test_pinned_legacy_seed_recovers_metadata_without_density_reuse(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            protocol = root / "protocol.json"
            protocol.write_text("{}\n")
            self.make_preserved_seed(root, protocol)
            p = {"extension_audit": {"case_id": "L15-V32-K28-extension-audit", "layers": 15, "vacuum_angstrom": 32.0, "kmesh": 28}}
            state = continuation.preserved_relaxation_seed(root, protocol, p)
            self.assertEqual(state["completion_segment"], 2)
            self.assertFalse(state["warm_started_from_prior_charge_density"])

    def test_warm_started_state_cannot_seed_a_new_independent_reproduction(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            protocol = root / "protocol.json"
            protocol.write_text("{}\n")
            path = self.make_preserved_seed(root, protocol)
            state = json.loads(path.read_text())
            state["warm_started_from_prior_charge_density"] = True
            path.write_text(json.dumps(state))
            p = {"extension_audit": {"case_id": "L15-V32-K28-extension-audit", "layers": 15, "vacuum_angstrom": 32.0, "kmesh": 28}}
            with self.assertRaisesRegex(SystemExit, "fresh reproduction start"):
                continuation.preserved_relaxation_seed(root, protocol, p)

    def test_clean_max_seconds_stop_continues(self):
        output = """
 total energy = -3196.0 Ry
 Maximum CPU time exceeded
 Calculation stopped in scf loop
 JOB DONE.
 """
        result = continuation.interpret_pw_output(output, 0, False)
        self.assertEqual(result["status"], "CONTINUE")
        self.assertTrue(result["clean_max_seconds_stop"])
        self.assertFalse(result["scf_converged"])

    def test_converged_scf_completes(self):
        output = """
 convergence has been achieved in 30 iterations
 !    total energy              =   -3196.38783029 Ry
 JOB DONE.
 """
        result = continuation.interpret_pw_output(output, 0, False)
        self.assertEqual(result["status"], "COMPLETE")
        self.assertAlmostEqual(result["final_energy_ry"], -3196.38783029)

    def test_invalid_paw_restart_is_not_counted_as_a_cell(self):
        output = """
 Error in routine read_scf (1):
 Reading PAW becsum
 MPI_ABORT was invoked on rank 0
 """
        with self.assertRaisesRegex(SystemExit, "return code 1"):
            continuation.interpret_pw_output(output, 1, False)

    def test_external_kill_is_not_a_checkpoint(self):
        with self.assertRaisesRegex(SystemExit, "external wrapper timeout"):
            continuation.interpret_pw_output("", -15, True)


if __name__ == "__main__":
    unittest.main()
