#!/usr/bin/env python3
"""Reproduce the capital-Chi rate pilot from Barrier Atlas v0.9 coordinates.

This script intentionally treats native tunneling/recrossing corrections as a control,
not as the definition of capital Chi.
"""
import json, math, statistics, sys
from collections import defaultdict

IDS = [
 'BR-GAS-HT-001-T300.0','BR-GAS-HT-002-T300.0','BR-GAS-HT-003-T200.0',
 'BR-XPH-PT-001-T150.0','BR-XPH-PT-001-T100.0',
 'BR-ENZ-HYD-001-HH-T298.0','BR-ENZ-HYD-001-DH-T298.0',
 'BR-ENZ-HYD-001-HD-T298.0','BR-ENZ-HYD-001-DD-T298.0']

def pearson(a,b):
    ma=sum(a)/len(a); mb=sum(b)/len(b)
    return sum((x-ma)*(y-mb) for x,y in zip(a,b))/math.sqrt(sum((x-ma)**2 for x in a)*sum((y-mb)**2 for y in b))

def F(chi_ref,r):
    return 2*chi_ref + (1+r*r)/(2*chi_ref) - r

def main(path):
    rows=json.load(open(path)); byid={r['coordinate_id']:r for r in rows}
    out=[]
    for cid in IDS:
        r=byid[cid]
        k0=r['classical_tst_rate']; kt=r.get('tunneling_factor') or 1.0; kd=r.get('transmission_coefficient') or 1.0
        kp=r['predicted_rate']; ko=r['observed_rate']
        assert math.isclose(k0*kt*kd,kp,rel_tol=2e-12)
        out.append((r['reaction_family_id'], abs(math.log(k0/ko)), abs(math.log(kp/ko)), math.log(ko/k0), math.log(kt*kd)))
    print('row_MAE_ln_baseline', sum(x[1] for x in out)/len(out))
    print('row_MAE_ln_corrected', sum(x[2] for x in out)/len(out))
    print('row_r_required_vs_native', pearson([x[3] for x in out],[x[4] for x in out]))
    fam=defaultdict(list)
    for x in out: fam[x[0]].append(x)
    fs=[]
    for k,v in fam.items():
        fs.append((k,statistics.median(x[1] for x in v),statistics.median(x[2] for x in v),statistics.median(x[3] for x in v),statistics.median(x[4] for x in v)))
    mb=sum(x[1] for x in fs)/len(fs); mc=sum(x[2] for x in fs)/len(fs)
    print('family_mean_median_abs_ln_baseline',mb,'factor',math.exp(mb))
    print('family_mean_median_abs_ln_corrected',mc,'factor',math.exp(mc))
    print('family_r_required_vs_native', pearson([x[3] for x in fs],[x[4] for x in fs]))
    print('families_improved',sum(x[2]<x[1] for x in fs),'/',len(fs))
    assert abs(F(0.5,0)-2.0)<1e-15
    assert abs(F(1/math.sqrt(3),1/math.sqrt(3))-math.sqrt(3))<1e-12
    print('analytic_checks PASS')

if __name__=='__main__':
    if len(sys.argv)!=2:
        raise SystemExit('usage: verify_capital_chi_rate_pilot.py path/to/coordinates.json')
    main(sys.argv[1])
