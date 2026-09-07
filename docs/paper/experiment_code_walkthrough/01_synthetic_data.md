# 01：一套合成 archive 是怎样生成的

源码：[dgp.py](../../../src/causal_atlas_sim/dgp.py)。先找 `SimulationConfig`，再找 `generate_minimal_archive`，最后读 `_generate_experiment`。源码顺序中的辅助报告函数可以第二遍阅读。

## 1. 先分清两层“实验”

`ExperimentData` 是一个受试者实验：400 个人，一份处理效应估计，一个四维实验表示。`GeneratedArchive` 是一次迁移任务：8 个源 ExperimentData，加 1 个目标 ExperimentData。Monte Carlo 的一次 replicate 重新生成整个迁移任务。

因此 300 次重复既不等于 300 人，也不等于一个固定 archive 上训练 300 次。每次有 8 个源实验，每个默认 400 人；目标默认再生成 400 人用于评价参考值。

## 2. 配置逐字段读

| 字段 | 默认值 | 代码中在哪里起作用 |
| --- | --- | --- |
| `n_archive` | 8 | 源机制数量、权重长度、子随机流数量 |
| `n_units_per_experiment` | 400 | 每个源对象的数组行数 |
| `n_units_target` | 400 | 目标对象的数组行数 |
| `propensity` | 0.5 | 处理分组概率和 AIPW 分母 |
| `overlap_lower_bound` | 0.10 | 参数合法性检查 |
| `outcome_noise_sd` | 1.0 | 两个潜在结果的高斯噪声标准差 |
| `moderator_sensitivity_radius` | 0.20 | 对隐藏坐标不确定性的声明半径参数 |
| `moderator_proxy_half_width` | 0.10 | 代理噪声的均匀分布半宽 |
| `archive_moderator_radius_spread` | 0 | 源对象之间声明半径逐步增加 |
| `target_shift_fraction` | 0 | 目标向指定四维锚点移动的比例 |
| `target_hidden_shift_fraction` | 0 | 额外只移动第 2 个，即 h 坐标 |
| `target_shift_anchor` | `(1,-1,1,-1)` | 目标移动的终点 |

`__post_init__` 检查半径足够包含代理相容集合直径，因此要求 `2 * moderator_proxy_half_width <= moderator_sensitivity_radius`。这里两个参数的含义不同，不能只把声明半径调小而维持较大的代理噪声。

## 3. 四维机制和效应曲面

`Mechanism(s1, s2, h, q)` 用四个数描述一个实验的真实机制，`.as_array()` 把对象变成 shape `(4,)` 的数组。`from_array` 检查恰好四项，再构造对象。`cls(*map(float, value))` 先逐项转浮点数，再把四项展开成四个参数。

`effect_surface` 的完整数值公式：

```python
1.15 * np.sin(1.1 * s1)
+ 0.65 * s2
+ 1.10 * h
+ 0.45 * s1 * h
- 0.28 * q**2
+ 0.25 * np.cos(s2 + q)
```

各行分别加入正弦项、线性项、隐藏调节项、交互项、二次项和余弦交互。传入同一机制就得到同一个真实 ATE。它不是从观测数据拟合的模型，是作者预先规定的生成真值。

`effect_gradient` 和 `effect_hessian` 是对应解析导数，用于检查已声明的光滑性界。顶部常数 `2.61`、`1.80`、`1.55` 分别用于整体 Lipschitz、曲率、隐藏坐标变化界。对生成点作导数检查只是代码诊断；全域界仍需要解析推导。

## 4. 外层生成器的随机流

源码：

```python
config = config or SimulationConfig()
child_seeds = np.random.SeedSequence(seed).spawn(config.n_archive + 3)
mechanism_rng = np.random.default_rng(child_seeds[0])
weight_rng = np.random.default_rng(child_seeds[1])
```

未传配置时使用默认配置。8 个源实验需要 11 个子流：第 0 个抽机制，第 1 个抽目标支持权重，第 2 到 9 个生成各源受试者，第 10 个生成目标受试者。`child_seeds[-1]` 中 -1 表示最后一个。

随后列表推导式调用 `uniform(-1, 1, size=4)` 八次，生成八个四维机制，坐标都在紧致区域内。

## 5. 为什么名义目标有凸支持

源码：

```python
target_support_weights = weight_rng.dirichlet(np.ones(config.n_archive))
supported_target = target_support_weights @ np.vstack(
    [mechanism.as_array() for mechanism in archive_mechanisms]
)
```

`np.ones(8)` 给 Dirichlet 分布八个参数。抽得权重非负、和为 1。把八个四维源机制堆成 `(8,4)`，左乘 `(8,)` 权重，得到 `(4,)` 的目标机制。名义目标因此处于源机制凸包中。

教学例子：源坐标为 `[0,0]` 和 `[1,1]`，权重 `.25,.75`，目标是 `[.75,.75]`。这里只有两维用于手算，仓库实际用四维八源。

`target_support_weights` 是生成器知道的“答案”，保存在对象里供诊断；ATLAS 自己的权重优化不读取它。不要把这组构造权重与 `AtlasResult.weights` 混为一谈。

## 6. 偏移操作逐句读

```python
target_values = (
    (1.0 - config.target_shift_fraction) * supported_target
    + config.target_shift_fraction * target_anchor
)
target_values[2] = (
    (1.0 - config.target_hidden_shift_fraction) * target_values[2]
    + config.target_hidden_shift_fraction * target_anchor[2]
)
```

