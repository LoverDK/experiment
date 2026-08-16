# 结果目录说明

`results/` 是固定种子实验产物区，不是源码区。数值应由 `scripts/run/` 生成，
组合图和论文表应由 `scripts/build/` 生成，不要手工修改 CSV 中的数字。

## 基础合成结果

- `main_experiment_*`、`formal_experiment_*`：主扫描与正式多种子基准。
- `calibration_experiment_*`、`risk_coverage_*`、`calibration_curve_*`：发布、
  覆盖率和宽度诊断。

## 论文级新增结果

- `representation_sensitivity_summary.csv`：25 个隐藏偏移×代理不确定性单元格。
- `certificate_diagnostics_summary.csv`：300 个共同目标的证书、误差和分量。
- `synthetic_benchmark_summary.csv`：ATLAS、消融、语义基线和 oracle 六方法主表。
- `bridge_budget_path_summary.csv`：严重失配场景的 0--4 预算路径诊断。
- `nsw_diagnostics_summary.csv`：1,680 条 ATLAS NSW held-out 诊断。
- `nsw_archive_map_summary.csv`：112 个 NSW 局部对象的 PCA 坐标与发布频率。
- `nsw_method_error_records.csv`：五种方法在共享 holdout 上的 8,400 条逐目标误差，
  用于原论文布局 NSW 图的完整误差分布面板。

## 理论与真实数据

- `partial_identification_*`、`minimax_experiment_*`、`bridge_experiment_*`、
  `bridge_optimality_*`：Theorem 5.4--5.6 数值实验。
- `nsw_experiment_*`：真实数据五方法主结果和元数据。

## 图、表与清单

- `figures/`：阶段图和 Figure 2--5；最终组合图同时提供 PNG 与 PDF。以
  `legacy_layout_` 开头的两张图复现原论文四面板布局，但使用当前协议数值。
- `tables/`：Markdown 阅读版和可由 Overleaf `\input{}` 的 LaTeX 表；
  `legacy_layout_table1`--`table3` 是原论文三张实验表的当前协议版本。
- `experiment_manifest.json`：结果文件大小、SHA-256 和预期行数。
