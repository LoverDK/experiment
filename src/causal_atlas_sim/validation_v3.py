"""Prespecified v3 validation; does not change any core estimator or paper asset."""
from __future__ import annotations
from dataclasses import replace
from pathlib import Path
from statistics import NormalDist
import hashlib
import json
import math
import numpy as np
import pandas as pd
from .dgp import SimulationConfig, generate_minimal_archive
from .methods import AtlasConfig, fit_causal_atlas, compute_certificate
from .extension_baselines import archive_baselines

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'results/validation_v3'
Z = NormalDist().inv_cdf(.975)


def save(name, rows):
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT / (name + '.csv'), index=False)


def seed(block, scenario, rep):
    return int(np.random.SeedSequence([20260906, 300 + block, scenario, rep]).generate_state(1)[0])


def finite_quantile(values, coverage):
    values = np.sort(np.asarray(values))
    rank = math.ceil((len(values) + 1) * coverage)
    return float(values[rank - 1]) if rank <= len(values) else float('inf')


def blind_target(t):
    # Core methods use representation/design only. Poison evaluation fields anyway.
    return replace(t, estimated_effect=float('nan'), true_effect=float('nan'),
                   standard_error_certificate=float('nan'))


def predictor_rows(g, config=None):
    config = config or AtlasConfig()
    a, t = g.archive, blind_target(g.target)
    atlas = fit_causal_atlas(a, t, config)
    x = np.vstack([e.observed_representation for e in a])
    y = np.array([e.estimated_effect for e in a])
    ses = np.array([e.standard_error_certificate for e in a])
    base, tuning = archive_baselines(x, y, ses, t.observed_representation)
    result = []
    for method in ('atlas', 'full_nearest', 'ivw_meta', 'ridge_meta_regression', 'rbf_kernel_ridge'):
        w = None
        if method == 'atlas':
            pred = atlas.raw_point_estimate; w = atlas.weights
        else:
            pred = float(base[method][0])
            if method == 'full_nearest':
                w = np.zeros(len(a)); w[np.argmin(((x-t.observed_representation)**2).sum(1))] = 1
            elif method == 'ivw_meta':
                w = 1 / np.maximum(ses**2, 1e-10); w /= w.sum()
        if w is not None:
            c = compute_certificate(a, t, w, config)
            bias = c.radius-c.statistical_term
            stderr = float(np.sqrt(np.sum(w*w*ses*ses)))
            score = c.radius
        else:
            key = 'ridge' if method == 'ridge_meta_regression' else 'kernel'
            dist = np.min(((x-t.observed_representation)**2).sum(1))
            score = np.sqrt(max(tuning[key]['loo_mse'], 1e-8)*(1+dist))
            bias = stderr = float('nan')
        result.append(dict(method=method, estimate=pred, score=score, bias=bias, stderr=stderr,
            native_radius=bias+Z*stderr, truth=g.target.true_effect,
            reference=g.target.estimated_effect, reference_se=g.target.standard_error_certificate,
            error=abs(pred-g.target.true_effect), signed_error=pred-g.target.true_effect))
    return result


