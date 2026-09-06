# Validation v3: experimental scope and proof audit

Fixed before v3 outcome analysis on 2026-09-06. Base implementation: fbbb728.
User requests all nine rows of the experimental-gap table and an Appendix A audit.
No theory, paper source, existing results, or Overleaf assets are modified.

## Reporting rules

- Keep all prespecified settings and failed replications. New files live in
  results/validation_v3. Record seeds, source hashes, software, command and time.
- Comparisons pair methods within the same archive/target replication. Standard
  errors cluster targets by independent simulation replication, never by overlapping
  NSW neighborhood. Repeated real-data splits describe design variation, not new people.
- Synthetic truth is evaluation-only. Calibration below uses separate historical
  target *estimates*, not latent target effects. Label its additional data access.
- Native interval rules are assessed empirically. An estimated variance is not
  automatically a sub-Gaussian certificate. Existing scientific constants are not
  certified for new response surfaces. Report coverage with width and release.
- Do not tune configurations to reverse negative findings. Only correct bugs;
  record any protocol deviations. No claim of unconditional publication readiness.

## 1--2: selection and intervals

Four original scenarios: nominal, shift .25, shift .8, and outcome noise SD 3.
150 independent historical calibration archives and 300 independent test archives
per scenario, from new seeds. Predict with native ATLAS, full-representation nearest
neighbor, inverse-variance pooling, ridge meta-regression and RBF kernel ridge.
Native bias-aware nearest/pooling intervals reuse the same scientific bounds.
Regression uncertainty ranking is a heuristic: source LOO residual RMS times
sqrt(1 + nearest source distance squared), calculated from source information only.

Report exact cohort release fractions .25/.5/.75/1 using uncertainty rankings
(no test outcomes); also report deployment thresholds learned from historical
calibration scores. Residual-calibrated intervals use finite-sample order statistics
at .8/.9/.95 of |prediction - independent noisy reference| / score. Check both noisy
reference inclusion and latent-effect coverage. Such calibration provides no asserted
latent-effect or shifted-distribution coverage guarantee. Nominal calibration applied
unchanged to shifted/noisy tests is an additional transfer stress test.

## 3: fitted nuisance regressions

200 replications per setting; 8 archive experiments and 100 or 400 units each.
Unit covariate uniform[-1,1]. Response regressions either match polynomial features
or deliberately omit quadratic structure. Two fixed random evaluation folds;
training data exclude each evaluation fold. Known propensity .5 or .1; additionally
logistic propensity .1+.8 expit(2x), estimated by clipped logistic regression or
misspecified intercept. Compare oracle and fitted AIPW, record experiment-level
bias/RMSE/SE and final transport coverage/width. Unknown-propensity nuisance bias
bound zero is explicitly an uncertified plug-in policy, not a valid new certificate.

## 4: response/mechanism benchmark

100 replications per prespecified setting. Five surfaces: original, affine,
oscillatory, discontinuous threshold, and Friedman #2 (published regression benchmark,
four inputs mapped from [-1,1]^4 to its original domains and response divided by 500).
The Friedman response is repurposed as an effect surface; this is not an established
causal benchmark. Reference: Friedman (1991), Multivariate adaptive regression splines,
Annals of Statistics 19(1), DOI 10.1214/aos/1176347963.
Cross each surface with baseline and one-factor changes: shift .8, n=100, archive
size 4/24, noise SD 3, standardized t3 noise, two irrelevant representation coordinates
replacing h/q, and hidden-proxy noise half-width .5. Effects and representation are
altered only in this experimental module. New surfaces are uncertified stress tests.

## 5: dependent archives

300 replications, correlations 0/.3/.7. Gaussian archive estimation noise with
known marginal SE .6 and equicorrelation. Native point weights held fixed across
the three interval variants: diagonal proxy, true proxy matrix, and a proxy matrix
estimated from 40 independent calibration noise vectors. Evaluate the statistical
component separately and the complete interval on original and constant surfaces.
This isolates dependence from geometry masking. Estimated-matrix results are empirical.

## 6: NSW design stability

20 treatment-stratified disjoint individual splits, source proportion 2/3;
neighborhoods 35/50/75; farthest-point and seeded random anchors. Each setting
uses 24 source and six reference objects, arm minima eight, and source-only
representation scaling. Preserve arm failures. Record signed gap, noisy-reference
MAE, inclusion, width, release and member indices. The existing jointly rebuilt
individual bootstrap remains the uncertainty reference; repeat splits only measure
design sensitivity and receive no independent-sample confidence interval.

## 7: second real dataset

Hillstrom randomized email trial, 64,000 customers, as documented by original
author and scikit-uplift. Fetch verified mirror with its published compressed-file
MD5, store SHA256 and provenance; do not disable TLS validation. Use Men's Email
versus No Email, website visit primary outcome, conversion secondary. This is a
second *trial*, not a multi-study archive. Construct 24 outcome-blind disjoint cells
from recency (three fixed bins), prior men's/women's purchase indicators and new
customer indicator. Leave one complete cell out. Source summaries and covariates
only during prediction. Compare native ATLAS workflow and summary baselines;
native constants in percentage-point units are sensitivity settings, not scientific
certificates. Report noisy-reference error, gap, reference SE and interval behavior;
source-only LOO residual calibration at 90/95% as an empirical alternative.

## 8: bridge stability

Same 24 archives and six-candidate subsets as v2. Re-enumerate original operational
and retained-certificate families with 8192 reference draws and 128 planning draws;
compare to existing 2048-draw result. Save every edge gain, minimum negative gain,
fraction of negative edges, greedy budget 1/2/3 value and empty intersections.
The original user exclusion of operational monotonicity from the paper persists.

## 9: scientific constant sensitivity

300 archives for nominal and severe shift. Multiply original L/H/hidden bounds
by .1/.25/.5/1/2; add a setting where actual proxy noise is .5 but declared radius
stays .2. Compare original fixed constants with residual calibration learned on
nominal historical data (block 1). No finite sample proves a hidden-moderator bound.

## Appendix A

Read every proof and theorem statement. Record exact source line/label, logical
dependencies, confirmed derivations, missing conditions, and explicit counterexamples.
Numerical counterexamples are supporting checks, with analytic arguments in the audit.
No assertion of machine-checked or exhaustive proof certification. No theory edits.
