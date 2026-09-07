"""Build the approved five-part appendix from committed evidence, without resampling."""
from pathlib import Path
import hashlib
import json
import re
import subprocess

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PAPER = ROOT / 'docs/paper/overleaf/01_causal_atlas_bridge.tex'
TABLES = PAPER.parent / 'experiments/causal_atlas_bridge/tables'
TEMPLATE = ROOT / 'docs/paper/appendix_B_template.tex'
EVIDENCE = ROOT / 'results/validation_v3'
BASE = 'cccf750'
START = r'\section{Appendix: Experimental Details}'
END = r'\begin{thebibliography}'
used_sources = set()
generated = []


def read(name, directory=EVIDENCE):
    path = directory / (name + '.csv')
    used_sources.add(path)
    return pd.read_csv(path)


def num(value):
    if pd.isna(value):
        return '--'
    if np.isinf(value):
        return r'$\infty$'
    return f'{value:.3f}'


def row(frame, **query):
    for key, value in query.items():
        frame = frame[frame[key] == value]
    assert len(frame) == 1, (query, len(frame))
    return frame.iloc[0]


def table(name, label, caption, headers, rows, note):
    columns = 'l' + 'r' * (len(headers) - 1)
    content = '\n'.join([
        '% Generated from committed CSV records by restructure_appendix_b.py.',
        r'\begin{table}[htbp]', r'\centering\small',
        r'\setlength{\tabcolsep}{4pt}',
        r'\caption{' + caption + '}', r'\label{' + label + '}',
        r'\begin{tabular}{' + columns + '}', r'\toprule',
        ' & '.join(headers) + r' \\', r'\midrule',
        *[' & '.join(str(x) for x in values) + r' \\' for values in rows],
        r'\bottomrule', r'\end{tabular}',
        r'\par\smallskip\begin{minipage}{0.97\linewidth}\footnotesize ' + note + r'\end{minipage}',
        r'\end{table}', '',
    ])
    path = TABLES / (name + '.tex')
    path.write_text(content, encoding='utf-8', newline='\n')
    generated.append(path)


