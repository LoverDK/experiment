# 04 部分识别补充证据与 minimax 下界

## 1. 多权重交集确实缩短了部分识别区间

### 正文覆盖状态

Section 6.4 已写四个支持场景中的拒绝率、部分识别直径、非空率和覆盖率，但没有解释为什么实现要对多个有效权重区间取交集，而不是只报告 support-optimized 权重对应的一个区间。

仓库固定了三类设计兼容权重：support-optimized 权重、全部兼容 archive 的均匀权重、四个最近兼容邻居的 singleton 权重。重复权重删除后，把总失败概率 0.05 平均分给实际保留的权重，再对各自的 Theorem 5.1 区间取交集。

结果表明，交集相对于同一 Bonferroni 水平下的单个 support-optimized 参考区间，平均宽度分别缩短：

| 场景 | 交集宽度 | 单权重参考宽度 | 相对缩短 |
| --- | ---: | ---: | ---: |
| nominal | 3.6462 | 3.7518 | 2.74% |
| mismatch 0.25 | 4.0945 | 4.3425 | 5.14% |
| mismatch 0.60 | 5.6743 | 6.4837 | 11.43% |
| mismatch 0.80 | 7.0760 | 8.0676 | 11.25% |

该收缩不是额外假设带来的“免费精度”，而是把多个同时有效的 archive 约束联合起来。正文可以在 Table 2 后补一句；完整四行表不必重复主表。

### 对应文件

| 文件 | 提供的证据 |
| --- | --- |
| `results/partial_identification_summary.csv` | 四场景交集宽度、单区间宽度和收缩比例 |
| `results/partial_identification_seed_summary.csv` | 逐种子覆盖率和宽度 |
| `results/partial_identification_metadata.json` | 权重族、失败概率和固定协议 |
| `docs/stages/partial_identification_experiment.md` | 权重去重、失败概率重分配和空交集解释 |
| `src/causal_atlas_sim/partial_identification.py` | Theorem 5.4 区间交集实现 |
| `scripts/run/run_partial_identification_experiment.py` | 复现入口 |

### 候选正文

> Intersecting the simultaneously valid weight-specific intervals is informative beyond the support-optimized interval alone. Relative to that single-reference interval at the same Bonferroni allocation, the intersection reduces mean width by 2.7% in the nominal scenario and by 11.4% and 11.3% under strong and severe mismatch, respectively.

## 2. Oracle 凸包距离和非识别分离量

### 仓库做了什么

仿真在估计完成后，使用真实机制坐标计算 target 到设计兼容 archive 凸包的距离，并根据 Theorem 5.4 的证明构造计算非识别分离量。它们随失配加重而增长：

| 场景 | Oracle 凸包距离 | 非识别分离量 |
| --- | ---: | ---: |
| nominal | 0.0000 | 0.0000 |
| mismatch 0.25 | 0.1325 | 0.3459 |
| mismatch 0.60 | 0.6471 | 1.6890 |
| mismatch 0.80 | 0.9974 | 2.5976 |

Section 6.4 的 Figure 4A 已使用 evaluation-only support 的概念，文字却没有给出这些量的数值，也没有把它们与拒绝率、区间宽度共同上升的关系说清楚。

### 信息边界

这两个量含有仿真真实机制信息，不能进入算法、检索、权重、拒绝或真实数据应用。它们只能在仿真结束后用于解释“人为设置的 support shift 是否真的造成了机制空间支持不足”。正文若补充，必须明确写 `evaluation-only` 或 `oracle`。

### 候选正文

> The evaluation-only distance from the target mechanism to the compatible archive hull increases from essentially zero to 0.133, 0.647, and 0.997 as mismatch grows; the corresponding nonidentification separation increases to 0.346, 1.689, and 2.598. These oracle diagnostics are never available to the procedure, but confirm that the widening reported sets track the intended loss of support.

