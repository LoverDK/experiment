# 03：正文合成实验与原始诊断，逐个追踪循环和分母

本章涵盖原始实验协议。后补更强基线与同发布率审计在第 6 章，失配压力测试在第 7 章。不要因文件名有 main 就认为正文全部来自 `run_main_experiment.py`；正文多面板图还读取 certificate、risk、calibration 等专用结果。

## 1. 先跑通一条最短调用链

`scripts/run/run_main_experiment.py::main` → [experiments.py](../../../src/causal_atlas_sim/experiments.py) 的 `run_main_experiment` → [comparison.py](../../../src/causal_atlas_sim/comparison.py) 的 `run_method_comparison` → `generate_minimal_archive` → `fit_method` → `comparison.summary()` → `ExperimentSummaryRow` → CSV。

生成一套数据、拟合一种方法的细节见第 1、2 章。这里解释外层是如何组织它们的。

## 2. 单因素扫描：`run_main_experiment`

源码核心：

```python
for sweep_index, sweep in enumerate(config.sweeps):
    for level in sweep.values:
        dgp_config, atlas_config = _configs_for_level(config, sweep.key, level)
        comparison = run_method_comparison(
            MethodComparisonConfig(
                repetitions=config.repetitions,
                base_seed=config.base_seed + sweep_index,
                dgp_config=dgp_config,
                atlas_config=atlas_config,
                methods=config.methods,
            )
        )
```

第一层遍历四个因素，第二层遍历各因素三个水平。`_configs_for_level` 返回两个对象，逗号左边分别接住它们。只改变一个因素，其他使用名义配置。

| `sweep.key` | 三个水平 | 真正修改的字段 |
| --- | --- | --- |
| `semantic_shift_fraction` | 0、.10、.25 | DGP 的 `target_shift_fraction` |
| `moderator_sensitivity_radius` | .20、.40、.60 | DGP 的声明半径；此扫描代理噪声半宽仍 .10 |
| `sample_size` | 100、400、1000 | 源和目标人数一起改变 |
| `scientific_tolerance` | 1.25、1.65、2.05 | ATLAS 的发布阈值 |

同一因素不同 level 使用相同 `base_seed+sweep_index`，有利于配对比较。换因素则 seed 加一。每个 level 默认 200 个 archive，5 种方法，因此输出 `4*3*5=60` 条汇总行。它不是四个因素的全组合 `3**4` 网格。

`comparison.py::run_method_comparison` 先生成每次重复的数据，再逐方法拟合，存 `MethodComparisonRecord`。`summary` 按方法收集记录。`accepted_mae` 只用发布点估计，空集合返回 None。`interval_coverage` 则按其有效区间集合计算，不能自动当成仅发布集覆盖率。

runner 的 `_write_table` 将 `rows_as_dicts` 的字典写入 `results/main_experiment_summary.csv`；`_write_metadata` 记录配置；`_write_figures` 使用 PIL 画早期扫描图。当前论文高清多面板图由后续 paper_figures 构建，并非这些早期 PNG 的简单重命名。

## 3. 正式多种子 benchmark 与消融

源码：[formal_experiment.py](../../../src/causal_atlas_sim/formal_experiment.py)。入口：[run_formal_experiment.py](../../../scripts/run/run_formal_experiment.py)。

配置的三组 seed 是 `(20260811,20260812,20260813)`，各 100 次。场景六个：名义、.10 偏移、.25 偏移、.40 隐藏半径、n=100、n=1000。注意这个早期文件把 .25 场景 label 写成 severe semantic mismatch，而 v3 的 severe 是 .8；比较时应使用数值和 key。

循环从外到内是 scenario → seed_batch → replicate → estimator。每个 scenario 建 300 套数据，每套数据跑七个 estimator，内存记录数 `6*300*7=12600`。汇总每个 scenario-estimator 一行，共 42 行。

七个估计器由 `FormalEstimator(key,method,...)` 描述。`key` 是结果标签；`method` 是实际调度名称。比如 `atlas_no_variance_penalty` 的 method 仍是 atlas，通过 `_estimator_config` 把 `lambda_sigma=0`；`atlas_top4_candidates` 修改 `max_candidates=4`。

去掉方差惩罚仅改变权重优化目标中的惩罚，不会同时删除最终证书的统计项。top4 也不仅改变绘图标签，它使检索只返回四个源。no_rejection 保持点估计算法，改变发布策略。

## 4. 正式表每列怎么计算

`_summarize_one` 先建三组：results 是全部输出；accepted_records 要求 point_estimate 非 None；interval_records 要求两个区间端点有限。

