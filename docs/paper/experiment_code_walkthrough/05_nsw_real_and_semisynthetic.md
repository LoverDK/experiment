# 05：NSW 数据怎样变成迁移实验

源码：[nsw_experiment.py](../../../src/causal_atlas_sim/nsw_experiment.py)、[extension_nsw.py](../../../src/causal_atlas_sim/extension_nsw.py)。本章分开讲原始正文重建、v2 受试者分离、v2 半合成。v3 更换切分、邻域和锚点见第 8 章。

## 1. 原始文件读取与单位

`build_nsw_local_archive(data_path,config)` 先 `read_bytes()` 读取 `data/nsw_dw.dta` 的字节，计算 SHA-256，与 `NSW_SOURCE_SHA256` 比较。不一致直接报错。这是检查是否使用同一数据快照，不是验证数据本身没有偏差。

`pd.read_stata` 读 Stata 文件，随后检查 treat、re78 和八个协变量存在、没有缺失。协变量是 age、education、black、hispanic、married、nodegree、re74、re75，顺序由 `NSW_COVARIATES` 固定。

```python
treatment = frame["treat"].to_numpy(dtype=int)
outcomes = frame["re78"].to_numpy(dtype=float) / 1000.0
covariates = frame[list(NSW_COVARIATES)].to_numpy(dtype=float)
```

第一行取分组列，第二行把收入单位从美元改成千美元，第三行按规定顺序取协变量矩阵。后面的预测、MAE、标准误与区间宽均继承千美元单位。

标准化 `standardized=(covariates-means)/scales`，means 是每列平均，scales 是每列样本 SD。某列几乎常数时 scale 改为 1，防止除以零。原始版本在建立局部对象之前对整份基线协变量标准化。

## 2. `_build_raw_local_contrasts` 如何选 50 人

每个原始人的协变量向量暂作 center。源码：

```python
distances = np.linalg.norm(standardized - center, axis=1)
neighbors = np.argsort(distances, kind="stable")[:config.n_neighbors]
```

`standardized-center` 将每行减同一个 center，叫广播。`axis=1` 沿列求长度，每个人得到一个距离。argsort 返回从近到远的下标，再取前 50。中心本人距离 0，通常在邻域内。

从 treatment 中取出这 50 人的分组，计算 treated_count 和 control_count。若任一少于 8，`continue` 跳过这个 center，继续下一个。

```python
effect = treated_outcomes.mean() - control_outcomes.mean()
standard_error = sqrt(
    treated_outcomes.var(ddof=1)/treated_count
    + control_outcomes.var(ddof=1)/control_count
)
```

这是局部两组均值差和相应标准误。这里没有调用合成 DGP 的 oracle AIPW。观测差是有噪声参考，不能赋予 `true_effect` 的含义。

## 3. 一个局部对象的表示

context 是这 50 人标准化协变量的列平均。semantic_representation 只用前六个均值。causal_representation 用八个均值，加 overlap_score 和 neighborhood_radius，共十维。

`overlap_score=4*p*(1-p)`，p 是局部处理比例：两组均衡 p=.5 时为 1，趋向单一组时变小。`radius=sqrt(mean(sum((X-context)**2,axis=1)))` 衡量邻域相对于自身中心的离散程度。

这些是作者为真实数据定义的可观测表示。十维 causal_representation 不等于已经观测到真实因果机制，也不沿用合成四维曲面的解析界。

`NswLocalContrast` 同时保存 center_row、neighborhood_rows，便于回查每个对象由哪些原始人构成。

## 4. 从很多候选选出 112 个局部对象

`_select_spread_objects` 先去掉半径和中心范数最极端的尾部，阈值默认各 .95 分位。然后找 context 最接近候选总体中心的第一个对象。

后续 while 循环保持 `minimum_distances`：每个未选点距已选集合最近点的距离。每轮取 argmax，选出“离当前已选集合最远”的点，再用 `np.minimum` 更新最近距离。已选点距离设 -1，避免重复选择。

直到得到 112 个对象。然后对语义/因果两类表示矩阵分别再次按列标准化。原始对象创建与标准化是预先固定的，重复拆分不会重新采集 445 名受试者。

