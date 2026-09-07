# 04：拒绝之后，部分识别与 bridge 怎样运行

本章读 [partial_identification.py](../../../src/causal_atlas_sim/partial_identification.py)、[algorithm1.py](../../../src/causal_atlas_sim/algorithm1.py)、[minimax_experiment.py](../../../src/causal_atlas_sim/minimax_experiment.py)、[bridge_experiment.py](../../../src/causal_atlas_sim/bridge_experiment.py)。bridge 的后补集合审计在第 8 章。

## 1. Algorithm 1 的第一个分叉

`run_algorithm1` 首先调用 `fit_causal_atlas`。若 `atlas_result.accepted`，立刻返回；PI 字段为 None，所选 bridge 列表和路径为空。若拒绝，才调用 `construct_partial_identification_interval`。

`fit_reject_or_identify` 只是兼容包装：构造 Algorithm1Config、执行 Algorithm 1，再从结果取出 atlas_result 和 partial_interval。它的局部 import 用来避免两个模块相互导入时出现循环。

## 2. `_weight_family`：为什么需要多套权重

源码先检索相容候选，又单独收集全部设计相容源。权重族包括：

1. 在全部相容源上优化的 support_optimized 权重；它不局限于检索 top-k。
2. 全部相容源的均匀权重 compatible_uniform。
3. 最多四个检索近邻的 singleton 权重，每套只给一个源权重 1。

最后通过 `np.allclose` 去掉数值相同的权重。`weights.copy()` 防止以后修改原数组影响保存的族。权重族数量通常至多六个，但去重后可以更少。

它是一组有限、可实际计算的候选组合。代码没有遍历单纯形里无限多套权重，因此不能把其交集等同于任意模型下最紧的全部识别集合。

## 3. 多个区间怎样取交集

源码核心：

```python
component_zeta = config.zeta / len(weights)
certificate_config = replace(config, zeta=component_zeta)
```

若总 zeta=.05，有六套不同权重，每套用 .05/6。这样每个分量区间使用更保守的失败概率分配，目的在于同时有效的控制。这里使用完整 certificate.radius，而不是第 2 章 Wald 区间半径。

循环对每套 weights_value：调用 compute_certificate；计算加权源效应 center；保存 center-radius、center+radius。

```python
interval_lower = max(lower_bounds)
interval_upper = min(upper_bounds)
```

教学例子：三个区间 `[0,4]`、`[1,5]`、`[-1,3]`，交集为 `[1,3]`，宽 2。若其中一个是 `[5,6]`，则 max lower=5、min upper=3，交集为空。

`PartialIdentificationInterval.nonempty` 检查 lower<=upper，`width` 在空交集时返回 None，`contains(truth)` 对空集合返回 False。空集合表示证据区间不相容，不能画成“宽度 0，信息最好”。

`reference_width` 是第一套 support_optimized 分量的全宽 `2*radii[0]`，它不是 oracle 真值范围。

## 4. PI 实验的每次重复

入口：[run_partial_identification_experiment.py](../../../scripts/run/run_partial_identification_experiment.py)。配置三组 seed 20260911–20260913，各 100 次。`run_partial_identification_experiment` 逐场景生成 archive，对目标运行拒绝/PI，再用真实目标效应计算是否被 PI 包含。

`oracle_hull_distance` 读取真实机制，在凸权重下最小化目标到真实源凸包的距离。它是评价变量，不传给可部署拟合。其迭代也用 simplex 投影，步长由源机制矩阵谱范数确定。

`_summarize_one` 区分所有目标和 rejected 子集，统计拒绝率、非空 PI、覆盖和宽度。当前包装只在拒绝时构造 PI，因此 partial_records 与 rejected 集合对应；空交集在 contains 中计为未覆盖，宽度平均仅纳入非空交集。具体输出列定义见返回类 `PartialIdentificationSummaryRow`。逐次记录存于内存 result.records；runner 保存 `results/partial_identification_summary.csv` 与 `results/partial_identification_seed_summary.csv`，没有单独的逐次 records CSV。

