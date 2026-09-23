"""HCN/HNC -> validated TS modal correspondence.

Uses exact Rowan R0/R2 geometries and mode displacement vectors.
Cross-configuration comparison is explicit:
1. atom mapping is H,C,N;
2. endpoints are mass-centred and optimally rigidly aligned to the TS by a
   mass-weighted proper Kabsch rotation;
3. modal overlaps use the atomic-mass Cartesian metric;
4. the exactly degenerate linear bend pair is reported as a 2D subspace.

No rate or kinetic target enters the correspondence.
"""
import numpy as np

MASS=np.array([1.00784,12.011,14.007])
HARTREE_TO_KCAL=627.509474

HCN_G=np.array([[0,0,-1.06148369],[0,0,0.00275523],[0,0,1.14672846]],float)
HNC_G=np.array([[0,0,-0.99599224],[0,0,1.16415287],[0,0,0.00183939]],float)
TS_G=np.array([[0.18728331,0.29380770,-0.67838864],
               [-0.35679594,-0.55981544,0.05647563],
               [0.16951971,0.26598555,0.70991904]],float)

HCN_MODES=[
 np.array([[-0.802016,-0.571772,0],[0.130020,0.092694,0],[-0.053699,-0.038283,0]]),
 np.array([[0.571772,-0.802016,0],[-0.092694,0.130020,0],[0.038283,-0.053699,0]]),
 np.array([[0,0,-0.819719],[0,0,-0.404434],[0,0,0.405578]]),
 np.array([[0,0,0.991362],[0,0,-0.125947],[0,0,0.036581]])]
HNC_MODES=[
 np.array([[-0.150256,-0.977167,0],[-0.010834,-0.070454,0],[0.020098,0.130704,0]]),
 np.array([[0.977167,-0.150256,0],[0.070454,-0.010834,0],[-0.130704,0.020098,0]]),
 np.array([[0,0,0.729862],[0,0,-0.544142],[0,0,0.413776]]),
 np.array([[0,0,0.995071],[0,0,0.027576],[0,0,-0.095249]])]
TS_MODES=[
 np.array([[-0.431971,-0.677774,-0.582133],[0.047106,0.073906,-0.038864],[-0.009278,-0.014554,0.075201]]),
 np.array([[0.051813,0.081279,-0.431777],[-0.304329,-0.477498,-0.367583],[0.257067,0.403345,0.346077]]),
 np.array([[0.305698,0.479604,-0.819500],[-0.004022,-0.006309,0.060406],[-0.018555,-0.029112,0.007216]])]

def center(x):
    return (x*MASS[:,None]).sum(axis=0)/MASS.sum()

def align(endpoint,target):
    a=endpoint-center(endpoint); b=target-center(target)
    H=(a*MASS[:,None]).T@b
    U,_,Vt=np.linalg.svd(H)
    R=U@Vt
    if np.linalg.det(R)<0:
        U[:,-1]*=-1
        R=U@Vt
    rms=np.sqrt((((a@R-b)**2)*MASS[:,None]).sum()/MASS.sum())
    return R,rms

def mnorm(v):
    return np.sqrt((v*v*MASS[:,None]).sum())

def overlap(a,b):
    return float((a*b*MASS[:,None]).sum()/(mnorm(a)*mnorm(b)))

def subspace_weight(vectors,target):
    X=np.column_stack([(v*np.sqrt(MASS[:,None])).ravel() for v in vectors])
    Q,_=np.linalg.qr(X)
    y=(target*np.sqrt(MASS[:,None])).ravel()
    y/=np.linalg.norm(y)
    return float(np.sum((Q.T@y)**2))

def analyse(name,geom,modes,groups):
    R,rms=align(geom,TS_G)
    rm=[v@R for v in modes]
    O=np.array([[overlap(v,t) for t in TS_MODES] for v in rm])
    W={label:[subspace_weight([rm[i] for i in inds],t) for t in TS_MODES]
       for label,inds in groups.items()}
    return R,rms,O,W

if __name__=="__main__":
    for args in [
      ("HCN",HCN_G,HCN_MODES,{"bend":[0,1],"CN_stretch":[2],"CH_stretch":[3]}),
      ("HNC",HNC_G,HNC_MODES,{"bend":[0,1],"CN_stretch":[2],"NH_stretch":[3]})]:
        name,RMSgeom,O,W = args[0], *analyse(*args)
        print(name,"alignment_mass_RMS_A",RMSgeom)
        print("signed normalized overlap matrix rows endpoint modes, cols TS [unstable,stable1,stable2]")
        print(O)
        print("basis-invariant endpoint carrier/subspace weights onto TS modes")
        print(W)
    print("barrier_from_HCN_kcalmol",(-93.410584+93.493238)*HARTREE_TO_KCAL)
    print("barrier_from_HNC_kcalmol",(-93.410584+93.471647)*HARTREE_TO_KCAL)