def selection_intervals():
    rows=[]
    scenarios=(('nominal',0,1),('moderate',.25,1),('severe',.8,1),('high_noise',0,3))
    for s,(name,shift,noise) in enumerate(scenarios):
        for part,n,offset in (('calibration',150,0),('test',300,10000)):
            for r in range(n):
                sd=seed(1,s,r+offset)
                g=generate_minimal_archive(SimulationConfig(target_shift_fraction=shift,outcome_noise_sd=noise),seed=sd)
                rows.extend(dict(scenario=name,part=part,replicate=r,seed=sd,**v) for v in predictor_rows(g))
            print('selection',name,part,flush=True)
    save('selection_predictions',rows)
    df=pd.DataFrame(rows); rankings=[]; intervals=[]; thresholds=[]
    for (scenario,method),test in df[df.part=='test'].groupby(['scenario','method']):
        test=test.sort_values('replicate')
        for origin in (scenario,'nominal') if scenario!='nominal' else ('nominal',):
            cal=df[(df.part=='calibration')&(df.scenario==origin)&(df.method==method)]
            for fraction in (.25,.5,.75,1.):
                threshold=finite_quantile(cal.score,fraction) if fraction<1 else float('inf')
                thresholds.append(dict(scenario=scenario,method=method,calibration=origin,fraction=fraction,threshold=threshold))
                take=test.score<=threshold
                for _,v in test.iterrows():
                    rankings.append(dict(scenario=scenario,method=method,calibration=origin,
                        rule='calibration_threshold',fraction=fraction,replicate=v.replicate,
                        released=bool(v.score<=threshold),error=v.error))
            residual=np.abs(cal.estimate-cal.reference)/cal.score
            for level in (.8,.9,.95):
                q=finite_quantile(residual,level)
                for _,v in test.iterrows():
                    radius=q*v.score
                    intervals.append(dict(scenario=scenario,method=method,calibration=origin,
                        interval='historical_noisy_reference',level=level,replicate=v.replicate,
                        width=2*radius,covered=v.error<=radius,reference_included=abs(v.estimate-v.reference)<=radius,
                        radius=radius,error=v.error))
        for fraction in (.25,.5,.75,1.):
            chosen=set(test.sort_values(['score','replicate']).head(round(len(test)*fraction)).replicate)
            for _,v in test.iterrows():
                rankings.append(dict(scenario=scenario,method=method,calibration='none',rule='cohort_rank',
                    fraction=fraction,replicate=v.replicate,released=v.replicate in chosen,error=v.error))
        if test.native_radius.notna().all():
            for level in (.8,.9,.95):
                z=NormalDist().inv_cdf((1+level)/2)
                for _,v in test.iterrows():
                    radius=v.bias+z*v.stderr
                    intervals.append(dict(scenario=scenario,method=method,calibration='none',interval='native_bias_aware',
                        level=level,replicate=v.replicate,width=2*radius,covered=v.error<=radius,
                        reference_included=abs(v.estimate-v.reference)<=radius,radius=radius,error=v.error))
    save('selection_records',rankings);save('selection_thresholds',thresholds);save('interval_records',intervals)


def surface_value(m,kind):
    x=np.asarray(m)
    if kind=='affine':return .5+x[0]+.6*x[1]+.8*x[2]-.3*x[3]
    if kind=='oscillatory':return np.sin(4*x[0])+np.cos(3*x[1])+.8*x[2]*x[3]
    if kind=='threshold':return 1.5*(x[2]>0)-1.2*(x[0]*x[1]>.15)+.4*x[3]
    if kind=='friedman2':
        a=50*(x[0]+1);b=40*np.pi+260*np.pi*(x[1]+1);c=(x[2]+1)/2;d=1+5*(x[3]+1)
        return np.sqrt(a*a+(b*c-1/(b*d))**2)/500
    raise ValueError(kind)


def transform(g,kind='original',noise='normal',proxy=False,omit=False,rng=None):
    rng=rng or np.random.default_rng(0)
    result=[]
    for obj in (*g.archive,g.target):
        truth=obj.true_effect if kind=='original' else float(surface_value(obj.mechanism.as_array(),kind))
        # Gaussian/standardized t3 summary noise isolates transport behavior.
        err=obj.estimated_effect-obj.true_effect
        if noise=='t3':err=float(rng.standard_t(3)/np.sqrt(3)*obj.standard_error_certificate)
        observed=obj.observed_representation.copy()
        if proxy:observed[2]=np.clip(obj.mechanism.h+rng.uniform(-.5,.5),-1,1)
        if omit:observed[2:]=rng.uniform(-1,1,2)
        delta=truth-obj.true_effect
        result.append(replace(obj,true_effect=truth,estimated_effect=truth+err,observed_representation=observed,
            potential_outcome_treated=obj.potential_outcome_treated+delta,
            observed_outcome=obj.observed_outcome+obj.treatment*delta,aipw_scores=obj.aipw_scores+delta))
    return replace(g,archive=tuple(result[:-1]),target=result[-1])


