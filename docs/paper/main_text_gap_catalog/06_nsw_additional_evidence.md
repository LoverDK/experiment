# 06 NSW 正文需要补充的实现口径与结果解释

## 1. Restricted 与 design-enriched 表示的分工没有写进正文

### 为什么这是正文最重要的 NSW 遗漏

Section 6.6 说 local archive objects 来自协变量邻域，也报告了五种方法的指标，但没有告诉读者 Causal ATLAS 和 semantic baselines 分别看哪些坐标。没有这个信息，读者无法判断 MAE 差异究竟来自什么。

仓库使用两层公开表示：

| 表示 | 坐标 | 用途 |
| --- | --- | --- |
| restricted representation | age、education、black、hispanic、married、nodegree | 模拟只按人口学语义检索的表示；ATLAS 先用它筛出最近 24 个候选，semantic baselines 只使用这一层 |
| design-enriched representation | 上述 6 个坐标，再加 re74、re75、local overlap、local neighborhood radius | ATLAS 在候选内学习非负 simplex 组合权重并构造证书 |

这不是在声称研究者已知“哪些变量是真正因果变量”。它是对原论文未公开 coordinate split 的一个固定、可审计实例化：第二层加入基线收入和局部设计质量，检验遗漏效应相关协变量及设计坐标会怎样影响重建。

### 对应文件

| 文件 | 提供的证据 |
| --- | --- |
| `results/nsw_experiment_summary.csv` | 五种方法的 1,680 次评价合并指标 |
| `results/nsw_experiment_metadata.json` | 两套坐标、候选上限和方法口径 |
| `docs/stages/nsw_experiment.md` | 表示分工及其非因果变量声明 |
| `src/causal_atlas_sim/nsw_experiment.py` | 标准化、检索、权重与证书实现 |
| `tests/test_nsw_experiment.py` | target effect 与标准误防泄漏测试 |

### 推荐正文位置与候选文本

建议在 Section 6.6 第一段、local object 构造概述之后增加下面一段。这是 P0 级正文补充，因为它定义了真实数据比较的处理差异。

> We prespecify two public representations. The restricted representation contains age, education, race indicators, marital status, and no-degree status; the design-enriched representation additionally contains 1974 and 1975 earnings, local treatment overlap, and neighborhood radius. Causal ATLAS retrieves up to 24 candidates in the restricted coordinates and learns its convex composition in the enriched coordinates, whereas the semantic baselines use only the restricted representation. This split is a fixed, auditable implementation choice rather than a claim that the enriched coordinates are known causal variables.

## 2. Local object 的完整构造参数只写了一半

### 仓库实际协议

- 原始 NSW 文件共 445 人：185 treatment、260 control；
- outcome 是 1978 earnings，除以 1,000 后以千美元为单位；
- 8 个协变量在全部 445 人上按样本均值和样本标准差标准化；
- 每个候选中心取 50 个最近邻；每个邻域至少 8 个 treatment 和 8 个 control；
- 去除 center norm 与 neighborhood radius 各自最高 5% 的极端候选；
- 用确定性的 farthest-point coverage 保留 112 个 local objects；
- 正式对象内 treatment 数实际为 12--31，control 数为 19--38；
- 每个 local object 保存 treated-minus-control 局部对比、Welch 标准误、overlap 和 radius。

Section 6.6 当前只写“covariate neighborhoods with minimum treated and control support”，没有给 neighborhood size、对象数或局部对比定义。正文无需容纳全部参数，但至少应写 50-nearest-neighbor neighborhoods 和最终 112 个对象，避免真实数据实验显得不可复核。

### 对应文件

| 文件 | 提供的证据 |
| --- | --- |
| `data/nsw_dw.dta` | 固定的 NBER 原始数据快照 |
| `results/nsw_experiment_metadata.json` | 样本量、邻居数、筛选规则、对象数和 arm count 范围 |
| `results/nsw_archive_map_summary.csv` | 112 个对象的 PCA 坐标和 ATLAS 接受频率 |
| `docs/stages/nsw_experiment.md` | 局部 effect、标准误、overlap 和 radius 公式 |

### 候选正文

> We standardize eight baseline covariates and form 50-nearest-neighbor contexts subject to minimum treated and control counts. After excluding extreme centers and radii and applying deterministic farthest-point coverage, the archive contains 112 local objects constructed from 445 NSW observations (185 treated and 260 control).

## 3. Holdout 重复数及“1,680 次评价”的真实含义

每个固定种子生成 20 个对象级拆分，每次从 112 个 local objects 中无放回留出 28 个 target。因此每种方法的评价数为：

\[
28\;\text{holdouts}\times20\;\text{splits}\times3\;\text{seeds}=1{,}680.
\]

