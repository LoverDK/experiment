# NSW 真实数据 local-contrast reconstruction

## 1. 对应论文位置与实验边界

本阶段实现重点论文 Section 6.2 和 Appendix B 的 NSW real-data archive。论文
规定使用 Dehejia-Wahba NSW job-training 随机实验，以 1978 earnings 为结果，
在标准化协变量空间内构造局部邻域；每个局部对象保存 context、overlap、radius、
treated-minus-control effect 和 standard error，再留出一部分 local objects 做
blind reconstruction。它是 Algorithm 1 思想在真实数据结构上的描述性压力测试，
不改变合成实验的统一 `run_algorithm1(...)` 入口；由于公开数据不能提供无噪声
target 真值，本阶段保留独立实现和明确的评价限制。

论文没有公开邻域大小、锚点选择、coordinate split、holdout seeds、证书常数和
拒绝阈值，因此无法仅凭论文逐数值复刻 Table 3。本仓库固定并公开这些缺失选择，
复现论文的实验结构和信息边界，不把当前数值冒充论文原始代码输出。

## 2. 数据来源与完整性

- 发布方：NBER 的 Rajeev Dehejia 数据页面；
- 下载地址：<https://users.nber.org/~rdehejia/data/nsw_dw.dta>；
- 仓库快照：`data/nsw_dw.dta`；
- SHA-256：`d1bd2680a1c6f799f1c6d2455bf29633fdf19be01cb19490621c20a560b4e072`；
- 样本：445 人，其中 treatment 185 人、control 260 人；
- outcome：`re78 / 1000`，单位为千美元；
- covariates：age、education、black、hispanic、married、nodegree、re74、re75。

运行时先验证原始文件 SHA-256；校验不一致会直接停止，而不是继续读取未知版本。

## 3. local object 构造

先对 8 个协变量使用全体 445 人的样本均值和样本标准差进行标准化。以每个人为
候选中心，按欧氏距离取最近的 50 人形成局部邻域。设邻域内 treatment 和 control
结果分别为 \(Y_1\) 和 \(Y_0\)，局部 effect 与标准误为

\[
\widehat\tau_g=\overline Y_{1g}-\overline Y_{0g},\qquad
\widehat{se}_g=\sqrt{\frac{s^2_{1g}}{n_{1g}}+\frac{s^2_{0g}}{n_{0g}}}.
\]

每个邻域至少含 8 个 treatment 和 8 个 control。局部 overlap 和 radius 定义为

\[
o_g=4p_g(1-p_g),\qquad
r_g=\sqrt{\frac{1}{|N_g|}\sum_{i\in N_g}\|x_i-\bar x_g\|_2^2}.
\]

为避免极端孤立中心主导对象库，先去除 center norm 和 radius 各自最高 5% 的
候选，再用确定性的 farthest-point coverage 选出 112 个 local objects。正式
样本内实际 treatment 数为 12--31，control 数为 19--38。

## 4. 表示、方法与防泄漏

本实现明确区分两个表示。它们不表示“已知哪些变量是因果变量”，而是模拟检索时
遗漏效应相关协变量和设计坐标的可审计情形：

- restricted representation：age、education、race indicators、married、nodegree；
- design-enriched representation：restricted coordinates、re74、re75、overlap、radius。

这一分工是对论文未公开 coordinate split 的可审计实例化。Causal ATLAS 先在
restricted representation 中取最近 24 个候选，再在完整 design-enriched representation
上求带标准误正则项的非负 simplex 权重。证书由 source statistical term 与
representation residual/dispersion term 相加；半宽超过固定的 3.30 千美元科学
容忍度时拒绝点发布。

比较方法为：

1. `atlas`：完整 causal composition 与拒绝规则；
2. `atlas_no_rejection`：相同点权重，强制发布并保留预设比例的表示项；
3. `semantic_forced`：仅用 demographics 的 inverse-distance 权重；
4. `nearest_semantic`：单个最近 demographics 邻居；
5. `global_mean`：全部剩余 local effects 的等权均值。

每次拆分时，target 的 context、overlap 和 radius 可见；target effect 和 target
standard error 都不会传给估计器。自动测试会把这两个评价量改成极端值，并验证
预测完全不变。

## 5. 固定 holdout 协议与指标

固定种子为 20261201、20261202、20261203。每个种子生成 20 个对象级拆分，每次
从 112 个 objects 中无放回留出 28 个，因此每种方法有 1,680 个 target evaluations，
五种方法总计 8,400 条记录。

报告 MAE、median absolute error、sign accuracy、interval coverage、mean interval
width 和 rejection rate。为了与论文 Table 3 的含义一致，点误差和 coverage 的
reference 是 held-out local contrast estimate，不是不可观测的真实 subgroup effect。
ATLAS 即使拒绝也保留 raw prediction 和 interval 供统一评价；rejection rate 单独
说明其是否建议发布点估计。

## 6. 正式结果

| 方法 | MAE | Median AE | Sign accuracy | Coverage | Mean width | Rejection |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Causal ATLAS | 0.8615 | 0.6989 | 0.8542 | 0.9744 | 5.6303 | 0.2321 |
| No-rejection | 0.8615 | 0.6989 | 0.8542 | 0.9696 | 5.2749 | 0.0000 |
| Semantic forced | 1.1688 | 0.9367 | 0.7536 | 0.6048 | 2.8541 | 0.0000 |
| Nearest semantic | 1.2422 | 1.0313 | 0.7804 | 0.9923 | 8.3108 | 0.0000 |
| Global mean | 1.6790 | 1.3490 | 0.7839 | 0.4458 | 2.4746 | 0.0000 |

ATLAS 和 no-rejection 使用相同点权重，所以三个点指标完全一致。完整表示相对
semantic-only 与 global pooling 改善 holdout reconstruction；ATLAS 的宽证书获得
较高的 held-out-reference coverage，同时拒绝约 23% 的高证书目标。nearest
semantic 的高 coverage 来自最宽的区间，不能单独解释为点预测更好。

## 7. 限制

1. held-out contrast 本身含采样噪声，因此 coverage 不是对真实局部效应的频率学
   覆盖证明；本阶段是 real-data reconstruction stress test，不是 causal ground-truth
   validation；
2. local neighborhoods 会重叠，对象级 holdout 不等于 unit-level independent
   holdout，重复指标是稳定性描述而不是 1,680 个独立样本；
3. coordinate split 与证书尺度是公开但非唯一的研究者选择；
4. 当前结果支持真实数据 archive behavior 的压力测试，不证明因果表示在其他人群、
   其他政策或其他结果上可泛化；
5. 与论文 Table 3 的数值差异不能归因于方法失败，因为论文没有提供唯一复刻所需的
   全部实现细节。

## 8. 复现命令与产物

```powershell
python scripts/run_nsw_experiment.py
python -m unittest tests.test_nsw_experiment -v
```

脚本生成：

- `results/nsw_experiment_summary.csv`；
- `results/nsw_experiment_seed_summary.csv`；
- `results/nsw_experiment_metadata.json`；
- `results/tables/nsw_experiment_tables.md`；
- `results/figures/nsw_experiment_overview.png`。
