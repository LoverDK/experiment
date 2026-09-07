# 08：附录 B.4、B.5 的新增稳定性实验

源码：[validation_v3.py](../../../src/causal_atlas_sim/validation_v3.py) 的 nsw_stability、hillstrom、bridge_stability，以及 [extension_bridge.py](../../../src/causal_atlas_sim/extension_bridge.py)。本章逐步解释三个真实/规划稳定性 block。

## 1. NSW 稳定性：一轮 replicate 的开始

读真实数据后，r=0..19 共 20 轮。seed 用 block=6。每个处理臂重新排列行号，将约 2/3 人分 source、其余 reference，两池不重叠。

```python
xx = (x-x[source].mean(0))/np.maximum(x[source].std(0),1e-8)
```

此处 source 的基线均值和 SD 决定新尺度，所有人的基线 x 都可用于计算目标距离。`read_data` 先前已对 x 做过全样本仿射标准化，再按 source 重标准化会抵消该仿射尺度（非常数列、忽略数值下限时）。最终距离使用该次 source 尺度。

没有用 y 定义邻域或锚点，但分组 t 用来保证两池分层和组内人数。这些输入的可用性需要与现实应用设计对应。

## 2. farthest 与 random 锚点

先算所有人 xx 的范数，保留不超过 .95 分位的人为 eligible。farthest 的初始点由 r 决定，随后每次选择距现有锚点最近距离最大的候选，直到 30 个。已选项距离设 -1，避免重复。

random 用 `rng.choice(eligible,30,replace=False)`。每类锚点前 24 为源，后 6 为目标。对于每种锚点方案又跑 k=35/50/75，共 `20*2*3=120` 个设计。

## 3. `nsw_objects` 的 k 改了什么

它与第 5 章 make_objects 相同，只把固定 50 改成参数 k。最近邻仍限制在各自 pool 内，任一臂少于 8 抛 arm_minimum。

k 改变邻域成员，所以同时改变了 reference estimand 与样本精度。若 k=75 的误差更小，不能解释为完全相同预测任务上单纯增加训练样本的收益。

成功设计将 source/reference 行号、两组锚点、六个目标成员写入 `nsw_stability_designs.json`。所有失败组合单独记录在 `nsw_stability_failures.csv`。既有结果 112/120 有效，准确度只在有效设计上汇总。

## 4. NSW 预测与记录

对象表示按 source 标准化；调用 archive_baselines，再用盲化的目标参考值运行 fit_nsw_method。predictions 字典包含 atlas 和五个基线。记录 gap=pred-reference，error=abs(gap)；covered 是 ATLAS 区间是否包含 noisy reference。

builder 传 `real=True`，有 replicate 的均值离散列名为 `_split_sd`，不会除以根号拆分次数。这些是同一批真实人反复重分的设计敏感性，不是独立采样重复的 MC SE。

最终 `nsw_stability_summary.csv` 按 anchor/k/method 汇总，附录 `app_b_nsw_stability.tex` 选其对应行。完整失败和成员必须与均值一起保留。

## 5. Hillstrom：数据筛选和结局

读取 `data/external/hillstrom.csv`，核对 `hillstrom_provenance.json` 的 SHA-256。仅保留 segment 为 Mens E-Mail 或 No E-Mail。第三个随机组没有参与当前对比。

`a=(segment=='Mens E-Mail').to_numpy(int)` 将男性营销邮件记 1，无邮件记 0。结局 visit、conversion 分别循环，y=原始 0/1*100，所以效应、gap、MAE、宽度单位都是百分点。

## 6. cell 编码如何得到 24 个可能单元

```python
cell = (np.minimum((recency-1)//4,2)*8
        + mens*4 + womens*2 + newbie).astype(int)
```

recency 按四个月区间分成三档，以 0/1/2 编码；乘 8 留出后三个二元变量的组合空间。mens/womens/newbie 按二进制权重 4/2/1 编码，因此最多 3*2*2*2=24 个不同 cell。

这是依据处理前属性定义的单元，实际数据有 18 个非空单元。源码遍历真实出现的 cell，每单元两臂须至少 8 人。记录 original_rows 以证明完整单元及人员成员关系；不同 cell 互斥，不像 NSW 重叠邻域。

