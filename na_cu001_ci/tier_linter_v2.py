#!/usr/bin/env python3
"""Reject overbroad computational labels and unlabeled generated rate claims."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path

FORBIDDEN="COMPUTATIONAL_FULL"
REQUIRED={"barrier_tier","saddle_tier","prefactor_tier","rate_tier","experimental_tier"}
RATE_RE=re.compile(r"\b(computed rate|attempt frequency|model rate)\b",re.I)
QUAL_RE=re.compile(r"\b(rate_tier|prefactor_tier|harmonic model|active-region|partial-hessian|tier)\b",re.I)

def walk(v):
    if isinstance(v,dict):
        for k,x in v.items():yield from walk(x)
    elif isinstance(v,list):
        for x in v:yield from walk(x)
    elif isinstance(v,str):yield v

def main():
    p=argparse.ArgumentParser();p.add_argument("paths",nargs="+");a=p.parse_args();errors=[]
    for raw in a.paths:
        path=Path(raw)
        files=[path] if path.is_file() else [x for x in path.rglob("*") if x.is_file() and x.suffix.lower() in {".json",".md",".tex",".txt"}]
        for f in files:
            text=f.read_text(errors="replace")
            if FORBIDDEN in text:errors.append(f"{f}: forbidden label {FORBIDDEN}")
            if f.suffix.lower()==".json":
                try:data=json.loads(text)
                except Exception:continue
                if data.get("schema") in {"na-cu001-barrier-coordinate-v0.2","na-cu001-atlas-admission-v0.2"}:
                    tiers=data.get("tiers") or (data.get("mechanism_record") or {}).get("tiers")
                    if not isinstance(tiers,dict) or not REQUIRED.issubset(tiers):errors.append(f"{f}: missing required tier fields")
            else:
                for n,line in enumerate(text.splitlines(),1):
                    if RATE_RE.search(line) and not QUAL_RE.search(line):errors.append(f"{f}:{n}: rate/prefactor statement lacks qualification")
    if errors:
        print("\n".join(errors));raise SystemExit(2)
    print("tier lint PASS")
if __name__=="__main__":main()