## 5. 原始 NSW 外层到底拆什么

`run_nsw_experiment` 创建一次固定局部对象集，然后三组 seed 各 20 次抽 28 个目标对象，剩下 84 个对象作为 archive。`rng.choice(...,replace=False)` 表示一次拆分内不重复选目标对象。

每次拆分、每个目标、五种方法均运行，得到 `60*28*5=8400` 条方法误差记录；ATLAS 目标诊断是 1680 条。

这里源与目标“对象 ID 不同”，但 `neighborhood_rows` 可能共享原始人。重复拆分也重复使用这份数据。因此这些记录不是 1680 个独立新试验，不能按这一行数声称独立样本量增加。

## 6. `fit_nsw_method` 的拟合与合成版不同

先用六维 semantic 表示选最近至多 24 个候选。ATLAS 在这些候选的十维 causal 表示上调用 `_optimize_weights`。

该优化与第 2 章同为 simplex 投影梯度，但方差先用源标准误中位数归一化：`normalized_variances=(standard_errors/error_scale)**2`；目标函数是表示残差平方加 `.15*sum(w**2*normalized_variances)`。不存在合成方法那个单独 hidden_gradient。

semantic_forced 使用 `1/max(distance,.05)` 归一化；nearest 取最近一个；global 对全部源平均。它们接着共用下面的预测与半径计算。

```python
predicted_effect = weights @ source_effects
support_residual = norm(target_representation - weights @ representations)
```

dispersion 是加权平方距离总和开根号。statistical_term 为 `1.96*sqrt(sum(w**2*source_se**2))`。

ATLAS 表示项为 `.80*(support_residual+.25*dispersion)`。其他方法使用各自 effect_scale；global 不加 dispersion。总半径为统计项+表示项；ATLAS 阈值为 3.30 千美元。

**特别注意源码中的 NSW no_rejection**：它还执行 `representation_term *= .75`。因此在这个模块里它与 ATLAS 的点预测相同，但区间表示项也缩小了；不能描述成只关闭拒绝、其余全部相同。这与 `methods.py::fit_no_rejection_atlas` 的行为不同。

`effective_source_count=1/sum(w**2)`：四个等权源时为 4，完全由一个源决定时为 1。它描述权重集中度，不是去重后的受试者数。

## 7. 原始输出怎么读

入口：[run_nsw_experiment.py](../../../scripts/run/run_nsw_experiment.py)。输出包括 `results/nsw_experiment_summary.csv`、逐 seed 汇总、`nsw_archive_map_summary.csv`、`nsw_diagnostics_summary.csv`、`nsw_method_error_records.csv` 和 metadata。

`nsw_archive_map_rows` 描述固定局部对象，用于画地图；`nsw_diagnostic_rows` 描述 ATLAS 的每个目标；`nsw_method_error_rows` 展开所有方法的预测减参考误差。

评价中的 reference=留出对象的观测局部均值差。区间包含它只能称参考值包含，不能称未知真实 ATE 覆盖。正文 Figure 5 对应这一重建任务，更多真实数据证据来自以下扩展。

## 8. v2 `read_data` 与 `fixed_design`

入口：[run_requested_extensions.py](../../../scripts/run/run_requested_extensions.py) 的 nsw block。`read_data` 同样检查 SHA-256，读取并标准化八个协变量、将收入除 1000。这里 `.std(0)` 默认 ddof=0，与原始模块的 ddof=1 有细微差别，应以各自协议为准。

`fixed_design` 固定 seed=2026090601。对每个处理臂：取得行号，随机排列，前 `2*len(indices)//3` 分给 source，其余分给 reference。`//` 是向下取整的整数除法。实际得到 296 个源人和 149 个参考人，交集为空。

锚点只根据基线 x 选择：去掉范数最外 5%，从最靠中心点开始，再最远点递增到 30 个。前 24 个源锚点、后 6 个目标锚点。锚点决定邻域中心，其个人不必属于对应池；查找邻居时严格只在对应 pool 内找。

`nsw_design.json` 保存四组行号。它是复核“人是否分离”的实际证据，不能只凭函数名 disjoint 判断。

