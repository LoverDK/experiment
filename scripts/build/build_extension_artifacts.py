"""Build extension summaries and paper assets only from saved v2 records."""
from pathlib import Path
import hashlib
import json
import sys
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from causal_atlas_sim.figure_style import apply_publication_style, finalize_figure, PALETTE
from causal_atlas_sim.extension_bridge import audit_set_function
import matplotlib.pyplot as plt

OUT = ROOT / 'results/extensions'
ASSETS = ROOT / 'docs/paper/overleaf/experiments/causal_atlas_bridge'
NAMES = {'atlas_no_rejection': 'ATLAS, no rejection', 'semantic_forced': 'Semantic forced',
         'ivw_meta': 'Inverse-variance pooling', 'random_effects_meta': 'Random-effects pooling',
         'full_nearest': 'Full-representation nearest', 'ridge_meta_regression': 'Ridge meta-regression',
         'rbf_kernel_ridge': 'RBF kernel ridge', 'unit_ridge_t_learner': 'Unit-data ridge T-learner'}
SCENARIOS = ['nominal', 'moderate', 'severe', 'high_noise']
SURFACES = ['constant', 'smooth', 'interaction']


def meanse(x):
    x = np.asarray(x, float)
    return float(np.mean(x)), float(np.std(x, ddof=1) / np.sqrt(len(x)))


def fmt(row, key='mae'):
    return f"{row[key]:.3f} ({row[key+'_mcse']:.3f})"


def table(name, label, caption, headers, rows, note=''):
    content = '\n'.join([r'\begin{table}[htbp]', r'\centering\small',
        r'\setlength{\tabcolsep}{4pt}', r'\caption{'+caption+'}', r'\label{'+label+'}',
        r'\begin{tabular}{l'+'r'*(len(headers)-1)+'}', r'\toprule',
        ' & '.join(headers)+r' \\', r'\midrule',
        *(' & '.join(row)+r' \\' for row in rows), r'\bottomrule', r'\end{tabular}',
        (r'\par\smallskip\begin{minipage}{0.97\linewidth}\footnotesize '+note+r'\end{minipage}' if note else ''),
        r'\end{table}', ''])
    (ASSETS/'tables'/name).write_text(content, encoding='utf-8')


