#!/usr/bin/env python3
import argparse, json, platform
from dataclasses import dataclass, asdict
from pathlib import Path
import numpy as np

KB=1.380649e-23; HBAR=1.054571817e-34; EV=1.602176634e-19
MEV=1e-3*EV; ANG=1e-10; PS=1e-12; AMU=1.66053906660e-27

@dataclass(frozen=True)
class Frozen:
    T: float=300.0; mass_u: float=65.095; a0_A: float=3.615
    mode_meV: float=4.6; eta_ps: float=2.6; dt_ps: float=0.001
    n_per_sign: int=8000; t_ps: float=15.0; early_ps: float=0.5
    early_sample_ps: float=0.005; long_sample_ps: float=0.1
    msd_fit_start_ps: float=4.0; bootstrap_B: int=2000
    seed_plus: int=62001; seed_minus: int=62002; bootstrap_seed: int=63001
    @property
    def m(self): return self.mass_u*AMU
    @property
    def L(self): return self.a0_A*ANG/np.sqrt(6.0)
    @property
    def omega(self): return self.mode_meV*MEV/HBAR
    @property
    def eta(self): return self.eta_ps/PS
    @property
    def k(self): return self.m*self.omega**2
    @property
    def chi(self): return self.eta/(2*self.omega)

FROZEN=Frozen(); BARRIERS=(40.0,55.0)

def coeffs(barrier,p=FROZEN):
    q=2*np.pi/p.L; A=(barrier/2)*MEV; B=(p.k/q**2-A)/4
    return q,A,B

def V(x,barrier,p=FROZEN):
    q,A,B=coeffs(barrier,p)
    return A*(1-np.cos(q*x))+B*(1-np.cos(2*q*x))

def force(x,barrier,p=FROZEN):
    q,A,B=coeffs(barrier,p)
    return -(A*q*np.sin(q*x)+2*B*q*np.sin(2*q*x))

def sample_well(n,barrier,rng,p=FROZEN):
    grid=np.linspace(-p.L/2,p.L/2,20001); w=np.exp(-(V(grid,barrier,p)-V(0,barrier,p))/(KB*p.T))
    c=np.cumsum((w[:-1]+w[1:])*0.5*np.diff(grid)); c=np.concatenate([[0],c]); c/=c[-1]
    x=np.interp(rng.random(n),c,grid); v=np.sqrt(KB*p.T/p.m)*rng.standard_normal(n)
    return x,v

def step(x,v,barrier,dt,rng,p=FROZEN):
    v += 0.5*dt*force(x,barrier,p)/p.m; x += 0.5*dt*v
    c=np.exp(-p.eta*dt); sig=np.sqrt(KB*p.T/p.m*(1-c*c)); v=c*v+sig*rng.standard_normal(v.shape)
    x += 0.5*dt*v; v += 0.5*dt*force(x,barrier,p)/p.m
    return x,v

def local(x,p=FROZEN): return x-np.round(x/p.L)*p.L

def exact_dho(t,p=FROZEN):
    wd=np.sqrt(p.omega**2-(p.eta/2)**2)
    return np.exp(-p.eta*t/2)*(np.cos(wd*t)+(p.eta/(2*wd))*np.sin(wd*t))

