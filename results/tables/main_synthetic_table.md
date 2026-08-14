# Synthetic benchmark with evaluation-only oracle

ATLAS 行的误差、覆盖率和宽度以实际发布目标为条件；其余强制发布方法
在全部共同目标上评价。因此发布率必须与条件误差一起解释。

| Method | Release | MAE | RMSE | Sign | Coverage | Width |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Causal ATLAS | 0.4633 | 0.1109 | 0.1375 | 0.9281 | 1.0000 | 2.9462 |
| ATLAS, no rejection | 1.0000 | 0.1387 | 0.1703 | 0.8933 | 1.0000 | 3.3391 |
| Semantic forced | 1.0000 | 0.2493 | 0.3102 | 0.7967 | 1.0000 | 2.8306 |
| Nearest semantic | 1.0000 | 0.5530 | 0.6970 | 0.7167 | 0.9700 | 3.1269 |
| Global mean | 1.0000 | 0.2816 | 0.3621 | 0.7800 | 1.0000 | 3.5638 |
| Oracle latent support* | 1.0000 | 0.1350 | 0.1595 | 0.8933 | 1.0000 | 3.3368 |

* Oracle latent support 使用仿真中不可被估计器观察的真实机制坐标，
  仅作为评价上界参考，不参与任何可部署方法的检索、权重、拒绝或 bridge 选择。