def build_tables():
    methods = ['atlas', 'ivw_meta', 'full_nearest', 'ridge_meta_regression', 'rbf_kernel_ridge']
    names = dict(zip(methods, ['ATLAS', 'IVW', 'Nearest', 'Ridge', 'RBF']))
    surfaces = ['original', 'affine', 'friedman2', 'oscillatory', 'threshold']
    df = read('mechanism_summary')
    rows = []
    for surface in surfaces:
        a = row(df, surface=surface, change='baseline', method='atlas')
        rows.append([surface.capitalize(), *[num(row(df, surface=surface, change='baseline', method=m).error) for m in methods], num(a.covered), num(a.width)])
    table('app_b_surfaces', 'tab:b-surfaces', 'Baseline performance across effect surfaces.',
          ['Surface', *[names[m] for m in methods], 'Cov.', 'Width'], rows,
          'First five numerical columns are all-target MAE on 100 paired draws per surface. '
          r'Coverage and width refer only to the ATLAS nominal 95\% Gaussian bias-aware interval. '
          'All methods use observed representations. New surfaces retain uncertified original constants; '
          'complete Monte Carlo errors and perturbations are archived.')

    df = read('nuisance_effect_summary')
    complete = read('nuisance_summary')
    rows = []
    mode_names = {'oracle': 'Oracle', 'linear_known': 'Linear', 'quadratic_known': 'Quadratic',
                  'logistic_fitted': 'Logistic fit', 'intercept_misspecified': 'Intercept fit'}
    for n, propensity in [(400, 'balanced'), (400, 'logistic'), (100, 'weak'), (400, 'weak')]:
        modes = ['oracle', 'logistic_fitted', 'intercept_misspecified'] if propensity == 'logistic' else ['oracle', 'linear_known', 'quadratic_known']
        for method in modes:
            a = row(df, n=n, propensity=propensity, method=method)
            count = int(row(complete, n=n, propensity=propensity, method=method).replications)
            rows.append([str(n), propensity.capitalize(), mode_names[method], f'{count}/200',
                         num(a.rmse) if count > 2 else '--', num(a.coverage) if count > 2 else '--'])
    table('app_b_nuisance', 'tab:b-nuisance', 'Fitted nuisance functions: completion and experiment-level accuracy.',
          ['$n$', 'Assignment', 'Fit', 'Complete', 'RMSE', 'Cov.'], rows,
          r'Coverage is for ordinary 95\% experiment-level intervals. Accuracy is conditional on a complete '
          'eight-experiment archive; partial failures are excluded from accuracy summaries and saved separately. '
          'The two surviving quadratic-fit archives at small n are too few for a stable performance summary. '
          'Balanced and weak assignment probabilities are 0.5 and 0.1; logistic assignment is expit(2X).')

    df = read('dependence_summary')
    rows = []
    for rho in [0, .3, .7]:
        for method, name in [('diagonal', 'Diagonal'), ('known_covariance', 'Known covariance'), ('estimated_covariance', 'Estimated covariance')]:
            a = row(df, surface='constant', correlation=rho, method=method)
            rows.append([str(rho), name, num(a.covered), num(a.width)])
    table('app_b_dependence', 'tab:b-dependence', 'Dependence diagnostic on a constant effect surface.',
          [r'$\rho$', 'Variance rule', 'Coverage', 'Width'], rows,
          r'Each setting has 300 paired archives. Nominal coverage is 95\%. All three rules use identical point weights. '
          'Estimated covariance uses 40 independent calibration noise vectors. Constant effects isolate the statistical component.')

    df = read('constant_summary')
    rows = []
    for scenario, name in [('nominal', 'Nominal'), ('severe', 'Severe'), ('proxy_understated', 'Proxy understated')]:
        for factor in [.1, .25, .5, 1, 2]:
            a = row(df, scenario=scenario, factor=factor)
            rows.append([name, str(factor), num(a.covered), num(a.width), num(a.released)])
    table('app_b_constants', 'tab:b-constants', 'Joint scientific-constant sensitivity with fixed point weights.',
          ['Scenario', 'Factor', 'Coverage', 'Width', 'Release'], rows,
          'All multipliers and all 300 archives per scenario are retained. L, H and the hidden bound are scaled jointly. '
          'Coverage and width use all targets, including rejected ones. These results do not certify unknown scientific constants.')

    df = read('interval_summary')
    rows = []
    for scenario, name in [('nominal', 'Nominal'), ('moderate', 'Moderate'), ('severe', 'Severe'), ('high_noise', 'High noise')]:
        settings = [('native_bias_aware', 'none', 'Native'), ('historical_noisy_reference', scenario, 'Matched history')]
        if scenario != 'nominal':
            settings.append(('historical_noisy_reference', 'nominal', 'Nominal history'))
        for interval, calibration, policy in settings:
            a = row(df, scenario=scenario, method='atlas', interval=interval, calibration=calibration, level=.95)
            rows.append([name, policy, num(a.covered), num(a.reference_included), num(a.width)])
    table('app_b_calibration', 'tab:b-calibration', r'ATLAS interval calibration and transfer at nominal 95\% confidence.',
          ['Test scenario', 'Interval', 'True cov.', 'Ref. incl.', 'Width'], rows,
          'Each test scenario has 300 independent archives. Historical intervals use 150 independent noisy reference '
          'estimates from the stated calibration scenario. True coverage and noisy-reference inclusion are evaluated separately. '
          'Native intervals use Gaussian quantiles and approximation terms; historical intervals have additional data access.')

    df = read('selection_rank_bootstrap')
    rows = []
    for scenario, name in [('nominal', 'Nominal'), ('moderate', 'Moderate'), ('severe', 'Severe'), ('high_noise', 'High noise')]:
        for method in methods:
            a = row(df, scenario=scenario, fraction=.5, method=method)
            interval = f'$[{a.paired_low:.4f}, {a.paired_high:.4f}]$' if method in methods[-2:] else '--'
            difference = f'${a.difference_vs_atlas:.4f}$' if method in methods[-2:] else '--'
            rows.append([name, names[method], num(a.mae), difference, interval])
    table('app_b_selection', 'tab:b-selection', r'Method comparison at a common 50\% release fraction.',
          ['Scenario', 'Method', 'MAE', r'$\Delta$ vs. ATLAS', r'95\% interval'], rows,
          'All five methods select 150 of the same 300 targets using source-derived scores. '
          'Regressor-minus-ATLAS differences use 1,000 paired bootstrap samples with re-ranking inside each sample. '
          'The selected cohorts can differ by method. Remaining release fractions and all-method uncertainty are archived.')

    df = read('formal_experiment_summary', ROOT / 'results')
    rows = []
    for key, name in [('atlas', 'ATLAS'), ('atlas_no_variance_penalty', 'No variance penalty'), ('atlas_top4_candidates', 'Top-4 candidates')]:
        a = row(df, scenario_key='nominal', estimator_key=key)
        rows.append([name, num(a.acceptance_rate), f'{a.accepted_mae:.3f} ({a.accepted_mae_mc_se:.3f})', num(a.mean_interval_width)])
    table('app_b_ablation', 'tab:b-ablation', 'Nominal component ablations under the original formal-stage protocol.',
          ['Method', 'Release', 'Released MAE (MC SE)', 'Width'], rows,
          'Each row uses the same 300 formal-stage draws. MAE conditions on release; width follows the original '
          'all-target interval summary. This homoskedastic setting has equal hidden radii.')

    df = read('nsw_stability_summary')
    rows = []
    for anchor in ['farthest', 'random']:
        for k in [35, 50, 75]:
            a = row(df, anchor=anchor, k=k, method='atlas')
            rows.append([anchor.capitalize(), str(k), f'{int(a.replications)}/20', num(a.error), num(a.released), num(a.covered), num(a.width)])
    table('app_b_nsw_stability', 'tab:b-nsw-stability', 'NSW disjoint-unit design sensitivity for ATLAS.',
          ['Anchors', '$k$', 'Valid', 'MAE', 'Release', 'Ref. incl.', 'Width'], rows,
          'Errors and widths are in thousands of dollars. Statistics condition on valid designs; eight of 120 attempts fail '
          'arm minima. Splits reuse the same individuals, so they measure design sensitivity, not independent-sample uncertainty. '
          'Neighbor size changes the reference estimand as well as precision.')

    df = read('hillstrom_summary')
    rows = []
    for method in methods:
        rows.append([names[method], *[num(row(df, outcome=o, method=method, interval='source_loo_empirical', level=.9).error) for o in ['visit', 'conversion']]])
    table('app_b_hillstrom_error', 'tab:b-hillstrom-error', 'Hillstrom all-cell prediction error against randomized references.',
          ['Method', 'Visit MAE', 'Conversion MAE'], rows,
          'MAE is in percentage points across all 18 held-out cells, without rejection. Visit is the primary outcome. '
          'Both outcomes use source-only preprocessing and tuning; subgroup references have sampling noise.')

    rows = []
    for outcome in ['visit', 'conversion']:
        for factor in ['0.5', '1', '2']:
            a = row(df, outcome=outcome, method='atlas', interval='native_factor_' + factor, level=.95)
            rows.append([outcome.capitalize(), factor, num(a.covered), num(a.width), num(a.released)])
    table('app_b_hillstrom_interval', 'tab:b-hillstrom-interval', 'Hillstrom ATLAS interval sensitivity.',
          ['Outcome', 'Factor', 'Ref. incl.', 'Width', 'Release'], rows,
          'Widths are in percentage points and inclusion is against noisy references across all 18 targets. '
          'The factor scales the existing workflow effect-scale constant; these values are not externally certified. '
          r'The separate 95\% source-LOO residual intervals are infinite for every method because only 17 residuals are available.')

    df = read('bridge_checks_8192')
    df = df[df.family == 'retained_certificates']
    rows = []
    for budget, group in df.groupby('budget'):
        assert group.bound_holds.all() and (group.lower_bound > 0).all()
        rows.append([str(budget), str(len(group)), f'{group.selected_value.mean():.4f}',
                     f'{group.optimum.mean():.4f}', f'{group.lower_bound.mean():.4f}'])
    table('app_b_bridge_retained', 'tab:ext-retained', 'Retained-certificate bridge diagnostic under a fixed planning law.',
          ['Budget', 'Archives', 'Greedy value', 'Best fixed set', 'Lower bound'], rows,
          'Entries are means across 24 archives. All 72 budget-specific checks have gamma=1, '
          'positive lower bounds, and greedy value at least the bound. Reference and planning samples have '
          '8,192 and 128 draws. This is a separate fixed-certificate objective; the table does not establish adaptive-policy optimality.')