def mechanism_benchmark():
    rows=[]
    changes=(('baseline',{}),('shift',dict(target_shift_fraction=.8)),('small_n',dict(n_units_per_experiment=100)),
        ('archive4',dict(n_archive=4)),('archive24',dict(n_archive=24)),('high_noise',dict(outcome_noise_sd=3)),
        ('t3',{}),('omit',{}),('proxy',{}))
    for si,kind in enumerate(('original','affine','oscillatory','threshold','friedman2')):
        for ci,(change,settings) in enumerate(changes):
            for r in range(100):
                sd=seed(4,si*20+ci,r)
                g=generate_minimal_archive(SimulationConfig(**settings),seed=sd)
                g=transform(g,kind,noise='t3' if change=='t3' else 'normal',proxy=change=='proxy',omit=change=='omit',rng=np.random.default_rng(sd+1))
                for v in predictor_rows(g):
                    rows.append(dict(surface=kind,change=change,replicate=r,seed=sd,**v,
                        released=v['score']<=1.65,covered=v['error']<=v['native_radius']))
            print('benchmark',kind,change,flush=True)
    save('mechanism_records',rows)


def sigmoid(x):return 1/(1+np.exp(-np.clip(x,-30,30)))


def fitted_aipw(x,a,y,tau,mode,propensity):
    """Two-fold nuisance fitting. Labels from evaluation folds never train models."""
    n=len(x); folds=np.arange(n)%2; mu0=1+.8*x+1.2*x*x
    p=np.full(n,propensity) if np.isscalar(propensity) else propensity
    if mode=='oracle':return tau+a*(y-mu0-tau)/p-(1-a)*(y-mu0)/(1-p)
    scores=np.empty(n)
    for fold in (0,1):
        train=folds!=fold;test=~train
        power=2 if mode in ('quadratic_known','logistic_fitted') else 1
        features=np.column_stack([x**k for k in range(power+1)])
        fitted=[]
        for arm in (0,1):
            use=train&(a==arm)
            if use.sum()<power+2:raise ValueError('arm_minimum')
            coef=np.linalg.lstsq(features[use],y[use],rcond=None)[0]
            fitted.append(features[test]@coef)
        if mode in ('logistic_fitted','intercept_misspecified'):
            z=np.column_stack([np.ones(n),x]) if mode=='logistic_fitted' else np.ones((n,1))
            beta=np.zeros(z.shape[1])
            for _ in range(30):
                pp=sigmoid(z[train]@beta)
                h=z[train].T@(z[train]*(pp*(1-pp))[:,None])+np.eye(z.shape[1])*1e-6
                step=np.linalg.solve(h,z[train].T@(a[train]-pp));beta+=step
                if np.linalg.norm(step)<1e-8:break
            pp=np.clip(sigmoid(z[test]@beta),.1,.9)
        else:pp=p[test]
        m0,m1=fitted
        scores[test]=m1-m0+a[test]*(y[test]-m1)/pp-(1-a[test])*(y[test]-m0)/(1-pp)
    return scores


