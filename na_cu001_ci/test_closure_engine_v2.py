#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from pathlib import Path
import tempfile
import unittest

import numpy as np

import closure_engine as legacy
import closure_engine_v2 as ce

PROTOCOL = Path(__file__).with_name("method_protocol_v0.2.json")


class CorrectedRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.protocol = ce.load_protocol(PROTOCOL)

    def test_one_sided_mobility_is_not_xy_rigid(self) -> None:
        cell, primitive = legacy.primitive_clean_geometry(3.60, 9, 16.0)
        supercell, atoms = legacy.replicate_surface(cell, primitive, 4)
        mobile = ce.apply_one_sided_mobility(atoms, "primary", self.protocol)
        layers = ce.unique_cu_layers(mobile)
        top = list(reversed(layers))
        for atom in mobile:
            z = atom["position_angstrom"][2]
            if any(abs(z-v) < 1e-4 for v in top[:3]):
                self.assertEqual(atom["flags"], [1,1,1])
            elif abs(z-top[3]) < 1e-4:
                self.assertEqual(atom["flags"], [0,0,1])
            else:
                self.assertEqual(atom["flags"], [0,0,0])

    def test_periodic_3d_distance_detects_desorption(self) -> None:
        cell = [[10.0,0,0],[0,10.0,0],[0,0,20.0]]
        a = [2.0,3.0,5.0]
        b = [2.0,3.0,11.0]
        self.assertAlmostEqual(np.linalg.norm(ce.periodic_delta(a,b,cell,include_z=False)), 0.0)
        self.assertAlmostEqual(ce.periodic_3d_distance(a,b,cell), 6.0)

    def test_basin_gate_rejects_same_xy_wrong_z(self) -> None:
        cell = [[10.0,0,0],[0,10.0,0],[0,0,20.0]]
        endpoint = [
            {"symbol":"Cu","position_angstrom":[2,3,2],"flags":[0,0,0]},
            {"symbol":"Na","position_angstrom":[2,3,4],"flags":[1,1,1]},
        ]
        desorbed = json.loads(json.dumps(endpoint))
        desorbed[1]["position_angstrom"][2] = 10.0
        metrics = ce.basin_metrics(desorbed, endpoint, [0,1], cell, -1.0, -1.0, self.protocol)
        self.assertFalse(metrics["pass"])
        self.assertFalse(metrics["checks"]["na_periodic_3d_distance"])
        self.assertFalse(metrics["checks"]["adsorption_height"])

    def test_active_region_rmsd_includes_cu(self) -> None:
        cell = [[10.0,0,0],[0,10.0,0],[0,0,20.0]]
        a = [
            {"symbol":"Cu","position_angstrom":[1,1,2],"flags":[1,1,1]},
            {"symbol":"Na","position_angstrom":[2,2,4],"flags":[1,1,1]},
        ]
        b = json.loads(json.dumps(a)); b[0]["position_angstrom"][0] += 1.0
        self.assertGreater(ce.active_rmsd(a,b,[0,1],cell), 0.6)

    def test_mass_weighted_modes_and_prefactor(self) -> None:
        atoms = [{"symbol":"Na","position_angstrom":[0,0,0],"flags":[0,0,0]}]
        hmin = np.diag([1.0,2.0,3.0])
        hsad = np.diag([-0.5,1.5,2.5])
        m = ce.mass_weighted_modes(hmin, atoms, [0], 1e20)
        s = ce.mass_weighted_modes(hsad, atoms, [0], 1e20)
        self.assertEqual(m["negative_count"], 0)
        self.assertEqual(s["negative_count"], 1)
        pref = ce.vineyard_prefactor(m,s,1e20)
        self.assertIsNotNone(pref)
        self.assertGreater(pref,0)

    def test_barrier_output_has_tiers_and_nested_curve(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            ci=root/'ci.json'; saddle=root/'sad.json'; sens=root/'sens.json'; mob=root/'mob.json'; out=root/'out.json'
            ci.write_text(json.dumps({"schema":"na-cu001-ci-neb-handoff-v0.2","status":"PASS","forward_barrier_ev":0.05,"reverse_barrier_ev":0.05}))
            saddle.write_text(json.dumps({"schema":"na-cu001-saddle-handoff-v0.2","status":"PASS","hessian":{"selected_prefactor_hz":5e11,"cancellation_test":{},"pass_checks":{}}}))
            sens.write_text(json.dumps({"schema":"na-cu001-barrier-sensitivity-v0.2","status":"PASS","barrier_numerical_sensitivity_envelope_ev":0.003}))
            mob.write_text(json.dumps({"schema":"na-cu001-mobility-convergence-v0.2","status":"PASS"}))
            ce.command_barrier(type('A',(),{"ci":str(ci),"saddle":str(saddle),"sensitivity":str(sens),"mobility_gate":str(mob),"out":str(out)})())
            data=json.loads(out.read_text())
            self.assertNotIn("COMPUTATIONAL_FULL", json.dumps(data))
            self.assertFalse(data["computed_rate_curve"]["eligible_as_independent_rows"])
            self.assertEqual(len(data["computed_rate_curve"]["points"]),5)
            self.assertIn("rate_tier",data["tiers"])

    def test_unexpected_adsorption_minimum_requires_new_mechanism(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            records=[]
            for model in ("primary","expanded"):
                for site in ("hollow","bridge","top"):
                    for h in (2.0,2.5,3.0):
                        final="bridge" if site=="bridge" else site
                        e=-10.0 if site=="bridge" else -9.0
                        rec={"schema":"na-cu001-adsorption-case-v0.2","status":"PASS","mobility_model":model,"start_site":site,"initial_height_angstrom":h,
                             "final_site_classification":{"site":final},"final_energy_ev":e}
                        d=root/f'{model}_{site}_{h}';d.mkdir();(d/'run_record.json').write_text(json.dumps(rec))
            out=root/'ads.json'
            clean=root/'clean.json';na=root/'na.json';parity=root/'parity.json'
            clean.write_text('{}');na.write_text('{}');parity.write_text('{}')
            with self.assertRaises(SystemExit):
                ce.command_adsorption_analyze(type('A',(),{"protocol":str(PROTOCOL),"records":str(root),"clean_handoff":str(clean),"na_handoff":str(na),"parity_handoff":str(parity),"out":str(out)})())
            data=json.loads(out.read_text())
            self.assertEqual(data["status"],"HOLD")
            self.assertEqual(data["mobility_analyses"]["primary"]["mechanism_state"],"MECHANISM_REVISION_REQUIRED")


    def test_rumpled_surface_layers_still_define_active_regions(self) -> None:
        cell, primitive = legacy.primitive_clean_geometry(3.60, 9, 16.0)
        supercell, atoms = legacy.replicate_surface(cell, primitive, 4)
        top = max(a["position_angstrom"][2] for a in atoms if a["symbol"] == "Cu")
        top_atoms = [a for a in atoms if a["symbol"] == "Cu" and abs(a["position_angstrom"][2]-top) < 1e-4]
        for i, atom in enumerate(top_atoms):
            atom["position_angstrom"][2] += 0.12 * ((i % 3) - 1)
        na_pos = legacy.frac_to_cart([0.375,0.375,0.0], supercell).tolist();na_pos[2]=top+2.2
        atoms.append({"symbol":"Na","position_angstrom":na_pos,"flags":[1,1,1]})
        regions = ce.active_indices_by_region(atoms, supercell)
        self.assertEqual(len(regions["na_only"]),1)
        self.assertEqual(len(regions["na_plus_4cu"]),5)
        self.assertEqual(len(regions["na_plus_8cu"]),9)

    def test_basin_gate_rejects_energy_mismatch(self) -> None:
        cell = [[10.0,0,0],[0,10.0,0],[0,0,20.0]]
        endpoint = [{"symbol":"Cu","position_angstrom":[2,3,2],"flags":[0,0,0]},
                    {"symbol":"Na","position_angstrom":[2,3,4],"flags":[1,1,1]}]
        metrics = ce.basin_metrics(endpoint, endpoint, [0,1], cell, -0.90, -1.0, self.protocol)
        self.assertFalse(metrics["pass"])
        self.assertFalse(metrics["checks"]["energy"])

if __name__ == '__main__':
    unittest.main(verbosity=2)
