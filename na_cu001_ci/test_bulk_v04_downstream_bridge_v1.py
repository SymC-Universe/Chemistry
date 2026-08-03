#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "bulk_v04_downstream_bridge_v1.py"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summary(root: Path, e: int, k: int, a0: float, e0: float) -> dict:
    records = []
    for i, a in enumerate([3.55, 3.58, 3.61, 3.64, 3.67, 3.70]):
        records.append({
            "a_angstrom": a,
            "returncode": 0,
            "job_done": True,
            "scf_converged": True,
            "final_energy_ev_per_atom": e0 + (a-a0)**2,
            "input_sha256": "a"*64,
            "output_sha256": "b"*64,
        })
    data = {"ecutwfc_ry": e, "ecutrho_ry": 3*e, "kmesh": k, "records": records}
    path = root / f"summary_e{e}_k{k}.json"
    path.write_text(json.dumps(data, indent=2)+"\n")
    return {"ecutwfc_ry": e, "ecutrho_ry": 3*e, "kmesh": k,
            "fit": {"a0_angstrom": a0, "e0_ev_per_atom": e0, "rms_residual_mev_per_atom": 0.0},
            "source_summary": f"bulk_summaries/{path.name}", "source_sha256": sha(path)}


def fixture(root: Path):
    summaries = root / "summaries"; summaries.mkdir()
    hist_e=[50,55,60,65,70]; hist_k=[8,10,12,14]
    ext_e=[80,90,100,110,120,130]; ext_k=[14,16,18,20]
    ref=(140,22); audit=(150,24)
    protocol={
      "schema":"na-cu001-bulk-extension-protocol-v0.1",
      "status":"FROZEN_AFTER_V0.3_HOLD_BEFORE_EXTENSION_RESULTS",
      "reused_historical_candidates":{"ecuts_ry":hist_e,"kmeshes":hist_k,"expected_count":20},
      "extension_candidates":{"ecuts_ry":ext_e,"kmeshes":ext_k,"expected_count":24},
      "reference":{"ecutwfc_ry":ref[0],"kmesh":ref[1]},
      "independent_reference_audit":{"ecutwfc_ry":audit[0],"kmesh":audit[1]},
      "joint_gate":{"delta_a_max_angstrom":0.005,"delta_e_max_ev_per_atom":0.001},
    }
    pp=root/"protocol.json"; pp.write_text(json.dumps(protocol)+"\n")
    reference=summary(summaries,*ref,3.6000,-100.0000)
    audit_row=summary(summaries,*audit,3.6002,-100.0002)
    candidates=[]
    for e in hist_e:
      for k in hist_k:
        row=summary(summaries,e,k,3.6000,-99.9900)
        row["candidate_origin"]="historical_v0.3"; candidates.append(row)
    for e in ext_e:
      for k in ext_k:
        de=0.0008 if (e,k)==(80,14) else 0.0005 if e>=90 else 0.002
        row=summary(summaries,e,k,3.6001,-100.0000+de)
        row["candidate_origin"]="post_hold_extension_v0.4"; candidates.append(row)
    for r in candidates:
      da=abs(r["fit"]["a0_angstrom"]-reference["fit"]["a0_angstrom"])
      de=abs(r["fit"]["e0_ev_per_atom"]-reference["fit"]["e0_ev_per_atom"])
      r["estimated_cost_score"]=r["ecutwfc_ry"]**1.5*r["kmesh"]**3
      r["joint_gate_against_audited_reference"]={"delta_a_angstrom":da,"delta_e_ev_per_atom":de,"delta_a_pass":da<=.005,"delta_e_pass":de<=.001,"pass":da<=.005 and de<=.001}
    selected=min([r for r in candidates if r["joint_gate_against_audited_reference"]["pass"]], key=lambda r:(r["estimated_cost_score"],r["ecutwfc_ry"],r["kmesh"]))
    result={"schema":"na-cu001-bulk-selection-v0.4","gate":"PASS","status":"PASS",
      "protocol":{"sha256":sha(pp)},"reference":reference,"independent_reference_audit":audit_row,
      "reference_audit_gate":{"delta_a_angstrom":.0002,"delta_e_ev_per_atom":.0002,"delta_a_pass":True,"delta_e_pass":True,"pass":True},
      "candidates":candidates,"recommended_smallest_cost_candidate":selected}
    rp=root/"result.json"; rp.write_text(json.dumps(result,indent=2)+"\n")
    hs={"ecutwfc_ry":selected["ecutwfc_ry"],"ecutrho_ry":selected["ecutrho_ry"],"kmesh_cubic":[selected["kmesh"]]*3,
        "equilibrium_lattice_constant_angstrom":selected["fit"]["a0_angstrom"],"equilibrium_energy_ev_per_atom":selected["fit"]["e0_ev_per_atom"]}
    handoff={"schema":"na-cu001-bulk-to-slab-handoff-v0.4","scientific_status":"bulk_convergence_passed_slab_not_yet_run",
      "source_result":{"sha256":sha(rp)},"protocol":{"sha256":sha(pp)},"selected_bulk_settings":hs}
    hp=root/"handoff.json"; hp.write_text(json.dumps(handoff,indent=2)+"\n")
    return pp,rp,hp,summaries


