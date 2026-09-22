import math
import json
import numpy as np

KB = 1.380649e-23
AMU = 1.66053906660e-27
J_PER_MEV = 1.602176634e-22
HBAR_MEV_PS = 0.6582119569
T = 300.0
M = (5*12.011 + 5*1.008) * AMU
ETA_PS = 2.6
ETA = ETA_PS * 1e12
E_MODE_MEV = 4.6
OMEGA0_PS = E_MODE_MEV / HBAR_MEV_PS
OMEGA0 = OMEGA0_PS * 1e12
K_LOCAL = M * OMEGA0**2
A0 = 3.615e-10
L = A0 / math.sqrt(6.0)
Q = 2*math.pi/L
KBT = KB*T
VTH = math.sqrt(KBT/M)
CHI = ETA_PS/(2*OMEGA0_PS)

BARRIERS = (40.0, 55.0)

def coeffs(barrier_mev):
    A_mev = barrier_mev/2.0
    A_j = A_mev*J_PER_MEV
    B_j = (K_LOCAL/Q**2 - A_j)/4.0
    return A_mev, B_j/J_PER_MEV

COEFFS = {b: coeffs(b) for b in BARRIERS}

def potential(x, barrier_mev):
    A_mev, B_mev = COEFFS[barrier_mev]
    return (A_mev*(1-np.cos(Q*x)) + B_mev*(1-np.cos(2*Q*x))) * J_PER_MEV

def force(x, barrier_mev):
    A_mev, B_mev = COEFFS[barrier_mev]
    A = A_mev*J_PER_MEV
    B = B_mev*J_PER_MEV
    return -Q*(A*np.sin(Q*x) + 2*B*np.sin(2*Q*x))

def force_harmonic(x):
    return -K_LOCAL*x

def baoab(x, v, dt, nsteps, force_fn, rng, noise=True, record_stride=1):
    c = math.exp(-ETA*dt)
    sigma = math.sqrt((1-c*c)*KBT/M) if noise else 0.0
    ts=[]; xs=[]; vs=[]
    for i in range(nsteps+1):
        if i % record_stride == 0:
            ts.append(i*dt)
            xs.append(x.copy())
            vs.append(v.copy())
        if i == nsteps:
            break
        f = force_fn(x)
        v = v + 0.5*dt*f/M
        x = x + 0.5*dt*v
        v = c*v + sigma*rng.standard_normal(v.shape)
        x = x + 0.5*dt*v
        f = force_fn(x)
        v = v + 0.5*dt*f/M
    return np.array(ts), np.array(xs), np.array(vs)

def analytic_harmonic(t_s, x0, v0=0.0):
    g=ETA
    wd=math.sqrt(OMEGA0**2-(g/2)**2)
    return np.exp(-g*t_s/2)*(x0*np.cos(wd*t_s) + ((v0+g*x0/2)/wd)*np.sin(wd*t_s))

def sample_conditional_well(n, barrier_mev, rng):
    grid=np.linspace(-L/2, L/2, 20001)
    w=np.exp(-(potential(grid,barrier_mev)-np.min(potential(grid,barrier_mev)))/KBT)
    cdf=np.cumsum((w[:-1]+w[1:])*0.5*np.diff(grid))
    cdf=np.concatenate([[0.0],cdf]); cdf/=cdf[-1]
    u=rng.random(n)
    x=np.interp(u,cdf,grid)
    v=rng.normal(0,VTH,size=n)
    return x,v

def rms(a):
    return math.sqrt(float(np.mean(np.asarray(a)**2)))

def harmonic_gate(dt_ps):
    dt=dt_ps*1e-12; nsteps=round(2e-12/dt)
    x0=0.05*L
    rng=np.random.default_rng(1001)
    t,xs,_=baoab(np.array([x0]),np.array([0.0]),dt,nsteps,force_harmonic,rng,noise=False)
    ana=analytic_harmonic(t,x0)
    nrms=rms((xs[:,0]-ana)/x0)
    return nrms

