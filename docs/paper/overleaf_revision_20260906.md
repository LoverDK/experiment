# Overleaf Revision 2026-09-06

This revision updates the paper-facing source and assets prepared for the Overleaf
project `main_direction_Causal_ATLAS_7papers`.

## Scope

- Theory, assumptions, theorem statements, and proofs were left unchanged.
- The synthetic results remain the committed fixed-seed results in `results/`.
- The NSW analysis remains a descriptive reconstruction stress test; no causal
  ground-truth claim was added.

## Paper changes

- Clarified that the ATLAS/no-rejection comparison measures selective release,
  while the all-target no-rejection ATLAS versus semantic-forced comparison is
  the representation comparison.
- Added the Wilson interval for the nominal release rate and the Monte Carlo SE
  for released-target MAE in the main experimental discussion.
- Added the cross-scenario bridge results and planning-inconsistency diagnostic.
- Added the fixed NSW construction counts, holdout protocol, and restricted versus
  design-enriched representation split to the main text.
- Reworded the abstract and conclusion so that the empirical claims are limited
  to the stated synthetic conditions and the NSW reconstruction protocol.
- Updated Figure 2, Figure 4, and Figure 5 captions to match the current panels.

## Assets

The Overleaf upload uses the following paper-facing paths:

```text
experiments/causal_atlas_bridge/figures/
experiments/causal_atlas_bridge/tables/
```

Figures are generated from the committed CSV/JSON results by
`scripts/build/build_paper_figures.py`. No new random draws are introduced by
the presentation update.

## Verification

The local source snapshot is `version1_work/01_final_integration.tex`. It compiles
with bundled Tectonic to a 50-page PDF. The Overleaf project is the final compile
target because its TeX distribution is the authoritative environment for the
submitted source.
