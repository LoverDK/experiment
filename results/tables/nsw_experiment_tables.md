# NSW real-data local-contrast reconstruction

Each row pools held-out local-object predictions across three independent
base seeds. The target local contrast is a noisy evaluation reference, not
a ground-truth subgroup effect.

| method | MAE | median AE | sign accuracy | coverage | mean width | rejection |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| atlas | 0.8615 | 0.6989 | 0.8542 | 0.9744 | 5.6303 | 0.2321 |
| atlas_no_rejection | 0.8615 | 0.6989 | 0.8542 | 0.9696 | 5.2749 | 0.0000 |
| semantic_forced | 1.1688 | 0.9367 | 0.7536 | 0.6048 | 2.8541 | 0.0000 |
| nearest_semantic | 1.2422 | 1.0313 | 0.7804 | 0.9923 | 8.3108 | 0.0000 |
| global_mean | 1.6790 | 1.3490 | 0.7839 | 0.4458 | 2.4746 | 0.0000 |

The Causal ATLAS and no-rejection rows use identical point weights. Their
difference is the rejection decision and the prespecified certificate
ablation, so their MAE, median AE, and sign accuracy should match.

Coverage here means that the reported interval contains the held-out local
contrast estimate. It does not establish coverage of an unobserved true local
effect because the held-out contrast itself has sampling noise.