def run(pp,rp,hp,summaries):
    return subprocess.run(["python3",str(SCRIPT),"--result",str(rp),"--handoff",str(hp),"--protocol",str(pp),"--summaries",str(summaries),"--out",str(rp.parent/"bridge.json")],capture_output=True,text=True)


def refresh_handoff(hp: Path, rp: Path, pp: Path):
    h=json.loads(hp.read_text()); h["source_result"]["sha256"]=sha(rp); h["protocol"]["sha256"]=sha(pp); hp.write_text(json.dumps(h)+"\n")


def test_pass():
  with tempfile.TemporaryDirectory() as d:
    pp,rp,hp,s=fixture(Path(d)); p=run(pp,rp,hp,s); assert p.returncode==0,p.stderr; assert json.loads((Path(d)/"bridge.json").read_text())["verified_eos_count"]==46

def test_reject_failed_audit():
  with tempfile.TemporaryDirectory() as d:
    pp,rp,hp,s=fixture(Path(d)); r=json.loads(rp.read_text()); r["reference_audit_gate"]["pass"]=False; rp.write_text(json.dumps(r)+"\n"); refresh_handoff(hp,rp,pp); assert run(pp,rp,hp,s).returncode!=0

def test_reject_nonminimal_selection():
  with tempfile.TemporaryDirectory() as d:
    pp,rp,hp,s=fixture(Path(d)); r=json.loads(rp.read_text()); passing=[x for x in r["candidates"] if x["joint_gate_against_audited_reference"]["pass"]]; passing.sort(key=lambda x:x["estimated_cost_score"]); r["recommended_smallest_cost_candidate"]=passing[-1]; rp.write_text(json.dumps(r)+"\n"); refresh_handoff(hp,rp,pp); h=json.loads(hp.read_text()); x=passing[-1]; h["selected_bulk_settings"].update({"ecutwfc_ry":x["ecutwfc_ry"],"ecutrho_ry":x["ecutrho_ry"],"kmesh_cubic":[x["kmesh"]]*3,"equilibrium_lattice_constant_angstrom":x["fit"]["a0_angstrom"],"equilibrium_energy_ev_per_atom":x["fit"]["e0_ev_per_atom"]}); hp.write_text(json.dumps(h)+"\n"); assert run(pp,rp,hp,s).returncode!=0

def test_reject_corrupt_summary():
  with tempfile.TemporaryDirectory() as d:
    pp,rp,hp,s=fixture(Path(d)); next(s.glob("summary_e*_k*.json")).write_text("{}\n"); assert run(pp,rp,hp,s).returncode!=0

def test_reject_handoff_hash_mismatch():
  with tempfile.TemporaryDirectory() as d:
    pp,rp,hp,s=fixture(Path(d)); r=json.loads(rp.read_text()); r["extra"]="changed"; rp.write_text(json.dumps(r)+"\n"); assert run(pp,rp,hp,s).returncode!=0

if __name__=="__main__":
  tests=[test_pass,test_reject_failed_audit,test_reject_nonminimal_selection,test_reject_corrupt_summary,test_reject_handoff_hash_mismatch]
  for t in tests: t(); print(f"PASS {t.__name__}")
  print(f"PASS {len(tests)} bulk v0.4 downstream bridge tests")