def nuisance_experiment():
    rows=[];effects=[];failures=[]
    for ni,n in enumerate((100,400)):
        for pi,prop in enumerate(('balanced','weak','logistic')):
            modes=('oracle','quadratic_known','linear_known') if prop!='logistic' else ('oracle','logistic_fitted','intercept_misspecified')
            for r in range(200):
                sd=seed(3,ni*10+pi,r);rng=np.random.default_rng(sd)
                g=generate_minimal_archive(SimulationConfig(n_units_per_experiment=n),seed=sd)
                data=[]
                for e in g.archive:
                    x=rng.uniform(-1,1,n);p=.5 if prop=='balanced' else (.1 if prop=='weak' else sigmoid(2*x))
                    a=rng.binomial(1,p,n);y=1+.8*x+1.2*x*x+a*e.true_effect+rng.normal(size=n)
                    data.append((x,a,y,p))
                for mode in modes:
                    try:
                        archive=[]
                        for j,(e,(x,a,y,p)) in enumerate(zip(g.archive,data)):
                            score=fitted_aipw(x,a,y,e.true_effect,mode,p)
                            se=float(score.std(ddof=1)/np.sqrt(n));est=float(score.mean())
                            archive.append(replace(e,estimated_effect=est,standard_error_certificate=se,
                                variance_proxy=float(score.var(ddof=1)),aipw_scores=score,x=x[:,None],
                                treatment=a,observed_outcome=y,nuisance_bias_bound=0.))
                            effects.append(dict(n=n,propensity=prop,method=mode,replicate=r,archive=j,
                                error=est-e.true_effect,se=se,covered=abs(est-e.true_effect)<=Z*se))
                        fitted=fit_causal_atlas(archive,blind_target(g.target))
                        rows.append(dict(n=n,propensity=prop,method=mode,replicate=r,seed=sd,
                            error=abs(fitted.raw_point_estimate-g.target.true_effect),released=fitted.accepted,
                            covered=fitted.interval_lower<=g.target.true_effect<=fitted.interval_upper,
                            width=fitted.interval_upper-fitted.interval_lower,
                            bias_bound_status='known_propensity_zero_mean' if prop!='logistic' else 'uncertified_zero_plugin'))
                    except ValueError as ex:
                        if str(ex)!='arm_minimum':raise
                        failures.append(dict(n=n,propensity=prop,method=mode,replicate=r,reason=str(ex)))
            print('nuisance',n,prop,flush=True)
    save('nuisance_records',rows);save('nuisance_effect_records',effects);save('nuisance_failures',failures)


def dependence_experiment():
    rows=[]
    for surface in ('original','constant'):
        for ci,corr in enumerate((0,.3,.7)):
            for r in range(300):
                sd=seed(5,ci+(10 if surface=='constant' else 0),r);rng=np.random.default_rng(sd)
                g=generate_minimal_archive(seed=sd)
                sigma=.36*((1-corr)*np.eye(8)+corr*np.ones((8,8)))
                errors=rng.multivariate_normal(np.zeros(8),sigma)
                a=tuple(replace(e,estimated_effect=(e.true_effect if surface=='original' else 0)+errors[j],
                    standard_error_certificate=.6,true_effect=e.true_effect if surface=='original' else 0) for j,e in enumerate(g.archive))
                t=replace(g.target,true_effect=g.target.true_effect if surface=='original' else 0)
                config=AtlasConfig() if surface=='original' else AtlasConfig(effect_lipschitz_bound=1e-12,
                    effect_curvature_bound=1e-12,hidden_moderator_lipschitz_bound=0)
                fit=fit_causal_atlas(a,blind_target(t),config);w=fit.weights
                bias=fit.certificate.radius-fit.certificate.statistical_term
                estcov=np.cov(rng.multivariate_normal(np.zeros(8),sigma,40),rowvar=False)
                for name,mat in (('diagonal',np.diag(np.diag(sigma))),('known_covariance',sigma),('estimated_covariance',estcov)):
                    se=float(np.sqrt(w@mat@w));radius=bias+Z*se
                    error=abs(fit.raw_point_estimate-t.true_effect)
                    rows.append(dict(surface=surface,correlation=corr,method=name,replicate=r,
                        statistical_covered=abs(w@errors)<=Z*se,covered=error<=radius,width=2*radius,
                        error=error,released=bias+np.sqrt(2*np.log(40))*se<=1.65,se=se))
            print('dependence',surface,corr,flush=True)
    save('dependence_records',rows)


