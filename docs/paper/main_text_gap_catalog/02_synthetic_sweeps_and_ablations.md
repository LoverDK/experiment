# 02 合成压力扫描、正式场景与消融

## 1. 四个单因素筛查扫描

### 做了什么

阶段 4 分别改变语义失配、隐藏调节半径、每实验样本量和科学容忍度，每个单元使用
同一套 200 个 target 比较多种方法。这是正式实验前的单种子筛查。

### 对应文件

| 文件 | 作用 |
| --- | --- |
| `docs/stages/main_experiment.md` | 四个扫描的构造和解释 |
| `results/main_experiment_summary.csv` | 60 行方法-因素-水平结果 |
| `results/main_experiment_metadata.json` | 单种子、重复数和水平网格 |
| `results/figures/main_experiment_acceptance.png` | 各扫描下的发布率 |
| `results/figures/main_experiment_mae.png` | 各扫描下的条件 MAE |
| `src/causal_atlas_sim/experiments.py` | 扫描协议和汇总实现 |
| `scripts/run/run_main_experiment.py` | 正式运行入口 |

### 正文覆盖状态

正文已通过 Figure 2C 写二维表示敏感性，通过 Figure 3A 写科学容忍度前沿，但没有
完整写语义失配、隐藏半径和样本量的单因素结果。

### 建议

不要把单种子筛查数字重新放进正文。对应现象已经在下一阶段的三种子正式场景中复现，
正文应使用 `formal_experiment_summary.csv`，单因素 60 行表保留为稳健性材料。

## 2. 正式多种子压力场景

### 做了什么

正式协议使用 6 个场景、3 个基础种子、每种子 100 个 target。当前正文 Table 1
主要使用名义共同目标基准，只在其他段落分散提到少量压力端点，没有集中说明这些结果。

### 对应文件

| 文件 | 作用 |
| --- | --- |
| `docs/stages/formal_experiment.md` | 场景、估计器、统计误差和正式发现 |
| `results/formal_experiment_summary.csv` | 42 行六场景-七估计器合并结果 |
| `results/formal_experiment_seed_summary.csv` | 126 行逐种子结果 |
| `results/formal_experiment_metadata.json` | 固定正式协议 |
| `results/figures/formal_experiment_overview.png` | 名义和压力结果总览 |
| `results/tables/formal_experiment_tables.md` | 完整正式表 |
| `src/causal_atlas_sim/formal_experiment.py` | 多种子和 Monte Carlo 不确定性实现 |
| `scripts/run/run_formal_experiment.py` | 正式多种子实验运行入口 |

### 正文值得补的结果

- 语义失配从名义值增至 `0.25`，ATLAS 发布率从 `0.4633` 降至 `0.2833`，
  发布点 MAE 从 `0.1109` 升至 `0.1581`；
- 每实验样本量从 `100` 增至 `1000`，发布率从 `0.2300` 升至 `0.5000`；
- 隐藏调节半径为 `0.40` 时全部拒绝。

这些是预先固定的多种子结果，适合在 6.2 末尾用一个短段说明方法对信息质量的响应。

### 候选正文

> The prespecified multi-seed stress scenarios show the same support-sensitive behavior beyond the nominal benchmark. Increasing the semantic mismatch from its nominal value to 0.25 lowers the release rate from 0.463 to 0.283 and raises released-target MAE from 0.111 to 0.158. Increasing the per-experiment sample size from 100 to 1,000 raises release from 0.230 to 0.500, whereas enlarging the hidden-moderator radius to 0.40 leads to complete rejection. These changes are consistent with the certificate responding separately to geometric, moderator, and sampling uncertainty.

## 3. 正式估计器消融

### 当前正文遗漏

Section 6.1 只说完整消融在附录，但正文没有告诉读者消融得到什么。两个消融分别检验
方差惩罚和候选库覆盖：

