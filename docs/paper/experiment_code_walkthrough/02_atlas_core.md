# 02：ATLAS 从公开信息到发布决定的完整计算

源码：[methods.py](../../../src/causal_atlas_sim/methods.py)。入口函数是 `fit_causal_atlas`。本章讲的计算由大量实验共同调用，后续章节只解释各实验怎样改变输入和汇总输出。

## 1. 先读返回对象，知道最后要得到什么

`AtlasResult` 的字段：

| 字段 | 含义 |
| --- | --- |
| `candidate_indices` | 可用源对象在原 archive 中的下标 |
| `candidate_distances` | 候选与目标公开表示的距离 |
| `weights` | 对整个 archive 的权重，未入选源为 0 |
| `raw_point_estimate` | 内部算出的点估计；无候选时 None |
| `point_estimate` | 实际发布的点估计；拒绝时 None |
| `accepted` | 布尔发布决定 |
| `rejection_reason` | 拒绝原因文本 |
| `certificate` | 五个分项与总半径 |
| `interval_lower/upper` | 即使点估计被拒绝也可能保留的区间 |
| `objective_value` | 数值优化目标函数的最终值 |

`raw_point_estimate` 不为空而 `point_estimate` 为空，通常表示正常拒绝。它不是运算失败，也不是“预测值为零”。

## 2. 第一阶段：候选检索

调用顺序：

```python
retrieved = retrieve_semantic_candidates(archive, target, config=config)
candidates = filter_design_compatible_candidates(archive, target, retrieved)
```

`_observed_representation` 先取 `observed_representation`。配置 `representation_dimensions=None` 时保留四维；设为 `(0,1)` 时只取前两个坐标。这个选择会影响检索、优化、证书中的几何量，不能仅当成绘图选轴。

`retrieve_semantic_candidates` 对每个源计算 `norm(source_rep-target_rep)`，把 `(距离, 原下标)` 放进列表。排序用 `(item[0],item[1])`，所以距离相同会按原下标稳定决定顺序。若指定 `semantic_radius`，丢掉太远的对象；若指定 `max_candidates`，取前 k 个。

名字含 semantic 不代表永远只看 s1、s2，实际维度由 config 决定。正式消融和诊断模块传入的 config 并非完全相同，详见第 3 章。

`design_compatible` 要求 source 与 target 的 `design`、`assumption_profile` 都相等。这个实现是记录字段的相等判断，不会自动理解自然语言描述中两个 estimand 是否等价。

## 3. 没有候选时为什么不进入优化

若 `not candidates`，程序返回零权重、无点估计、无限证书、NaN 区间及拒绝理由。继续在空集合上优化没有含义，因此这里提前 return。后续 CSV 汇总是否排除这些 NaN，必须读对应汇总器。

## 4. 进入 `optimize_support_weights`

设实际候选 k 个、表示 d 维：

```python
representations = np.vstack([...])
standard_error_squares = np.array([...])
hidden_radii = np.array([...])
```

这里省略的是按候选下标取字段的列表推导式。三个变量形状依次为 `(k,d)`、`(k,)`、`(k,)`。目标表示是 `(d,)`。以下用 R 代表 representations、t 代表目标、w 代表候选权重。

源码目标函数：

```python
residual = target_representation - weights @ representations
return float(
    residual @ residual
    + config.lambda_sigma * np.sum(weights**2 * standard_error_squares)
    + hidden_gradient @ weights
)
```

第一项让加权表示接近目标；第二项避免过多依赖标准误大的源；第三项让权重考虑源的隐藏不确定性。`hidden_gradient = lambda_hidden * L_h * hidden_radii`。目标自己的隐藏半径不随 w 改变，省略它不影响最优权重。

注意优化目标不是最终证书半径：这里用平方残差、方差惩罚和线性隐藏项；证书中还包含曲率、统计分位系数等。`objective_value` 与 `certificate.radius` 数值通常不同。

## 5. 梯度是什么，代码怎样用它

源码：

```python
residual = weights @ representations - target_representation
return (
    2.0 * representations @ residual
    + 2.0 * config.lambda_sigma * weights * standard_error_squares
    + hidden_gradient
)
```

梯度的第 j 项描述稍微增加 w[j] 时目标函数增加的速度。第一块 `(k,d) @ (d,)` 得到 k 项；后两块也是 k 项，因此能逐项相加。更新时沿负梯度移动。

`weights=np.full(k,1/k)` 先均匀赋权。`step` 是移动步长。每轮提议 `weights-step*gradient(weights)`，再投影到非负、和为 1 的集合。

接受条件是新目标值不大于旧值加 `1e-14` 浮点容差。接受后步长最多放大 5%，上限 1；变化量小于 `convergence_tolerance` 则停止。不接受则步长减半，太小也停止。最多 800 次是默认数值预算，不代表一定执行满 800 次。

## 6. `_project_to_simplex` 为什么要排序

任意负梯度更新可能产生负权重或和不等于 1。投影寻找距离提议向量最近的合法权重。源码依次：