五维表示用 recency、history、mens、womens、newbie 的单元均值，其中 history 先 `log1p`，即 log(1+history)，避免 0 的对数并压缩长尾。这里 semantic 和 causal 表示都用这五维，没有构造合成版隐藏机制。

## 7. 外层留一 cell 的数据流

18 个单元依次作为 target，其余 17 为 sources。`scale_objects(sources,[target])` 从这 17 源估计表示尺度。拟合 archive 基线及 ATLAS 时，目标的 effect/reference SE 被设 NaN。

target 的观测两组差直到评价时才作为 reference。holdout 一个完整 cell 的人不在其他 cell 内，因此源/目标受试者分离；但它们来自同一营销试验，不能改称跨独立研究迁移。

## 8. 内层 source LOO 为什么又要拟合一遍

对当前 17 个源中的每一个 h，移除它，用剩下 16 个 inner 对象重新 scale_objects。然后重新拟合基线与 ATLAS，预测被留出源 hold 的效应，保存 `abs(pred-hold.estimated_effect)`。

内层的标准化在当前 16 源上重做，与第 6 章回归函数内部固定平滑矩阵的 LOO 调参是两层不同操作。内层 hold 的观测效应只用于该次 residual，外层 target 效应始终不参与校准。

`hillstrom_loo_records.csv` 每条含 outcome、外层 target、source_holdout、method、residual，可复查任何一个最终半径的 17 个来源。

## 9. 为什么 95% 残差区间是无限宽

17 残差调用 finite_quantile：90% 秩 `ceil(18*.9)=17`，取最大残差；95% 秩 `ceil(18*.95)=18`，大于可用 17，返回 inf。width=2*radius 仍为 inf，covered 对有限 gap 总为 True。

这是一条有意义的实验结果：当前档案量下，该秩规则无法给出有限 95% 半径。不能把 100% reference inclusion 脱离无限宽度宣传为高精度，也不能为了美观把 infinity 替换成一个最大有限宽。

记录 interval='source_loo_empirical'。重复拟合、重用源残差、真实单元异质性没有因为使用 n+1 分位就变成标准 split-conformal 设置；论文按经验参考包含报告。

## 10. Hillstrom 的原生区间敏感性

另外遍历 factor=.5/1/2：将 `NswExperimentConfig(causal_effect_scale=.8*factor)` 传给 fit_nsw_method。它改变 NSW 表示项的尺度，点权重的 `_optimize_weights` 不使用该尺度，因此这里主要改变半径和发布。

每条记录 interval='native_factor_...'、level=.95，保存 estimate/reference/gap/error/width/covered/released。不要将三种 factor 行与 source_loo 的两个 level 行一起当成多次独立预测重复。

`hillstrom_summary.csv` 的误差比较需要固定一种 interval/level 口径，才能避免同一目标被重复计数。B.4 分别以 `app_b_hillstrom_error.tex` 和 `app_b_hillstrom_interval.tex` 展示误差与区间行为。

## 11. v2 bridge：先冻结设计分布

`bridge_checks` 默认 moderate=.25、severe=.8，各 12 个 archive，使用专门 seed。每 archive 三个随机流：生成 archive、生成候选、模拟候选观测。

从 12 候选挑 `(0,1,4,5,8,9)` 六项，各族两项。每候选用初始 archive 预测效应均值；得到 means 和 se 后，一次生成 `(2048+128,6)` 的联合正态 draws。

前 128 行给 planning 估计，后 2048 行给 reference 积分。每行是一组包含六候选潜在观测的共同向量，各子集使用同一行对应列。这会减少不同子集比较中的 Monte Carlo 噪声。

这里预测分布在初始源 archive 上固定，并未像 Algorithm 1 选择一个候选之后再动态更新它的所有预测均值。

## 12. 用二进制 mask 枚举子集

6 候选共有 `1<<6=64` 个子集。`1<<j` 是仅第 j 位为 1 的二进制整数。`mask & (1<<j)` 为真表示候选 j 在集合里。`mask | (1<<j)` 表示把 j 加入集合。

