# 逐文件源码导航

本章是前面各实验章节的索引，不替代逐行讲解。先用论文位置或想复现的问题定位一行，再打开相应 runner；runner 通常只负责解析参数、调用核心函数和保存文件，计算细节在 `src/causal_atlas_sim/`。下列路径都相对仓库根目录。

## 1. 核心模块：数据、方法和公共结果

| 文件 | 从哪里开始读 | 做什么 | 被哪些章节使用 |
| --- | --- | --- | --- |
| `dgp.py` | `SimulationConfig`、`generate_minimal_archive` | 定义合成机制，生成八个源实验和目标；计算 AIPW 分数、真值、公开表示和假设构造信息。 | 01--04、07 |
| `methods.py` | `fit_causal_atlas` | 检索候选源、投影到 simplex、优化权重、计算五项证书，给出接受或拒绝。 | 02--08 |
| `algorithm1.py` | `run_algorithm1` | 在 ATLAS 拒绝后计算多个允许权重族的区间交集。 | 02、04 |
| `experiments.py` | `run_main_experiment` | 主合成扫描的配置、循环和汇总行。 | 03 |
| `formal_experiment.py` | `run_formal_experiment` | 三个种子、六个正式场景和七种估计器的共同目标比较。 | 03、06 |
| `certificate_diagnostics.py` | `run_certificate_diagnostics` | 保存 300 个目标的权重、误差、五项证书分量及接受标记。 | 03、09 |
| `comparison.py` | `run_method_comparison` | 早期五方法合成比较。 | 03 |
| `reporting.py` | 汇总和 CSV 工具函数 | 把 dataclass 结果转成表格行，供若干 runner 复用。 | 03--06 |
| `paper_artifacts.py`、`paper_figures.py` | `build_*` 函数 | 把保存记录聚合为论文表和组合图的中间结果。 | 09 |
| `figure_style.py` | 图形常量 | 统一 Matplotlib 的字体、颜色和导出设置。 | 09 |

## 2. 正文合成和原始诊断

| Runner | 调用的核心代码 | 主要输入 | 写出的主要文件 | 导读章节 |
| --- | --- | --- | --- | --- |
| `scripts/run/run_sanity_check.py` | `dgp.py`、`methods.py` | 一个固定种子 archive | `results/sanity_check.json` | 01、02、03 |
| `scripts/run/run_monte_carlo.py` | `monte_carlo.py` | 固定 DGP 下的重复抽样 | `results/monte_carlo_*` | 03 |
| `scripts/run/run_method_comparison.py` | `comparison.py` | 合成 archive | `results/method_comparison_*` | 03 |
| `scripts/run/run_main_experiment.py` | `experiments.py` | `MainExperimentConfig` 的扫描网格 | `results/main_experiment_summary.csv` 和两张 PNG | 03 |
| `scripts/run/run_formal_experiment.py` | `formal_experiment.py` | 3 个种子、6 场景、7 方法 | `results/formal_experiment_summary.csv`、seed summary、metadata | 03、06 |
| `scripts/run/run_certificate_diagnostics.py` | `certificate_diagnostics.py` | 3 个种子、每种子 100 个目标 | `results/certificate_diagnostics_summary.csv` | 03、09 |
| `scripts/run/run_representation_sensitivity.py` | `representation_sensitivity.py` | 隐藏偏移和代理噪声网格 | `results/representation_sensitivity_summary.csv` | 03、07 |
| `scripts/run/run_risk_coverage_experiment.py` | `risk_coverage.py` | 同一目标记录上的发布阈值 | `results/risk_coverage_summary.csv` | 03 |
| `scripts/run/run_calibration_experiment.py` | `calibration_experiment.py` | 名义覆盖水平 | `results/calibration_experiment_summary.csv` | 03 |
| `scripts/run/run_calibration_curve_experiment.py` | `calibration_curve.py` | 多个区间水平与 Wald 对照 | `results/calibration_curve_summary.csv` | 03 |

这些 runner 会写固定结果目录。先阅读 [10_running_and_debugging.md](10_running_and_debugging.md) 的保护步骤，避免用小规模试跑覆盖已提交的正式 CSV。

## 3. 拒绝、部分识别、minimax 和 bridge

| Runner | 核心模块 | 输出 | 说明 |
| --- | --- | --- | --- |
| `scripts/run/run_algorithm1.py` | `algorithm1.py` | 控制台 JSON | 一条完整 Algorithm 1 路径，适合先看分支。 |
| `scripts/run/run_partial_identification_experiment.py` | `partial_identification.py`、`algorithm1.py` | `results/partial_identification_summary.csv`、seed summary、metadata | 保存汇总，不保存逐目标 records CSV。 |
| `scripts/run/run_minimax_experiment.py` | `minimax_experiment.py` | `results/minimax_experiment_summary.csv`、seed summary、metadata | 数值 minimax 对照，保存口径同上。 |
| `scripts/run/run_bridge_experiment.py` | `bridge_experiment.py`、`algorithm1.py` | `results/bridge_experiment_summary.csv`、seed summary、metadata | 正式四场景、三策略 bridge。 |
| `scripts/run/run_bridge_optimality_experiment.py` | `bridge_experiment.py` | `results/bridge_optimality_summary.csv`、metadata | 小候选库的事后穷举对照。 |
| `scripts/run/run_bridge_budget_path_experiment.py` | `bridge_experiment.py` | `results/bridge_budget_path_summary.csv`、metadata | 只跑 severe 场景的 focused path；会覆盖同名路径汇总。 |

