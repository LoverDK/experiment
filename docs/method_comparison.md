# Stage 3: transport methods and baselines

This stage implements the first observable-only version of the Causal ATLAS
transport decision. Each method receives only:

- observed_representation = (s1, s2, h_proxy, q);
- the recorded DesignProfile;
- an estimated archive effect;
- its standard-error certificate, nuisance-bias bound, and moderator radius.

The target mechanism, target true effect, and oracle support weights are not
read by any estimator. They are used only by the comparison layer to score the
outputs after fitting.

## Candidate retrieval and compatibility

Archive experiments are sorted by Euclidean distance between their observed
representations and the target representation. The recorded design profile is
checked before an archive experiment can become a candidate. The retrieval
function supports an optional maximum candidate count and semantic radius.

## ATLAS weights

For the retrieved candidate set, weights are constrained to the simplex and
optimized with projected gradient descent:

    ||r_target - sum_j alpha_j r_j||^2
      + lambda_sigma sum_j alpha_j^2 s_j^2
      + lambda_hidden L_h sum_j alpha_j delta_j

The final full-length weight vector has zeros outside the candidate set. The
optimizer uses no true mechanism values.

## Certificate and decision

The observable certificate is decomposed into:

    L * representation_residual
    + H/2 * weighted_representation_dispersion
    + R_hidden
    + weighted_nuisance_bias
    + sqrt(2 log(2/zeta) * sum_j alpha_j^2 s_j^2)

The point estimate is the weighted archive effect estimate. It is returned
only when the certificate radius is at most the configurable
scientific_tolerance; otherwise the full ATLAS result is rejected while its
interval is retained.

atlas_no_rejection is an ablation that uses exactly the same learned weights
and interval but always exposes the point estimate.

## Baselines

- semantic_forced: inverse-distance composition over retrieved candidates,
  without a rejection decision.
- nearest_semantic: the closest design-compatible archive experiment.
- global_mean: the uniform mean over all design-compatible archive
  experiments.

All baselines use the same uncertainty certificate implementation so interval
coverage can be compared on the same scale.

## Fair repeated comparison

run_method_comparison.py generates one archive-target draw per replicate and
passes that same draw to every method. The independent child seed is recorded,
so comparisons do not mix different DGP realizations. The 200-repetition
default reports acceptance/rejection, accepted-point error, sign accuracy,
interval coverage, interval width, and certificate components.

With the current illustrative tolerance 1.65, the default run gives:

| method | acceptance | accepted MAE | interval coverage |
| --- | ---: | ---: | ---: |
| atlas | 0.530 | 0.1184 | 1.000 |
| atlas_no_rejection | 1.000 | 0.1372 | 1.000 |
| semantic_forced | 1.000 | 0.2011 | 1.000 |
| nearest_semantic | 1.000 | 0.4715 | 1.000 |
| global_mean | 1.000 | 0.2614 | 1.000 |

These are implementation checks for the synthetic DGP, not claims about
real-world performance. The tolerance is a scientific decision parameter and
must be selected or sensitivity-analysed in the final experiment.

Run:

    python scripts/run_method_comparison.py
