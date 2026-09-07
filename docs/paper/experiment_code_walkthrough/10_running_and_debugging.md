# 10：从可运行小例子到完整复现

本章提供两个已经放进仓库的教学脚本，并解释它们的每个计算步骤。脚本只在内存生成一个示例或读取保存 CSV，均不修改结果、图表和论文。

## 1. 解释器与依赖

从仓库根目录操作。代码使用 `zip(...,strict=True)`、联合类型提示等 Python 3.10+ 语法。实际复现版本应核对各 metadata 中 python、numpy、pandas 字段；同一 seed 不替代版本记录。

```powershell
python --version
python -m pip show numpy pandas matplotlib pillow
```

`python -m pip` 明确使用当前 python 的包管理器，避免另一个环境的 pip。仓库当前没有统一 requirements/pyproject 锁版本文件，不能声称已提供一键锁定的依赖环境。缺失包时可安装：

```powershell
python -m pip install numpy pandas matplotlib pillow
```

这安装当前可用版本；要逐数值复现应参考对应运行 metadata 选择相同版本。普通教学读取只需 numpy、pandas，图表构建另需 matplotlib、Pillow。

## 2. 第一个脚本：亲眼看一次 ATLAS 拟合

```powershell
python docs/paper/experiment_code_walkthrough/examples/inspect_one_archive.py
```

打开 [inspect_one_archive.py](examples/inspect_one_archive.py) 对照本节。它自身位于 docs/paper/experiment_code_walkthrough/examples，因此 `parents[4]` 才是仓库根目录，不是 runner 中的 parents[2]。

顶部导入 replace/asdict、Path、json、sys、numpy，再把 src 加入 sys.path，导入 DGP、方法、Algorithm 1。执行 main 时：

1. `config=SimulationConfig()` 建默认 8 源、400 人设置。
2. `generate_minimal_archive(...,seed=20260805)` 只生成一次迁移任务。
3. `source=generated.archive[0]` 抽出首个源对象用于展示。
4. shapes 字典从真实数组 `.shape` 读取维度，打印出来，不手写伪造数据。
5. mean_score、score_se 直接从 source.aipw_scores 重算均值和标准误，assert_allclose 与源对象字段比较。
6. replace 把目标的评价字段设 NaN，fit_causal_atlas 只收到盲化目标。
7. effects 列表收集八个源效应，`weights@effects` 独立重算 raw 点估计；检查权重和及非负。
8. asdict(certificate) 将数据类变字典，手工排除 radius 键，再相加五项，核对总半径。
9. 打印 raw、published 和 accepted，再用没有传给拟合器的原目标真值计算误差。
10. 另以阈值 0 调用 Algorithm 1，进入拒绝 PI 分支，预算默认 0，不选择 bridge。
11. 以每个中心±分量半径手工求 max lower/min upper，核对 PI 返回端点。
12. 打印权重族标签、component_zeta、PI 宽度与是否含真值，然后退出。

`np.testing.assert_allclose` 允许浮点数很小误差；若不一致会抛异常，而不是印一句“成功”掩盖问题。脚本没有 `open('w')`、to_csv 或 savefig，因此不会覆盖论文结果。

## 3. 第二个脚本：从已存记录还原表里的数

```powershell
python docs/paper/experiment_code_walkthrough/examples/trace_saved_results.py
```

打开 [trace_saved_results.py](examples/trace_saved_results.py)。ROOT 与第一个相同，RESULTS 指向根目录 results。read(relative) 只是 pd.read_csv；same(actual,expected) 包装 assert_allclose。

### 3.1 正文六方法表中的 ATLAS 行

读取 300 条 certificate 诊断。published 是 atlas_accepted 布尔列；`.loc[published,'atlas_absolute_error']` 只保留发布误差，mean 得发布 MAE。全列 mean 得 raw MAE。与 synthetic_benchmark_summary 的 atlas/no_rejection 两行比较。

