# 05 Bridge design 的跨场景证据与诊断

## 1. 正文只写了 severe，仓库实际完成了四个支持场景

### 正文覆盖状态

Section 6.5 只报告 severe mismatch：causal greedy 把平均部分识别直径从 6.942 降到 1.877，缩减 72.96%。仓库的正式协议还包含 supported、moderate 和 strong 三个场景，每个“场景--策略”单元都是 3 个基础种子 × 100 次，共 300 条路径。

四个场景的 causal-support greedy 结果是：

| 场景 | 初始直径 | 最终直径 | 缩减比例 |
| --- | ---: | ---: | ---: |
| supported | 3.3502 | 2.3093 | 31.07% |
| moderate | 3.7867 | 2.0674 | 45.40% |
| strong | 5.5042 | 1.8620 | 66.17% |
| severe | 6.9423 | 1.8772 | 72.96% |

causal greedy 在四个场景中都得到最小平均最终直径，而且全部路径都选满预算 4。这个跨场景结果比只报告 severe 更能支持一个有限而清楚的结论：在当前候选库和 plug-in 规划模型下，使用完整设计表示的顺序选择优势并非只出现在最极端失配点。

注意，不能把缩减比例随 mismatch 单调上升解释成普遍规律。初始集合越宽，同一个候选库可缩减的绝对空间也可能越大；不同 DGP 和候选库不必保持同样排序。

### 对应文件

| 文件 | 提供的证据 |
| --- | --- |
| `results/bridge_experiment_summary.csv` | 4 场景 × 3 策略的 12 行正式结果 |
| `results/bridge_experiment_seed_summary.csv` | 36 行逐种子结果 |
| `results/bridge_experiment_metadata.json` | 候选库、预算、规划分布、种子和评价边界 |
| `results/tables/bridge_experiment_tables.md` | 完整正式结果表 |
| `docs/stages/bridge_experiment.md` | 条件边际 VoI、空交集和 claim 边界解释 |
| `src/causal_atlas_sim/bridge_experiment.py` | 正式候选生成、策略和汇总实现 |
| `src/causal_atlas_sim/algorithm1.py` | Algorithm 1 拒绝后启动 bridge 的统一入口 |
| `scripts/run/run_bridge_experiment.py` | 3,600 条正式策略路径入口 |

### 推荐正文位置与候选文本

建议紧接 severe 结果补一句跨场景概括，不需要把四行表放进正文。

> The advantage is not confined to the severe endpoint. Across supported, moderate, strong, and severe scenarios, causal-support greedy reduces mean diameter by 31.1%, 45.4%, 66.2%, and 73.0%, respectively, and attains the smallest mean final diameter among the three policies in every scenario under the fixed candidate library and planning model.

## 2. Semantic-only 规划会出现证书不一致

### 做了什么

实现没有把空的权重区间交集当作直径 0。根据 Lemma 5.1，空交集表示 archive 估计和声明证书在当前置信水平下相互冲突；程序记录规划不一致并停止该条路径的直径型规划。

完整四维评价表示下，三种策略的 evaluation inconsistency rate 都是 0。但 semantic-only greedy 在自己的规划表示下出现：

| 场景 | 规划不一致率 | 预算完成率 |
| --- | ---: | ---: |
| supported | 0.0067 | 0.9967 |
| moderate | 0.0200 | 0.9833 |
| strong | 0.0600 | 0.9433 |
| severe | 0.0367 | 0.9667 |

causal-support greedy 和 random 在这四个场景的规划不一致率均为 0。random 不计算条件边际 VoI，因而这里“不一致率为 0”不能被解释成它的规划证书更好；它只是没有经历同一种语义规划交集计算。

### 正文价值

这项结果值得在 Section 6.5 加一句，因为它说明完整表示的作用不仅是最终直径更小，还能避免纯语义规划层出现内部冲突。正文应同时说明完整四维评价交集均保持非空，防止读者把规划不一致误解为最终评价失败。

### 候选正文