解释图表时同时看覆盖和宽度：一个很宽但包含真值的集合，与一个窄而漏掉真值的集合反映不同问题。空集合比例也必须另看。

## 5. minimax 实验使用另一种生成模型

入口：[run_minimax_experiment.py](../../../scripts/run/run_minimax_experiment.py)。此处不生成 400 人 AIPW 数据，而是直接生成源实验效应的高斯摘要，用于展示下界构造。

`minimax_parameters` 先算 `information=archive_count/archive_standard_error**2`，再 `estimator_standard_error=1/sqrt(information)`。所有源标准误相同，所以这等于源 SE 除以根号源数。

几何量：`geometric_scale=min(L*hull_distance,effect_absolute_bound)`，再取四分之一为正负替代世界的目标幅度。`geometric_surface_value` 在源位置 0 取 0，在目标位置 d 取正或负幅度，中间是有界线性坡面。

统计量：`information_scale=min(estimator_standard_error,effect_absolute_bound)`，乘 `le_cam_constant` 得到正负常数世界幅度；下界使用源码相应系数。`combined_lower_bound=max(geometric_lower_bound,statistical_lower_bound)`。

## 6. 两种困难如何分别模拟

```python
geometric_observations = standard_errors * rng.normal(size=config.archive_count)
```

几何正负世界有完全相同的源分布，因此同一次源数据与同一估计，分别和正目标、负目标比较绝对误差。再分别生成 statistical_positive_observations 和 statistical_negative_observations，这两个是不同均值的独立高斯抽样。

`_inverse_variance_estimate` 用 `standard_errors**-2` 归一化加权。`MinimaxRecord` 保存四个正负世界误差。汇总器对各世界计算平均风险，并对照解析参考量和下界。它展示特定构造与具体估计器的风险，不会通过有限模拟证明“所有估计器”都满足下界；后者属于理论证明。

默认三组 seed 20261011–20261013，各 100 次。逐次 MinimaxRecord 在内存中；runner 保存 `results/minimax_experiment_summary.csv`、`results/minimax_experiment_seed_summary.csv` 和 `results/minimax_experiment_metadata.json`，没有单独的逐次 records CSV。

## 7. bridge 候选对象的哪些字段能用

`BridgeCandidate` 包含 key、family、公开表示、预期 standard_error、隐藏半径，也包含用于模拟评价的 mechanism、true_effect、observed_effect。

选择前，算法只能用公开表示、设计标准误与半径。observed_effect 只有该候选被选中后才能加入 archive；true_effect 和 mechanism 用于评价，不用于挑选。

`_candidate_experiment` 把候选包装成 ExperimentData。原始受试者数组填空数组，true_effect 填 NaN，mechanism 用公开坐标占位重建，避免 planning 读取模拟真机制。其输入 estimated_effect 可以是假设观测，也可以是选中后真正揭示的观测。

## 8. 12 个候选是怎样人为设计的

`_build_bridge_library` 以目标公开表示为中心，加预先指定的 12 个 offset，然后 clip 到 [-1,1]。前三族各四项：causal_full 四维都近；semantic_trap 前两维近而 h/q 较远；mixed 中间状态。

候选真实 h 在代理允许范围内再随机扰动，候选真效应由原曲面计算，observed_effect=真效应+标准误*正态随机数，默认 bridge SE=.10。这是摘要层模拟，不再生成一个新 400 人数据集。

候选库本身包含有利与干扰设计，用于检验选择机制。结果不能直接代表任意现实实验库的优劣分布。

## 9. 选择前怎样算“预期区间宽度”

`expected_partial_id_diameter` 将候选暂作目标，用现有 archive 预测其均值。如果没有预测，退回源效应平均。然后：

```python
nodes, weights = np.polynomial.hermite.hermgauss(quadrature_points)
hypothetical_effect = predictive_mean + np.sqrt(2.0) * candidate.standard_error * node
```

默认三点 Gauss-Hermite 求积，用少量带权节点近似正态分布积分。对于每个假设候选结果，临时增广 archive，重新构造目标 PI，取宽度乘求积权重。总和除以 sqrt(pi) 完成正态积分归一化。