教学例子：mask=5 的二进制为 000101，含第 0、第 2 个候选；再加第 1 个得到 7。`mask.bit_count()` 数里面有多少个 1，即集合大小。mask=0 是空集合。

对每个 mask 收集 chosen，增广 archive，构造权重族，再把所有 draws 作为矩阵一次计算区间中心。`outcomes @ weights.T` 的结果形状是 `(draw数,权重族数)`。

## 13. operational 与 retained 两种集合目标

operational 对每个子集重新 `_weight_family`，按当前族大小分 zeta，算交集宽度。子集之间权重族、误差分配都可能改变。

retained 先保留初始权重族的所有区间，并为六候选各准备 singleton 区间，统一用 `initial_family_size+6` 固定分配。加候选只用 `lo=maximum(lo,new_lower)`、`hi=minimum(hi,new_upper)` 更新，保留已有约束。

后一种是单独诊断变体，不等于 operational Algorithm 1 已经采用该规则。文档说明两者是为了读懂仓库完整代码；按用户已批准取舍，operational 单调性诊断继续仅留仓库，不加入论文。

## 14. 空交集与集合 value

`width<0` 标记空交集。代码按 family 统计所有 mask×draw 的空集数。如果任何一项为空，整份该 archive-family 的 values、est 都置 NaN；不会把负宽度减出来的异常大收益当成好结果。

reference value=空集合平均宽度-该 mask 平均宽度，planning value 同样从前 128 行算。两者分别近似同一冻结规划分布下的收益。reference 是较高精度 Monte Carlo 近似，不是无误差解析真值。

保存 `bridge_set_values.csv` 每行包括 scenario、replicate、family、mask、cardinality、reference_value、planning_value；12*2*2*64=3072 行。

## 15. `audit_set_function` 逐步审计哪些量

先检查 64 项 reference/estimate 都有限，否则 valid=False。对每个集合 s、每个不在其中的 j，算 delta=values[s+j]-values[s]；负于 -1e-9 计一次违反；epsilon 取所有边的 planning delta 与 reference delta 差的最大绝对值。

然后 remainder 是未选候选的 bit mask，`u=(u-1)&remainder` 依次枚举其全部非空子集。若联合收益正，计算“分别加入这些候选的边际收益之和 / 联合加入收益”。所有这些比率取最小，再不超过 1，得到该有限 reference 表上的 gamma。

贪心按 planning_value 的边际增益连选 budget 次。optimum 在 cardinality<=budget 的所有子集中取 reference value 最大值。只有全部单调、gamma 存在且正时，计算：

```python
lower = (1-np.exp(-gamma))*optimum - 2*budget*epsilon/gamma
```

`bound_holds` 检查所选 reference value 是否大于此界，`vacuous` 检查界是否<=0。eligible 条件失败时 lower=None，不给出适用性结论。

这是对当前枚举有限表的内部检查，不能仅用 gamma=1 推导所有真实规划分布、所有自适应轨迹都满足同样系数。

## 16. v3 `bridge_stability` 改了什么

它调用 `bridge_checks(12,8192,128)`，同 24 archive、六候选、128 planning，将 reference 增到 8192。输出 checks_8192、sets_8192、failures_8192。

随后同时读取旧 `results/extensions/bridge_set_values.csv` 和新 `bridge_sets_8192.csv`，对每个 mask 枚举所有可加 j，保存 gain。每 archive-family 有 `6*2**5=192` 条边。

builder 将两种 draw 数按 scenario/replicate/family/mask/bridge 精确对齐，比较负边符号是否一致、最大增益变化。随机流有共同前缀，因此是积分精度敏感性，不是新独立 24 archive 的外部验证。

B.5 表 `app_b_bridge_retained.tex` 从 8192 checks 筛 retained_certificates，按 budget 汇总两个场景共 24 个 archive；每个预算一行。当前留档 72 个 archive×budget 检查均通过且非空泛；这句话限定在该 retained 有限积分实验，不外推到 operational 策略。

## 17. 必要运行依赖

先跑 v2 bridge 才有 2048 的对比输入；再跑 v3 bridge；最后 build_validation_v3 汇总。只跑最后一个 builder 不会补生成缺失的子集值。完整路径和命令见第 10 章。
