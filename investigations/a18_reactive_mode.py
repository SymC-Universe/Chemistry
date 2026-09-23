import numpy as np, csv

omega_b=1.0
omega=np.array([0.5,3.0])
phis=np.array([0,15,30,45,60,75,90],float)

rows=[]
for phi in phis:
    p=np.deg2rad(phi)
    g=np.array([np.cos(p),np.sin(p)])
    c=omega*g
    S=np.sum(c**2/omega**2)

    K=np.array([
        [-omega_b**2+S, -c[0], -c[1]],
        [-c[0], omega[0]**2, 0.0],
        [-c[1], 0.0, omega[1]**2]
    ])

    vals,vecs=np.linalg.eigh(K)
    idx=np.argmin(vals)
    lam=np.sqrt(-vals[idx])
    v=vecs[:,idx]
    if v[0] < 0:
        v=-v

    Pq=v[0]**2
    kappa=lam/omega_b
    rows.append([phi,S,*c,*vals,*v,Pq,kappa])

with open("a18_reactive_mode_results.csv","w",newline="") as f:
    w=csv.writer(f)
    w.writerow(["phi_deg","S_scalar","c1","c2","eig1","eig2","eig3",
                "v_q","v_x1","v_x2","P_q","kappa_GH"])
    w.writerows(rows)