```python
errors = np.asarray([
    record.result.point_estimate - record.target_true_effect
    for record in accepted_records
], dtype=float)
```

然后 `mean(abs(errors))` 为 MAE，`sqrt(mean(errors**2))` 为 RMSE，`mean(errors)` 为偏差。一个偏大 .5、一个偏小 .5，偏差为 0，但 MAE=.5；两者回答不同问题。

教学例子：三次 raw 误差 `[.1,.9,.3]`，发布标记 `[True,False,True]`。发布率 `2/3`，accepted MAE `.2`，全体 raw MAE 约 `.4333`。不能把第三列的 .2 当成覆盖所有目标的平均误差。

`accepted_mae_mc_se=std(abs(errors),ddof=1)/sqrt(发布数)` 是该实现对接受误差平均的 Monte Carlo 标准误估计。`between_seed_mae_sd` 先各 seed_batch 算一个 MAE，再对这三个数求 SD，不能当作 300 次重复的标准误。

`wilson_interval(successes,trials)` 用 Wilson 公式给发布率区间：先计算比例、修正分母、中心、半宽，再截回 [0,1]。当发布数为 0 或全部发布，边界按代码设为 0 或 1。

runner 保存 pooled summary 和 seed summary，分别为 `results/formal_experiment_summary.csv` 与 `results/formal_experiment_seed_summary.csv`。内存里有 12600 个 FormalRecord 不等于 runner 将每一项原始对象都序列化到磁盘；看 `_write_*` 确认实际保存层级。

## 5. certificate diagnostics：正文合成六方法对照的来源

源码：[certificate_diagnostics.py](../../../src/causal_atlas_sim/certificate_diagnostics.py)。入口：[run_certificate_diagnostics.py](../../../scripts/run/run_certificate_diagnostics.py)。

这里用同样三组 seed、每组 100，但只做名义 DGP。`atlas_config` 显式用完整表示，`semantic_config` 使用默认 `(0,1)`。因此它与 formal 的默认基线不能按标签无条件互换。

每次得到 atlas、semantic、nearest、global、oracle。字典中 `atlas_no_rejection` 直接指向同一个 atlas 结果，然后在 `_MethodEvaluation` 把它的 `released=True`。这确保这组诊断里 no_rejection 与 atlas 的 raw 预测完全相同。

一套数据产生一条 `CertificateDiagnosticRecord`，其中同一行并列保存六种误差、目标和最近语义源的真实机制坐标、证书五分项、是否发布等。因此 `results/certificate_diagnostics_summary.csv` 虽然叫 summary，实质是 300 条逐目标诊断，不是一个六行平均表。

`_summarize_method` 再对每种方法筛选 released 记录，计算 MAE、RMSE、sign accuracy、区间覆盖和宽度，得到 `results/synthetic_benchmark_summary.csv`。这里区间指标基于各方法发布集合，与 formal 的有效区间总体口径不同。

`_spearman` 先 `_average_ranks`，再 `corrcoef`。相同数值给平均名次，最后衡量半径排序与误差排序的一致程度。`mean(errors>radii)` 则直接统计误差超证书比例。相关性高与覆盖有效并非同一命题。

## 6. risk-coverage：只改变发布阈值

源码：[risk_coverage.py](../../../src/causal_atlas_sim/risk_coverage.py)。入口：[run_risk_coverage_experiment.py](../../../scripts/run/run_risk_coverage_experiment.py)。

三组 seed 20260821–20260823，每组 100。拟合时阈值设为 infinity，存好每个目标的绝对误差、覆盖、区间宽、证书半径。然后才扫描阈值 `.75,1,1.25,1.5,1.65,2,2.5,3`。

```python
accepted = np.asarray(radii, dtype=float) <= threshold + 1e-12
accepted_errors = error_array[accepted]
```

accepted 是布尔筛选向量。对它求平均是发布比例，对选中误差求平均是条件 MAE。提高 threshold 时不会重新生成目标，也不会在该循环重新优化权重。末尾另加 threshold=inf 的显式全发布端点。

因此横轴 coverage 在此通常指“发布比例”，不是置信区间覆盖率。CSV 另外有 `conditional_interval_coverage` 专门表示区间含真值的比例。正文读图时要把两个 coverage 分开。

输出 `results/risk_coverage_summary.csv`。没有发布目标的阈值，其 conditional 字段为空，不能补成 0 再连成表现优秀的曲线。

## 7. calibration experiment：故意低报平滑性界