def preflight():
    p=FROZEN; out={}
    dt=p.dt_ps*PS; delta=.05*p.L; x=np.array([delta]); v=np.array([0.0]); ts=[]; rr=[]
    for i in range(int(2/p.dt_ps)+1):
        if i%5==0: ts.append(i*dt); rr.append(x[0]/delta)
        if i==int(2/p.dt_ps): break
        v += .5*dt*(-p.k*x)/p.m; x += .5*dt*v; v=np.exp(-p.eta*dt)*v; x += .5*dt*v; v += .5*dt*(-p.k*x)/p.m
    rms=float(np.sqrt(np.mean((np.array(rr)-exact_dho(np.array(ts),p))**2))); out['G1_harmonic_rms']=rms
    rng=np.random.default_rng(1201); x,v=sample_well(12000,40,rng,p); acc=[]
    for i in range(800):
        x,v=step(x,v,40,dt,rng,p)
        if i>=400 and i%10==0: acc.append(np.mean(p.m*v*v)/(KB*p.T))
    out['G2_equipartition_ratio']=float(np.mean(acc))
    rng=np.random.default_rng(1301); n=12000; x=np.zeros(n); v=np.sqrt(KB*p.T/p.m)*rng.standard_normal(n); x0=x.copy(); tt=[]; mm=[]
    c=np.exp(-p.eta*dt); sig=np.sqrt(KB*p.T/p.m*(1-c*c))
    for i in range(int(5/p.dt_ps)+1):
        if i%100==0: tt.append(i*dt); mm.append(np.mean((x-x0)**2))
        if i==int(5/p.dt_ps): break
        x += .5*dt*v; v=c*v+sig*rng.standard_normal(n); x += .5*dt*v
    tt=np.array(tt); mm=np.array(mm); mask=tt>=PS; D=float(np.polyfit(tt[mask],mm[mask],1)[0]/2); D0=KB*p.T/(p.m*p.eta)
    out['G3_D_ratio']=D/D0
    pot={}
    for b in BARRIERS:
        h=1e-3*p.L; f=lambda z: V(z,b,p); kn=(-f(2*h)+16*f(h)-30*f(0)+16*f(-h)-f(-2*h))/(12*h*h)
        pot[str(int(b))]={'barrier_relerr':float(abs((V(p.L/2,b,p)-V(0,b,p))/(b*MEV)-1)),'curvature_relerr':float(abs(kn/p.k-1))}
    out['G4_potential']=pot
    def resp(b,a,sign,dt_ps,seed):
        rng=np.random.default_rng(seed); hN=4000; xb,vb=sample_well(hN,b,rng,p); x=sign*np.r_[xb,-xb]; v=sign*np.r_[vb,-vb]; d=sign*a*p.L; x+=d
        vals=[]; dt=dt_ps*PS
        for i in range(int(.5/dt_ps)+1):
            if i%max(1,int(.005/dt_ps))==0: vals.append(local(x,p).mean()/d)
            if i==int(.5/dt_ps): break
            zh=rng.standard_normal(hN); z=sign*np.r_[zh,-zh]
            v += .5*dt*force(x,b,p)/p.m; x += .5*dt*v; cc=np.exp(-p.eta*dt); ss=np.sqrt(KB*p.T/p.m*(1-cc*cc)); v=cc*v+ss*z; x += .5*dt*v; v += .5*dt*force(x,b,p)/p.m
        return np.array(vals)
    lin={}
    for b in BARRIERS:
        seed=int(20000+b*10); c25p=resp(b,.025,1,p.dt_ps,seed); c50p=resp(b,.05,1,p.dt_ps,seed); c50m=resp(b,.05,-1,p.dt_ps,seed)
        lin[str(int(b))]={'amplitude_rms':float(np.sqrt(np.mean((c25p-c50p)**2))),'sign_rms':float(np.sqrt(np.mean((c50p-c50m)**2)))}
    out['G6_linearity']=lin
    out['PASS']=bool(rms<=.01 and abs(out['G2_equipartition_ratio']-1)<=.03 and abs(out['G3_D_ratio']-1)<=.05 and all(z['barrier_relerr']<=1e-8 and z['curvature_relerr']<=1e-8 for z in pot.values()) and all(z['amplitude_rms']<=.05 and z['sign_rms']<=.05 for z in lin.values()))
    return out

def simulate(barrier,sign,seed,p=FROZEN):
    rng=np.random.default_rng(seed); n=p.n_per_sign; x,v=sample_well(n,barrier,rng,p); delta=sign*.05*p.L; x=x+delta; x_start=x.copy(); w0=np.round((x-delta)/p.L).astype(int)
    fpt=np.full(n,np.inf); dt=p.dt_ps*PS; steps=int(round(p.t_ps/p.dt_ps)); early_every=int(round(p.early_sample_ps/p.dt_ps)); long_every=int(round(p.long_sample_ps/p.dt_ps))
    early_t=[]; early_local=[]; long_t=[]; sq=[]
    for i in range(steps+1):
        if i<=int(round(p.early_ps/p.dt_ps)) and i%early_every==0:
            early_t.append(i*p.dt_ps); early_local.append(local(x,p).copy()/delta)
        if i%long_every==0:
            long_t.append(i*p.dt_ps); sq.append(((x-x_start)/ANG)**2)
        if i==steps: break
        x,v=step(x,v,barrier,dt,rng,p); wi=np.round((x-delta)/p.L).astype(int); hit=np.isinf(fpt)&(wi!=w0); fpt[hit]=(i+1)*p.dt_ps
    return {'early_t':np.array(early_t),'early_local':np.stack(early_local,axis=1),'long_t':np.array(long_t),'sq':np.stack(sq,axis=1),'fpt':fpt}

