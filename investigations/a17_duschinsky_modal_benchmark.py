import numpy as np
from math import factorial
from scipy.special import gammaln, logsumexp

W1=1.0
W2=4.5
FREQ1=400.0
FREQ2=1800.0
LAM_S=3000.0
T=78.0
KB_CM=0.69503476
KT=KB_CM*T
E00=12000.0
ANGLES=[0,5,10,20,30,45,60]

def rotation(theta_deg):
    th=np.deg2rad(theta_deg)
    return np.array([[np.cos(th),np.sin(th)],[-np.sin(th),np.cos(th)]],float)

def modal_coefficients(theta_deg):
    J=rotation(theta_deg)
    A=np.diag([W1,W2])
    M=A + J.T @ A @ J
    invM=np.linalg.inv(M)
    a1=np.sqrt(W1)*J[0]
    a2=np.sqrt(W2)*J[1]
    alpha=2*(a1@invM@a1)-1
    beta=2*(a2@invM@a2)-1
    cross=4*(a1@invM@a2)
    base=2*np.sqrt(W1*W2)/np.sqrt(np.linalg.det(M))
    return alpha,beta,cross,base

def overlap(theta_deg,n1,n2):
    alpha,beta,cross,base=modal_coefficients(theta_deg)
    coeff=0.0
    for k in range(min(n1,n2)+1):
        if (n1-k)%2 or (n2-k)%2:
            continue
        p=(n1-k)//2
        q=(n2-k)//2
        coeff += (alpha**p)/factorial(p) * (beta**q)/factorial(q) * (cross**k)/factorial(k)
    if coeff == 0.0:
        return 0.0
    lognorm=0.5*(gammaln(n1+1)+gammaln(n2+1))-0.5*(n1+n2)*np.log(2.0)
    return base*np.exp(lognorm)*coeff

def overlap_matrix(theta_deg,n1max,n2max):
    out=np.zeros((n1max+1,n2max+1))
    for i in range(n1max+1):
        for j in range(n2max+1):
            out[i,j]=overlap(theta_deg,i,j)
    return out

def rate_proxy(overlaps):
    n1=np.arange(overlaps.shape[0])[:,None]
    n2=np.arange(overlaps.shape[1])[None,:]
    Ef=n1*FREQ1+n2*FREQ2
    fc=overlaps**2
    logsolv=-(-E00+Ef+LAM_S)**2/(4*LAM_S*KT)
    mask=fc>0
    return np.exp(logsumexp(np.log(fc[mask])+logsolv[mask])), fc.sum()

if __name__=="__main__":
    trunc=(80,40)
    rates=[]
    for angle in ANGLES:
        ov=overlap_matrix(angle,*trunc)
        rate,psum=rate_proxy(ov)
        rates.append(rate)
        print(angle, rotation(angle).tolist(), psum, rate)
    print("log10 ratios:", [np.log10(r/rates[0]) for r in rates])
