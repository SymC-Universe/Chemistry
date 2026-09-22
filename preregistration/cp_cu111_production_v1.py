import argparse, json, math, pathlib
import numpy as np
import cp_cu111_pr_v1 as core

DT_PS = 0.001
RECOVERY_T_PS = 0.5
RECOVERY_STRIDE = 5
N_RECOVERY = 20000
LONG_T_PS = 100.0
LONG_STRIDE = 500
N_LONG = 5000
MSD_FIT_MIN_PS = 20.0
MSD_FIT_MAX_PS = 100.0
DELTA_FRAC = 0.05
BOOTSTRAP_B = 2000
BOOTSTRAP_SEED = 92026
SEEDS = {
    40: {'rec_plus': 41040, 'rec_minus': 42040, 'long': 40040},
    55: {'rec_plus': 41055, 'rec_minus': 42055, 'long': 40055},
}

def simulate_recovery(barrier, sign, seed):
    rng = np.random.default_rng(seed)
    x, v = core.sample_conditional_well(N_RECOVERY, float(barrier), rng)
    delta = sign * DELTA_FRAC * core.L
    x = x + delta
    dt = DT_PS * 1e-12
    nsteps = round(RECOVERY_T_PS / DT_PS)
    t, xs, _ = core.baoab(x, v, dt, nsteps,
                          lambda z: core.force(z, float(barrier)),
                          rng, noise=True, record_stride=RECOVERY_STRIDE)
    local = xs - np.round(xs/core.L)*core.L
    resp_traj = (local / delta).T.astype(np.float32)
    return (t/1e-12).astype(np.float64), resp_traj

def simulate_long(barrier, seed):
    rng = np.random.default_rng(seed)
    x = np.zeros(N_LONG, dtype=float)
    v = rng.normal(0, core.VTH, size=N_LONG)
    x0 = x.copy()
    fpt = np.full(N_LONG, np.nan, dtype=float)
    dt = DT_PS * 1e-12
    nsteps = round(LONG_T_PS / DT_PS)
    c = math.exp(-core.ETA*dt)
    sigma = math.sqrt((1-c*c)*core.KBT/core.M)
    rec_steps = list(range(0, nsteps+1, LONG_STRIDE))
    pos = np.empty((N_LONG, len(rec_steps)), dtype=np.float32)
    ri = 0
    pos[:, ri] = x
    ri += 1
    for i in range(1, nsteps+1):
        f = core.force(x, float(barrier))
        v += 0.5*dt*f/core.M
        x += 0.5*dt*v
        v = c*v + sigma*rng.standard_normal(N_LONG)
        x += 0.5*dt*v
        f = core.force(x, float(barrier))
        v += 0.5*dt*f/core.M
        uncrossed = np.isnan(fpt)
        crossed = uncrossed & (np.abs(x-x0) >= core.L/2)
        fpt[crossed] = i*DT_PS
        if i % LONG_STRIDE == 0:
            pos[:, ri] = x.astype(np.float32)
            ri += 1
    times_ps = np.asarray(rec_steps, dtype=float)*DT_PS
    return times_ps, pos, fpt

def save_barrier(barrier, outdir):
    barrier = int(barrier)
    outdir = pathlib.Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    t, rp = simulate_recovery(barrier, +1, SEEDS[barrier]['rec_plus'])
    _, rm = simulate_recovery(barrier, -1, SEEDS[barrier]['rec_minus'])
    lt, pos, fpt = simulate_long(barrier, SEEDS[barrier]['long'])
    np.savez_compressed(outdir/f'cp_barrier_{barrier}_production.npz',
                        recovery_time_ps=t,
                        recovery_plus=rp,
                        recovery_minus=rm,
                        long_time_ps=lt,
                        long_positions_m=pos,
                        first_passage_ps=fpt)
    meta = {
        'barrier_meV': barrier,
        'dt_ps': DT_PS,
        'n_recovery': N_RECOVERY,
        'recovery_t_ps': RECOVERY_T_PS,
        'recovery_record_dt_ps': DT_PS*RECOVERY_STRIDE,
        'n_long': N_LONG,
        'long_t_ps': LONG_T_PS,
        'long_record_dt_ps': DT_PS*LONG_STRIDE,
        'msd_fit_ps': [MSD_FIT_MIN_PS, MSD_FIT_MAX_PS],
        'delta_fraction_L': DELTA_FRAC,
        'seeds': SEEDS[barrier],
    }
    (outdir/f'cp_barrier_{barrier}_metadata.json').write_text(json.dumps(meta, indent=2, sort_keys=True))

