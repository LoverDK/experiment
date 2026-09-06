# Validation v3 execution notes

- Protocol drafted 2026-09-06; long-running session crossed midnight in Asia/Shanghai.
  Metadata records UTC start times. No outcome-driven configuration changes.
- Hillstrom official blog confirms three randomized email arms and 64,000 customers.
  Original CSV host failed TLS verification. Used the scikit-uplift documented S3
  mirror; compressed MD5 matches its published hash; raw SHA256 retained. No TLS
  bypass. Dataset has 42,613 Men's Email/No Email individuals. The 24 prespecified
  cells have only 18 nonempty combinations (no prior purchaser has both purchase
  indicators zero); all 18 were retained, so source LOO has only 17 residuals.
- Regression point-only mechanism records originally encoded unavailable native
  coverage as False. Corrected to missing and reran the unchanged 45 settings.
  Added native width explicitly to each record, derived from its saved radius.
- Nuisance runner initially appended individual experiment diagnostics before
  knowing whether the entire eight-experiment archive passed arm minima. Corrected
  atomic reporting: completed archives populate the main effect table; partial
  diagnostics from failed archives are preserved separately. Same settings/seeds
  rerun; no failures suppressed. Small n / weak propensity failures remain evidence.
- Source LOO Hillstrom intervals are empirical; they are not ordinary split
  conformal intervals and no conformal validity is claimed. At 95%, the prescribed
  finite-sample rank exceeds the available residual count: interval is infinite.
- Cohort-rank uncertainty is evaluated by 1,000 paired bootstrap resamples with
  rankings recalculated. Simple ratio MC SE in the generic summary does not include
  rank-estimation variation; use selection_rank_bootstrap.csv for that comparison.
- New mechanism perturbations operate at the archive-summary layer. Heavy-tail
  perturbations replace the summary estimation error; they do not claim to be a
  new unit-level heavy-tail AIPW experiment. Nuisance experiments are unit-level.
- The coefficient and monotonicity checks remain frozen-law numerical diagnostics.
  Operational bridge results remain excluded from manuscript integration per user.
- Final code/protocol reconciliation found one DGP discrepancy: the protocol says
  logistic propensity .1 + .8 expit(2x), while the executed runner uses expit(2x),
  x in [-1,1], with range approximately [.1192,.8808]. The fitted logistic model
  is correctly specified for the executed propensity, with [.1,.9] clipping.
  Results and seeds are retained and labeled with the executed DGP. The original
  pre-analysis protocol is preserved; this is a documented implementation deviation.
- Mechanism benchmark release columns apply the common numerical threshold 1.65
  to method-specific scores. Regression scores are heuristic and have no native
  certificate. Do not interpret those columns as an equal-confidence comparison;
  the prespecified cohort-rank block supplies the equal-release comparison.
- Native bias-aware intervals in the selection/mechanism blocks use a Gaussian
  quantile plus the saved approximation radius. Their coverage is empirical;
  this is distinct from the finite-sample sub-Gaussian Chernoff radius.