def constants_experiment():
    rows=[]
    for si,scenario in enumerate(('nominal','severe','proxy_understated')):
        for r in range(300):
            sd=seed(9,si,r)
            g=generate_minimal_archive(SimulationConfig(target_shift_fraction=.8 if scenario=='severe' else 0),seed=sd)
            if scenario=='proxy_understated':g=transform(g,proxy=True,rng=np.random.default_rng(sd+1))
            for factor in (.1,.25,.5,1,2):
                # Fixed estimator and weights: isolate radius choices, not optimization.
                fit=fit_causal_atlas(g.archive,blind_target(g.target))
                config=AtlasConfig(effect_lipschitz_bound=2.61*factor,effect_curvature_bound=1.8*factor,
                    hidden_moderator_lipschitz_bound=1.55*factor)
                c=compute_certificate(g.archive,blind_target(g.target),fit.weights,config)
                bias=c.radius-c.statistical_term
                se=np.sqrt(sum(w*w*e.standard_error_certificate**2 for w,e in zip(fit.weights,g.archive)))
                err=abs(fit.raw_point_estimate-g.target.true_effect)
                rows.append(dict(scenario=scenario,factor=factor,replicate=r,error=err,
                    released=c.radius<=1.65,covered=err<=bias+Z*se,width=2*(bias+Z*se),
                    certificate_violated=err>c.radius,score=fit.certificate.radius,
                    estimate=fit.raw_point_estimate,truth=g.target.true_effect))
        print('constants',scenario,flush=True)
    save('constant_records',rows)


def nsw_objects(x,t,y,pool,anchors,k):
    from .nsw_experiment import NswLocalContrast
    objects=[]
    for j,anchor in enumerate(anchors):
        ids=np.asarray(pool)[np.argsort(((x[pool]-x[anchor])**2).sum(1),kind='stable')[:k]]
        a=t[ids];yy=y[ids]
        if min(a.sum(),len(a)-a.sum())<8:raise ValueError('arm_minimum')
        context=x[ids].mean(0);effect=yy[a==1].mean()-yy[a==0].mean()
        se=np.sqrt(yy[a==1].var(ddof=1)/a.sum()+yy[a==0].var(ddof=1)/(len(a)-a.sum()))
        overlap=4*a.mean()*(1-a.mean());radius=np.sqrt(((x[ids]-context)**2).sum(1).mean())
        objects.append(NswLocalContrast(str(j),int(anchor),tuple(map(int,ids)),context,context[:6],
            np.r_[context,overlap,radius],float(effect),float(se),float(overlap),float(radius),int(a.sum()),int(len(a)-a.sum())))
    return objects