现有结果为发布 139/300，发布 MAE 约 .110919，全体 raw MAE 约 .138699。这个数字例子直接来自保存 CSV，和第 3 章的三个数教学例子性质不同。

### 3.2 B.3 强基线的配对差

取 v2 nominal，pivot 成每 seed 一行、每 method 一列。difference=ridge 列-no_rejection 列。求 mean，再用差值 SD/根号 300 求 MCSE，核对 synthetic_paired_summary。不能先筛 atlas 发布集合，因为这张表的问题是全目标比较。

### 3.3 B.3 同发布率点值

取 v3 moderate test，各方法按 score/replicate 排序，取前 round(300*.5)=150 行，求 error 均值。与 selection_rank_bootstrap 的原始点值比较。脚本没有重跑其 1000 轮 bootstrap；bootstrap 区间来源和代码在第 6 章解释。

### 3.4 B.2 曲面与 nuisance

threshold/baseline/atlas 的 error、covered、width 分别平均，对照 mechanism_summary。然后取 nuisance n=400、balanced、quadratic_known 的完整源效果记录，算 `sqrt(mean(error**2))`，对照 nuisance_effect_summary。

这里源记录通常每 replicate 八条，与迁移任务每 replicate 一条不同。脚本输出记录数量，避免把 source-level RMSE 误读为 target transfer RMSE。

### 3.5 B.2 相关性和常数

取 constant surface、rho=.7，按方差 method 平均 covered，直观看忽略相关的后果。另取 constants nominal 按 factor 平均 width，观察点权重固定时扩大常数的区间变化。

### 3.6 B.4 半合成与真实数据

半合成先 groupby replicate 求六目标均值，得到 100 个独立重复的均值，再求总体 MAE 与 MCSE，对照 summary。

NSW 稳定性取 replicate/anchor/k 三列并 drop_duplicates，数有效设计，和失败表相加检查 120。Hillstrom 固定 visit/source_loo_empirical/.9，按 method 算 18 个 cell 的 MAE；另检查所有 .95 残差区间无限宽。

### 3.7 B.5 retained bridge

取 bridge_checks_8192 的 retained family，检查恰好 72 条、所有 bound_holds 为真且 lower_bound>0。按 budget 平均 selected_value、optimum、lower_bound，对应附录的三行。计算不扩展为 operational 的理论结论。

## 4. 在编辑器里设置断点

在第一个脚本 `generated=...` 之后设置断点，调试时看 generated；在 fit 之后看 result；在 PI 之后看 interval。Watch 中可以输入 `source.x.shape`、`result.weights`、`result.certificate.radius`。

“单步进入”会进入调用的函数，“单步跳过”执行完整一行再停下。建议先跳过 NumPy 内部计算，仅进入本仓库 dgp/methods/algorithm1；否则会落进大量第三方库细节，难以看清实验结构。

## 5. 缩小实验时改哪里的配置

原始 dataclass 协议通常允许在 Python 中构造 config：例如 `FormalExperimentConfig(repetitions_per_seed=2,base_seeds=(20260811,))`。这改变内存任务规模；若仍调用正式 runner 的写出函数，则可能覆盖正式路径，应另写到自己明确区分的教学目录。

v2 runner 支持 `--repetitions`、`--bootstrap`、`--bridge-repetitions`，但仍写固定 results/extensions，所以小规模也会覆盖该 block 正式 CSV。v3 block 函数规模多写在函数体中，本教程不建议为学习直接改正式代码和结果。

一个小例子成功只验证调用可通，不验证 300 次重复或 8192 积分的论文结果。不要用 smoke metadata 替换正式规模 metadata。

## 6. 完整重跑顺序：原始协议

以下不是本次文档验证实际执行的命令清单，而是你将来从头复现的顺序。正式 bridge 尤其耗时，runner 写固定输出路径。