| 方法 | 发布率 | 发布点 MAE | RMSE | 覆盖率 |
| --- | ---: | ---: | ---: | ---: |
| 完整 ATLAS | 0.4633 | 0.1109 | 0.1375 | 1.0000 |
| 去方差惩罚 | 0.4400 | 0.1124 | 0.1398 | 1.0000 |
| 只保留 Top-4 候选 | 0.3200 | 0.1234 | 0.1545 | 1.0000 |

### 证据文件

主数值来自 `results/formal_experiment_summary.csv` 的名义场景；配置和方法定义分别见
`formal_experiment_metadata.json` 与 `src/causal_atlas_sim/formal_experiment.py`。

### 建议

这是最值得补正文的遗漏之一。它说明当前 DGP 中取消方差惩罚影响较小，而限制候选集合
造成更明显的发布和误差损失。结论必须限定在当前 DGP，不能写成方差惩罚普遍不重要。

### 候选正文

> Two prespecified ablations clarify which components matter in the nominal design. Removing the variance penalty changes release only from 0.463 to 0.440 and released-target MAE from 0.111 to 0.112. Restricting retrieval to the four nearest candidates has a larger effect, lowering release to 0.320 and increasing MAE to 0.123. In this DGP, access to a sufficiently rich candidate set matters more empirically than the variance regularizer, although this ordering need not persist when archive precisions are more heterogeneous.

## 4. 必须修正：ATLAS 与 no-rejection 不是表示比较

当前正文写道，ATLAS 与 no-rejection 是“公平的表示比较”。这个解释不成立：两者使用
同一套完整表示、候选和点权重，区别是 ATLAS 根据证书拒绝，而 no-rejection 强制发布。
同时，主表的 ATLAS MAE 是 139 个已发布目标上的条件 MAE 0.1109，no-rejection MAE 是
全部 300 个目标上的 MAE 0.1393。两者甚至不是同一个 target 子集上的无条件风险。

应把比较拆成三层：

1. ATLAS 对 no-rejection：展示选择/拒绝带来的风险--发布率权衡；
2. no-rejection ATLAS 对 semantic forced：两者都发布全部 target，用于比较完整表示组合与
   纯语义表示，MAE 分别为 0.1393 和 0.2491；
3. no-rejection ATLAS 对 latent Oracle：说明公开表示与仿真潜在机制信息之间仍有差距，
   但 Oracle 只可评价，不可部署。

建议把正文原句改为：

> The ATLAS--no-rejection contrast isolates the effect of selective release, although their MAEs are reported on different target populations. To isolate representation while holding publication fixed, we compare no-rejection ATLAS with semantic forced composition; their full-target MAEs are 0.139 and 0.249, respectively. The latent-support oracle remains evaluation-only.

证据来自 `results/synthetic_benchmark_summary.csv`、
`src/causal_atlas_sim/evaluation_baselines.py` 和正文主表生成器
`src/causal_atlas_sim/paper_figures.py`。这不是新增实验，而是对现有实验叙事的必要校正。

## 5. 完整 5x5 表示敏感性网格

正文 Figure 2C 已经展示全部 25 个单元，但文字只解释 proxy uncertainty `0.10`
的一条切片。完整数值位于：

- `results/representation_sensitivity_summary.csv`；
- `results/representation_sensitivity_metadata.json`；
- `results/tables/representation_sensitivity_tables.md`；
- `src/causal_atlas_sim/representation_sensitivity.py`；
- `scripts/run/run_representation_sensitivity.py`。

不建议再向正文加入 25 个数字。热图和当前切片已经完成正文论证，完整矩阵适合保留在
附录或可复现材料中。

## 6. 逐种子和 Monte Carlo 误差

正式结果还保存 Wilson 发布率区间、MAE Monte Carlo 标准误、跨种子标准差和 126 行
逐种子结果。它们对审计很重要，但正文主表已经较宽，不宜继续扩展。正文最多增加一句
“qualitative patterns were stable across the three prespecified seed batches”，详细数值留附录。
