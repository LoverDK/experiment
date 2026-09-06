# Requested experiments 2, 3 and 5: completed v2 runs

The fixed protocol is [extension_protocol_v2.md](extension_protocol_v2.md).
Run from the repository root:

```powershell
python -u scripts/run/run_requested_extensions.py synthetic
python -u scripts/run/run_requested_extensions.py nsw
python -u scripts/run/run_requested_extensions.py bridge
python scripts/build/build_extension_artifacts.py
python -m unittest discover -s tests -v
```

## Scope and interpretation

- Synthetic: 300 paired archives per condition, four conditions, eight method
  records per draw. The nominal ATLAS and semantic-forced errors reproduce the
  existing common-target CSV to numerical precision. Regression tuning is
  source-only smoother leave-one-out, with source covariate scaling/kernel
  construction fixed across its deletion residual calculations.
- NSW real: disjoint source/reference individuals; 24 source and six target
  neighborhoods. ATLAS releases one of six original targets. The all-target
  signed gap is -0.670 thousand dollars, with a wide descriptive percentile
  bootstrap interval [-3.978, 3.032]. Of 200 bootstrap samples, 196 satisfy the
  arm minima and four failures are preserved. Neither a near-zero gap nor an
  interval containing zero demonstrates equivalence or accurate latent effects.
- NSW semi-synthetic: 100 independent outcome/assignment draws on each of three
  fixed surfaces, six targets each. Outcomes follow mu(X)+A*tau(X)+noise with
  SD 3. Known truth is the average tau over exactly the target units. ATLAS
  released coverage is 0.995--0.998 with width 4.25--4.37 thousand dollars;
  this is conservative empirical inclusion under existing NSW interval rules.
  Pooling and the unit-data T-learner have smaller point error in some settings.
- Bridge: all 64 subsets of a six-candidate sublibrary, 24 archives, two
  certificate families. The unchanged operational family is nonmonotone in
  all 24 archives under the sampled frozen law. Thus no theorem coefficient
  is reported for it. The retained-certificate diagnostic has empirical gamma
  one, with all 72 budget checks eligible, positive and satisfied. This variant
  does not replace Algorithm 1 or validate its adaptive guarantee.
- Strong baselines: ridge/kernel predictors outperform no-rejection ATLAS in
  several synthetic settings. The paper must distinguish point prediction,
  selective release and certified uncertainty. No claim of uniformly best
  accuracy is warranted.

## Audit trail

`results/extensions/` contains per-target, per-subset and per-bootstrap records,
failures, fixed design indices, metadata and derived summaries. The final
`artifact_manifest.json` hashes all records and generator/protocol inputs after
the concurrent runs. Individual run metadata captures the files available at
that run's completion; the final artifact manifest is the comprehensive one.
Draft age/education-cell calculations and aggregate ex-post bridge diagnostics
were rejected during development and removed from final outputs. Reasons are
documented in protocol v2; no draft result entered the paper.

New assets comprise one vector figure and six table inputs. Their numerical
content is generated from saved records. Raw simulations never run during the
artifact build. Existing core algorithms and paper theory remain unchanged.
