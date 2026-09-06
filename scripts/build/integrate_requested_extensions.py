"""Idempotent, scoped integration of approved extension evidence into the paper."""
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]
PAPER=ROOT/'docs/paper/overleaf/01_causal_atlas_bridge.tex'


def integrate(source):
    if '% Approved extension integration' in source:
        return source
    def before(marker, block):
        nonlocal source
        assert source.count(marker)==1,marker
        source=source.replace(marker,block+'\n\n'+marker)

    before(r'\subsection{Selective Prediction and Honest Uncertainty}',r'''% Approved extension integration: common-target baselines.
The stronger summary-data comparison in Tables~\ref{tab:ext-baselines}--\ref{tab:ext-paired} evaluates inverse-variance pooling, random-effects pooling, full-representation nearest neighbor, ridge meta-regression, and RBF kernel ridge on the same targets. All-target MAE is $0.120$ for kernel ridge and $0.139$ for no-rejection ATLAS in the nominal condition. Under severe shift, ridge and kernel ridge attain $0.328$ and $0.396$, compared with $0.707$ for no-rejection ATLAS. ATLAS has the lowest mean point error among these methods in the high-noise condition. These results delimit the accuracy claim: enriched representations help relative to semantic retrieval, while flexible regressors can further reduce point error. The release and interval diagnostics assess additional properties of the atlas.''')

    before(r'\subsection{Real-Data NSW Archive}',r'''A separate retained-certificate variant checks the coefficient expression against an enumerated, frozen planning law (Appendix Table~\ref{tab:ext-retained}). This diagnostic keeps a fixed collection of constraints and a fixed confidence allocation. Its numerical checks concern that variant; applicability of the guarantee to the operational adaptive policy remains conditional on the theorem's assumptions.''')

    marker='Across the synthetic experiments, Causal ATLAS improves composition'
    index=source.index(marker)
    end=source.index('\n',index)
    source=source[:index]+r'''Two additional NSW checks address distinct sources of uncertainty (Appendix~\ref{app:nsw-details}). The first partitions individuals into disjoint source and reference pools before forming local objects. Across six targets, the all-target ATLAS prediction-minus-reference gap is $-0.670$ thousand dollars, with a descriptive 95\% bootstrap interval $[-3.978,3.032]$; the comparison is too imprecise to establish agreement. The second retains NSW covariates and simulates three response surfaces with known target average effects. Across 100 replicates per surface, ATLAS has all-target MAE $0.488$--$0.504$ thousand dollars, release $0.915$--$0.947$, and released-target coverage $0.995$--$0.998$, with mean width $4.248$--$4.373$. Several comparators achieve smaller point errors. This extension supplies a known-truth check of the existing NSW rules, with substantial interval conservatism.

Across the synthetic experiments, Causal ATLAS improves composition relative to semantic baselines when causal support is informative, exposes a transparent risk--coverage frontier, and protects interval validity when its declared uncertainty bounds are correct. When support is insufficient, it transitions to partial identification; bridge experiments shrink the resulting diameter in the reported policy experiments. The real NSW checks use noisy randomized contrasts, while the semi-synthetic extension evaluates known effects under three specified response surfaces.'''+source[end:]

    before(r'\subsection{Representation Sensitivity and One-Factor Robustness}',r'''\paragraph{Stronger archive baselines.}
We add five comparators using the full observed representation and the same source effects and standard errors. Inverse-variance pooling weights source effects by $s_i^{-2}$. Random-effects pooling uses $(s_i^2+\widehat v)^{-1}$, with the nonnegative DerSimonian--Laird moment estimate $\widehat v$ of between-object variance. Full-representation nearest neighbor returns the effect of the nearest source object. Ridge meta-regression and RBF kernel ridge use an unpenalized intercept and source-standardized covariates. Regularization is selected from $\{0.01,0.1,1,10,100\}$ by source-only leave-one-out smoother error; kernel bandwidth multipliers are $\{0.5,1,2\}$ times the median nonzero source distance. Source preprocessing is held fixed in these deletion-residual calculations. No target outcomes enter tuning.

The comparison uses 300 paired draws in each of four conditions: nominal, shifts $0.25$ and $0.80$, and outcome noise SD $3$. All other synthetic settings remain fixed. Table~\ref{tab:ext-baselines} reports all-target error, using no-rejection ATLAS so that every method is evaluated on the same targets. Table~\ref{tab:ext-paired} reports paired regressor-minus-ATLAS error differences and their Monte Carlo uncertainty. The nominal ATLAS and semantic-forced records reproduce the existing common-target diagnostic. Kernel ridge improves nominal MAE by $0.019$, with paired 95\% Monte Carlo interval $[0.011,0.027]$ for the reduction. Both regressors improve accuracy under the two shift conditions. Under high noise, no-rejection ATLAS has MAE $0.162$, compared with $0.172$ for ridge and $0.177$ for kernel ridge. Point-only comparators are evaluated for prediction; no confidence intervals are assigned to them.

\input{experiments/causal_atlas_bridge/tables/app_stronger_baselines.tex}
\input{experiments/causal_atlas_bridge/tables/app_stronger_paired.tex}''')

    before(r'\subsection{NSW Construction, Stability, and Error Distributions}',r'''\paragraph{Retained-certificate coefficient check.}
We also study a diagnostic variant with a fixed family of original archive certificates and one singleton certificate for each candidate bridge. All certificates use the same Bonferroni allocation over this complete family; previously available constraints are retained after selection. This construction changes the objective used in the diagnostic and leaves Algorithm~\ref{alg:atlas} unchanged.

For each of 12 archives in the moderate and severe conditions, we take candidates with indices $0,1,4,5,8,9$ from the twelve-candidate library and enumerate all 64 subsets. The outcome law is fixed before selection: independent normal bridge estimates have initial archive-only ATLAS predictive means and the candidate standard errors. We use 2,048 joint draws for reference values $F(S)$ and 128 separate joint draws for planning values $\widehat F(S)$, with common outcome vectors across subsets within each sample. Seeds are $2026090621$ and $2026090622$. The reference submodularity ratio is the minimum, capped above at one, over all 665 strict subset extensions with positive joint gain. The discrepancy $\epsilon$ is the maximum absolute difference between planning and reference singleton marginal gains over all 192 edges.

For budgets $B=1,2,3$, we compare the reference value of the set chosen greedily using $\widehat F$ with $(1-e^{-\gamma})F_B^\star-2B\epsilon/\gamma$, where $F_B^\star$ is the best reference value among sets of size at most $B$. The sampled retained-certificate objectives have $\gamma=1$ and no empty intersections. All 72 lower bounds are positive and below the corresponding greedy value (Table~\ref{tab:ext-retained}). These are numerical consistency checks for the stated finite-library variant. The reference law is estimated by Monte Carlo, and $\epsilon$ is obtained from the completed enumeration; it is not a prospective population error certificate. The result does not establish the theorem's assumptions for the operational adaptive policy.

\input{experiments/causal_atlas_bridge/tables/app_bridge_retained.tex}''')

    before(r'\subsection*{Reproducibility and Reporting Boundaries}',r'''\paragraph{Disjoint-unit randomized reference.}
The additional protocol fixes source and reference pools before constructing local objects. Within each original treatment arm, seed $2026090601$ assigns two thirds of individuals to the source pool and the remainder to the reference pool. The resulting pools have 296 and 149 individuals and no shared units. Thirty anchors are chosen by farthest-point coverage of standardized baseline covariates within the inner 95\% of covariate norm, without outcomes; the first 24 define source objects and the last six define targets. Each object uses 50 nearest neighbors from its own pool, with at least eight treated and eight control individuals. Object context is the mean neighborhood covariate vector; representation scaling uses source objects only. Target contrasts and their standard errors are hidden during prediction.

The six randomized target contrasts are noisy references. We report the average signed prediction-minus-reference gap across all six raw predictions in Table~\ref{tab:ext-reference}. A stratified individual bootstrap independently resamples the source and reference pools within treatment arms and rebuilds every overlapping object jointly, with anchors fixed. Of 200 replicates using seed $2026090602$, 196 meet the arm minima; four failures are retained in the repository. Percentile intervals describe the fixed-design bootstrap distribution conditional on valid replicates. ATLAS releases one of the six original targets. The wide interval for its mean raw gap, $[-3.978,3.032]$ thousand dollars, leaves considerable uncertainty and does not establish equivalence to the randomized reference.

\input{experiments/causal_atlas_bridge/tables/app_nsw_reference.tex}

\paragraph{Known-truth NSW-covariate extension.}
We retain the covariates, disjoint pools and anchors, and simulate treatment independently with probability $0.5$. With covariates in the order listed above, the common baseline response is
\[
 m_0(x)=3+0.7x_1+1.5\tanh(x_7)+0.5x_2^2.
\]
The constant, smooth and interaction effect surfaces are respectively
\begin{align*}
 \tau_{\mathrm{constant}}(x)&=2,\\
 \tau_{\mathrm{smooth}}(x)&=2+0.8\tanh(x_1)+1.2\tanh(x_8),\\
 \tau_{\mathrm{interaction}}(x)&=1+2\tanh(x_1x_8)+0.8\,\mathbf{1}\{x_6>0\}.
\end{align*}
Outcomes are $Y=m_0(X)+A\tau(X)+\varepsilon$, with independent $\varepsilon\sim N(0,9)$. For each target neighborhood $I$, the exact estimand is $|I|^{-1}\sum_{i\in I}\tau(X_i)$. There are 100 independent assignment/outcome replicates per surface, using seeds $2026090611$--$2026090613$; all replicates meet the arm minima. Point-error Monte Carlo SE uses the 100 replicate means across six targets. Release-conditioned metrics use pooled ratios with replicate-cluster influence-function SEs, preserving dependence among overlapping targets.

The summary-data comparators follow the source-only protocol in Appendix B.2. We additionally fit a ridge T-learner to source individuals, with separate response regressions in the two treatment arms and source-only tuning. Its target prediction averages the fitted treatment-effect difference over the target's covariates; its richer individual-data access is identified separately in Table~\ref{tab:ext-semi}. Constant effects favor pooling, and the T-learner has smaller mean error than ATLAS on all three surfaces. Figure~\ref{fig:ext-nsw} displays selected comparisons; Tables~\ref{tab:ext-semi}--\ref{tab:ext-calibration} retain the full point-error and interval summaries.

\input{experiments/causal_atlas_bridge/tables/app_nsw_semisynthetic.tex}
\input{experiments/causal_atlas_bridge/tables/app_nsw_calibration.tex}

\begin{figure}[htbp]
\centering
\includegraphics[width=\textwidth]{experiments/causal_atlas_bridge/figures/extension_nsw_validation.pdf}
\caption{Additional NSW checks. \textbf{(a)} Mean signed gaps against disjoint-unit randomized references, with descriptive 95\% individual-bootstrap intervals. \textbf{(b)} All-target MAE against known effects on three semi-synthetic surfaces, with mean $\pm1.96$ Monte Carlo SE across assignment/outcome replicates. Method colors match between panels; complete comparisons are in Tables~\ref{tab:ext-reference} and~\ref{tab:ext-semi}. The T-learner uses source individual data.}
\label{fig:ext-nsw}
\end{figure}

The semi-synthetic extension evaluates the existing NSW interval rules empirically. Released-target coverage is $0.995$--$0.998$ with widths above four thousand dollars. Scientific certificate constants have not been established for these three new surfaces, and source summaries remain correlated through overlapping neighborhoods. Consequently, the observed inclusion rates do not verify the independent-archive assumptions or establish honest coverage for real NSW subgroup effects. They document the conservative behavior of this implementation under the specified response surfaces.''')
    source=source.replace('at release commit \\texttt{96fba35}.',
        'at the original release commit \\texttt{96fba35}, with the additional experiments recorded in commit \\texttt{a859b66}.')
    source=source.replace('The NSW analysis uses noisy held-out contrasts and one fixed local-object construction.',
        'The NSW analyses include the original overlapping-object reconstruction, a disjoint-unit randomized-reference check, and three semi-synthetic response surfaces on one fixed population and split. The retained-certificate bridge check concerns a separate frozen-law variant.')
    return source


if __name__=='__main__':
    source=PAPER.read_text(encoding='utf-8')
    updated=integrate(source)
    # Verify theoretical material against the actual pre-integration source.
    for start,end in [(r'\documentclass',r'\begin{abstract}'),
                      (r'\section{Introduction}',r'\section{Experiments:'),
                      (r'\section{Discussion}',r'\section{Appendix: Experimental Details}'),
                      (r'\begin{thebibliography}',r'\end{document}')]:
        assert source[source.index(start):source.index(end)]==updated[updated.index(start):updated.index(end)]
    PAPER.write_text(updated,encoding='utf-8',newline='\n')
    print('Integrated approved extensions; protected sections unchanged.')
