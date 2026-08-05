# Stage 4: fixed-seed main experiment protocol

This stage turns the method comparison into a reproducible screening protocol.
It changes one factor at a time and keeps the other DGP and estimator settings
at their defaults. At every level, all methods receive the same archive-target
draws and the same child seeds.

## Controlled factors

| factor | levels | implementation |
| --- | --- | --- |
| semantic mismatch fraction | 0, 0.10, 0.25 | move the target from the oracle archive mixture toward an in-domain anchor |
| hidden moderator sensitivity radius | 0.20, 0.40, 0.60 | enlarge the declared compatible h set |
| units per experiment | 100, 400, 1000 | set archive and target unit counts together |
| scientific tolerance | 1.25, 1.65, 2.05 | change only the accept/reject threshold |

The semantic mismatch move is a convex interpolation between the exact-support
target and the fixed anchor (1, -1, 1, -1). The target therefore remains in
the compact mechanism space [-1, 1]^4. It is a controlled violation of exact
archive support, not a violation of the smoothness, randomization, design, or
uncertainty assumptions.

The hidden-radius sweep changes the certificate conservativeness. The proxy
noise remains bounded by 0.10, so all levels continue to satisfy the declared
proxy-compatible set condition.

## Reproducibility

The default run uses 200 repetitions and base seed 20260806. Each factor level
uses a deterministic seed derived from the factor index; every method within a
level sees exactly the same generated experiments.

The script writes:

- results/main_experiment_summary.csv: long-form method-by-factor table;
- results/main_experiment_metadata.json: fixed configuration and levels;
- results/figures/main_experiment_acceptance.png: ATLAS acceptance rates;
- results/figures/main_experiment_mae.png: accepted-point MAE for all methods.

Run:

    python scripts/run_main_experiment.py

## Reading the current result

At the default tolerance 1.65, ATLAS acceptance falls from 0.515 to 0.300 as
semantic mismatch increases from 0 to 0.25. Increasing the hidden sensitivity
radius from 0.20 to 0.40 increases the hidden certificate term enough that the
acceptance rate becomes 0. The sample-size sweep raises acceptance from 0.25 to
0.605 because statistical uncertainty shrinks. Raising the tolerance from 1.25
to 2.05 raises acceptance from 0.015 to 0.945.

All reported certificate intervals cover the synthetic target truth in these
screening runs. Empty accepted-MAE cells mean that ATLAS rejected every draw
at that factor level; this is an intended decision outcome, not a missing
calculation.

These results are protocol checks for the certified synthetic setting. They are
not yet claims about external or real-world performance. The next stage should
pre-register the final grid, add multiple DGP seeds, and produce publication
tables after reviewing this screening behavior.