这估计的是给定 plug-in 预测均值和设计方差下的条件期望。它不预先读取 candidate.observed_effect，也不使用 future 真值。积分模型错误时，其选择收益也会受到影响。

## 10. `run_algorithm1` 的逐轮选择

`sources=list(archive)` 是可追加的当前证据，`remaining=list(bridge_library)` 是未选候选，`selected=[]` 记录已选项。

每轮先检查 planning_interval 的直径有限。对每个候选算 expected_diameter，再算 `marginal=current_planning_diameter-expected_diameter`。若设置 selection_error_bound，加入范围内均匀扰动。

`scores.append((marginal+error,-index,marginal,abs(error)))` 保存四元组；`max` 首先比含误差的得分，并以 -index 决定平局。因此相同最高得分倾向原列表较前候选。非有限得分先过滤；一个也没有则停止并保留原因。

随机策略直接 `rng.integers(len(remaining))` 选下标。选中后 `remaining.pop(chosen_index)` 从未选列表移除，`selected.append(chosen)` 留档，`sources.append(_candidate_experiment(...,chosen.observed_effect))` 才揭示观测。

然后分别重新算 planning 和 evaluation PI。语义策略 planning_dimensions=(0,1)，评价仍使用完整配置；因此有两条宽度路径。不能用二维 planning 的改善替代完整表示下的评价改善。

预算结束或不相容停止后，返回初始和更新 PI、候选 key/family、边际得分、两条路径、选择误差和 stopping_reason。

## 11. bridge benchmark 的外层循环

入口：[run_bridge_experiment.py](../../../scripts/run/run_bridge_experiment.py)。四个 shift 场景 0/.25/.60/.80；每场景三组 seed 各 100 次；每次三策略 causal_greedy、semantic_greedy、random，共 3600 条 policy path。

`BridgeExperimentConfig.support_tolerance=0` 会把普通目标导入拒绝分支来研究 bridge，包括名为 supported 的场景。不要把这里进入 bridge 的频率当作正文阈值 1.65 下的实际拒绝频率。

`_run_policy` 在算法完成后才计算 initial/final oracle hull distance 和已选 bridge 观测误差。`_summarize_one` 单独报告 planning/evaluation 不相容率、完成预算率、实际选择个数、有限直径记录数和收缩量。有限直径均值的分母不包含非有限路径，因此必须同时读有限数和失败率。

## 12. 预算路径与事后穷举

`bridge_budget_path_rows` 读取已存路径，不重新选实验。budget=0 对应初始宽度，budget=1 对应第一步。如果某次提前停止，用 `min(budget,len(path)-1)` 延用最后状态；每个预算平均前过滤有限值。

[run_bridge_budget_path_experiment.py](../../../scripts/run/run_bridge_budget_path_experiment.py) 实际重新运行 severe 场景，每个 seed 30 次，共每策略 90 条路径，再调用上述汇总函数。它覆盖正式 bridge runner 也写入的 `results/bridge_budget_path_summary.csv`，所以复现论文图时需先正式 bridge、后 focused path。正式四场景结论仍来自每策略每场景 300 次的汇总。

`run_bridge_optimality_experiment` 默认 30 次 severe 场景，budget=1/2/3。`combinations(candidates,budget)` 穷举恰好该预算的子集，分别 12、66、220 个；每个子集用其已知 observed_effect 构造 PI，并取最小有限宽度作为事后 oracle。

`greedy_to_optimal_value_ratio` 是“平均 greedy 收缩 / 平均 optimal 收缩”，不是每次比值的平均。它也不是理论中期望集合函数的同义量。完整观测已用于 oracle 比较，不能把事后最优策略作为无需额外信息的可实施基线。

正式 bridge 的逐次 BridgeRecord 存在内存 result.records，runner 输出 `results/bridge_experiment_summary.csv`、`results/bridge_experiment_seed_summary.csv` 与 metadata；路径和穷举另输出 `results/bridge_budget_path_summary.csv`、`results/bridge_optimality_summary.csv`。没有单独的原始 bridge_records CSV。后补 v2/v3 使用另一套六候选集合积分，下一步见第 8 章。