def main():
    syn = pd.read_csv(OUT/'synthetic_baselines_records.csv')
    semi = pd.read_csv(OUT/'nsw_semisynthetic_records.csv')
    real = pd.read_csv(OUT/'nsw_real_records.csv')
    bridge = pd.read_csv(OUT/'bridge_checks.csv')
    sets = pd.read_csv(OUT/'bridge_set_values.csv')
    assert len(syn)==9600 and len(semi)==16200 and len(sets)==3072
    design = json.loads((OUT/'nsw_design.json').read_text())
    assert not set(design['source_units']) & set(design['reference_units'])
    # Verify the new nominal run exactly reproduces the prior common-target records.
    old = pd.read_csv(ROOT/'results/certificate_diagnostics_summary.csv')
    for method in ('atlas', 'semantic_forced'):
        joined = syn[(syn.scenario=='nominal') & (syn.method==method)].merge(old, on='seed')
        assert len(joined)==300
        np.testing.assert_allclose(joined.absolute_error, joined[method+'_absolute_error'], atol=1e-12)
    for keys, group in sets.groupby(['scenario','replicate','family']):
        g = group.sort_values('mask')
        assert list(g['mask'])==list(range(64))
        for budget in (1,2,3):
            check = audit_set_function(g.reference_value.to_numpy(), g.planning_value.to_numpy(), budget)
            stored = bridge[(bridge.scenario==keys[0]) & (bridge.replicate==keys[1]) &
                            (bridge.family==keys[2]) & (bridge.budget==budget)].iloc[0]
            for key in ('gamma','epsilon','selected_value','optimum','lower_bound'):
                if check[key] is not None:
                    np.testing.assert_allclose(check[key],stored[key],rtol=1e-7,atol=1e-9)

    summary, paired = [], []
    for scenario, group in syn.groupby('scenario'):
        wide=group.pivot(index='seed',columns='method',values='absolute_error')
        for method, errors in wide.items():
            avg,se=meanse(errors)
            summary.append(dict(scenario=scenario,method=method,mae=avg,mae_mcse=se,n=len(errors)))
            d=errors-wide.atlas_no_rejection; avg,se=meanse(d)
            paired.append(dict(scenario=scenario,method=method,difference=avg,mcse=se,
                               lower=avg-1.96*se,upper=avg+1.96*se))
    summary=pd.DataFrame(summary); summary.to_csv(OUT/'synthetic_summary.csv',index=False)
    pd.DataFrame(paired).to_csv(OUT/'synthetic_paired_summary.csv',index=False)
    rows=[]
    for method,name in NAMES.items():
        if method=='unit_ridge_t_learner':continue
        rows.append([name]+[fmt(summary[(summary.method==method)&(summary.scenario==s)].iloc[0]) for s in SCENARIOS])
    table('app_stronger_baselines.tex','tab:ext-baselines',
          'Stronger summary-data baselines on 300 common targets per synthetic condition. Cells are all-target MAE (Monte Carlo SE).',
          ['Method','Nominal','Moderate','Severe','High noise'],rows,
          'All-target ATLAS uses the no-rejection point estimate. Every method uses the same draws; ridge and kernel tuning uses source outcomes only. Point-only baselines have no reported confidence interval.')
    paired_frame=pd.DataFrame(paired)
    table('app_stronger_paired.tex','tab:ext-paired',
          'Paired all-target MAE differences for the fitted regressors, relative to no-rejection ATLAS. Negative differences favor the comparator.',
          ['Condition','Comparator','Difference','MC SE',r'95\% MC interval'],
          [[s.replace('_',' ').title(),NAMES[m],f'{r.difference:.3f}',f'{r.mcse:.3f}',f'$[{r.lower:.3f}, {r.upper:.3f}]$']
           for s in SCENARIOS for m in ('ridge_meta_regression','rbf_kernel_ridge')
           for _,r in paired_frame[(paired_frame.scenario==s)&(paired_frame.method==m)].iterrows()])

    semi_summary=[]
    for (surface,method),group in semi.groupby(['surface','method']):
        avg,se=meanse(group.groupby('replicate').absolute_error.mean())
        semi_summary.append(dict(surface=surface,method=method,mae=avg,mae_mcse=se))
    semi_summary=pd.DataFrame(semi_summary);semi_summary.to_csv(OUT/'nsw_semisynthetic_summary.csv',index=False)
    table('app_nsw_semisynthetic.tex','tab:ext-semi',
          'NSW-covariate semi-synthetic validation against the exact target average effect. Cells are all-target MAE (Monte Carlo SE), in thousands of dollars.',
          ['Method','Constant','Smooth','Interaction'],
          [[name]+[fmt(semi_summary[(semi_summary.method==method)&(semi_summary.surface==s)].iloc[0]) for s in SURFACES]
           for method,name in NAMES.items()],
          'Each surface has 100 independent assignment/outcome replicates and six overlapping targets. MC SE uses the 100 replicate means. The T-learner has source individual data; the other methods have archive summaries. ATLAS raw point estimates equal its no-rejection counterpart.')
    calibration=[]
    for surface,group in semi[semi.method=='atlas'].groupby('surface'):
        r=dict(surface=surface)
        group=group.copy();group['width']=group.upper-group.lower
        release=group.groupby('replicate').released.mean()
        r['release'],r['release_mcse']=meanse(release)
        # Ratio estimators use a cluster influence-function SE (replicate = cluster).
        for key, column in [('mae','absolute_error'),('coverage','covered'),('width','width')]:
            per=group.assign(num=group[column].astype(float)*group.released).groupby('replicate').agg(num=('num','sum'),den=('released','sum'))
            value=per.num.sum()/per.den.sum()
            influence=(per.num-value*per.den)/per.den.mean()
            r[key]=float(value);r[key+'_mcse']=meanse(influence)[1]
        calibration.append(r)
    calibration=pd.DataFrame(calibration);calibration.to_csv(OUT/'nsw_calibration_summary.csv',index=False)
    table('app_nsw_calibration.tex','tab:ext-calibration',
          'ATLAS release and interval behavior in the semi-synthetic extension. Parentheses give Monte Carlo SE with assignment/outcome replicates as clusters.',
          ['Surface','Release','Released MAE','Coverage','Width'],
          [[s.title()]+[fmt(calibration[calibration.surface==s].iloc[0],k) for k in ('release','mae','coverage','width')] for s in SURFACES],
          'MAE, coverage of the known average effect, and width are conditional on release; release uses all targets. Existing NSW interval rules are evaluated empirically, without asserting new certified scientific bounds for these surfaces.')
    real_summary=[]
    for method,group in real.groupby('method'):
        boot=group[group.bootstrap>0].groupby('bootstrap').gap.mean()
        lo,hi=np.quantile(boot,[.025,.975]);original=group[group.bootstrap==0]
        real_summary.append(dict(method=method,gap=original.gap.mean(),lower=lo,upper=hi,
                                 valid_bootstraps=len(boot),release=original.released.mean()))
    real_summary=pd.DataFrame(real_summary);real_summary.to_csv(OUT/'nsw_real_summary.csv',index=False)
    table('app_nsw_reference.tex','tab:ext-reference',
          'Disjoint-unit NSW comparison: mean signed prediction-minus-randomized-reference gap across six targets, in thousands of dollars.',
          ['Method','Mean gap',r'95\% bootstrap interval'],
          [[name,f'{r.gap:.3f}',f'$[{r.lower:.3f}, {r.upper:.3f}]$'] for method,name in NAMES.items()
           for _,r in real_summary[real_summary.method==method].iterrows()],
          'Intervals use 196 valid stratified individual bootstrap replicates out of 200; four fail the minimum of eight units per arm. Source and reference individuals are disjoint, and overlapping local objects are rebuilt jointly. Gaps use all raw predictions. The real randomized reference is noisy; these intervals are descriptive bootstrap uncertainty under the fixed design.')
    bridge_summary=[]
    for (scenario,family),group in bridge.groupby(['scenario','family']):
        one=group[group.budget==1]
        bridge_summary.append(dict(scenario=scenario,family=family,archives=len(one),monotone=int(one.monotone.sum()),
            mean_violating_edges=float(one.monotonicity_violations.mean()),gamma=float(one.gamma.min()) if one.monotone.all() else None,
            epsilon=one.epsilon.mean(),eligible=int(group.lower_bound.notna().sum()),
            passed=int(group.bound_holds.eq(True).sum()),nonvacuous=int(group.vacuous.eq(False).sum())))
    bridge_summary=pd.DataFrame(bridge_summary);bridge_summary.to_csv(OUT/'bridge_summary.csv',index=False)
    table('app_bridge_conditions.tex','tab:ext-bridge',
          'Finite-law bridge diagnostics: 12 archives per condition, 64 subsets per archive, and budgets 1--3.',
          ['Condition / family','Monotone','Bad edges',r'$\gamma$',r'$\epsilon$','Checks'],
          [[r.scenario.title()+' / '+('operational' if r.family=='operational' else 'retained'),
            f'{r.monotone}/12',f'{r.mean_violating_edges:.1f}', '--' if pd.isna(r.gamma) else f'{r.gamma:.3f}',
            f'{r.epsilon:.4f}', '--' if not r.eligible else f'{r.passed}/{r.eligible}'] for _,r in bridge_summary.iterrows()],
          r'Bad edges is the mean count of negative singleton gains out of 192 edges. $\epsilon$ is the mean across archives of the maximum planning/reference marginal discrepancy. Checks are reported only for monotone objectives with positive $\gamma$; all 72 eligible bounds are positive. Retained certificates form a diagnostic variant, not the operational adaptive policy. No empty intersections occurred in the sampled evaluations.')

    retained=bridge[bridge.family=='retained_certificates']
    table('app_bridge_retained.tex','tab:ext-retained',
          'Coefficient consistency check for the retained-certificate diagnostic variant. Values are means over 12 archives per condition; the bound is evaluated separately for each archive.',
          ['Condition','Budget','Greedy value','Optimum','Lower bound','Checks'],
          [[s.title(),str(b),f'{g.selected_value.mean():.3f}',f'{g.optimum.mean():.3f}',
            f'{g.lower_bound.mean():.3f}',f'{int(g.bound_holds.eq(True).sum())}/{len(g)}']
           for (s,b),g in retained.groupby(['scenario','budget'])],
          r'This fixed-law variant keeps the original and candidate singleton certificates with one fixed Bonferroni allocation. Its sampled ratio is $\gamma=1$; the mean maximum marginal discrepancies are 0.0113 (moderate) and 0.0141 (severe). All displayed lower bounds are positive. These are internal checks against an enumerated Monte Carlo reference; they do not establish a guarantee for the operational adaptive policy.')

    apply_publication_style()
    fig,axes=plt.subplots(1,2,figsize=(11.5,4.5),gridspec_kw={'width_ratios':[1.08,1]})
    selected=['atlas_no_rejection','semantic_forced','ivw_meta','ridge_meta_regression','rbf_kernel_ridge','unit_ridge_t_learner']
    colors=[PALETTE[k] for k in ('blue_main','neutral','gold','green','violet','teal')]
    for i,(method,color) in enumerate(zip(selected,colors)):
        r=real_summary[real_summary.method==method].iloc[0]
        axes[0].plot([r.lower,r.upper],[i,i],color=color,lw=2)
        axes[0].scatter(r.gap,i,color=color,s=34,zorder=3)
        g=semi_summary[semi_summary.method==method].set_index('surface').loc[SURFACES]
        axes[1].errorbar(np.arange(3)+(i-2.5)*.07,g.mae,yerr=1.96*g.mae_mcse,
                         fmt='o',capsize=3,color=color,ms=5)
    axes[0].axvline(0,color='#999999',ls='--',lw=1)
    axes[0].set_yticks(range(len(selected)),[NAMES[m] for m in selected]);axes[0].invert_yaxis()
    axes[0].set_xlabel('Signed gap (thousand dollars)')
    axes[0].set_title('(a) Disjoint-unit real references',loc='left',fontweight='bold')
    axes[1].set_xticks(range(3),['Constant','Smooth','Interaction']);axes[1].set_ylabel('All-target MAE (thousand dollars)')
    axes[1].set_title('(b) Known-truth response surfaces',loc='left',fontweight='bold')
    for ax in axes:ax.grid(axis='x' if ax==axes[0] else 'y',color='#E8E8E8',lw=.7);ax.set_axisbelow(True)
    paths=finalize_figure(fig,ROOT/'results/figures/extension_nsw_validation')
    for p in paths:
        if p.suffix=='.pdf':(ASSETS/'figures'/p.name).write_bytes(p.read_bytes())

    manifest_paths=[*OUT.glob('*'),Path(__file__),ROOT/'docs/paper/extension_protocol_v2.md',
                    ROOT/'scripts/run/run_requested_extensions.py',* (ROOT/'src/causal_atlas_sim').glob('extension_*.py'),
                    * (ASSETS/'tables').glob('app_*baseline*.tex'),*(ASSETS/'tables').glob('app_stronger_paired.tex'),
                    *(ASSETS/'tables').glob('app_nsw_*synthetic.tex'),*(ASSETS/'tables').glob('app_nsw_calibration.tex'),
                    *(ASSETS/'tables').glob('app_nsw_reference.tex'),*(ASSETS/'tables').glob('app_bridge_conditions.tex'),
                    *(ASSETS/'tables').glob('app_bridge_retained.tex'),*paths]
    manifest={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(set(manifest_paths)) if p.is_file() and p.name!='artifact_manifest.json'}
    (OUT/'artifact_manifest.json').write_text(json.dumps({'sha256':manifest,'checks':{
        'nominal_matches_committed_target_records':True,'bridge_values_reproduce_all_144_checks':True,
        'source_reference_disjoint':True,'subset_extensions_per_archive':665,
        'synthetic_records':len(syn),'semisynthetic_records':len(semi)}},indent=2)+'\n')
    print(calibration.to_string(index=False));print(real_summary.to_string(index=False));print(bridge_summary.to_string(index=False))


if __name__=='__main__':main()
