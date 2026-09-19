#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, math, pathlib, re, statistics

ITER_RE = re.compile(r"iteration\s+#\s*(\d+)", re.I)
ACC_RE = re.compile(r"estimated scf accuracy\s*<\s*([-+0-9.Ee]+)\s*Ry", re.I)
ETOT_RE = re.compile(r"^\s*total energy\s+=\s*([-+0-9.Ee]+)\s*Ry", re.M)
BANG_RE = re.compile(r"!\s+total energy\s+=\s*([-+0-9.Ee]+)\s*Ry")
RY_TO_EV = 13.605693122994

def classify(values):
    vals=[v for v in values if v is not None and v>0 and math.isfinite(v)]
    if len(vals)<4:
        return "INSUFFICIENT_HISTORY"
    logs=[math.log10(v) for v in vals]
    x=list(range(len(logs)))
    xm=statistics.mean(x); ym=statistics.mean(logs)
    den=sum((i-xm)**2 for i in x) or 1.0
    slope=sum((i-xm)*(y-ym) for i,y in zip(x,logs))/den
    diffs=[logs[i]-logs[i-1] for i in range(1,len(logs))]
    flips=sum(1 for i in range(1,len(diffs)) if diffs[i]*diffs[i-1] < 0)
    span=max(logs)-min(logs)
    if slope < -0.02:
        return "DECAYING"
    if flips >= max(2, len(diffs)//3):
        return "OSCILLATORY"
    if span < 0.5:
        return "PLATEAU"
    return "NONMONOTONIC_OR_SLOW"

def parse_file(path):
    txt=path.read_text(encoding="utf-8", errors="replace")
    iterations=[int(x) for x in ITER_RE.findall(txt)]
    acc=[float(x) for x in ACC_RE.findall(txt)]
    iter_energy=[float(x)*RY_TO_EV for x in ETOT_RE.findall(txt)]
    final_energy=[float(x)*RY_TO_EV for x in BANG_RE.findall(txt)]
    return {
        "file": str(path),
        "bytes": path.stat().st_size,
        "iteration_count_markers": len(iterations),
        "max_reported_iteration": max(iterations) if iterations else None,
        "accuracy_samples_ry": acc,
        "accuracy_first_ry": acc[0] if acc else None,
        "accuracy_last_ry": acc[-1] if acc else None,
        "accuracy_min_ry": min(acc) if acc else None,
        "accuracy_class": classify(acc),
        "iter_energy_samples_ev": iter_energy,
        "last_iter_energy_ev": iter_energy[-1] if iter_energy else None,
        "final_bang_energy_ev": final_energy[-1] if final_energy else None,
        "job_done": "JOB DONE." in txt,
        "converged": "convergence has been achieved" in txt.lower(),
        "not_converged": "convergence not achieved" in txt.lower(),
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", required=True)
    args=ap.parse_args()
    root=pathlib.Path(args.root).expanduser().resolve()
    out=pathlib.Path(args.out).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    patterns=["H_atom_70*.out","H_atom_80*.out","*atom*70*.out","*atom*80*.out"]
    files=[]
    for pat in patterns:
        files.extend(root.rglob(pat))
    files=sorted(set(p for p in files if p.is_file()))
    records=[parse_file(p) for p in files]

    for r in records:
        # keep JSON compact: full accuracy/energy traces go to CSV only
        r["accuracy_sample_count"]=len(r.pop("accuracy_samples_ry"))
        r["iter_energy_sample_count"]=len(r.pop("iter_energy_samples_ev"))

    summary={
        "schema":"symc-powercell-shared-h-scf-postmortem-v0.1",
        "root":str(root),
        "files_found":len(records),
        "scientific_settings_changed":False,
        "thresholds_changed":False,
        "compute_type":"read_only_log_diagnostic",
        "records":records,
    }
    (out/"SCF_POSTMORTEM_SUMMARY.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")

    with (out/"SCF_POSTMORTEM_FILES.csv").open("w",newline="",encoding="utf-8") as f:
        cols=["file","bytes","iteration_count_markers","max_reported_iteration","accuracy_sample_count",
              "accuracy_first_ry","accuracy_last_ry","accuracy_min_ry","accuracy_class",
              "iter_energy_sample_count","last_iter_energy_ev","final_bang_energy_ev",
              "job_done","converged","not_converged"]
        w=csv.DictWriter(f,fieldnames=cols); w.writeheader()
        for r in records: w.writerow({k:r.get(k) for k in cols})

    print(json.dumps({
        "files_found":len(records),
        "classes":{r["file"]:r["accuracy_class"] for r in records},
        "out":str(out),
    },indent=2))

if __name__=="__main__":
    main()