源码：[calibration_experiment.py](../../../src/causal_atlas_sim/calibration_experiment.py)。入口：[run_calibration_experiment.py](../../../scripts/run/run_calibration_experiment.py)。

四场景为名义、源隐藏半径异质 spread=.40、shift=.60、shift=.80。三策略为 certified_atlas、no_rejection、understated_smoothness。后一策略将 L=.20、H=.05，低于原曲面的默认界。

循环每个场景生成共同数据，然后给三个策略不同 config。结果记录含 scientific_tolerance，以便汇总 `released_above_tolerance_rate`。该指标检验发布点的证书是否超过阈值；它不等于真实误差超过阈值的比例。

`_summarize_one` 同时计算 raw MAE、发布 MAE、发布区间覆盖、总体区间覆盖。`released_interval_uncovered_rate` 是 1 减发布覆盖。发生全拒绝时发布条件指标 None，但总体区间可能仍能统计。

输出 `results/calibration_experiment_summary.csv` 及对应 metadata。这里检验失配常数对发布和区间的影响，不能用较窄区间和较高发布率本身证明低报常数合理。

## 8. calibration curve：置信水平改变哪些行

源码：[calibration_curve.py](../../../src/causal_atlas_sim/calibration_curve.py)。入口：[run_calibration_curve_experiment.py](../../../scripts/run/run_calibration_curve_experiment.py)。

每个共享 archive 在 `.80,.90,.95,.975` 四个置信水平上重算区间，`zeta=1-level`。记录五个策略：honest_atlas、wald_only、semantic_forced、understated_smoothness、no_hidden_moderator_inflation。

wald_only 保持 honest 的权重和 raw，半径只保留 `z*SE`，且 accepted=True。低报平滑性界改 L/H。no_hidden 将 `hidden_moderator_lipschitz_bound=0`，它既影响证书隐藏项，也影响优化中的隐藏惩罚。默认源半径相同使后者为权重无关常数，但不能把这个结论推广到任意异质半径。

代码对后三者中两个消融的记录 `estimate` 使用 honest 的 raw，区间端点来自消融自身结果。解释此文件的 conditional MAE 时要遵守这一实际写法。当前名义等半径设置下权重相关差别受限；修改为异质半径后要重新审阅该口径。

最后按 level-policy 分组：全部记录算 empirical_coverage、mean_width；accepted_mask 选中记录算 conditional_coverage、conditional_width、conditional_mae。输出 `results/calibration_curve_summary.csv`。

## 9. 表示敏感性：分开看表示贡献与发布筛选

源码：[representation_sensitivity.py](../../../src/causal_atlas_sim/representation_sensitivity.py)。入口：[run_representation_sensitivity.py](../../../scripts/run/run_representation_sensitivity.py)。

核心循环先固定全坐标 shift=0，只改变 `target_hidden_shift_fraction`，再改变 proxy_uncertainty。这里声明半径和代理噪声半宽一起改：`moderator_sensitivity_radius=proxy_uncertainty`，`moderator_proxy_half_width=proxy_uncertainty/2`。这一点与第 2 节“只改声明半径”的扫描不同。

每个网格格子用同一批种子。ATLAS 看全表示，semantic forced 看前两维。记录 `realized_hidden_shift`，它由真实目标 h 与构造加权源 h 的差计算，是实际位移，而配置中的 fraction 是插值比例。

汇总公式：

```python
representation_advantage = semantic_mae - atlas_mae
selection_gain = atlas_mae - accepted_mae
```

第一个差的两边都是全目标 raw MAE，用于看表示与权重方案的综合差异。第二个差在同一 ATLAS 预测里比较全体与发布集合，描述筛选效果。不能把二者相加后说成一个单独模块的因果贡献。其表与记录位于 `results/representation_sensitivity_summary.csv`、`results/representation_sensitivity_records.csv`。

## 10. sanity check 与 Monte Carlo 为什么还保留

[run_sanity_check.py](../../../scripts/run/run_sanity_check.py) 用单个生成任务打印假设构造报告，检查管线是否接通。[monte_carlo.py](../../../src/causal_atlas_sim/monte_carlo.py) 的 `run_monte_carlo` 则多次评估构造权重下噪声、代理差与界。

它们使用 oracle 构造信息用于检查生成器，不能替代 learned ATLAS 的方法比较。[run_method_comparison.py](../../../scripts/run/run_method_comparison.py) 是五方法基础比较入口；formal、certificate 模块才补充多种子、消融与正文专用诊断。

这些脚本即使不直接贡献当前正文某张图，也是理解和复核实验链的起点。完整命令与后处理依赖见第 10、11 章。