## 9. `make_objects`、`scale_objects`、`predictions`

`make_objects` 对每个 anchor 在给定 pool 中选最近 50 人，计算与上文相同的均值差、SE、context、overlap、radius。组内少于 8 人时抛 `ValueError('arm_minimum')`，交给外层记录失败。

`scale_objects` 对 semantic、causal 两类表示逐一处理：均值与尺度只从 source 对象估计，然后同一变换应用 source 和 targets。使用 getattr 动态取字段，replace 构造替换后的对象。

`predictions` 一次对 targets 的表示运行所有 archive_baselines，又让 T-learner 使用源受试者数据，预测拼接后的 target_units。每个目标 50 人，所以 `unit_effect[j*50:(j+1)*50].mean()` 得到第 j 个目标的平均预测效应。

ATLAS 拟合前用 `replace(target,estimated_effect=nan,standard_error=nan)` 隐藏目标参考结果。返回记录的 data_access 标出 `archive_summaries` 或 `source_individuals`。这解释了 T-learner 为何不能当成同信息预算的纯摘要基线。

## 10. 真实参考 bootstrap 的每一步

`real_reference` 先断言两个池不共享行号。循环 b=0..200，其中 b=0 原样使用池，保存原始估计。b>0 时分别在 source/ref 内，按 treatment 臂有放回抽样，保持各臂人数。

`rng.choice(...,replace=True)` 可能重复某个原始行号。随后用重新抽到的两池整体重建全部邻域并重新拟合。这保留了同一池不同局部对象共享人所带来的依赖。

每条记录追加 reference、reference_se、`gap=estimate-reference`。这是有符号差；正负可以抵消。失败 bootstrap 单独进入 failures，原设计 b=0 失败则整体报错。

保存 `results/extensions/nsw_real_records.csv`、`nsw_real_failures.csv`。builder 对原设计六目标平均 gap 给点值，对有效 bootstrap 的六目标平均 gap 取 .025/.975 分位。既有留档为 196/200 有效；不是 200 个全部成功后又挑选 196 个表现好的结果。

## 11. 半合成数据到底保留了什么

`semisynthetic` 保留真实 x、上一步源/参考池和锚点；重新生成分组 t 和结局 y。真实 NSW 的 re78 此时不作为评价真值。

`response_surface` 三条 tau(X)：

```python
constant:    tau = 2
smooth:      tau = 2 + .8*tanh(x[:,0]) + 1.2*tanh(x[:,7])
interaction: tau = 1 + 2*tanh(x[:,0]*x[:,7]) + .8*(x[:,5] > 0)
```

这是源码公式的并排列示，不是可直接执行的 Python 语句。共同基线 `mu=3+.7*x[:,0]+1.5*tanh(x[:,6])+.5*x[:,1]**2`。`tanh` 是平滑有界函数，条件表达式产生 True/False，乘 .8 后变成 .8/0。

每个曲面 100 次独立重复，seed 分别 2026090611/12/13。每次 `t=binomial(1,.5,len(x))`，`y=mu+t*tau+Normal(0,3)`；随后重建局部对象、拟合全部方法。

## 12. 半合成目标真值和聚类标准误

```python
truth = float(tau[list(targets[row['target']].neighborhood_rows)].mean())
```

先找到记录对应目标 j，再取该目标实际 50 人的行号，索引每人的 tau，最后求平均。这是已知的局部平均效应，允许直接计算绝对误差和覆盖；不能用目标 y 均值差代替它。

每个 replicate 的六个目标可能相互重叠。builder 因而先对同一 replicate 的目标误差平均，再用 100 个 replicate 均值算 MC SE。若条件于发布，每次发布目标数不同，需要计算总误差/总发布数的比值，再以 replicate 为 cluster 计算影响函数标准误；第 9 章细讲。

原始结果 `results/extensions/nsw_semisynthetic_records.csv`；表源汇总 `nsw_semisynthetic_summary.csv`。附录 B.4 使用 `app_nsw_semisynthetic.tex`。结论范围是“真实协变量分布下、人为指定效应与结局的性能”，真实效应曲面仍由作者设定。
