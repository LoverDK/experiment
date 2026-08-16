# 仓库文件功能对照表

本文件是仓库的文件级导航与维护清单。表中覆盖所有受 Git 跟踪的项目文件，
不包含 Git 内部元数据目录 .git。

维护规则：

1. 新增、删除、移动或重命名项目文件时，必须在同一提交中更新本表。
2. 既有文件的职责、输入输出或生成关系发生变化时，必须同步修订其说明。
3. 修改后运行 python -m unittest discover -s tests -v；其中
   test_repository_file_map.py 会检查本表是否遗漏当前项目文件。
4. results/ 下的 CSV、JSON、PNG、Markdown 和 TeX 是可复现实验产物；
   优先通过对应 scripts/ 中的生成器更新，不应手工篡改数值。

| 路径 | 类别 | 功能与维护关系 |
| --- | --- | --- |
| .gitignore | 仓库配置 | 排除 Python 缓存和临时输出，并显式保留各阶段固定种子 CSV、JSON、图表等可复现产物。 |
| .agents/skills/lean-bisect/SKILL.md | 本地代理技能 | Lean 工具链版本二分工作流说明；不参与本项目仿真运行。 |
| .agents/skills/lean-mwe/SKILL.md | 本地代理技能 | Lean 错误最小可复现示例工作流说明；不参与本项目仿真运行。 |
| .agents/skills/lean-pr/SKILL.md | 本地代理技能 | Lean 项目 PR 约定；不参与本项目仿真运行。 |
| .agents/skills/lean-proof/SKILL.md | 本地代理技能 | Lean 证明协作工作流说明；不参与本项目仿真运行。 |
| .agents/skills/lean-setup/SKILL.md | 本地代理技能 | Lean 仓库与 toolchain 配置说明；不参与本项目仿真运行。 |
| .agents/skills/mathlib-build/SKILL.md | 本地代理技能 | Mathlib 构建工作流说明；不参与本项目仿真运行。 |
| .agents/skills/mathlib-pr/SKILL.md | 本地代理技能 | Mathlib PR 约定；不参与本项目仿真运行。 |
| .agents/skills/mathlib-review/SKILL.md | 本地代理技能 | Mathlib 代码审查工作流说明；不参与本项目仿真运行。 |
| .agents/skills/nightly-testing/SKILL.md | 本地代理技能 | Lean/Mathlib nightly 测试说明；不参与本项目仿真运行。 |
| .agents/skills/scientific-figure-making/SKILL.md | 本地代理技能 | 学术图表制作与检查工作流说明；可用于后续论文图表整理。 |
| .agents/skills/scientific-figure-making/references/api.md | 技能参考 | scientific-figure-making 的 API 参考。 |
| .agents/skills/scientific-figure-making/references/common-patterns.md | 技能参考 | scientific-figure-making 的常见图表模式参考。 |
| .agents/skills/scientific-figure-making/references/demos.md | 技能参考 | scientific-figure-making 的示例参考。 |
| .agents/skills/scientific-figure-making/references/design-theory.md | 技能参考 | scientific-figure-making 的图表设计原则参考。 |
| .agents/skills/scientific-figure-making/references/tutorials.md | 技能参考 | scientific-figure-making 的教程参考。 |
| README.md | 项目入口 | 说明研究目标、各实验阶段、复现命令和主要产物位置；新增阶段时同步更新。 |
| data/nsw_dw.dta | 阶段 12 数据 | NBER 发布的 Dehejia-Wahba NSW 随机实验原始快照；运行前按固定 SHA-256 校验。 |
| docs/README.md | 文档导航 | 按 stages、reference 和 paper 三个区域解释文档结构与阅读顺序。 |
| docs/paper/final_experiment_report.md | 阶段 7 产物 | 汇总全部合成仿真实验的中文报告，由 scripts/build/build_final_report.py 生成。 |
| docs/paper/main_text_gap_catalog/01_foundational_checks.md | 正文遗漏目录 | 对照 DGP 假设校验、早期 oracle Monte Carlo 和方法演示，判断是否仍应进入正文。 |
| docs/paper/main_text_gap_catalog/02_synthetic_sweeps_and_ablations.md | 正文遗漏目录 | 整理合成扫描、正式多种子压力场景、消融、表示网格，并修正选择效应与表示效应的解释。 |
| docs/paper/main_text_gap_catalog/03_certificate_diagnostics.md | 正文遗漏目录 | 整理证书分量、异质隐藏半径和完整校准政策，给出正文候选文本与附录边界。 |
| docs/paper/main_text_gap_catalog/04_partial_identification_and_minimax.md | 正文遗漏目录 | 整理多权重交集、oracle 非识别诊断和 Theorem 5.5 minimax 数值实验。 |
| docs/paper/main_text_gap_catalog/05_bridge_additional_evidence.md | 正文遗漏目录 | 整理 bridge 跨场景结果、规划不一致、oracle 支持缩减和 focused 路径计数。 |
| docs/paper/main_text_gap_catalog/06_nsw_additional_evidence.md | 正文遗漏目录 | 整理 NSW 表示分工、local object、holdout 口径和 no-rejection 指标解释。 |
| docs/paper/main_text_gap_catalog/README.md | 正文遗漏总索引 | 汇总仓库已做而当前 Section 6 未写或只写部分的实验，按 P0--P2 给出正文取舍。 |
| docs/paper/paper_experiment_extension.md | 论文扩展说明 | 说明 Oracle、表示敏感性、证书诊断和 Figure 2--5 的设计、边界与复现方式。 |
| docs/paper/paper_results_section.md | 阶段 8 产物 | 面向论文写作的中文结果段落，由 scripts/build/build_paper_artifacts.py 生成。 |
| docs/reference/algorithm1_alignment.md | 算法对照 | 将论文 Algorithm 1 逐行映射到统一代码入口、阶段、公式、分支和肉眼可见产出。 |
| docs/reference/repository_file_map.md | 维护索引 | 本文件；任何项目文件或职责变更时同步更新。 |
| docs/stages/bridge_experiment.md | 阶段 11 文档 | 说明 Definition 5.2 条件边际期望部分识别直径、三种策略、不一致诊断和 Theorem 5.6 边界。 |
| docs/stages/calibration_experiment.md | 阶段 6 文档 | 说明证书校准、异质隐藏半径、失效边界和 coverage--width 校准曲线。 |
| docs/stages/formal_experiment.md | 阶段 5 文档 | 说明多种子正式基准、消融设置、统计不确定性与结果解释。 |
| docs/stages/main_experiment.md | 阶段 4 文档 | 说明四个单因素参数扫描、图表和空单元含义。 |
| docs/stages/method_comparison.md | 阶段 3 文档 | 记录 Causal ATLAS、拒绝消融和语义基线的方法比较。 |
| docs/stages/minimal_dgp.md | 阶段 1 文档 | 对应论文 Assumption 3.1--3.5，解释最小 DGP 的数学构造与证书。 |
| docs/stages/minimax_experiment.md | 阶段 10 文档 | 说明 Theorem 5.5 的二点构造、固定协议、构造下界、经验风险和适用限制。 |
| docs/stages/monte_carlo.md | 阶段 2 文档 | 说明独立 Monte Carlo 重复、oracle 评估和区间覆盖检查。 |
| docs/stages/nsw_experiment.md | 阶段 12 文档 | 说明 NSW 数据来源、local object 构造、blind holdout、方法、诊断和真实数据限制。 |
| docs/stages/partial_identification_experiment.md | 阶段 9 文档 | 说明 Theorem 5.4 权重区间交集、固定协议、覆盖率、宽度和非识别结论。 |
| results/README.md | 结果导航 | 解释结果根目录、figures、tables、metadata 和 manifest 的职责及重建方式。 |
| results/bridge_budget_path_metadata.json | Bridge 路径元数据 | 记录严重失配绘图诊断的三种策略、三个固定种子、预算网格和评价边界。 |
| results/bridge_budget_path_summary.csv | Bridge 路径主表 | 15 行预算-策略汇总，用于 Figure 4 的预算路径；不替代正式 bridge 主表。 |
| results/calibration_experiment_metadata.json | 阶段 6 产物 | 保存证书校准实验的固定配置、种子和场景元数据。 |
| results/calibration_experiment_seed_summary.csv | 阶段 6 产物 | 按基准种子汇总的证书校准结果，用于检查跨种子稳定性。 |
| results/calibration_experiment_summary.csv | 阶段 6 产物 | 证书校准与失效边界的主汇总表；阶段 7、8 从中读取数值。 |
| results/calibration_curve_metadata.json | 校准曲线元数据 | 保存多置信水平 coverage--width 校准协议、固定种子与证书配置。 |
| results/calibration_curve_summary.csv | 校准曲线主表 | 20 行名义水平-策略汇总，联合报告发布率、经验覆盖率、宽度与条件指标。 |
| results/certificate_diagnostics_metadata.json | 证书诊断元数据 | 保存 300 个目标的固定多种子协议、证书口径和评价限定。 |
| results/certificate_diagnostics_summary.csv | 证书诊断主表 | 逐目标记录证书半径、绝对误差、接受状态及各证书分量。 |
| results/bridge_optimality_metadata.json | Bridge 穷举元数据 | 保存 12 候选、预算 1--3、30 次重复和事后穷举评价边界。 |
| results/bridge_optimality_summary.csv | Bridge 穷举主表 | 三个预算下 causal greedy 与 exhaustive optimum 的最终直径、价值比和集合命中率。 |
| results/experiment_manifest.json | 可复现性产物 | 记录结果、图表和报告的 SHA-256 校验值，由两个 build 脚本刷新。 |
| results/figures/calibration_experiment_overview.png | 阶段 6 图 | 比较正确证书、无拒绝和低报界策略的发布率与覆盖率。 |
| results/figures/calibration_curve.png | 校准曲线图 | 展示多个名义置信水平下各策略的经验覆盖率与平均区间宽度。 |
| results/figures/bridge_experiment_overview.png | 阶段 11 图 | 比较 causal greedy、semantic greedy 和 random bridge 的最终直径及预算路径。 |
| results/figures/formal_experiment_overview.png | 阶段 5 图 | 展示正式多种子基准中的发布率、消融与已发布点 MAE。 |
| results/figures/main_experiment_acceptance.png | 阶段 4 图 | 展示四项参数扫描下各方法的发布率。 |
| results/figures/main_experiment_mae.png | 阶段 4 图 | 展示四项参数扫描下各方法的已发布点 MAE。 |
| results/figures/minimax_experiment_overview.png | 阶段 10 图 | 并列展示 Theorem 5.5 两个构造下界分量及其与代表性估计器最坏风险的关系。 |
| results/figures/nsw_diagnostics_overview.pdf | Figure 5 矢量图 | NSW archive map、holdout 重建和证书诊断的论文排版版本。 |
| results/figures/nsw_diagnostics_overview.png | Figure 5 预览图 | NSW archive map、holdout 重建和证书诊断的位图预览。 |
| results/figures/nsw_experiment_overview.png | 阶段 12 图 | 展示五种方法的 NSW holdout MAE、coverage 和 rejection diagnostics。 |
| results/figures/partial_identification_overview.png | 阶段 9 图 | 展示拒绝率、部分识别非空率、覆盖率和拒绝点区间宽度。 |
| results/figures/rejection_bridge_overview.pdf | Figure 4 矢量图 | 将支持恶化、部分识别与 bridge 预算路径连成完整流程。 |
| results/figures/rejection_bridge_overview.png | Figure 4 预览图 | 支持恶化、部分识别与 bridge 预算路径的位图预览。 |
| results/figures/risk_coverage_curve.png | 风险--覆盖率图 | 展示证书阈值变化引起的发布率与已发布点条件 MAE frontier。 |
| results/figures/selective_uncertainty_overview.pdf | Figure 3 矢量图 | 汇总风险--发布率、校准、区间宽度和失效边界。 |
| results/figures/selective_uncertainty_overview.png | Figure 3 预览图 | 选择性预测与诚实不确定性的位图预览。 |
| results/figures/synthetic_composability_overview.pdf | Figure 2 矢量图 | 汇总几何直觉、误差 ECDF、二维敏感性和证书诊断。 |
| results/figures/synthetic_composability_overview.png | Figure 2 预览图 | 合成可组合性四面板论文图的位图预览。 |
| results/formal_experiment_metadata.json | 阶段 5 产物 | 保存正式多种子协议的场景、估计器、种子与参数配置。 |
| results/formal_experiment_seed_summary.csv | 阶段 5 产物 | 按基准种子汇总正式实验，支持跨种子变异检查。 |
| results/formal_experiment_summary.csv | 阶段 5 产物 | 正式实验的 42 行场景和估计器汇总；阶段 7、8 从中读取数值。 |
| results/main_experiment_metadata.json | 阶段 4 产物 | 保存主参数扫描的固定种子、扫参水平和方法配置。 |
| results/main_experiment_summary.csv | 阶段 4 产物 | 主扫描的 60 行长表，包含发布率、误差、区间和证书分解。 |
| results/bridge_experiment_metadata.json | 阶段 11 产物 | 保存 bridge 场景、候选库、预算、plug-in 正态模型、Gauss-Hermite 求积、不一致处理和信息边界。 |
| results/bridge_experiment_seed_summary.csv | 阶段 11 产物 | 按基准种子汇总三种策略的条件 VoI、预算完成率、不一致率和 oracle 支持距离。 |
| results/bridge_experiment_summary.csv | 阶段 11 产物 | 12 个场景-策略单元的部分识别直径、缩减、实际选择数、完成率和不一致诊断主表。 |
| results/minimax_experiment_metadata.json | 阶段 10 产物 | 保存二点子模型、定理常数、场景、种子和代表性估计器配置。 |
| results/minimax_experiment_seed_summary.csv | 阶段 10 产物 | 按基准种子汇总下界分量和最坏 MAE，用于检查 Monte Carlo 跨种子稳定性。 |
| results/minimax_experiment_summary.csv | 阶段 10 产物 | 8 个距离与噪声场景的构造下界、经验风险和解析风险主汇总表。 |
| results/nsw_archive_map_summary.csv | NSW archive map | 112 个 archive/target 对象的固定 PCA 坐标、角色与接受状态。 |
| results/nsw_diagnostics_summary.csv | NSW 逐目标诊断 | 1,680 条 ATLAS holdout 记录，用于 Figure 5 的重建与证书面板。 |
| results/nsw_experiment_metadata.json | 阶段 12 产物 | 保存原始数据校验值、local object 协议、表示分工、种子、方法和指标边界。 |
| results/nsw_experiment_seed_summary.csv | 阶段 12 产物 | 按基准种子汇总 NSW reconstruction 指标，用于检查对象拆分稳定性。 |
| results/nsw_experiment_summary.csv | 阶段 12 产物 | 五种方法的 MAE、median AE、sign、coverage、width 和 rejection 主表。 |
| results/partial_identification_metadata.json | 阶段 9 产物 | 保存部分识别场景、种子、总失败概率和权重族配置。 |
| results/partial_identification_seed_summary.csv | 阶段 9 产物 | 按基准种子汇总部分识别覆盖率、非空率、宽度和支持距离。 |
| results/partial_identification_summary.csv | 阶段 9 产物 | 4 个支持场景的正式汇总，是阶段 9 的主结果表。 |
| results/risk_coverage_metadata.json | 风险--覆盖率元数据 | 保存共享 target 抽样、阈值网格和固定种子。 |
| results/risk_coverage_summary.csv | 风险--覆盖率主表 | 9 行阈值结果，包含发布率、条件误差、区间指标和无拒绝端点。 |
| results/representation_sensitivity_metadata.json | 表示敏感性元数据 | 保存 5×5 网格、三个固定种子和每格 100 次重复的正式协议。 |
| results/representation_sensitivity_summary.csv | 表示敏感性主表 | 25 个网格单元的表示收益、选择收益和 ATLAS 发布率汇总。 |
| results/synthetic_benchmark_summary.csv | 合成方法基准 | 六种方法的统一合成评价表；Oracle 明确为 evaluation-only。 |
| results/tables/calibration_experiment_tables.md | 阶段 6 产物 | Markdown 形式的证书校准结果表。 |
| results/tables/bridge_experiment_tables.md | 阶段 11 产物 | Markdown 形式的 Definition 5.2 策略比较、部分识别直径、预算完成和不一致诊断表。 |
| results/tables/bridge_optimality_tables.md | Bridge 穷举表 | 小候选库 causal greedy 与事后 exhaustive optimum 的预算对照。 |
| results/tables/calibration_curve_tables.md | 校准曲线表 | 多置信水平下 coverage、width 和发布率的联合表。 |
| results/tables/final_summary_tables.md | 阶段 7 产物 | 紧凑的正式基准与失效边界摘要表，由 build_final_report.py 生成。 |
| results/tables/formal_experiment_tables.md | 阶段 5 产物 | Markdown 形式的正式多种子实验与消融表。 |
| results/tables/main_synthetic_table.md | 论文主表预览 | 六种合成方法的发布率、误差、符号、覆盖率与宽度。 |
| results/tables/main_synthetic_table.tex | 论文主表 LaTeX | 可由 Overleaf 直接输入的合成基准表，含 Oracle 评价限定。 |
| results/tables/minimax_experiment_tables.md | 阶段 10 产物 | Markdown 形式的 Theorem 5.5 下界分量与代表性估计器风险表。 |
| results/tables/nsw_experiment_tables.md | 阶段 12 产物 | Markdown 形式的 NSW local-contrast reconstruction 结果与评价边界。 |
| results/tables/paper_results_tables.tex | 阶段 8 产物 | 可输入论文的 LaTeX 基准和失效边界表，由 build_paper_artifacts.py 生成。 |
| results/tables/partial_identification_tables.md | 阶段 9 产物 | Markdown 形式的 Theorem 5.4 部分识别结果表。 |
| results/tables/representation_sensitivity_tables.md | 敏感性扩展表 | 展开 5×5 二维网格的表示收益、选择诊断与发布率。 |
| results/tables/risk_coverage_tables.md | 风险--覆盖率表 | 证书阈值、发布率与条件风险的完整 frontier 表。 |
| results/tables/support_failure_table.md | 失效边界表预览 | 支持恶化、拒绝与部分识别结果的论文表格预览。 |
| results/tables/support_failure_table.tex | 失效边界表 LaTeX | 可由 Overleaf 直接输入的支持失效摘要表。 |
| scripts/README.md | 脚本导航 | 按 run 与 build 两类说明执行顺序、运行成本和输入输出。 |
| scripts/build/build_final_report.py | 阶段 7 脚本 | 读取保存结果，生成最终报告、摘要表并刷新产物清单。 |
| scripts/build/build_paper_artifacts.py | 阶段 8 脚本 | 读取保存结果，生成论文写作稿、LaTeX 表格并刷新产物清单。 |
| scripts/build/build_paper_figures.py | 论文图构建脚本 | 只读取既有 CSV，生成 Figure 2--5、论文主表和扩展表，不重新运行仿真。 |
| scripts/run/run_algorithm1.py | 算法快速入口 | 运行一条拒绝、部分识别、两轮条件边际 bridge 的完整 Algorithm 1 路径并打印关键状态。 |
| scripts/run/run_bridge_budget_path_experiment.py | Bridge 路径脚本 | 在严重失配场景生成预算 0--4 的三策略绘图诊断，不替代 300 次正式 bridge 主表。 |
| scripts/run/run_bridge_experiment.py | 阶段 11 脚本 | 运行正式严格条件边际 VoI 路径，写入直径、完成率、不一致诊断、JSON、图和表。 |
| scripts/run/run_bridge_optimality_experiment.py | Bridge 穷举脚本 | 运行 12 候选预算 1--3 的事后 exhaustive benchmark，写入结果表和元数据。 |
| scripts/run/run_calibration_curve_experiment.py | 校准曲线脚本 | 运行多置信水平的 coverage--width 诊断，写入 CSV、JSON、图和表。 |
| scripts/run/run_calibration_experiment.py | 阶段 6 脚本 | 运行证书校准与失效边界实验，写入阶段 6 的 CSV、JSON、图和表。 |
| scripts/run/run_certificate_diagnostics.py | 证书诊断脚本 | 生成逐目标证书半径、真实误差、接受状态和证书分量，仅用于仿真评价。 |
| scripts/run/run_formal_experiment.py | 阶段 5 脚本 | 运行正式多种子协议，写入阶段 5 的 CSV、JSON、图和表。 |
| scripts/run/run_main_experiment.py | 阶段 4 脚本 | 运行四个受控参数扫描，写入阶段 4 的 CSV、JSON 和两张图。 |
| scripts/run/run_method_comparison.py | 阶段 3 脚本 | 运行固定设置下的方法比较并输出文字摘要。 |
| scripts/run/run_minimax_experiment.py | 阶段 10 脚本 | 运行 Theorem 5.5 多种子二点子模型，写入 CSV、JSON、图和 Markdown 表。 |
| scripts/run/run_monte_carlo.py | 阶段 2 脚本 | 运行独立重复和 oracle 评估的 Monte Carlo 管线。 |
| scripts/run/run_nsw_experiment.py | 阶段 12 脚本 | 运行固定 NSW 对象级 holdout 协议，写入主结果与逐目标诊断。 |
| scripts/run/run_partial_identification_experiment.py | 阶段 9 脚本 | 运行多种子部分识别实验，写入 CSV、JSON、图和 Markdown 表。 |
| scripts/run/run_representation_sensitivity.py | 表示敏感性脚本 | 扫描隐藏调节偏移与代理不确定性二维网格，比较表示收益和发布率。 |
| scripts/run/run_risk_coverage_experiment.py | 风险--覆盖率脚本 | 运行同一 target 抽样下的阈值 frontier，写入 CSV、JSON、图和表。 |
| scripts/run/run_sanity_check.py | 阶段 1 脚本 | 生成最小 DGP 并执行 Assumption 3.1--3.5 的快速校验。 |
| src/causal_atlas_sim/__init__.py | 包接口 | 集中导出 DGP、方法、实验、报告和论文产物的公开 API。 |
| src/causal_atlas_sim/algorithm1.py | 统一算法入口 | 严格调度 Algorithm 1 接受/拒绝分支，计算条件边际期望部分识别直径并自适应选择 bridge。 |
| src/causal_atlas_sim/calibration_experiment.py | 阶段 6 源码 | 定义证书校准场景、策略、汇总指标和图表生成。 |
| src/causal_atlas_sim/calibration_curve.py | 校准曲线源码 | 在多个名义置信水平下生成 honest/Wald/失配对照的 coverage--width 汇总。 |
| src/causal_atlas_sim/bridge_experiment.py | 阶段 11 源码 | 构造 bridge 候选库，调用统一 Algorithm 1 比较 causal/semantic/random 策略并汇总完成率和不一致率。 |
| src/causal_atlas_sim/certificate_diagnostics.py | 证书诊断源码 | 生成逐目标 Theorem 5.1 风格证书与实际误差数据，并汇总排序能力和超界诊断。 |
| src/causal_atlas_sim/comparison.py | 阶段 3 源码 | 定义共享重复下的方法比较协议及其汇总。 |
| src/causal_atlas_sim/dgp.py | 阶段 1 源码 | 定义最小机制空间、随机试验、共同设计/识别假设档案、式 (4.2) AIPW 样本方差及 Assumption 3.1--3.5 校验。 |
| src/causal_atlas_sim/evaluation_baselines.py | 评价基线源码 | 实现 ATLAS-no-rejection、semantic forced 与仅限合成评价的 latent Oracle。 |
| src/causal_atlas_sim/experiments.py | 阶段 4 源码 | 定义主参数扫描、固定重复、长表汇总和主实验图表。 |
| src/causal_atlas_sim/figure_style.py | 图形样式 | 集中定义论文图字体、颜色、线型、面板标记与导出设置。 |
| src/causal_atlas_sim/formal_experiment.py | 阶段 5 源码 | 定义预注册式多种子场景、消融估计器、Wilson 区间和正式汇总。 |
| src/causal_atlas_sim/methods.py | 方法源码 | 实现候选/兼容筛选、式 (4.3) 权重、Theorem 5.1 接受证书、Corollary 5.2 区间和基线。 |
| src/causal_atlas_sim/minimax_experiment.py | 阶段 10 源码 | 实现 Theorem 5.5 几何与统计二点子模型、下界常数、代表性估计器和多种子汇总。 |
| src/causal_atlas_sim/monte_carlo.py | 阶段 2 源码 | 实现独立种子重复、oracle 对照和 Monte Carlo 指标汇总。 |
| src/causal_atlas_sim/nsw_experiment.py | 阶段 12 源码 | 实现 NSW 数据校验、局部对比对象、blind reconstruction、证书与多种子汇总。 |
| src/causal_atlas_sim/paper_artifacts.py | 阶段 8 源码 | 从已保存结果渲染论文写作稿和 LaTeX 表，禁止重新抽样。 |
| src/causal_atlas_sim/paper_figures.py | 论文图源码 | 从既有 CSV 构建 Figure 2--5 和论文表格，不调用数据生成机制。 |
| src/causal_atlas_sim/partial_identification.py | 阶段 9 源码 | 实现仅在拒绝分支构造的 Theorem 5.4 权重区间交集、oracle 凸包评价和多种子协议。 |
| src/causal_atlas_sim/reporting.py | 阶段 7 源码 | 验证结果行数，渲染最终报告和摘要表，计算产物 SHA-256 清单。 |
| src/causal_atlas_sim/representation_sensitivity.py | 表示敏感性源码 | 扫描隐藏调节偏移与代理不确定性，分离表示收益与选择性诊断。 |
| src/causal_atlas_sim/risk_coverage.py | 风险--覆盖率源码 | 用共享 target 抽样按证书阈值汇总发布率、条件风险、区间覆盖和无拒绝端点。 |
| tests/test_calibration_experiment.py | 阶段 6 测试 | 检验校准场景、策略、行数和固定协议的确定性。 |
| tests/test_calibration_curve.py | 校准曲线测试 | 检验五个对照策略、置信水平网格和固定协议确定性。 |
| tests/test_certificate_diagnostics.py | 证书诊断测试 | 检验逐目标字段、固定种子、误差口径与评价真值隔离。 |
| tests/test_algorithm1.py | 算法测试 | 检验分支互斥、Corollary 5.2、兼容过滤、真值隔离、条件边际更新、复现性和空交集诊断。 |
| tests/test_bridge_experiment.py | 阶段 11 测试 | 检验候选库、统一 Algorithm 1 直径路径、预算完成汇总、固定协议确定性和产物清单。 |
| tests/test_bridge_optimality.py | Bridge 穷举测试 | 检验小库穷举的组合计数以及 greedy 不优于事后最优的基本性质。 |
| tests/test_comparison.py | 阶段 3 测试 | 检验共享随机重复、方法集合和比较结果的确定性。 |
| tests/test_dgp.py | 阶段 1 测试 | 检验最小 DGP、五条假设、随机化一致性和证书界。 |
| tests/test_experiments.py | 阶段 4 测试 | 检验主扫描行数、固定种子和语义失配的机制范围。 |
| tests/test_formal_experiment.py | 阶段 5 测试 | 检验多种子协议、消融集合、汇总行数和 Wilson 区间。 |
| tests/test_methods.py | 方法测试 | 检验权重优化、候选筛选、证书分解、拒绝消融和基线输出。 |
| tests/test_minimax_experiment.py | 阶段 10 测试 | 检验二点曲面的边界、信息量公式、固定协议确定性和 Stage 10 产物清单。 |
| tests/test_monte_carlo.py | 阶段 2 测试 | 检验 oracle 参考、重复种子、确定性和覆盖率。 |
| tests/test_nsw_experiment.py | 阶段 12 测试 | 检验原始数据哈希、局部对象有效性、target 防泄漏、确定性和正式产物。 |
| tests/test_paper_artifacts.py | 阶段 8 测试 | 检验论文写作稿、LaTeX 数值和清单中第 8 步产物的存在。 |
| tests/test_paper_figures.py | 论文图测试 | 检验 Figure 2--5 双格式、论文表、新结果行数及构图与仿真分离。 |
| tests/test_partial_identification.py | 阶段 9 测试 | 检验失败概率分配、区间交集、覆盖、凸包距离和协议确定性。 |
| tests/test_reporting.py | 阶段 7 测试 | 检验结果行数、最终报告、摘要表和清单哈希。 |
| tests/test_risk_coverage.py | 风险--覆盖率测试 | 检验无拒绝端点、单调发布率和固定协议确定性。 |
| tests/test_repository_file_map.py | 维护测试 | 检验本表覆盖全部受跟踪或待提交项目文件，防止未来更新遗漏对照说明。 |
| tests/test_representation_sensitivity.py | 表示敏感性测试 | 检验二维网格、共享随机协议、隐藏偏移边界与确定性。 |
