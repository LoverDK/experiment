# Experimental extension protocol v2 (2026-09-06)

This protocol supersedes the unvalidated draft in
`experiment_extension_plan_20260906.md`. That draft was not preregistered with
an external registry. Initial development exposed an estimand mismatch between
age/education cells and local neighborhoods, shared-unit leakage, and a fallback
to the target contrast. Those draft calculations are excluded from the paper.
Aggregate ex-post bridge ratios cannot identify submodularity and are also
excluded as new evidence. All new results below are generated independently of
those exploratory outputs. Original committed experiments are preserved.

## NSW: two complementary checks

Use the committed 445-person randomized NSW sample with its existing SHA-256.
Fix 24 source anchors and six target anchors by farthest-point coverage of
standardized baseline covariates, without outcomes. Assign individuals to a
source pool (two thirds) and a reference pool (one third), stratified by treatment,
using seed 2026090601. No individual may occur in both pools. Each local object
uses the 50 nearest individuals in its own pool, with at least eight per arm.
Neighborhood context is the mean covariate vector. Both representations and
their scaling use source objects only. Target effect and standard error are
hidden from prediction. Compare predictions with independent randomized local
contrasts, reporting their uncertainty as noisy references, never known truth.
Stratified individual bootstrap (200 replicates, seed 2026090602) resamples
source and reference pools independently and rebuilds all overlapping objects
jointly; report percentile intervals for signed prediction-minus-reference gaps.
Replicates failing arm minima are recorded, never replaced by target outcomes.

Separately, preserve the empirical covariates and disjoint pools, simulate
Bernoulli(0.5) assignment and potential outcomes on three fixed response surfaces
(constant, smooth heterogeneous, nonlinear interaction). Noise SD is 3 in
thousands of dollars. Exact target truth is mean tau(X) over its 50 individuals.
Use 100 replicates per surface (seeds 2026090611--13). This is NSW-covariate
semi-synthetic validation, not validation against real unobserved potential
outcomes. Report all-target and released-target MAE, coverage and width where
an interval exists, and Monte Carlo SE across replicate means. Existing NSW
interval rules are evaluated empirically; no new scientific certificate bound
is asserted for these surfaces.

## Comparable stronger baselines

Use identical observed representations, source estimates and source standard
errors for inverse-variance pooling, DerSimonian--Laird random-effects pooling,
full-representation nearest neighbor, linear ridge meta-regression, and RBF
kernel ridge regression. Ridge and kernel parameters are selected exclusively
by source-object leave-one-out squared prediction error on fixed grids.
Do not claim these generic regressors implement a named modern causal method.
For NSW additionally report a unit-data ridge T-learner, trained only on source
individuals; label its richer data access separately. Synthetic evaluation uses
300 shared draws in each of nominal, moderate-shift, severe-shift and high-noise
conditions. Existing ATLAS, no-rejection and semantic forced are rerun jointly.
All-target paired comparisons use no-rejection ATLAS; MC SE uses paired errors.
No interval is invented for a point-only baseline.

## Bridge set-function and coefficient diagnostic

Take a fixed balanced six-candidate sublibrary (indices 0,1,4,5,8,9) from the
existing twelve-candidate generator. For moderate and severe support scenarios,
use 12 independent archives each (seeds 2026090621--22). Enumerate all 64 subsets
and all 665 strict nonempty subset extensions. Define the ex-ante outcome law
once from initial archive-only ATLAS predictive means and known bridge SEs;
draw 2,048 joint outcome vectors with common random numbers for every subset.
Use a separate 128-vector estimate to select a fixed-law greedy set. Retain all
set values so global finite-library monotonicity, submodularity ratios and
uniform marginal estimation discrepancy can be audited.

Evaluate both the unchanged operational PI family and a diagnostic that retains
a fixed collection of original/singleton certificates with a fixed Bonferroni
allocation across the entire library. The latter isolates loss of nestedness
from changing weight families; it does not replace Algorithm 1. Any empty
intersection invalidates the corresponding finite-law check and is recorded.
For positive gains compute the minimum ratio of summed singleton marginals to
joint marginal gain over all S subset T, clipped above at one. Check the
Theorem 5.6 coefficient expression only when empirical monotonicity and positive
gamma hold; negative lower bounds are reported as vacuous. Budgets are 1--3.
These are finite-library Monte Carlo diagnostics of an explicit frozen law,
not proofs for the population objective or the adaptive plug-in policy.

## Artifacts and checks

Save per-target/per-subset/per-bootstrap records, summaries, parameters, seeds,
source/code hashes and software versions under `results/extensions/`.
Builders read these records to generate paper tables and vector figures under
the requested Overleaf asset paths. Preserve all failures and unfavorable
comparisons. Tests check information isolation, estimand alignment, paired SEs,
subset enumeration, monotonicity failures and deterministic execution. Commit
experimental code/results before integrating the paper. Theory stays unchanged.