def analyze(file40, file55, out_json):
    d40=np.load(file40); d55=np.load(file55)
    t=d40['recovery_time_ps']
    assert np.allclose(t,d55['recovery_time_ps'])
    def mean_pair(d):
        p=d['recovery_plus'].astype(float); m=d['recovery_minus'].astype(float)
        return 0.5*(p.mean(0)+m.mean(0)), p, m
    r40,p40,m40=mean_pair(d40); r55,p55,m55=mean_pair(d55)
    sign40=float(np.sqrt(np.mean((p40.mean(0)-m40.mean(0))**2)))
    sign55=float(np.sqrt(np.mean((p55.mean(0)-m55.mean(0))**2)))
    cross_rms=float(np.sqrt(np.mean((r40-r55)**2)))
    def zero_cross_time(r):
        idx=np.where(np.signbit(r[:-1]) != np.signbit(r[1:]))[0]
        return float(t[idx[0]+1]) if len(idx) else None
    z40=zero_cross_time(r40); z55=zero_cross_time(r55)
    def diffusion(d):
        tp=d['long_time_ps'].astype(float); x=d['long_positions_m'].astype(float)
        msd=np.mean((x-x[:,[0]])**2,axis=0)
        mask=(tp>=MSD_FIT_MIN_PS)&(tp<=MSD_FIT_MAX_PS)
        slope=np.polyfit(tp[mask]*1e-12,msd[mask],1)[0]
        return slope/2, tp, x, mask
    D40,tp40,x40,mask40=diffusion(d40); D55,tp55,x55,mask55=diffusion(d55)
    f40=d40['first_passage_ps'].astype(float); f55=d55['first_passage_ps'].astype(float)
    med40=float(np.nanmedian(f40)); med55=float(np.nanmedian(f55))
    cens40=float(np.mean(np.isnan(f40))); cens55=float(np.mean(np.isnan(f55)))
    rng=np.random.default_rng(BOOTSTRAP_SEED)
    cross=[]; logDr=[]; logFr=[]
    nrec=p40.shape[0]; nlong=x40.shape[0]
    for _ in range(BOOTSTRAP_B):
        i40=rng.integers(0,nrec,nrec); i55=rng.integers(0,nrec,nrec)
        br40=0.5*(p40[i40].mean(0)+m40[i40].mean(0))
        br55=0.5*(p55[i55].mean(0)+m55[i55].mean(0))
        cross.append(math.sqrt(float(np.mean((br40-br55)**2))))
        j40=rng.integers(0,nlong,nlong); j55=rng.integers(0,nlong,nlong)
        def bd(x,tp,mask,j):
            xx=x[j]
            msd=np.mean((xx-xx[:,[0]])**2,axis=0)
            return np.polyfit(tp[mask]*1e-12,msd[mask],1)[0]/2
        bd40=bd(x40,tp40,mask40,j40); bd55=bd(x55,tp55,mask55,j55)
        if bd40>0 and bd55>0: logDr.append(math.log(bd55/bd40))
        bf40=f40[j40]; bf55=f55[j55]
        if np.mean(np.isnan(bf40))<0.5 and np.mean(np.isnan(bf55))<0.5:
            logFr.append(math.log(np.nanmedian(bf55)/np.nanmedian(bf40)))
    def ci(a):
        return [float(np.quantile(a,0.025)),float(np.quantile(a,0.975))]
    cross_ci=ci(cross); d_ci=ci(logDr) if logDr else [None,None]; f_ci=ci(logFr) if logFr else [None,None]
    cp1=(sign40<=0.05 and sign55<=0.05 and z40 is not None and z40<=0.5 and z55 is not None and z55<=0.5 and cross_rms<=0.05 and cross_ci[1]<=0.05)
    if d_ci[0] is None or f_ci[0] is None:
        cp2='INDETERMINATE'
    elif d_ci[1] < 0 and f_ci[0] > 0:
        cp2='PASS'
    elif d_ci[0] > 0 or f_ci[1] < 0:
        cp2='FAIL'
    else:
        cp2='INDETERMINATE'
    out={
      'CP_PR_01':{'status':'PASS' if cp1 else 'FAIL','sign_rms_40':sign40,'sign_rms_55':sign55,'cross_embedding_rms':cross_rms,'cross_embedding_rms_bootstrap95':cross_ci,'zero_cross_ps_40':z40,'zero_cross_ps_55':z55},
      'CP_PR_02':{'status':cp2,'D_40_m2_s':float(D40),'D_55_m2_s':float(D55),'log_D55_D40_bootstrap95':d_ci,'median_FPT_40_ps':med40,'median_FPT_55_ps':med55,'log_FPT55_FPT40_bootstrap95':f_ci,'censored_40':cens40,'censored_55':cens55},
    }
    out['CP_PR_03']={'status':'PASS' if cp1 and cp2=='PASS' else ('INDETERMINATE' if cp1 and cp2=='INDETERMINATE' else 'FAIL')}
    pathlib.Path(out_json).write_text(json.dumps(out,indent=2,sort_keys=True))
    print(json.dumps(out,indent=2,sort_keys=True))

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    sub=ap.add_subparsers(dest='cmd',required=True)
    s=sub.add_parser('simulate'); s.add_argument('--barrier',type=int,choices=[40,55],required=True); s.add_argument('--outdir',required=True)
    a=sub.add_parser('analyze'); a.add_argument('--file40',required=True); a.add_argument('--file55',required=True); a.add_argument('--out-json',required=True)
    args=ap.parse_args()
    if args.cmd=='simulate': save_barrier(args.barrier,args.outdir)
    else: analyze(args.file40,args.file55,args.out_json)