五种方法合计产生 8,400 条 target-method 记录。被留出的 target context、overlap 和 radius 可见，但 target 的局部 effect 和标准误不会传入任何估计器；它们只作为 noisy evaluation reference。

因为 local neighborhoods 会共享原始个体，这 1,680 条记录并非相互独立的 1,680 个统计样本。正文已经提到对象重叠和描述性边界，这一点写得正确。建议只在实验设置中补充 28 × 20 × 3 的协议，逐种子结果留附录。

### 候选正文

> For each of three fixed seeds, we generate 20 object-level splits and hold out 28 of the 112 local objects per split, yielding 1,680 target evaluations per method. Held-out effects and standard errors are inaccessible to every estimator and are retained only as noisy evaluation references; overlapping neighborhoods mean that these evaluations are not independent observational units.

## 4. ATLAS 与 no-rejection 的点指标为什么完全相同

### 肉眼可见的结果

主表中两者的 MAE、median absolute error 和 sign accuracy 完全相同：

| 方法 | MAE | Median AE | Sign accuracy | Coverage | Width | Rejection |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ATLAS | 0.8615 | 0.6989 | 0.8542 | 0.9744 | 5.6303 | 0.2321 |
| ATLAS no-rejection | 0.8615 | 0.6989 | 0.8542 | 0.9696 | 5.2749 | 0.0000 |

原因不是两种方法“偶然一样好”，而是实现有意让 no-rejection 使用与 ATLAS 完全相同的点权重和 raw prediction。两者只在是否执行拒绝，以及 no-rejection 区间保留的预设表示偏差比例上不同。NSW 表中 ATLAS 即使拒绝也仍保留 raw prediction 参加统一的全体 target 点误差评价，所以三个点指标数学上必然相同。

这和合成主表的口径不同：合成主表中的 ATLAS MAE 是已发布目标的条件 MAE，而 no-rejection MAE 是全部目标 MAE，不能直接把两者差值解释为表示收益。

### 正文价值与候选文本

建议在 Section 6.6 指标段后补一句，防止读者误以为拒绝没有作用。拒绝改变的是发布决策和证书报告，不会回头改写已经计算好的 raw prediction。

> ATLAS and its no-rejection counterpart have identical point metrics by construction because they use the same composition weights and raw predictions, which are evaluated on all held-out objects. Their difference lies in the release decision and certificate interval, not in the point estimator itself.

## 5. 正确解释 NSW 的三个比较

仓库的结果支持三种不同问题，不能混成一个“ATLAS 更好”的比较：

1. **ATLAS 对 no-rejection**：相同点估计，比较拒绝与证书报告的作用；
2. **no-rejection ATLAS 对 semantic forced**：都强制给出点预测，比较 design-enriched composition 与 restricted semantic weighting；MAE 为 0.862 对 1.169；
3. **no-rejection ATLAS 对 evaluation-only Oracle**：NSW 没有真实机制或无噪声 subgroup truth，因此不存在合成实验那种 latent Oracle，此比较不能在 NSW 中进行。

当前正文已经正确把 held-out local contrast 称为 noisy reference，没有把 0.974 inclusion 写成真实 subgroup-effect coverage。这一边界应保持。

## 6. 只应保留在附录或复现材料的 NSW 产物

以下内容已经完成，但不建议挤入正文：

- 112 个对象逐点的 PCA 坐标与接受频率；
- 1,680 条 ATLAS target 诊断和三个种子的逐种子指标；
- 原始数据 SHA-256、精确下载地址与校验失败规则；
- center norm/radius 的 0.95 分位筛选细节；
- 最大候选数 24、容忍度 3.30、权重迭代次数 300 和数值收敛阈值；
- target effect 和 target standard error 防泄漏单元测试。

它们对审计和复现很重要，但不会改变正文的科学结论。

### 文件位置

| 文件 | 用途 |
| --- | --- |
| `results/nsw_experiment_seed_summary.csv` | 五种方法的逐种子结果 |
| `results/nsw_method_error_records.csv` | 五种方法在共享 holdout 上的逐目标误差与区间记录 |
| `results/nsw_diagnostics_summary.csv` | target 级重建、接受状态和证书分量 |
| `results/nsw_archive_map_summary.csv` | archive map 数据 |
| `results/figures/nsw_diagnostics_overview.pdf` | 正文 Figure 5 的矢量版本 |
| `results/tables/nsw_experiment_tables.md` | 完整 NSW 指标表 |
| `scripts/run/run_nsw_experiment.py` | 正式复现入口 |

## 7. 本主题的正文取舍

建议正文补三项：两套表示的坐标分工、112 个 local objects 与 1,680 次 holdout 的基本协议、ATLAS/no-rejection 点指标相同的构造原因。完整预处理、逐种子和数据完整性信息后续统一进入附录。
