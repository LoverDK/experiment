"""Summarize saved v3 records; no experiment generation or outcome-based tuning."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/validation_v3'

def read(name):return pd.read_csv(OUT/(name+'.csv'))
def write(name,rows):pd.DataFrame(rows).to_csv(OUT/(name+'.csv'),index=False)

def ratio_se(df,value,select):
    x=df[value].astype(float);w=select.astype(float);ratio=(x*w).sum()/w.sum() if w.sum() else np.nan
    influence=(x-ratio)*w
    grouped=pd.DataFrame({'influence':influence,'weight':w,'cluster':df.replicate}).groupby('cluster').sum()
    # Ratio of sums, equally weighted independent replicate clusters.
    se=grouped.influence.std(ddof=1)/np.sqrt(len(grouped))/grouped.weight.mean() if w.sum() and len(grouped)>1 else np.nan
    return ratio,se

def summarize(name,keys,real=False):
    df=read(name);rows=[]
    for key,g in df.groupby(keys,dropna=False):
        if not isinstance(key,tuple):key=(key,)
        row=dict(zip(keys,key));row['n_records']=len(g);row['replications']=g.replicate.nunique() if 'replicate' in g else np.nan
        selected=g.released.fillna(False).astype(bool) if 'released' in g else pd.Series(True,index=g.index)
        for col in ('error','width','covered','statistical_covered','released','certificate_violated','reference_included','gap','se'):
            if col not in g:continue
            x=pd.to_numeric(g[col],errors='coerce');row[col]=x.mean()
            if 'replicate' in g:
                means=x.groupby(g.replicate).mean();row[col+('_split_sd' if real else '_mcse')]=means.std(ddof=1)/(1 if real else np.sqrt(len(means)))
        row['release_count']=int(selected.sum())
        for col in ('error','covered','width'):
            if col not in g:continue
            row['released_'+col]=pd.to_numeric(g.loc[selected,col],errors='coerce').mean()
            if not real and 'replicate' in g and g[col].notna().all():
                _,se=ratio_se(g,col,selected);row['released_'+col+'_mcse']=se
        rows.append(row)
    write(name.replace('_records','_summary'),rows)

def rank_bootstrap():
    df=read('selection_predictions');df=df[df.part=='test'];rows=[]
    for si,(scenario,g) in enumerate(df.groupby('scenario')):
        errors=g.pivot(index='replicate',columns='method',values='error')
        scores=g.pivot(index='replicate',columns='method',values='score')[errors.columns]
        e=errors.to_numpy();s=scores.to_numpy();rng=np.random.default_rng(2026090731+si)
        for fraction in (.25,.5,.75,1.):
            k=round(len(e)*fraction);order=np.argsort(s,axis=0,kind='stable')[:k]
            point=np.take_along_axis(e,order,axis=0).mean(0);boot=[]
            for _ in range(1000):
                ids=rng.integers(0,len(e),len(e));ee=e[ids];ss=s[ids]
                chosen=np.argsort(ss,axis=0,kind='stable')[:k]
                boot.append(np.take_along_axis(ee,chosen,axis=0).mean(0))
            boot=np.array(boot);ai=list(errors.columns).index('atlas')
            for j,method in enumerate(errors.columns):
                diff=boot[:,j]-boot[:,ai];lo,hi=np.quantile(diff,[.025,.975])
                rows.append(dict(scenario=scenario,fraction=fraction,method=method,mae=point[j],
                    bootstrap_se=boot[:,j].std(ddof=1),difference_vs_atlas=point[j]-point[ai],paired_low=lo,paired_high=hi))
    write('selection_rank_bootstrap',rows)

def main():
    summarize('selection_records',['scenario','method','calibration','rule','fraction'])
    summarize('interval_records',['scenario','method','calibration','interval','level'])
    summarize('mechanism_records',['surface','change','method'])
    summarize('nuisance_records',['n','propensity','method'])
    effects=read('nuisance_effect_records');out=[]
    for key,g in effects.groupby(['n','propensity','method']):
        means=g.groupby('replicate').error.mean()
        out.append(dict(zip(['n','propensity','method'],key))|dict(n_effects=len(g),bias=g.error.mean(),
            bias_mcse=means.std(ddof=1)/np.sqrt(len(means)),rmse=np.sqrt(np.mean(g.error**2)),
            coverage=g.covered.mean(),mean_se=g.se.mean()))
    write('nuisance_effect_summary',out)
    summarize('dependence_records',['surface','correlation','method'])
    summarize('constant_records',['scenario','factor'])
    summarize('nsw_stability_records',['anchor','k','method'],real=True)
    summarize('hillstrom_records',['outcome','method','interval','level'],real=True)
    edges=read('bridge_edge_records');out=[]
    for key,g in edges.groupby(['draws','scenario','family']):
        out.append(dict(zip(['draws','scenario','family'],key))|dict(n_edges=len(g),
            minimum_gain=g.gain.min(),mean_negative_magnitude=-g.loc[g.gain< -1e-9,'gain'].mean(),
            negative_fraction=(g.gain< -1e-9).mean(),archives_with_negative=int(g.groupby('replicate').gain.min().lt(-1e-9).sum())))
    write('bridge_edge_summary',out)
    x=edges.pivot(index=['scenario','replicate','family','mask','bridge'],columns='draws',values='gain').reset_index()
    write('bridge_stability_summary',[dict(family=family,negative_sign_agreement=np.mean((g[2048]<-1e-9)==(g[8192]<-1e-9)),
        max_absolute_gain_change=np.max(np.abs(g[8192]-g[2048]))) for family,g in x.groupby('family')])
    cal=read('selection_predictions');cal=cal[(cal.part=='calibration')&(cal.scenario=='nominal')&(cal.method=='atlas')]
    values=np.sort(np.abs(cal.estimate-cal.reference)/cal.score);q=values[int(np.ceil((len(values)+1)*.95))-1]
    c=read('constant_records');c=c[c.factor==1].copy();c['width']=2*q*c.score;c['covered']=c.error<=q*c.score
    write('constant_nominal_calibration_records',c)
    summarize('constant_nominal_calibration_records',['scenario'])
    rank_bootstrap()
    # A searchable Markdown companion includes every summary row.
    lines=['# Validation v3 numerical tables','',
        'Simulation MC SE clusters by independent replicate. NSW split SD is design sensitivity.',
        'Hillstrom and NSW references are noisy observed contrasts. No latent-effect coverage claim.',
        'Cohort-rank SE uses 1,000 paired bootstrap resamples and recomputes ranks in each resample.','']
    for p in sorted(OUT.glob('*summary.csv')):
        df=pd.read_csv(p);lines.extend(['## '+p.stem,'','```csv',df.to_csv(index=False).strip(),'```',''])
    (ROOT/'docs/paper/validation_v3_tables.md').write_text('\n'.join(lines),encoding='utf8')
    print('Built v3 summaries, paired rank bootstrap and numerical tables.')

if __name__=='__main__':main()
