# 脚本运行导航

脚本按职责分成两个区域：`run/` 负责产生统计结果，`build/` 只读取已经保存的
结果并整理报告、图表和清单。所有命令都应在仓库根目录执行。

## 1. 快速检查

```powershell
python scripts/run/run_sanity_check.py
python scripts/run/run_algorithm1.py
```

第一条验证 Assumption 3.1--3.5；第二条展示一条完整 Algorithm 1 接受或拒绝、
部分识别和 bridge 路径，不运行完整 Monte Carlo。

## 2. 基础合成实验

```powershell
python scripts/run/run_monte_carlo.py
python scripts/run/run_method_comparison.py
python scripts/run/run_main_experiment.py
python scripts/run/run_formal_experiment.py
python scripts/run/run_calibration_experiment.py
python scripts/run/run_risk_coverage_experiment.py
python scripts/run/run_calibration_curve_experiment.py
```

这些命令依次覆盖重复抽样、方法比较、参数扫描、正式多种子基准、证书失效边界、
risk--coverage 和 coverage--width。

## 3. 理论扩展与实验设计

```powershell
python scripts/run/run_partial_identification_experiment.py
python scripts/run/run_minimax_experiment.py
python scripts/run/run_bridge_experiment.py
python scripts/run/run_bridge_optimality_experiment.py
python scripts/run/run_bridge_budget_path_experiment.py
```

`run_bridge_experiment.py` 是最慢的正式协议。最后一个命令只为 Figure 4 的严重
失配预算路径运行 3 种策略×3 个种子×30 次，不替代正式 300 次主汇总。

## 4. 真实数据

```powershell
python scripts/run/run_nsw_experiment.py
```

除五方法主表外，还保存 ATLAS 的逐目标诊断、112 个局部对象的 PCA 地图数据，
以及五种方法共享 target 的 8,400 条逐目标误差记录。

## 5. 论文级新增评价

```powershell
python scripts/run/run_representation_sensitivity.py
python scripts/run/run_certificate_diagnostics.py
```

第一条运行 25 个隐藏偏移×代理不确定性单元格；第二条生成证书与实际误差诊断、
六方法共同目标表和 evaluation-only oracle。真实机制不得进入其他 runner。

## 6. 只构建产物

```powershell
python scripts/build/build_final_report.py
python scripts/build/build_paper_artifacts.py
python scripts/build/build_paper_figures.py
```

这三条命令不重新抽样。最后一条从 CSV/JSON 生成 Figure 2--5、两张原论文布局
兼容图的 PNG/PDF，以及当前论文表和原论文 Table 1--3 的 Markdown/LaTeX 版本。

## 7. 核验 Overleaf 留档

```powershell
python scripts/build/verify_overleaf_revision.py
```

核验最终源稿与修改前在线版本的理论段落、引用图表和标签，复算保存记录中的
Wilson 区间与 MAE Monte Carlo SE，并检查最终 Overleaf 编译日志。
审计结果写入 `docs/paper/revision_evidence/source_and_results_audit.json`。