第一块令全部坐标按比例向锚点移动。比例 0 保留原目标，1 到锚点。两点都在 `[-1,1]^4`，插值仍在该区域，但可能离开八个源点的凸包。是否离开需要用 hull distance 评价，不能仅根据 shift 非零断言。

第二块只修改下标 2 的隐藏 h，其他坐标不再改变。表示敏感性实验将全坐标偏移设成 0，以隔离隐藏坐标偏移的效果。

## 7. 进入 `_generate_experiment`：先生成一个源实验

源码中的第一个关键计算：

```python
true_effect = effect_surface(mechanism)
covariates = rng.normal(loc=0.0, scale=1.0, size=(n_units, 2))
baseline_outcome = 0.50 * covariates[:, 0] - 0.30 * covariates[:, 1]
```

这里 `true_effect` 是一个标量。`covariates` 是 400 行两列独立标准正态数。`baseline_outcome` 是长度 400 的向量，第 i 项由第 i 人的两个协变量算出。协变量属于受试者层，机制属于实验层。

接下来生成两个独立噪声向量：

```python
potential_outcome_control = baseline_outcome + error_control
potential_outcome_treated = baseline_outcome + true_effect + error_treated
treatment = rng.binomial(1, config.propensity, size=n_units).astype(np.int8)
observed_outcome = np.where(treatment == 1, potential_outcome_treated, potential_outcome_control)
```

每人都有潜在的 Y(0)、Y(1)，但观测结果依据 0/1 分组二选一。`np.where` 是逐人的 if。`astype(np.int8)` 把分组保存为小整数类型。

两个噪声独立，所以每人的潜在处理效应并不必然恰好等于 true_effect；其总体均值是 true_effect。不能把有限样本 `mean(Y1-Y0)` 自动当作本实验评价使用的总体真值。

## 8. AIPW 分数逐项计算

源码：

```python
nuisance_control = baseline_outcome
nuisance_treated = baseline_outcome + true_effect
aipw_scores = (
    nuisance_treated - nuisance_control
    + treatment * (observed_outcome - nuisance_treated) / config.propensity
    - (1 - treatment) * (observed_outcome - nuisance_control) / (1.0 - config.propensity)
)
```

前两行提供真实的条件结果均值。它们不是从有限数据训练出来的回归。这就是本批实验的 known/oracle nuisance 设置。

分数第一项是两个结果回归之差。第二项只对处理组生效，因为对照组 treatment=0；它补偿处理结果回归残差，并除以处理概率。第三项只对对照组生效，带负号，并除以对照概率。

教学手算：真实效应 2、基线 3、处理概率 .5。一位处理组个体观测 6，则分数 `2+(6-5)/.5=4`；一位对照组个体观测 4，则分数 `2-(4-3)/.5=0`。两人平均为 2。此例仅说明代数，正式实验并不保证每次平均都等于真值。

## 9. 点估计和标准误如何落在对象中

```python
variance_proxy = float(np.var(aipw_scores, ddof=1))
estimated_effect = float(np.mean(aipw_scores))
standard_error_certificate = float(sqrt(variance_proxy / n_units))
```

第二、三行在源码的 `ExperimentData(...)` 参数中出现，这里抽出来便于一起读。`ddof=1` 表示样本方差分母是 n-1。均值的标准误估计是分数标准差除以根号 n。`float` 把 NumPy 标量转成普通 Python 浮点数，便于写 JSON。

字段名叫 `standard_error_certificate`，数值实际来自经验样本方差，不是直接存入已知总体方差上界。由此得到的覆盖率需要按实现口径解释，不能凭字段名宣称严格有限样本有效性。

`nuisance_bias_bound=0.0` 对应这一 known-nuisance 构造。后面 nuisance 压力实验会另行讨论把这个字段仍置零的含义。

## 10. 隐藏机制怎样变成公开表示

`proxy_error` 在 `[-.1,.1]` 均匀抽取，`moderator_proxy=np.clip(h+proxy_error,-1,1)` 把边界外值截回合法域。最后公开表示是 `[s1,s2,moderator_proxy,q]`。

`mechanism.h` 保留真实隐藏值，只供评价。`observed_representation[2]` 是方法可用的代理。两者都存放在同一 Python 对象不意味着方法有权使用两者；要看拟合函数真正读了哪个字段。

## 11. 返回后还发生什么

八个源对象通过 tuple 收集，目标单独构造。`GeneratedArchive` 装入 archive、target、构造权重、配置，然后调用 `assert_minimal_assumptions`。

报告检查观测结果与分组的一致性、统一设计卡、机制范围、抽样点导数、标准误计算、代理差异等。它返回字典，每项有 `satisfied`。失败列表非空则抛出异常，实验不会悄悄继续。

`support_residual()` 用真实目标机制减构造加权源机制，取长度。`proxy_gap_discrepancy()` 比较真实曲面组合差与代理曲面组合差。`hidden_moderator_certificate()` 计算 `1.55*(目标半径+加权源半径)`。这些是生成与评价辅助量，不是拟合阶段自动读取真值的许可。

## 12. 你可以亲自检查的对象

第 10 章的内存例子会打印这些字段。建议先逐个预测它的形状，再运行：`g.archive[0].x.shape`、`g.target.observed_representation.shape`、`g.target_support_weights.sum()`、`g.target.true_effect`、`g.target.estimated_effect`。

下一章追踪 ATLAS 如何只利用公开表示、源效应估计和不确定性信息完成迁移。