`bridge_experiment.py` 负责条件期望、Gauss--Hermite 积分、策略轨迹和空交集记录。`extension_bridge.py` 则服务于 v2/v3 的固定候选库、保留证书和积分稳定性诊断，见第 5 节。

## 4. NSW 和 v2 补充实验

| Runner 或入口 | 核心模块 | 输入与输出 | 导读章节 |
| --- | --- | --- | --- |
| `scripts/run/run_nsw_experiment.py` | `nsw_experiment.py` | 读取 `data/nsw_dw.dta`，写 `results/nsw_*` 描述性 reconstruction 记录。 | 05 |
| `scripts/run/run_requested_extensions.py synthetic --repetitions 100` | `extension_baselines.py` | 写 `results/extensions/synthetic_*` 的强基线和配对比较。 | 06 |
| `scripts/run/run_requested_extensions.py nsw --repetitions 100 --bootstrap 200` | `extension_nsw.py` | 写分离源/参考单位的 NSW、失败记录和半合成记录。 | 05 |
| `scripts/run/run_requested_extensions.py bridge --bridge-repetitions 12` | `extension_bridge.py` | 写全部子集值、空交集和 frozen-law bridge 检查。 | 04、08 |

`run_requested_extensions.py` 是 v2 的参数分派入口；它不是单一实验。三个子命令依赖的原始数据、随机种子和输出都不同，应分别运行。`extension_baselines.py` 实现 ridge、RBF、IVW 和 source LOO 基线；`extension_nsw.py` 负责 NSW 的固定设计、分离池和半合成真值。

## 5. v3 附录 B 实验

`scripts/run/run_validation_v3.py` 只接受一个 `block` 参数。它在 `try/finally` 中写出对应的 `*_metadata.json`，因此失败时也会留下命令、耗时和错误文字。计算都在 `validation_v3.py`。

| 命令中的 block | 函数 | 主要结果 | 当前附录位置 | 导读章节 |
| --- | --- | --- | --- | --- |
| `selection` | `selection_intervals` | calibration/test 预测、排序 bootstrap | B.3 | 06 |
| `mechanisms` | `mechanism_benchmark` | 五种效应曲面、变换和失败边界 | B.2 | 07 |
| `nuisance` | `nuisance_experiment` | 完整与部分 archive、拟合 nuisance 误差 | B.2 | 07 |
| `dependence` | 相关性实验段 | 各相关系数下的覆盖和宽度 | B.2 | 07 |
| `constants` | 常数敏感性实验段 | 原生证书常数的倍数扫描 | B.2 | 07 |
| `nsw` | `nsw_stability` | 20 个划分、锚点和 k 的有效/失败设计 | B.4 | 08 |
| `hillstrom` | `hillstrom` | 单元 LOO 误差与经验残差区间 | B.4 | 08 |
| `bridge` | `bridge_stability` | 8,192 draw 的 retained-certificate 积分检查 | B.5 | 08 |

## 6. 构建脚本和历史脚本

| 文件 | 正确用途 |
| --- | --- |
| `scripts/build/build_final_report.py` | 从原始合成结果重建中文总报告。 |
| `scripts/build/build_paper_artifacts.py` | 汇总保存记录，生成论文写作辅助产物。 |
| `scripts/build/build_paper_figures.py` | 从保存 CSV 生成 Figure 2--5 等组合图。 |
| `scripts/build/build_paired_comparison_table.py` | 从共同目标诊断生成配对比较表。 |
| `scripts/build/build_extension_artifacts.py` | 汇总 v2 的 synthetic、NSW 和 bridge 结果。 |
| `scripts/build/build_validation_v3.py` | 汇总全部 v3 block，并执行其中定义的固定 bootstrap。 |
| `scripts/build/restructure_appendix_b.py` | 用已保存 CSV 与模板重建当前五板块附录 B 的表和内嵌内容；会改本地论文源稿。 |
| `scripts/build/audit_appendix_b_assets.py` | 检查保存的 Overleaf 文件树、引用资产和历史编译证据；不发起线上编译。 |
| `scripts/build/verify_overleaf_revision.py` | 核验当时保存的修订证据范围，不读取当前线上编辑器。 |
| `scripts/build/integrate_requested_extensions.py` | v2 的历史集成入口；当前附录 B 不使用它。 |

`scripts/run/audit_proof_counterexamples.py` 读取或生成附录 A 的理论审计材料。它不是性能实验，也不能把数值反例搜索当成形式化证明验证。论文理论的人工审计结论在 `docs/paper/appendix_A_proof_audit.md`。

## 7. 最短的源码追踪练习

1. 运行 `python docs/paper/experiment_code_walkthrough/examples/inspect_one_archive.py`，然后同时打开 `dgp.py`、`methods.py` 和 `algorithm1.py`。
2. 运行 `python docs/paper/experiment_code_walkthrough/examples/trace_saved_results.py`，让每一行输出回到相应 CSV 和汇总表。
3. 选一个附录 B 表，先在 [09_results_figures_tables_paper.md](09_results_figures_tables_paper.md) 找输入 CSV，再在本章第 5 节找生成它的 block 和函数。

这条路径能避免直接从最终表格猜测计算口径，也能明确区分“生成新随机实验”和“读取已有记录做汇总”两类脚本。