def nsw_stability():
    from .extension_nsw import read_data,scale_objects
    from .nsw_experiment import fit_nsw_method,NswExperimentConfig
    x,t,y=read_data(ROOT/'data/nsw_dw.dta');rows=[];failures=[];designs=[]
    for r in range(20):
        sd=seed(6,0,r);rng=np.random.default_rng(sd);source=[];ref=[]
        for arm in (0,1):
            ids=rng.permutation(np.flatnonzero(t==arm));cut=2*len(ids)//3
            source.extend(ids[:cut]);ref.extend(ids[cut:])
        source=np.array(source);ref=np.array(ref)
        # Source-only standardization, with target baseline covariates available.
        xx=(x-x[source].mean(0))/np.maximum(x[source].std(0),1e-8)
        norms=np.linalg.norm(xx,axis=1);eligible=np.flatnonzero(norms<=np.quantile(norms,.95))
        anchors=[int(eligible[r%len(eligible)])]
        while len(anchors)<30:
            distances=((xx[eligible,None]-xx[anchors][None,:])**2).sum(2).min(1)
            distances[np.isin(eligible,anchors)]=-1
            anchors.append(int(eligible[np.argmax(distances)]))
        random_anchors=rng.choice(eligible,30,replace=False)
        for name,aa in (('farthest',anchors),('random',random_anchors)):
            for k in (35,50,75):
                try:
                    a=nsw_objects(xx,t,y,source,aa[:24],k);targets=nsw_objects(xx,t,y,ref,aa[24:],k)
                    designs.append(dict(replicate=r,anchor=name,k=k,source=source.tolist(),reference=ref.tolist(),
                        source_anchors=list(map(int,aa[:24])),target_anchors=list(map(int,aa[24:])),
                        target_members=[list(q.neighborhood_rows) for q in targets]))
                    a,targets=scale_objects(a,targets)
                    base,_=archive_baselines(np.vstack([q.causal_representation for q in a]),
                        [q.estimated_effect for q in a],[q.standard_error for q in a],np.vstack([q.causal_representation for q in targets]))
                    for j,target in enumerate(targets):
                        fit=fit_nsw_method('atlas',a,replace(target,estimated_effect=float('nan'),standard_error=float('nan')),NswExperimentConfig())
                        predictions={'atlas':fit.predicted_effect,**{m:float(v[j]) for m,v in base.items()}}
                        for method,pred in predictions.items():
                            rows.append(dict(replicate=r,anchor=name,k=k,target=j,method=method,estimate=pred,
                                reference=target.estimated_effect,reference_se=target.standard_error,gap=pred-target.estimated_effect,
                                error=abs(pred-target.estimated_effect),released=fit.accepted if method=='atlas' else True,
                                width=fit.interval_upper-fit.interval_lower if method=='atlas' else float('nan'),
                                covered=fit.interval_lower<=target.estimated_effect<=fit.interval_upper if method=='atlas' else float('nan')))
                except ValueError as ex:
                    if str(ex)!='arm_minimum':raise
                    failures.append(dict(replicate=r,anchor=name,k=k,reason=str(ex)))
        print('NSW stability',r+1,flush=True)
    save('nsw_stability_records',rows);save('nsw_stability_failures',failures)
    (OUT/'nsw_stability_designs.json').write_text(json.dumps(designs,indent=2)+'\n')


