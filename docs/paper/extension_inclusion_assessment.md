# Inclusion assessment before any Overleaf integration

User steering: assess whether the completed extensions belong in the paper
before editing Overleaf. At this checkpoint, the main TeX source is unchanged;
the generated extension assets are repository artifacts only.

## Recommendation

1. **Stronger synthetic baselines: include.** This directly addresses whether
   enriched representations alone or flexible prediction explains the gain
   over semantic baselines. Shared draws and source-only tuning support a
   useful comparison. Report all-target no-rejection ATLAS for matched point
   error and keep selective metrics distinct. Ridge/kernel win in several
   conditions; these unfavorable results must remain. Put a compact result
   in the main experimental narrative and details in B.2. The comparators
   are generic archive regressors; do not claim comprehensive coverage of
   modern transport estimators. Point-only baselines cannot settle interval
   quality or selective-prediction superiority.

2. **NSW-covariate semi-synthetic experiments: include as supplementary evidence.**
   Exact target-unit average effects remove the unknown-truth ambiguity of
   the original reconstruction experiment. Disjoint individual pools remove
   source/reference reuse; replicate-level uncertainty respects overlapping
   targets. Three hand-designed surfaces on one fixed population and split
   limit external scope. Existing NSW certificate constants have not been
   analytically justified for these surfaces, and source neighborhood
   summaries remain correlated. Thus high empirical inclusion is not a
   verification of the independent-archive theorem assumptions. Put MAE,
   release, released coverage and width together in B.8; briefly reference
   the known-truth check in the main text. Label the unit-data T-learner's
   additional information access.

3. **Real NSW disjoint-unit reference: appendix only, modest evidential weight.**
   It usefully diagnoses shared-unit dependence in the previous construction.
   However, only six target neighborhoods remain, ATLAS releases one, and
   the all-target mean gap bootstrap interval is very wide. An interval
   containing zero does not establish agreement or equivalence. The 196/200
   bootstrap interval is conditional on passing arm minima and on the fixed
   split/anchors. Local object rebuilding is nonsmooth. Treat this as a
   transparent robustness check, not external causal validation. The large
   combined real/semi figure is not presently recommended for the main text.

4. **Operational bridge nonmonotonicity: relevant limitation; scrutinize first.**
   All 24 sampled finite-law objectives fail an assumption of the bridge
   guarantee. This concerns application of the conditional theorem to the
   implementation, not the theorem's proof. An honest diagnostic belongs in
   B.7 and its substantive limitation should be acknowledged in the main
   bridge paragraph. Before final publication wording, quantify the magnitude
   and Monte Carlo stability of violating gains, beyond reporting counts.
   The current 2,048-draw law is an approximation and the six-candidate library
   is small. Do not generalize the observed failure rate to all archives.

5. **Retained-certificate coefficient checks: diagnostic only; low priority.**
   Keeping all constraints and fixing Bonferroni allocation changes the set
   function. It isolates how nesting affects the assumption, but does not
   establish Algorithm 1's operational/adaptive guarantee. The discrepancy
   epsilon is computed against an enumerated reference after the experiment;
   it is not a prospectively certified population error bound. Therefore
   72/72 positive checks are internal numerical consistency evidence for
   this variant, not independent confirmation of the original theorem's
   applicability. A short appendix comparison is sufficient if retained.

## Editorial boundary

Do not insert all six generated tables merely because they exist. Consolidate
main accuracy and paired uncertainty where space permits; retain full records
in the repository. Theory, proofs, and unrelated text remain untouched.
No new Overleaf source or asset has been uploaded at this assessment checkpoint.