def slice_between(source, start, end):
    return source[source.index(start):source.index(end)]


def main():
    build_tables()
    rel = PAPER.relative_to(ROOT).as_posix()
    baseline = subprocess.check_output(['git', 'show', f'{BASE}:{rel}'], cwd=ROOT).decode('utf-8').replace('\r\n', '\n')
    current = PAPER.read_text(encoding='utf-8')
    dgp = slice_between(baseline, r'\paragraph{Mechanisms and support.}', r'\subsection{Formal Stress Scenarios and Estimator Ablations}').strip()
    dgp = dgp.replace(
        'Before any performance comparison, the implementation validates the five conditions used by the theory.',
        'Before performance comparisons, the implementation checks the declared data-generating conditions.')
    dgp = dgp.replace(
        'Independent archive random streams, the AIPW score variance, and zero oracle-nuisance remainder instantiate the uncertainty certificate in Assumption~3.4.',
        'Archive random streams are independent and the oracle nuisance remainder is zero. The stored score variance is a plug-in estimate; the reported numerical checks do not establish a finite-sample sub-Gaussian proxy certificate for that estimate.')
    dgp = dgp.replace(
        'These checks validate the declared simulation model; they are not additional evidence about estimator performance.',
        'These checks document the declared simulation model. Performance and interval calibration are evaluated separately.')
    semi = slice_between(baseline, 'We retain the covariates, disjoint pools and anchors,', 'The summary-data comparators follow').strip()
    appendix = TEMPLATE.read_text(encoding='utf-8').replace('@@ORIGINAL_DGP@@', dgp).replace('@@NSW_SEMISYNTHETIC_PROTOCOL@@', semi)
    # Inline only the new tables so Overleaf needs a single source edit.
    for path in generated:
        marker = r'\input{' + path.relative_to(PAPER.parent).as_posix() + '}'
        assert appendix.count(marker) == 1
        appendix = appendix.replace(marker, path.read_text(encoding='utf-8').strip())
    prefix = current[:current.index(START)]
    substitutions = {
        r'Appendix~\ref{app:formal-ablations} (B.2)': r'Appendix~\ref{app:formal-ablations}',
        r'A separate target-level certificate diagnostic is reported in Appendix Figure~\ref{fig:v1-app-certificate-diagnostic};': r'A separate target-level certificate diagnostic is summarized in Appendix~\ref{app:certificate-calibration};',
        r'Tables~\ref{tab:ext-baselines}--\ref{tab:ext-paired}': r'Table~\ref{tab:ext-baselines}',
        r'(Appendix Table~\ref{tab:v1-app-bridge-all})': r'(Appendix~\ref{app:bridge-design})',
        'The results therefore support the practical behavior of the framework while leaving external validity, alternative neighborhood definitions, and nuisance-estimation uncertainty for future work.':
        r'Appendices~\ref{app:robustness} and~\ref{app:nsw-details} examine fitted nuisance functions, alternative neighborhood definitions, and a second randomized trial; external validity across independent studies remains open.',
    }
    for old, new in substitutions.items():
        assert old in prefix or new in prefix, old
        prefix = prefix.replace(old, new)
    updated = prefix + appendix + '\n' + current[current.index(END):]
    protected = [(r'\documentclass', r'\section{Experiments:'),
                 (r'\section{Discussion}', START)]
    hashes = {}
    for start, end in protected:
        block = slice_between(current, start, end)
        assert block == slice_between(updated, start, end), start
        hashes[start] = hashlib.sha256(block.encode()).hexdigest()
    assert current[current.index(END):] == updated[updated.index(END):]
    assert len(re.findall(r'\\subsection\{', appendix)) == 5
    assert '@@' not in appendix
    PAPER.write_text(updated, encoding='utf-8', newline='\n')
    staging = ROOT / 'results/appendix_b_build'
    staging.mkdir(parents=True, exist_ok=True)
    (staging / 'baseline.txt').write_text(baseline, encoding='utf-8', newline='\n')
    (staging / 'updated.txt').write_text(updated, encoding='utf-8', newline='\n')
    (staging / 'appendix.txt').write_text(appendix, encoding='utf-8', newline='\n')
    dependencies = used_sources | {TEMPLATE, Path(__file__)}
    manifest = {
        'base_commit': BASE,
        'source': rel,
        'protected_normalized_sha256': hashes,
        'appendix_A_sha256': hashlib.sha256(slice_between(updated, r'\section{Appendix: Notation and Proofs}', START).encode()).hexdigest(),
        'source_sha256': hashlib.sha256(PAPER.read_bytes()).hexdigest(),
        'dependencies': {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(dependencies)},
        'generated_tables': {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in generated},
        'appendix_subsections': re.findall(r'\\subsection\{([^}]+)\}', appendix),
        'old_input_tables': baseline[baseline.index(START):baseline.index(END)].count(r'\input{'),
        'new_input_tables': appendix.count(r'\input{'),
        'new_inline_tables': appendix.count(r'\begin{table}'),
        'new_figures': appendix.count(r'\includegraphics'),
        'note': 'Only Appendix B and necessary experimental cross-references are revised. No experimental resampling or theory edits.',
    }
    path = ROOT / 'docs/paper/revision_evidence/appendix_B_restructure.json'
    path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({k: v for k, v in manifest.items() if k not in ['dependencies', 'generated_tables']}, indent=2))


if __name__ == '__main__':
    main()