1. `np.sort(values)[::-1]`：降序排列，`[::-1]` 是反向切片。
2. `np.cumsum`：得到前 1、前 2、……项累计和。
3. `eligible=...>0`：找在共同平移后仍可为正的活动坐标。
4. `np.flatnonzero(eligible)[-1]`：最后一个活动下标 rho。
5. `threshold=(cumulative[rho]-1)/(rho+1)`：需要统一减掉的量。
6. `np.maximum(values-threshold,0)`：负数截成 0，剩余项刚好加成 1。

教学例子：提议 `[.8,.5,-.1]` 排序后前两项和 1.3，阈值 .15；得到 `[.65,.35,0]`。这不是简单除以总和，简单归一化不能同时处理负数。

最后 `full_weights=np.zeros(len(archive))`，再 `full_weights[list(indices)]=weights`。如果候选下标是 `[5,2]`，候选第一项权重写回原 archive 的第 5 项，第二项写回第 2 项，避免位置错配。

## 7. 五项证书逐项计算

`compute_certificate` 先检查权重长度正确、非负且和为 1，然后计算 `weighted_representation=weights@representations`。

### 7.1 表示残差项

`representation_term = L * norm(target_representation-weighted_representation)`。

目标与源加权表示越不一致，该项越大。L 默认 2.61。这里只有公开表示，没有访问 `mechanism`。

### 7.2 曲率项

`dispersion = sum(w_i * norm(r_i-r_bar)**2)`，再乘 `H/2`，默认 H=1.80。即使 r_bar 正好等于目标，各源分散时非线性函数的平均仍可能偏离目标函数值，故该项可能非零。

### 7.3 隐藏调节项

`hidden_moderator_term = L_h*(target_radius + weights@archive_radii)`，默认 L_h=1.55。当目标和所有源半径都 .20 时，由于权重和 1，此项恒为 `1.55*(.20+.20)=.62`。这能解释为什么某些图中隐藏项是一条固定高度的色带。

### 7.4 nuisance 偏差项

`bias_term=sum(w_i*nuisance_bias_bound_i)`。基础 DGP 每个值为 0，所以此项为 0。真实拟合 nuisance 时置零是否有保证，需要另外讨论，代码不会自行推导有效偏差界。

### 7.5 统计项

源码结构：

```python
sqrt(2.0 * log(2.0 / config.zeta)
     * sum(weight**2 * experiment.standard_error_certificate**2
           for weight, experiment in zip(weights, archive, strict=True)))
```

源独立时加权估计的方差形式为 `sum(w_i**2*s_i**2)`，不是 `sum(w_i*s_i)`，也不是标准误简单平均。`zeta=.05` 时外侧系数是 `sqrt(2*log(40))`。最后将这五项相加得到 `Certificate.radius`。

## 8. 区间半径与拒绝半径有两个公式

`honest_interval_radius` 取前四项之和，加 `NormalDist().inv_cdf(1-zeta/2)*SE`。zeta=.05 时这个分位数约 1.96。拒绝半径使用上一节较大的 `sqrt(2*log(40))` 系数。

教学例子：前四项合计 1，SE=.2，则拒绝半径约 1.543，区间半径约 1.392。不能从区间全宽除以二反推拒绝半径。两者都利用估计标准误；函数名里的 honest 不替代实际适用条件。

## 9. 点估计与发布决定

```python
raw = float(sum(weight * experiment.estimated_effect
                for weight, experiment in zip(weights, archive, strict=True)))
accepted = bool(certificate.radius <= config.scientific_tolerance + 1e-12)
```

第一行只加权源效应估计。第二行不使用目标真值或实际误差，只比较证书与事先给定容忍度。默认容忍度 1.65。返回区间是 `raw ± honest_interval_radius(...)`，发布值是 `raw if accepted else None`。

所以“误差小却被拒绝”是可能的。证书是保守上界式评分，不是一次实验实际误差的预测器。

## 10. 五种原始方法分别走哪里

| 方法 | 源权重 | 点估计是否可能拒绝 |
| --- | --- | --- |
| `atlas` | 上述约束优化 | 是 |
| `atlas_no_rejection` | 调用同一 ATLAS 拟合，保留权重 | 有 raw 时总发布 |
| `semantic_forced` | `1/max(distance,1e-8)` 再归一化 | 总发布 |
| `nearest_semantic` | 最近相容源权重 1 | 总发布 |
| `global_mean` | 所有相容源均匀权重 | 总发布 |

`_uniform_result` 和 `_result_from_weights` 统一把基线权重转成结果、证书、区间。基线是否用两维还是四维必须检查调用者传入的配置。

`fit_method('atlas',...)` 经由 `run_algorithm1(...).atlas_result` 返回，默认 bridge 预算 0。若被拒绝，Algorithm 1 仍可能构造 PI，但此接口最终只交回 AtlasResult。直接调 `fit_causal_atlas` 不执行 PI。

`evaluation_baselines.py::fit_oracle_latent_support` 使用真实潜在机制替换表示，只作评价对照。它不属于现实可部署的信息预算。

## 11. 一次拟合的人工检查顺序

先看候选下标，再检查权重非负、和 1，再独立加权源效应，最后相加五项证书并与 1.65 比较。第 10 章提供不写文件的可运行例子。完成这一步后，后续大实验只是反复进行此计算，并改变输入和统计分组。