def equipartition_gate(dt_ps, n=20000, total_ps=5.0):
    dt=dt_ps*1e-12; nsteps=round(total_ps/dt_ps)
    rng=np.random.default_rng(1002)
    x=np.zeros(n); v=np.zeros(n)
    _,_,vs=baoab(x,v,dt,nsteps,lambda z:np.zeros_like(z),rng,noise=True,record_stride=max(1,nsteps//20))
    vv=vs[-5:,:,:] if vs.ndim==3 else vs[-5:]
    ratio=M*np.mean(vv**2)/KBT
    return float(ratio)

def free_diffusion_gate(dt_ps, n=12000, total_ps=5.0):
    dt=dt_ps*1e-12; nsteps=round(total_ps/dt_ps)
    rng=np.random.default_rng(1003)
    x=np.zeros(n); v=rng.normal(0,VTH,size=n)
    t,xs,_=baoab(x,v,dt,nsteps,lambda z:np.zeros_like(z),rng,noise=True,record_stride=nsteps)
    msd=float(np.mean((xs[-1]-xs[0])**2))
    tf=total_ps*1e-12
    denom=2*(tf-(1-math.exp(-ETA*tf))/ETA)
    D=msd/denom
    D_exact=KBT/(M*ETA)
    return float(D),float(D_exact),float(D/D_exact)

def potential_gate(barrier):
    v0=float(potential(np.array([0.0]),barrier)[0])
    vb=float(potential(np.array([L/2]),barrier)[0])
    barrier_num=(vb-v0)/J_PER_MEV
    A_mev,B_mev=COEFFS[barrier]
    curv=Q**2*((A_mev+4*B_mev)*J_PER_MEV)
    return barrier_num,float(curv),float(curv/K_LOCAL)

def response_curve(barrier, amp_frac, sign, dt_ps=0.001, n=12000, total_ps=0.5, seed=1100):
    dt=dt_ps*1e-12; nsteps=round(total_ps/dt_ps); rng=np.random.default_rng(seed)
    x,v=sample_conditional_well(n,barrier,rng)
    delta=sign*amp_frac*L
    x=x+delta
    t,xs,_=baoab(x,v,dt,nsteps,lambda z:force(z,barrier),rng,noise=True,record_stride=1)
    local=xs - np.round(xs/L)*L
    mean=np.mean(local,axis=1)
    return t,mean/delta

def linearity_gate(barrier, sign):
    paired_seed=1200+int(barrier)+10*(sign>0)
    t,r1=response_curve(barrier,0.025,sign,seed=paired_seed)
    _,r2=response_curve(barrier,0.05,sign,seed=paired_seed)
    diff=rms(r1-r2)
    return diff

def run_preflight():
    out={
      'constants':{'mass_kg':M,'L_A':L*1e10,'omega0_ps^-1':OMEGA0_PS,'k_N_m':K_LOCAL,'eta_ps^-1':ETA_PS,'chi':CHI,'vth_m_s':VTH},
      'coeffs_meV':{str(b):{'A':COEFFS[b][0],'B':COEFFS[b][1]} for b in BARRIERS}
    }
    h1=harmonic_gate(0.001); h05=harmonic_gate(0.0005)
    eq1=equipartition_gate(0.001); eq05=equipartition_gate(0.0005)
    d1=free_diffusion_gate(0.001); d05=free_diffusion_gate(0.0005)
    out['harmonic']={'dt_0.001_nrms':h1,'dt_0.0005_nrms':h05,'pass':h1<=0.01 and h05<=0.01}
    out['equipartition']={'dt_0.001_ratio':eq1,'dt_0.0005_ratio':eq05,'pass':abs(eq1-1)<=0.03 and abs(eq05-1)<=0.03}
    out['free_diffusion']={'dt_0.001':d1,'dt_0.0005':d05,'pass':abs(d1[2]-1)<=0.05 and abs(d05[2]-1)<=0.05 and abs(d1[0]/d05[0]-1)<=0.05}
    pots={}
    for b in BARRIERS:
        bn,curv,ratio=potential_gate(b)
        pots[str(b)]={'barrier_meV':bn,'curvature_N_m':curv,'curvature_ratio':ratio,'pass':abs(bn/b-1)<=1e-8 and abs(ratio-1)<=1e-8}
    out['potential_identity']=pots
    lin={}
    for b in BARRIERS:
        for s in (-1,1):
            val=linearity_gate(b,s)
            lin[f'{b}_{s:+d}']={'rms':val,'pass':val<=0.05}
    out['linearity']=lin
    out['all_pass']=out['harmonic']['pass'] and out['equipartition']['pass'] and out['free_diffusion']['pass'] and all(x['pass'] for x in pots.values()) and all(x['pass'] for x in lin.values())
    return out

if __name__=='__main__':
    out=run_preflight()
    print(json.dumps(out,indent=2,sort_keys=True))
