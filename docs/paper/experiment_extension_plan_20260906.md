> Superseded by [extension_protocol_v2.md](extension_protocol_v2.md). Draft designs are excluded from final results.

# Planned experimental extensions

This document records the three extensions requested after the Overleaf revision.
They are separate from the original fixed-seed results and will be reported with
their own metadata and hashes.

## 1. NSW causal-target validation

The current NSW analysis reconstructs noisy held-out local contrasts. The extension
will add a causal target with an estimable randomized-data reference: for each
pre-registered covariate partition, estimate the treatment effect using the full
randomized NSW sample, then evaluate archive reconstruction on held-out local
objects against that partition-level randomized reference. The reference estimate
will be computed without exposing the held-out local contrast to the prediction
step. Bootstrap intervals will be clustered at the individual level because local
objects overlap in their underlying units.

The paper will label this as finite-sample randomized-reference validation. It will
not call the result a known subgroup ground truth or an external-validity test.

## 2. Bridge-theorem empirical diagnostic

The extension will estimate the marginal-value diminishing-returns ratio on the
same bridge library used by the formal experiment. For every path and budget,
record the largest observed violation of monotonicity and the ratio

`sum single-step marginal values / joint set value`.

The diagnostic will be evaluation-only when it uses realized future bridge
outcomes. It will be reported as evidence about the finite library, not as a proof
of the weak-submodularity assumption or of the coefficient in Theorem 5.6.

## 3. Stronger baseline comparison

The extension will add three pre-specified baselines using the same archive and
target draws: inverse-variance meta-analytic pooling, covariate-adjusted outcome
regression transport, and nearest-neighbor transport in the full observed
representation. Each baseline will have the same release/interval reporting
where a certificate is available; otherwise it will be marked forced-release and
evaluated on all targets. No baseline may access target truth or held-out outcomes.

## Reproducibility boundary

Each extension will write a protocol JSON, result CSV, source-data hash, and
software revision. Existing result files will not be overwritten. The paper will
state clearly which results are randomized-reference validation, which are
evaluation-only bridge diagnostics, and which are baseline comparisons.