> Semantic-only planning also produces an empty planning intersection on 0.7%--6.0% of paths across the four scenarios, causing early termination, whereas causal-support greedy completes the full budget on every path. All policies retain nonempty intersections under the common full-representation evaluation, so this discrepancy is a planning-representation diagnostic rather than an evaluation failure.

## 3. Bridge 确实补上了真实机制支持缺口

在 severe 场景中，causal greedy 选择后，target 到扩展 archive 真实机制凸包的平均距离从 1.0015 降到 0.0316。这与部分识别直径大幅下降方向一致，说明选中的 bridge 在仿真真实机制空间中确实接近 target 缺失的支持区域。

这是一个 **oracle、evaluation-only** 结果。真实应用中 target 和候选的真实机制不可见，选择器也从未读取这些坐标；选择只使用公开表示、估计效应、标准误和声明的规划模型。因此正文可以把它作为仿真机制检查，但不能把 oracle 距离写成可部署的选择准则。

### 候选正文

> As an evaluation-only mechanism check, the severe-scenario oracle distance from the target to the expanded archive hull falls from 1.001 to 0.032 after causal-support bridge selection. True mechanism coordinates are not read by the planner; they are used only after selection to verify that the chosen experiments fill the intended support gap.

## 4. Figure 4C 的路径数量需要写清楚

`bridge_budget_path_summary.csv` 有 15 行，即 3 个策略 × 5 个预算点。每个策略的曲线由 3 个种子 × 30 次 = 90 条路径汇总，因此：

- causal greedy：90 条；
- semantic greedy：90 条；
- random：90 条；
- 图中三策略合计：270 条路径。

当前 caption 的 “a focused 90-path visualization” 容易被理解成三条策略合计只有 90 条。更准确的表达应为 “90 paths per policy (270 policy paths in total)”。这组 focused path 只负责展示预算 0--4 的轨迹；正式跨场景结论仍来自每个场景、每个策略 300 次的主表。

### 对应文件

| 文件 | 提供的证据 |
| --- | --- |
| `results/bridge_budget_path_summary.csv` | 每策略每预算点的 90 次汇总 |
| `results/bridge_budget_path_metadata.json` | focused 路径的场景、种子、重复数和预算 |
| `scripts/run/run_bridge_budget_path_experiment.py` | Figure 4C 路径数据入口 |
| `src/causal_atlas_sim/paper_figures.py` | Figure 4 的构建与 caption 对应关系 |

### Caption 修订候选

> (c) Sequential bridge-budget paths in the severe-mismatch diagnostic, summarized over 90 paths per policy (270 policy paths in total); formal cross-policy claims use 300 repetitions per policy and scenario.

## 5. 小规模 exhaustive 对照已经写入正文，但边界材料更多

Section 6.5 已正确报告预算 1、2、3 时 greedy/exhaustive bridge value 比例为 0.9957、0.9776、0.9857，并明确 exhaustive 使用已实现结果，是 evaluation oracle。仓库还保存了恰好选中最优集合的比例 0.6667、0.3333、0.4333，以及每个预算枚举 12、66、220 个组合。

这些细节不必补进正文。正文现在的关键边界是正确的：本实验没有估计弱次模参数，也没有证明 Theorem 5.6 的理论近似系数。精确命中率和全部枚举表后续留附录。

### 对应文件

| 文件 | 提供的证据 |
| --- | --- |
| `results/bridge_optimality_summary.csv` | 三个预算的 value ratio、精确命中率和枚举量 |
| `results/bridge_optimality_metadata.json` | 30 次事后基准的固定协议 |
| `results/tables/bridge_optimality_tables.md` | 完整 exhaustive 表 |
| `scripts/run/run_bridge_optimality_experiment.py` | 复现入口 |

## 6. 只应保留到附录的 bridge 产物

下面内容已做完，但主文不宜展开：12 个候选的三类构成、3 点 Gauss--Hermite 求积细节、标准误 0.10、边际值最多 0.01 的测量误差、逐种子直径标准差，以及全部候选选择记录。它们用于审计 Definition 5.2 的数值实例化，不是新的正文结论。