```powershell
python scripts/run/run_sanity_check.py
python scripts/run/run_monte_carlo.py
python scripts/run/run_method_comparison.py
python scripts/run/run_algorithm1.py
python scripts/run/run_main_experiment.py
python scripts/run/run_formal_experiment.py
python scripts/run/run_calibration_experiment.py
python scripts/run/run_risk_coverage_experiment.py
python scripts/run/run_calibration_curve_experiment.py
python scripts/run/run_representation_sensitivity.py
python scripts/run/run_certificate_diagnostics.py
python scripts/run/run_partial_identification_experiment.py
python scripts/run/run_minimax_experiment.py
python scripts/run/run_bridge_experiment.py
python scripts/run/run_bridge_optimality_experiment.py
python scripts/run/run_bridge_budget_path_experiment.py
python scripts/run/run_nsw_experiment.py
```

bridge focused path 放在正式 bridge 后面，确保 Figure 4 使用 90 路径/策略的专用文件。部分原始基础脚本仅打印 JSON，不会自动把终端输出保存为一个新 tracked CSV。

## 7. 完整重跑顺序：v2 与 v3

```powershell
python scripts/run/run_requested_extensions.py synthetic --repetitions 100
python scripts/run/run_requested_extensions.py nsw --repetitions 100 --bootstrap 200
python scripts/run/run_requested_extensions.py bridge --bridge-repetitions 12
python scripts/run/run_validation_v3.py selection
python scripts/run/run_validation_v3.py mechanisms
python scripts/run/run_validation_v3.py nuisance
python scripts/run/run_validation_v3.py dependence
python scripts/run/run_validation_v3.py constants
python scripts/run/run_validation_v3.py nsw
python scripts/run/run_validation_v3.py hillstrom
python scripts/run/run_validation_v3.py bridge
```

Hillstrom 输入必须已有 csv 和 provenance。v3 bridge 依赖 v2 bridge_set_values。每 block 读 metadata.status 判断完成，失败表非空不一定说明整个 block 执行失败：它可能是成功记录设计失效的预期结果。

## 8. 从保存结果重建展示

```powershell
python scripts/build/build_final_report.py
python scripts/build/build_paper_artifacts.py
python scripts/build/build_paper_figures.py
python scripts/build/build_paired_comparison_table.py
python scripts/build/build_extension_artifacts.py
python scripts/build/build_validation_v3.py
```

这些会重写报告、汇总或图表，v2 builder 要全部 v2 block 输出，v3 builder 要全 v3 记录及 selection 的历史校准输入。builder 不替缺失 runner 补实验。

只有决定更新本地稿时再执行 `python scripts/build/restructure_appendix_b.py`。当前集成用它，不用历史 integrate_requested_extensions。不要运行不存在的 verify_validation_v3.py；当前仓库没有该入口。

## 9. 常见报错怎样定位

| 现象 | 先检查什么 | 原因 |
| --- | --- | --- |
| can't open file | 当前目录、路径拼写 | 命令未从仓库根运行 |
| No module named numpy/pandas | 当前 python 和 pip show | 包装在另一个解释器或未安装 |
| NSW hash mismatch | data 快照与 provenance | 输入文件版本不同 |
| arm_minimum | failures 表、n 与处理比例 | 一个训练臂/邻域人数不足 |
| builder 行数 assert | metadata 正式重复规模 | smoke 输出覆盖正式文件 |
| missing bridge_set_values | v2 bridge 是否完成 | v3 需要旧积分对照 |
| infinity width | finite_quantile 的 n、rank | 未必是程序故障，可能为规定输出 |
| accepted MAE 空白 | 发布个数 | 全拒绝时该平均没有定义 |
| 文件索引测试失败 | git status 和 file map | 新文档或临时未跟踪文件未入索引 |

## 10. 本次文档的验证与留痕

本次只运行两个教学脚本和文档专用核验，具体结果见 [verification.md](verification.md)。不重新跑论文规模的所有实验，不重建图表，不修改理论，也不把历史编译日志当成新编译。

文档与教学代码一起纳入 Git 提交；原 source/result/tex 作为链接来源，保留原有版本。通过 `git log -- docs/paper/experiment_code_walkthrough` 可查本次新增与后续维护。
