# 06：强基线、配对比较与发布选择审计

本章对应附录 B.3，并涵盖 B.2 使用的历史残差校准。源码：[extension_baselines.py](../../../src/causal_atlas_sim/extension_baselines.py)、[validation_v3.py](../../../src/causal_atlas_sim/validation_v3.py)、[build_validation_v3.py](../../../scripts/build/build_validation_v3.py)。

## 1. 强基线收到的四个输入

`archive_baselines(x,effects,ses,target)` 中 x 是源表示矩阵 `(m,d)`，effects 是 m 个源效应估计，ses 是 m 个源 SE，target 是一个或多个目标表示。

`np.atleast_2d(target)` 将单个 `(d,)` 转为 `(1,d)`，因此其返回预测总是长度为目标数的数组。`float(base[method][0])` 是取单目标预测的第 0 项。

这些函数没有 target outcome 参数。源效应可以用于拟合与调参，目标真值只能出现在外层评价。

## 2. IVW 和随机效应汇总

源码：

```python
variance = np.maximum(np.asarray(ses)**2, 1e-10)
weight = 1 / variance
fixed = weight @ y / weight.sum()
q = np.sum(weight * (y - fixed)**2)
c = weight.sum() - np.sum(weight**2) / weight.sum()
tau2 = max(0.0, (q - len(y) + 1) / c)
random_weight = 1 / (variance + tau2)
```

variance 是 SE 平方，以 1e-10 作下限防止除零。IVW 让低方差源权重大。q 衡量源效应相对共同均值的差异。c 是异质性估计中的校正量。tau2 是 DerSimonian-Laird 非负异质性方差估计，加到每个源方差上，再重算加权平均。

这两种预测不随 target 表示变化，所以 `np.full(len(target),fixed)` 为每个目标复制同一个值。它们可降低采样噪声，但不显式拟合效应随表示变化。

## 3. full_nearest 的广播逐维看

`target[:,None]` 形状 `(t,1,d)`，`x[None,:]` 形状 `(1,m,d)`，相减广播成 `(t,m,d)`。平方后 `.sum(2)` 得到每个目标到每个源的平方距离 `(t,m)`。`argmin(...,axis=1)` 给每目标最近源下标，再返回 `y[nearest]`。

此基线使用完整公开表示，与早期二维 semantic nearest 的信息量不同。比较时名字里的 full 不是装饰。

## 4. `regression_predictions` 第一步：标准化

`mean=x.mean(0)` 和 `scale=x.std(0)` 只来自源表示；近零尺度改成 1。目标用同一 mean、scale 标准化。这里无目标效应泄漏。

ridge 参数网格为 `.01,.1,1,10,100`。kernel 模式另遍历 bandwidth `.5,1,2`；线性模式只走一个占位 bandwidth=1。

## 5. 线性与 RBF 核矩阵怎么构造

线性：`matrix=x@x.T` 是 m×m 的源之间内积；`cross=target@x.T` 是 t×m 的目标与源内积。`.T` 转置行列。

RBF：先求源间平方距离 dist，取正距离中位数 base 作尺度；`matrix=exp(-dist/(2*bandwidth**2*base))`。距离 0 相似度 1，距离大则相似度衰减。cross 同样算目标到源的相似度。

所有距离与带宽由源表示及目标基线表示确定，没有读取目标结局。

## 6. 中心化、特征分解和不惩罚截距

```python
center = np.eye(n) - np.ones((n,n))/n
centered = center @ matrix @ center
eig, vec = np.linalg.eigh(centered)
eig = np.maximum(eig, 0)
```

eye(n) 是单位矩阵，ones/n 是求均值矩阵。center 左乘向量相当于减去均值。双侧中心化处理核矩阵。eigh 把对称矩阵分解成特征值 eig 和特征向量 vec，极小负特征值因浮点误差截成 0。

每个 ridge 值用 `(vec/(eig+ridge))@vec.T` 计算稳定的正则逆。`smoother=centered@inverse+ones/n` 恢复一个不受惩罚的均值/截距部分。