def per_traj_D(long_t,sq,p=FROZEN):
    mask=long_t>=p.msd_fit_start_ps; t=long_t[mask]; y=sq[:,mask]; tc=t-t.mean(); denom=np.sum(tc*tc); slopes=(y@tc)/denom
    return slopes/2

def ci_percentile(x): return [float(np.quantile(x,.025)),float(np.quantile(x,.975))]

def production(outdir):
    p=FROZEN; outdir=Path(outdir); outdir.mkdir(parents=True,exist_ok=True)
    allruns={}
    for sign,seed in ((1,p.seed_plus),(-1,p.seed_minus)):
        for b in BARRIERS:
            key=f'b{int(b)}_s{sign:+d}'; allruns[key]=simulate(b,sign,seed,p)
            np.savez_compressed(outdir/f'{key}.npz',**allruns[key])
    rng=np.random.default_rng(p.bootstrap_seed); B=p.bootstrap_B; n=p.n_per_sign
    local_results={}
    for sign in (1,-1):
        a=allruns[f'b40_s{sign:+d}']['early_local']; b=allruns[f'b55_s{sign:+d}']['early_local']
        ma=a.mean(0); mb=b.mean(0); rms=float(np.sqrt(np.mean((ma-mb)**2))); boots=np.empty(B)
        for j in range(B):
            idx=rng.integers(0,n,n); boots[j]=np.sqrt(np.mean((a[idx].mean(0)-b[idx].mean(0))**2))
        local_results[str(sign)]={'rms':rms,'bootstrap95':ci_percentile(boots),'upper95':float(np.quantile(boots,.975))}
    sign_results={}
    for b in BARRIERS:
        rp=allruns[f'b{int(b)}_s+1']['early_local'].mean(0); rm=allruns[f'b{int(b)}_s-1']['early_local'].mean(0)
        sign_results[str(int(b))]=float(np.sqrt(np.mean((rp-rm)**2)))
    kin={}
    Ds={}; F={}
    for b in BARRIERS:
        d=np.r_[per_traj_D(allruns[f'b{int(b)}_s+1']['long_t'],allruns[f'b{int(b)}_s+1']['sq'],p),per_traj_D(allruns[f'b{int(b)}_s-1']['long_t'],allruns[f'b{int(b)}_s-1']['sq'],p)]
        f=np.r_[allruns[f'b{int(b)}_s+1']['fpt'],allruns[f'b{int(b)}_s-1']['fpt']]
        Ds[b]=d; F[b]=f; kin[str(int(b))]={'D_A2_ps':float(d.mean()),'median_FPT_ps':float(np.median(f)),'censored_fraction':float(np.isinf(f).mean())}
    logD=np.empty(B); logF=np.empty(B); N=2*n
    for j in range(B):
        idx=rng.integers(0,N,N); logD[j]=np.log(Ds[55][idx].mean()/Ds[40][idx].mean()); logF[j]=np.log(np.median(F[55][idx])/np.median(F[40][idx]))
    adjud={'local':local_results,'sign_symmetry_rms':sign_results,'kinetics':kin,'log_D55_D40_ci95':ci_percentile(logD),'log_FPT55_FPT40_ci95':ci_percentile(logF)}
    adjud['CP_PR_01_PASS']=bool(all(v['upper95']<=.05 for v in local_results.values()) and all(v<=.05 for v in sign_results.values()) and all(np.any(np.diff(np.sign(allruns[f'b{int(b)}_s+1']['early_local'].mean(0)))!=0) for b in BARRIERS))
    adjud['CP_PR_02_PASS']=bool(adjud['log_D55_D40_ci95'][1]<0 and adjud['log_FPT55_FPT40_ci95'][0]>0)
    adjud['CP_PR_03_PASS']=bool(adjud['CP_PR_01_PASS'] and adjud['CP_PR_02_PASS'])
    meta={'frozen':asdict(p),'python':platform.python_version(),'numpy':np.__version__,'barriers_meV':BARRIERS,'L_A':p.L/ANG,'omega_ps':p.omega*PS,'chi':p.chi}
    (outdir/'result.json').write_text(json.dumps({'metadata':meta,'adjudication':adjud},indent=2))
    return {'metadata':meta,'adjudication':adjud}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--preflight',action='store_true'); ap.add_argument('--production'); args=ap.parse_args()
    if args.preflight: print(json.dumps(preflight(),indent=2))
    elif args.production: print(json.dumps(production(args.production),indent=2))
    else: ap.error('choose --preflight or --production OUTDIR')
if __name__=='__main__': main()
