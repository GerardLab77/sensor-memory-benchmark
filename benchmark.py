"""Causal gas-sensor history baseline. No neural network or hardware claims."""
import argparse, hashlib, json, platform, time, zipfile
from pathlib import Path
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import mean_absolute_error, mean_squared_error
import sklearn
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def features(x, kind, history):
    if kind == 'current': return x.copy()
    if kind == 'summary':
        parts=[x, np.vstack([np.zeros_like(x[:1]), np.diff(x,axis=0)])]
        for tau in (5,30,120):
            state=x[0].copy(); out=np.empty_like(x)
            for i,row in enumerate(x):
                state += (row-state)/(tau+1); out[i]=state
            parts.append(out)
        return np.column_stack(parts)
    # Raw samples at sparse, fixed lags; not all samples within the horizon.
    lags=sorted(set([0,1,history//4,history//2,history]))
    return np.column_stack([x[np.maximum(np.arange(len(x))-lag,0)] for lag in lags])


def split_indices(n, gap):
    a,b=int(.6*n),int(.8*n)
    if a <= gap or b+gap >= n: raise ValueError('Recording too short for split and gap')
    return np.arange(gap,a),np.arange(a+gap,b),np.arange(b+gap,n)


def main():
    p=argparse.ArgumentParser();p.add_argument('--zip',type=Path,default=Path('data/uci322.zip'))
    p.add_argument('--member',default=None);p.add_argument('--stride',type=int,default=100)
    p.add_argument('--out',type=Path,default=Path('results'));args=p.parse_args()
    if args.stride < 1: p.error('stride must be positive')
    with zipfile.ZipFile(args.zip) as z:
        members=[n for n in z.namelist() if n.endswith('.txt')]
        member=args.member or members[0]
        with z.open(member) as f:
            header=f.readline().decode().strip()
            rows=[np.fromstring(line.decode(),sep=' ') for i,line in enumerate(f) if i%args.stride==0]
    a=np.asarray(rows,dtype=np.float64)
    if a.ndim != 2 or a.shape[1] != 19 or not np.isfinite(a).all(): raise ValueError('Expected 19 finite columns')
    t,y,x=a[:,0],a[:,1:3],a[:,3:]
    if not np.all(np.diff(t)>0): raise ValueError('Timestamps must increase')
    dt=float(np.median(np.diff(t)))
    # Causal previous-observation resampling handles timestamp jitter/gaps.
    max_gap=float(np.max(np.diff(t)))
    grid=np.arange(t[0],t[-1]+dt*.001,dt)
    idx=np.searchsorted(t,grid,side='right')-1
    t,y,x=grid,y[idx],x[idx]
    # Summary constants are in samples; describe actual seconds in metadata.
    horizon=max(1,round(120/dt));gap=max(horizon,600)
    tr,va,te=split_indices(len(x),gap)
    args.out.mkdir(parents=True,exist_ok=True)
    records=[];predictions={}
    configs=[('current','current',0),('summary','summary',0)]+[(f'lags_{s}s','lags',max(1,round(s/dt))) for s in (10,30,120)]
    for name,kind,h in configs:
        f=features(x,kind,h);best=None
        for alpha in (0.1,1.,10.,100.):
            model=make_pipeline(StandardScaler(),Ridge(alpha=alpha))
            model.fit(f[tr],y[tr]);score=mean_absolute_error(y[va],model.predict(f[va]))
            if best is None or score<best[0]:best=(score,alpha,model)
        start=time.perf_counter();pred=best[2].predict(f[te]);elapsed=time.perf_counter()-start
        record={'model':name,'alpha':best[1],'validation_mae_mean':best[0],
                'test_mae_per_target':mean_absolute_error(y[te],pred,multioutput='raw_values').tolist(),
                'test_rmse_per_target':np.sqrt(mean_squared_error(y[te],pred,multioutput='raw_values')).tolist(),
                'features':f.shape[1],'batch_prediction_seconds':elapsed}
        records.append(record);predictions[name]=pred
        print(json.dumps(record),flush=True)
    metadata={'source':'UCI 322 real recorded sensor data','member':member,'header':header,
              'sha256':hashlib.file_digest(args.zip.open('rb'),'sha256').hexdigest(),
              'max_original_subsample_gap_seconds':max_gap,'resampling':'causal previous observation on median-interval grid','rows':len(x),'stride':args.stride,'sample_interval_seconds':dt,'gap_samples':gap,
              'summary_time_constants_samples':[5,30,120],
              'split_ranges':{k:[int(v[0]),int(v[-1])] for k,v in [('train',tr),('validation',va),('test',te)]},
              'python':platform.python_version(),'numpy':np.__version__,'sklearn':sklearn.__version__,
              'platform':platform.platform(),'results':records}
    (args.out/'metrics.json').write_text(json.dumps(metadata,indent=2)+'\n')
    np.savez_compressed(args.out/'test_predictions.npz',time=t[te],target=y[te],**predictions)
    fig,axes=plt.subplots(2,1,figsize=(11,6),sharex=True)
    for j,ax in enumerate(axes):
        ax.plot(t[te]/60,y[te,j],label='recorded concentration target',color='black',lw=1.5)
        for name in ('current','summary','lags_120s'):ax.plot(t[te]/60,predictions[name][:,j],label=name,alpha=.7,lw=.7)
        ax.set_ylabel(f'Target {j+1} (ppm)');ax.legend(fontsize=7)
    axes[-1].set_xlabel('Recording time (minutes)');fig.tight_layout();fig.savefig(args.out/'predictions.png',dpi=140)

if __name__=='__main__':main()