这段写法是核/线性平滑矩阵形式，初学者不必先掌握全部谱分解证明；须知道它把“给定 ridge 下源 y 如何变成拟合 y”的线性变换明确算了出来。

## 7. source LOO 评分的实际口径

```python
residual = (y - smoother @ y) / np.maximum(1 - np.diag(smoother), 1e-8)
score = float(np.mean(residual**2))
```

分子是源训练残差，分母的 `1-H_ii` 将线性平滑残差转换为固定平滑矩阵下的留一残差。求平方均值作为调参评分，最小时更新 best。best 同时保存 score、预测、ridge、bandwidth。

该函数先用全 source 的 x 标准化、构造核尺度，再用平滑矩阵公式评价；它没有在每个源留一折重新估计这一步协变量尺度。因此准确说法是固定 source 预处理下的 LOO 平滑评分，不能把它描述成完整嵌套预处理交叉验证。它仍然没有使用最终 target outcome。

预测是 `y.mean()+cross_centered@inverse@(y-y.mean())`。return 给预测数组，以及含 ridge、bandwidth_multiplier、loo_mse 的字典，外层将调参选择留档。

## 8. T-learner 的额外数据访问

`unit_t_learner` 对 arm=0、1 分别选择源受试者，拟合上述线性 ridge 结果回归，预测目标受试者的两个结局，再 `mu[1]-mu[0]`。因此它访问个体 X、A、Y，而 archive_baselines 只有实验摘要。它出现在 NSW 扩展，结果要注明这一区别。

## 9. v2 synthetic runner 如何记录共同目标

[run_requested_extensions.py](../../../scripts/run/run_requested_extensions.py) 的 `synthetic(repetitions)` 取四个场景：nominal、moderate=.25、severe=.8、high_noise 的 SD=3。每个场景三组 seed 各 100，共 1200 个迁移任务。

每任务调用 archive_baselines 得五方法，再加 atlas、atlas_no_rejection、semantic_forced 共八方法，所以 `synthetic_baselines_records.csv` 正式为 9600 行。atlas 和 no_rejection 的 raw 值相同；release 标记只有 atlas 使用其接受决定。

v2 builder 的 `synthetic_summary` 将全部行按 seed×method 展开并算全目标 MAE，不先筛掉未发布 atlas。论文表因此使用 no-rejection 标签说明这个口径。paired difference=比较方法绝对误差-ATLAS raw 绝对误差；正数有利 ATLAS，负数有利对照。

## 10. v3 为何新增 `blind_target` 和 `predictor_rows`

`blind_target(t)` 返回目标副本，把 estimated_effect、true_effect、standard_error_certificate 全置 NaN。即使核心接口本来不读这些字段，也明确阻止后续修改不小心用到它们。

`predictor_rows(g,config)` 同时返回五方法的 estimate 和 score。ATLAS、IVW、full_nearest 能写出凸权重，于是调用共同 compute_certificate。IVW 权重为归一化逆方差；nearest 为 one-hot。

ridge/RBF 不强行赋予凸组合证书。代码采用 `sqrt(max(loo_mse,1e-8)*(1+dist))`，dist 为目标到最近源的原始公开表示平方距离。它是启发式风险分数，不是理论置信半径。对应 bias、stderr 设 NaN。

随后返回 truth、reference、reference_se、error、signed_error，用于保存评价。truth 来自原 g.target，拟合时用的是盲化副本。

## 11. v3 seed、校准集与测试集

`seed(block,scenario,rep)` 使用 `SeedSequence([20260906,300+block,scenario,rep])` 生成整数。selection 使用 block=1。每个场景分 calibration 150、test 300 两部分，test 的 rep 加 10000 偏移，避免重复种子。

`rows.extend(dict(scenario=...,part=...,replicate=...,seed=...,**v) for v in predictor_rows(g))` 一套数据添加五条方法记录。总 prediction 行数 `4*(150+300)*5=9000`。

150 个 calibration 单位都是完整 archive-target 任务，不是从当前八个源里切 150 人。历史校准访问各自目标的 noisy reference，属于额外历史信息；当前测试目标结局仍不进入预测或阈值选择。