## 3. Theorem 5.5 的 minimax 数值实验完全未进入正文

### 为什么这是重要遗漏

当前 Section 6 从部分识别直接进入 bridge design，没有给 Theorem 5.5 任何数值对应。仓库实际上已经完成 8 个预设场景、3 个基础种子、每场景每种子 100 次、共 2,400 次的下界实验。它将定理证明中的两个困难来源分别实例化：

1. **几何不可识别项**：target 离 archive 凸包越远，两个在 archive 上完全相同的效应曲面可以在 target 处相差越大；
2. **有限精度统计项**：即使 target 位于凸包内，archive 标准误仍使两个高斯世界难以区分。

实验使用保守常数 L=2.61、效应绝对值界 M=3.88，并把证明中的构造常数固定为 1/4 和 0.09375。它同时运行 inverse-variance archive mean 作为可核对的代表性估计器；该估计器不是新 ATLAS，也没有被声称为 minimax 最优。

### 正文最值得报告的数值

- 当凸包距离为 0 时，几何下界为 0，但 archive 标准误从 0.35 增至 1.20 会使统计构造下界从 0.0116 增至 0.0398，代表性估计器的经验最坏 MAE 从 0.0989 增至 0.3391；
- 当距离为 0.60、archive 标准误为 0.35 时，构造下界为 0.3915，经验最坏 MAE 为 0.3918；
- 当距离为 1.00、archive 标准误为 0.35 时，构造下界为 0.6525，经验最坏 MAE 为 0.6528。

后两组数值非常接近，只说明在这两个受限证明子模型和当前参数下几何项主导风险。它们不能证明全模型类的常数最优，更不能证明该代表性估计器达到全局 minimax 最优。

### 对应文件

| 文件 | 提供的证据 |
| --- | --- |
| `results/minimax_experiment_summary.csv` | 8 个场景的两项构造下界、经验风险和解析风险 |
| `results/minimax_experiment_seed_summary.csv` | 逐种子最坏风险 |
| `results/minimax_experiment_metadata.json` | 距离、噪声、构造常数和固定种子 |
| `results/figures/minimax_experiment_overview.png` | 几何项、统计项与代表性风险总览 |
| `results/tables/minimax_experiment_tables.md` | 完整数值表 |
| `docs/stages/minimax_experiment.md` | 两个证明子模型与 claim 边界 |
| `src/causal_atlas_sim/minimax_experiment.py` | 二点构造、下界和代表性估计器实现 |
| `scripts/run/run_minimax_experiment.py` | 正式复现入口 |

### 推荐插入位置

建议在 Section 6.4 末尾、进入 Bridge Experiment Design 之前增加一个短段落，标题不必另起小节。正文只需保留“距离为零时仍有统计困难”和“距离较大时几何下界主导”两层结论；完整 8 行表和 Figure 留附录。

### 候选正文

> A numerical instantiation of the two proof submodels in Theorem 5.5 separates geometric nonidentification from finite archive precision. When the target lies in the archive hull, the geometric term vanishes but increasing the common archive standard error from 0.35 to 1.20 raises the empirical worst-case MAE of an inverse-variance reference estimator from 0.099 to 0.339. With precise archives, increasing the hull distance to 0.60 and 1.00 yields constructed lower bounds of 0.392 and 0.653, closely matched by empirical worst-case MAEs of 0.392 and 0.653. This experiment illustrates the theorem's two restricted proof submodels; it is neither a numerical proof of the minimax theorem nor evidence that the reference estimator is globally minimax optimal.

## 4. 本主题的正文取舍

建议补入：一条多权重宽度收缩、一条明确标注 oracle 的支持诊断、一个 minimax 短段。逐种子表、全部八个场景和下界常数推导后续放附录。这样可以把正文逻辑补成“拒绝为何发生、拒绝后集合为何变宽、这种困难为何具有理论下界、bridge 为什么有必要”。
