#!/usr/bin/env python3
"""Rate-relevant relaxation projection for a harmonic GLE with exponential memory modes.

Dimensionless units use omega0=1. Each memory component is (chi_i, r_i), where
chi_i = gamma_i/(2 m omega0), r_i=tau_i*omega0.
The total integrated-friction reference ratio is sum chi_i.
"""
import numpy as np
from scipy.signal import tf2ss
from scipy.linalg import solve_continuous_lyapunov

def pmul(a,b): return np.polynomial.polynomial.polymul(a,b)
def padd(a,b):
    n=max(len(a),len(b)); c=np.zeros(n); c[:len(a)]+=a; c[:len(b)]+=b; return c

def rate_projection(components):
    Q=np.array([1.0])
    for chi,r in components:
        Q=pmul(Q,np.array([1.0,r]))
    G=np.zeros(len(Q)-1 if len(Q)>1 else 1)
    for i,(chi,r) in enumerate(components):
        q=np.array([1.0])
        for j,(chj,rj) in enumerate(components):
            if j!=i:
                q=pmul(q,np.array([1.0,rj]))
        G=padd(G,2*chi*q)
    num=padd(np.r_[0.0,Q],G)
    den=padd(pmul(Q,np.array([1.0,0.0,1.0])),np.r_[0.0,G])
    def trim(p):
        while len(p)>1 and abs(p[-1])<1e-14:
            p=p[:-1]
        return p
    num=trim(num); den=trim(den)
    A,B,C,D=tf2ss(num[::-1],den[::-1])
    if abs(float(np.asarray(D).squeeze()))>1e-12:
        raise ValueError("expected strictly proper transfer")
    eig=np.linalg.eigvals(A)
    if np.max(np.real(eig))>=-1e-12:
        raise ValueError(f"unstable/marginal realization: {eig}")
    P=solve_continuous_lyapunov(A,-B@B.T)
    h2=float((C@P@C.T)[0,0])
    return 2*h2

if __name__=="__main__":
    examples={
      "single_fast":[(1.0,0.1)],
      "single_mid":[(1.0,1.0)],
      "single_slow":[(1.0,10.0)],
      "two_fast":[(0.5,0.1),(0.5,0.2)],
      "split_fast_slow":[(0.5,0.1),(0.5,10.0)],
      "two_slow":[(0.5,5.0),(0.5,10.0)],
    }
    for name,comp in examples.items():
        F=rate_projection(comp)
        print(name,"chi_total=",sum(c for c,r in comp),"F=",F,"rate_prefactor_rel=",1/F)