## 12. `finite_quantile` 的排序为什么有 n+1

```python
values = np.sort(np.asarray(values))
rank = math.ceil((len(values)+1)*coverage)
return float(values[rank-1]) if rank <= len(values) else float('inf')
```

ceil 向上取整。数组下标从 0 起，所以 rank-1。要求的秩超出已保存残差数时返回 infinity，不偷偷改成最大值。150 条 calibration 的 .95 分位取第 144 项；17 条残差的 .95 取第 18 项，超界必须无穷。

这里使用有限样本秩规则本身不证明交换性、独立性或所选分数有效。尤其历史 noisy reference 与潜在真值是不同评价对象。

## 13. 两种发布规则逐句比较

历史阈值规则：先用校准 score 的 fraction 分位作 threshold，再对 test 每条记录写 `released=(v.score<=threshold)`。fraction=1 明确取 infinity。测试集实际发布比例不必恰好等于 fraction，分布迁移时可能差很多。

同队列 rank 规则：

```python
chosen = set(test.sort_values(['score','replicate'])
             .head(round(len(test)*fraction)).replicate)
```

先按 score 再按 replicate 排序，取前 k 个目标 ID，用集合查询 `v.replicate in chosen`。300 个目标、fraction=.5 时恰取 150 个。不同方法可以选不同目标，因此这是同发布比例下各自选择策略风险，不是同一发布子集上预测误差比较。

`origin` 同时评价场景内校准和 nominal 历史迁移校准。校准来源写在 calibration 列，不能把两种结果合并平均。

## 14. 历史区间怎样建立

```python
residual = np.abs(cal.estimate-cal.reference)/cal.score
q = finite_quantile(residual, level)
radius = q*v.score
```

首先用历史预测与历史 noisy reference 的差，按 score 归一化；再取 .8/.9/.95 对应 q；当前目标半径=q*当前 score。

每条 interval_records 同时保存 `covered=(error<=radius)` 和 `reference_included=(abs(estimate-reference)<=radius)`。前者在合成环境能对真值评价，后者对有噪声观测参考评价。用参考残差校准不自动保证潜在真值覆盖。

另一个 native_bias_aware 分支只对 bias、stderr 全部非空的方法运行：半径=bias+对应正态分位*stderr。ridge/RBF 因没有这些量，不出这个 native 区间记录。

## 15. 同发布率 bootstrap 为什么要重新排序

`rank_bootstrap` 将 test 数据 pivot 成 300×5 的 errors、scores 矩阵，列顺序对齐。原始点值先各列按 score 选前 k 求 MAE。

```python
ids = rng.integers(0,len(e),len(e))
ee = e[ids]
ss = s[ids]
chosen = np.argsort(ss,axis=0,kind='stable')[:k]
boot.append(np.take_along_axis(ee,chosen,axis=0).mean(0))
```

每轮有放回抽取目标行号，同一 ids 同时应用所有方法，因此配对关系保留。重复目标会出现多次，符合 bootstrap。重抽后的 score 重新排序，才计入筛选规则本身的变异。

`take_along_axis` 按每列自己的 chosen 下标选误差；mean(0) 每方法得到一个 MAE。1000 轮后求方法 MAE 的 SD 作 bootstrap SE；逐轮对照方法减 atlas，再取差值 .025/.975 分位作 paired interval。

输出 `selection_rank_bootstrap.csv` 才包含重排的不确定性。普通 `selection_summary.csv` 汇总已固定的发布标记，不包含这一步重排变异。附录 B.3 的 50% 操作点应读前者。

## 16. 结果如何进入论文

`app_paired_comparison.tex` 来自原始 300 目标诊断；`app_stronger_baselines.tex` 来自 v2 的四场景八方法全目标记录；`app_b_selection.tex` 来自 v3 配对 rank bootstrap。三张表各有不同目标批次与比较问题。

历史区间校准则进入 B.2 的校准相关表。这套实验可以说明选择与区间在指定环境中的表现，不能通过挑一个较好 fraction 或场景消除不利的其他结果；完整网格仍保留在 CSV。