def hillstrom():
    from .nsw_experiment import NswLocalContrast,fit_nsw_method,NswExperimentConfig
    from .extension_nsw import scale_objects
    path=ROOT/'data/external/hillstrom.csv';frame=pd.read_csv(path)
    provenance=json.loads((path.parent/'hillstrom_provenance.json').read_text())
    assert hashlib.sha256(path.read_bytes()).hexdigest()==provenance['sha256']
    frame=frame[frame.segment.isin(['Mens E-Mail','No E-Mail'])].copy()
    frame['cell']=(np.minimum((frame.recency.to_numpy()-1)//4,2)*8+frame.mens*4+frame.womens*2+frame.newbie).astype(int)
    cov=['recency','history','mens','womens','newbie']
    xx=frame[cov].to_numpy(float);xx[:,1]=np.log1p(xx[:,1]);a=(frame.segment=='Mens E-Mail').to_numpy(int)
    rows=[];design=[];loo_records=[]
    for outcome in ('visit','conversion'):
        y=frame[outcome].to_numpy(float)*100 # percentage points
        objects=[]
        for cell in sorted(frame.cell.unique()):
            ids=np.flatnonzero(frame.cell.to_numpy()==cell);t=a[ids];yy=y[ids]
            if min(t.sum(),len(t)-t.sum())<8:raise ValueError('Hillstrom arm minimum')
            center=xx[ids].mean(0);effect=yy[t==1].mean()-yy[t==0].mean()
            se=np.sqrt(yy[t==1].var(ddof=1)/t.sum()+yy[t==0].var(ddof=1)/(len(t)-t.sum()))
            objects.append(NswLocalContrast(str(cell),int(ids[0]),tuple(map(int,ids)),center,center,
                center,float(effect),float(se),float(4*t.mean()*(1-t.mean())),0.,int(t.sum()),int(len(t)-t.sum())))
            design.append(dict(outcome=outcome,cell=int(cell),n=len(ids),treated=int(t.sum()),reference_se=se,
                original_rows=frame.index.to_numpy()[ids].tolist()))
        for j,target in enumerate(objects):
            sources=[o for i,o in enumerate(objects) if i!=j]
            src,tt=scale_objects(sources,[target]);tt=tt[0]
            base,_=archive_baselines(np.vstack([q.causal_representation for q in src]),
                [q.estimated_effect for q in src],[q.standard_error for q in src],tt.causal_representation)
            # Nested source-only LOO prediction errors: target outcome never calibrates.
            residual={m:[] for m in ('atlas','ivw_meta','ridge_meta_regression','rbf_kernel_ridge','full_nearest')}
            for h,hold in enumerate(sources):
                inner=[o for i,o in enumerate(sources) if i!=h];ii,hh=scale_objects(inner,[hold]);hh=hh[0]
                bb,_=archive_baselines(np.vstack([q.causal_representation for q in ii]),
                    [q.estimated_effect for q in ii],[q.standard_error for q in ii],hh.causal_representation)
                ff=fit_nsw_method('atlas',ii,replace(hh,estimated_effect=float('nan'),standard_error=float('nan')),NswExperimentConfig())
                pp={'atlas':ff.predicted_effect,**{m:float(v[0]) for m,v in bb.items()}}
                for method in residual:
                    residual[method].append(abs(pp[method]-hold.estimated_effect))
                    loo_records.append(dict(outcome=outcome,target=target.object_id,source_holdout=hold.object_id,
                        method=method,residual=abs(pp[method]-hold.estimated_effect)))
            fit=fit_nsw_method('atlas',src,replace(tt,estimated_effect=float('nan'),standard_error=float('nan')),NswExperimentConfig())
            pp={'atlas':fit.predicted_effect,**{m:float(v[0]) for m,v in base.items()}}
            for method in residual:
                for level in (.9,.95):
                    radius=finite_quantile(residual[method],level)
                    rows.append(dict(outcome=outcome,target=target.object_id,method=method,interval='source_loo_empirical',level=level,
                        estimate=pp[method],reference=target.estimated_effect,reference_se=target.standard_error,
                        gap=pp[method]-target.estimated_effect,error=abs(pp[method]-target.estimated_effect),
                        width=2*radius,covered=abs(pp[method]-target.estimated_effect)<=radius,released=True))
            for factor in (.5,1,2):
                c=NswExperimentConfig(causal_effect_scale=.8*factor)
                ff=fit_nsw_method('atlas',src,replace(tt,estimated_effect=float('nan'),standard_error=float('nan')),c)
                rows.append(dict(outcome=outcome,target=target.object_id,method='atlas',interval='native_factor_'+str(factor),level=.95,
                    estimate=ff.predicted_effect,reference=target.estimated_effect,reference_se=target.standard_error,
                    gap=ff.predicted_effect-target.estimated_effect,error=abs(ff.predicted_effect-target.estimated_effect),
                    width=ff.interval_upper-ff.interval_lower,covered=ff.interval_lower<=target.estimated_effect<=ff.interval_upper,
                    released=ff.accepted))
            print('Hillstrom',outcome,j+1,len(objects),flush=True)
    save('hillstrom_records',rows);save('hillstrom_loo_records',loo_records)
    (OUT/'hillstrom_design.json').write_text(json.dumps(design,indent=2)+'\n')


def bridge_stability():
    from .extension_bridge import bridge_checks
    records,sets,failures=bridge_checks(12,8192,128)
    save('bridge_checks_8192',records);save('bridge_sets_8192',sets);save('bridge_failures_8192',failures)
    edges=[]
    for draws,path in ((2048,ROOT/'results/extensions/bridge_set_values.csv'),(8192,OUT/'bridge_sets_8192.csv')):
        df=pd.read_csv(path)
        for (scenario,rep,family),group in df.groupby(['scenario','replicate','family']):
            values=group.set_index('mask').reference_value
            for mask in range(64):
                for j in range(6):
                    if not mask&(1<<j):
                        edges.append(dict(draws=draws,scenario=scenario,replicate=rep,family=family,mask=mask,bridge=j,
                            gain=values[mask|(1<<j)]-values[mask]))
    save('bridge_edge_records',edges)
