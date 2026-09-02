# Algorithm 1 严格对照说明

本文件把论文第 9 页的 `Algorithm 1: Rejectable Causal Atlas and Greedy
Bridge Design` 逐行对应到仓库实现。仓库的“阶段 1--12”是开发和验证阶段，
不是论文算法的 12 个步骤；真正的端到端入口只有
`run_algorithm1(...)`。

## 输入与输出

论文要求输入历史实验档案、目标对象、候选 bridge 库、bridge 预算、支持容忍度、
平滑常数和置信水平。代码分别由 `archive`、`target`、`bridge_library`、
`Algorithm1Config.bridge_budget`、`AtlasConfig.scientific_tolerance`、
`AtlasConfig` 中的 (L,H) 和 `zeta` 承载。

输出是二选一的分支：

- 接受分支：点预测和 Corollary 5.2 诚实区间；
- 拒绝分支：Theorem 5.4 部分识别区间和按预算选择的 bridge 集合。

`Algorithm1Result.branch` 明确记录实际分支。接受时
`partial_interval=None` 且 bridge 集合为空；拒绝时 `point_estimate=None`，
只有这时才构造部分识别并启动 bridge 设计。

## 论文逐行映射

| 论文行 | 论文动作 | 代码位置 | 实验阶段与可见产出 |
| --- | --- | --- | --- |
| 1 | 按式 (4.2) 对每个历史效应去偏并保存表示、设计、假设、估计、方差和样本量 | `dgp.py::_generate_experiment` | 阶段 1；快速检查会打印 8 个 archive、目标效应、支持残差和 Assumption 3.1--3.5 报告 |
| 2 | 用语义和元数据筛选候选集合 | `methods.py::retrieve_semantic_candidates` | 阶段 3；得到按公开表示距离排序的候选索引 |
| 3 | 删除设计不兼容候选 | `methods.py::design_compatible` | 阶段 3；设计档案或识别假设档案不一致的实验不会进入权重学习 |
| 4 | 按式 (4.3) 学习支持权重 | `methods.py::optimize_support_weights` | 阶段 3；得到非负且和为 1 的 archive 权重及目标函数值 |
| 5 | 按 Theorem 5.1 计算证书 | `methods.py::compute_certificate` | 阶段 3；得到支持、曲率、隐藏调节、nuisance 和有限样本统计项 |
| 6 | 比较完整证书半径与科学容忍度 | `methods.py::fit_causal_atlas` | 阶段 3；产生明确的接受或拒绝状态 |
| 7 | 接受时返回点预测和 Corollary 5.2 区间 | `methods.py::honest_interval_radius`、`algorithm1.py::run_algorithm1` | 阶段 3；点预测可见，区间半径为确定性逼近界加 Wald 统计项 |
| 8 | 进入拒绝分支 | `algorithm1.py::run_algorithm1` | 阶段 9/11；点预测被置空，避免强制外推 |
| 9 | 构造 Theorem 5.4 部分识别区域 | `partial_identification.py::construct_partial_identification_interval` | 阶段 9；得到多个同时有效区间的交集、宽度和非空状态 |
| 10 | 初始化空 bridge 集合 | `algorithm1.py::run_algorithm1` | 阶段 11；`selected_bridge_keys=()` |
| 11--13 | 每轮选择当前集合条件下边际 VoI 最大的 bridge，并加入集合 | `algorithm1.py::expected_partial_id_diameter`、`run_algorithm1` | 阶段 11；每轮得到候选、边际价值和更新后的直径 |
| 14 | 达到预算后结束循环 | `Algorithm1Config.bridge_budget` | 阶段 11；正常路径选择 4 个 bridge |
| 15 | 返回部分识别区间和 bridge 集合 | `Algorithm1Result` | 阶段 11；CSV 保存初始/最终直径、选择数、完成率和不一致诊断 |
| 16 | 分支结束 | `run_algorithm1` 返回 | 可用 `scripts/run_algorithm1.py` 在数秒内查看一条完整路径 |

## 式 (4.2) 与 Corollary 5.2

每个实验保存 AIPW 分数均值

\[
\widehat\tau_i=\frac1{n_i}\sum_{\ell=1}^{n_i}\phi_i(W_{i\ell}),
\]

以及分数的无偏样本方差

\[
\widehat v_i=\frac1{n_i-1}\sum_{\ell=1}^{n_i}
\{\phi_i(W_{i\ell})-\widehat\tau_i\}^2,
\qquad s_i^2=\widehat v_i/n_i.
\]

接受判断使用 Theorem 5.1 的完整有限样本证书；接受后的报告区间则严格使用
Corollary 5.2：

\[
\widehat\theta_\alpha
\pm\left{z_{1-\zeta/2}\widehat V_\alpha^{1/2}
+\widehat D(\alpha)\right}.
\]

因此“用于决定是否接受的半径”和“接受后报告的渐近诚实区间半径”是两个理论
对象，代码没有把它们混成同一个量。

## 条件边际 bridge VoI

第 (b) 轮不是给每个候选一个固定分数，而是在当前已选集合 (S_{b-1}) 下计算

\[
\widehat{\operatorname{VoI}}(u\mid S_{b-1})
=\operatorname{diam}\widehat\Theta_{A\cup S_{b-1}}(e_\star)
-\mathbb E\left[
\operatorname{diam}\widehat\Theta_{A\cup S_{b-1}\cup\{u\}}(e_\star)
\right].
\]

未来 bridge 效应尚未观测，因此仿真公开声明一个可复现的规划模型：先用当前公开
archive 对候选效应作 plug-in 预测，再令未来估计以该预测为均值、候选设计标准误
为标准差服从正态分布，用 3 点 Gauss-Hermite 求积计算期望。候选被选中以后，
才把它的模拟观测结果加入 archive；下一轮会基于更新后的集合重新计算所有边际值。

target 真值、target 真实机制、候选真实效应和候选真实机制均不进入选择。它们只在
选择结束后评价误差与 oracle 凸包距离。

## 空交集诊断

按照 Lemma 5.1，Theorem 5.4 交集为空表示当前置信水平下 archive 估计与声明
证书彼此不一致。代码将其直径记为未定义并停止直径型 VoI 规划，绝不把空集当作
“直径为 0 的完美识别”。阶段 11 单独汇报预算完成率、规划不一致率和评价
不一致率。

## 快速核查

```powershell
python scripts/run_algorithm1.py
python -m unittest tests.test_algorithm1 -v
```

第一个命令展示一条拒绝、部分识别、连续选择两个 bridge 并逐步缩小区间的完整
路径；第二个命令检查分支互斥、公式、设计兼容、真值隔离、条件边际选择、固定
种子复现和空交集处理。
