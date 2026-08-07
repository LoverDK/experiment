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
| README.md | 项目入口 | 说明研究目标、各实验阶段、复现命令和主要产物位置；新增阶段时同步更新。 |
| data/nsw_dw.dta | 阶段 12 数据 | NBER 发布的 Dehejia-Wahba NSW 随机实验原始快照；运行前按固定 SHA-256 校验。 |
| docs/calibration_experiment.md | 阶段 6 文档 | 说明证书校准、异质隐藏半径和失效边界实验的设计、指标与结论。 |
| docs/bridge_experiment.md | 阶段 11 文档 | 说明 Definition 5.2 的 bridge value、三种候选选择策略、直径代理、结果和 Theorem 5.6 的限制。 |
| docs/final_experiment_report.md | 阶段 7 产物 | 汇总全部合成仿真实验的中文报告，由 scripts/build_final_report.py 生成。 |
| docs/formal_experiment.md | 阶段 5 文档 | 说明多种子正式基准、消融设置、统计不确定性与结果解释。 |
| docs/main_experiment.md | 阶段 4 文档 | 说明四个单因素参数扫描、图表和空单元含义。 |
| docs/method_comparison.md | 阶段 3 文档 | 记录 Causal ATLAS、拒绝消融和语义基线的方法比较。 |
| docs/minimax_experiment.md | 阶段 10 文档 | 说明 Theorem 5.5 的几何与高斯二点构造、固定协议、构造下界、经验风险和适用限制。 |
| docs/minimal_dgp.md | 阶段 1 文档 | 对应论文 Assumption 3.1--3.5，解释最小 DGP 的数学构造与证书。 |
| docs/monte_carlo.md | 阶段 2 文档 | 说明独立 Monte Carlo 重复、oracle 评估和区间覆盖检查。 |
| docs/nsw_experiment.md | 阶段 12 文档 | 说明 NSW 数据来源、local object 构造、blind holdout、五种方法、结果和真实数据限制。 |
| docs/paper_results_section.md | 阶段 8 产物 | 面向论文写作的中文结果段落，链接三张主图，由 scripts/build_paper_artifacts.py 生成。 |
| docs/partial_identification_experiment.md | 阶段 9 文档 | 说明 Theorem 5.4 权重区间交集、固定协议、覆盖率、宽度和非识别结论。 |
| docs/repository_file_map.md | 维护索引 | 本文件；任何项目文件或职责变更时同步更新。 |
| results/calibration_experiment_metadata.json | 阶段 6 产物 | 保存证书校准实验的固定配置、种子和场景元数据。 |
| results/calibration_experiment_seed_summary.csv | 阶段 6 产物 | 按基准种子汇总的证书校准结果，用于检查跨种子稳定性。 |
| results/calibration_experiment_summary.csv | 阶段 6 产物 | 证书校准与失效边界的主汇总表；阶段 7、8 从中读取数值。 |
| results/experiment_manifest.json | 可复现性产物 | 记录结果、图表和报告的 SHA-256 校验值，由两个 build 脚本刷新。 |
| results/figures/calibration_experiment_overview.png | 阶段 6 图 | 比较正确证书、无拒绝和低报界策略的发布率与覆盖率。 |
| results/figures/bridge_experiment_overview.png | 阶段 11 图 | 比较 causal greedy、semantic greedy 和 random bridge 的最终直径及预算路径。 |
| results/figures/formal_experiment_overview.png | 阶段 5 图 | 展示正式多种子基准中的发布率、消融与已发布点 MAE。 |
| results/figures/main_experiment_acceptance.png | 阶段 4 图 | 展示四项参数扫描下各方法的发布率。 |
| results/figures/main_experiment_mae.png | 阶段 4 图 | 展示四项参数扫描下各方法的已发布点 MAE。 |
| results/figures/minimax_experiment_overview.png | 阶段 10 图 | 并列展示 Theorem 5.5 两个构造下界分量及其与代表性估计器最坏风险的关系。 |
| results/figures/nsw_experiment_overview.png | 阶段 12 图 | 展示五种方法的 NSW holdout MAE、coverage 和 rejection diagnostics。 |
| results/figures/partial_identification_overview.png | 阶段 9 图 | 展示拒绝率、部分识别非空率、覆盖率和拒绝点区间宽度。 |
| results/formal_experiment_metadata.json | 阶段 5 产物 | 保存正式多种子协议的场景、估计器、种子与参数配置。 |
| results/formal_experiment_seed_summary.csv | 阶段 5 产物 | 按基准种子汇总正式实验，支持跨种子变异检查。 |
| results/formal_experiment_summary.csv | 阶段 5 产物 | 正式实验的 42 行场景和估计器汇总；阶段 7、8 从中读取数值。 |
| results/main_experiment_metadata.json | 阶段 4 产物 | 保存主参数扫描的固定种子、扫参水平和方法配置。 |
| results/main_experiment_summary.csv | 阶段 4 产物 | 主扫描的 60 行长表，包含发布率、误差、区间和证书分解。 |
| results/bridge_experiment_metadata.json | 阶段 11 产物 | 保存 bridge 场景、候选库、策略、预算、直径代理和信息边界。 |
| results/bridge_experiment_seed_summary.csv | 阶段 11 产物 | 按基准种子汇总三种 bridge 策略的直径缩减和 oracle 支持距离。 |
| results/bridge_experiment_summary.csv | 阶段 11 产物 | 12 个场景-策略单元的初始直径、最终直径、缩减比例和测量误差汇总。 |
| results/minimax_experiment_metadata.json | 阶段 10 产物 | 保存二点子模型、定理常数、场景、种子和代表性估计器配置。 |
| results/minimax_experiment_seed_summary.csv | 阶段 10 产物 | 按基准种子汇总下界分量和最坏 MAE，用于检查 Monte Carlo 跨种子稳定性。 |
| results/minimax_experiment_summary.csv | 阶段 10 产物 | 8 个距离与噪声场景的构造下界、经验风险和解析风险主汇总表。 |
| results/nsw_experiment_metadata.json | 阶段 12 产物 | 保存原始数据校验值、local object 协议、表示分工、种子、方法和指标边界。 |
| results/nsw_experiment_seed_summary.csv | 阶段 12 产物 | 按基准种子汇总 NSW reconstruction 指标，用于检查对象拆分稳定性。 |
| results/nsw_experiment_summary.csv | 阶段 12 产物 | 五种方法的 MAE、median AE、sign、coverage、width 和 rejection 主表。 |
| results/partial_identification_metadata.json | 阶段 9 产物 | 保存部分识别场景、种子、总失败概率和权重族配置。 |
| results/partial_identification_seed_summary.csv | 阶段 9 产物 | 按基准种子汇总部分识别覆盖率、非空率、宽度和支持距离。 |
| results/partial_identification_summary.csv | 阶段 9 产物 | 4 个支持场景的正式汇总，是阶段 9 的主结果表。 |
| results/tables/calibration_experiment_tables.md | 阶段 6 产物 | Markdown 形式的证书校准结果表。 |
| results/tables/bridge_experiment_tables.md | 阶段 11 产物 | Markdown 形式的 bridge value、策略比较、直径缩减和 oracle 评估表。 |
| results/tables/final_summary_tables.md | 阶段 7 产物 | 紧凑的正式基准与失效边界摘要表，由 build_final_report.py 生成。 |
| results/tables/formal_experiment_tables.md | 阶段 5 产物 | Markdown 形式的正式多种子实验与消融表。 |
| results/tables/minimax_experiment_tables.md | 阶段 10 产物 | Markdown 形式的 Theorem 5.5 下界分量与代表性估计器风险表。 |
| results/tables/nsw_experiment_tables.md | 阶段 12 产物 | Markdown 形式的 NSW local-contrast reconstruction 结果与评价边界。 |
| results/tables/paper_results_tables.tex | 阶段 8 产物 | 可输入论文的 LaTeX 基准和失效边界表，由 build_paper_artifacts.py 生成。 |
| results/tables/partial_identification_tables.md | 阶段 9 产物 | Markdown 形式的 Theorem 5.4 部分识别结果表。 |
| scripts/build_final_report.py | 阶段 7 脚本 | 读取三张结果 CSV，生成最终报告、摘要表并刷新产物清单。 |
| scripts/build_paper_artifacts.py | 阶段 8 脚本 | 读取三张结果 CSV，生成论文写作稿、LaTeX 表格并刷新产物清单。 |
| scripts/run_calibration_experiment.py | 阶段 6 脚本 | 运行证书校准与失效边界实验，写入阶段 6 的 CSV、JSON、图和表。 |
| scripts/run_bridge_experiment.py | 阶段 11 脚本 | 运行 Definition 5.2/Theorem 5.6 bridge 协议，写入 CSV、JSON、图和 Markdown 表。 |
| scripts/run_formal_experiment.py | 阶段 5 脚本 | 运行正式多种子协议，写入阶段 5 的 CSV、JSON、图和表。 |
| scripts/run_main_experiment.py | 阶段 4 脚本 | 运行四个受控参数扫描，写入阶段 4 的 CSV、JSON 和两张图。 |
| scripts/run_method_comparison.py | 阶段 3 脚本 | 运行固定设置下的方法比较并输出文字摘要。 |
| scripts/run_minimax_experiment.py | 阶段 10 脚本 | 运行 Theorem 5.5 多种子二点子模型，写入 CSV、JSON、图和 Markdown 表。 |
| scripts/run_monte_carlo.py | 阶段 2 脚本 | 运行独立重复和 oracle 评估的 Monte Carlo 管线。 |
| scripts/run_nsw_experiment.py | 阶段 12 脚本 | 运行固定 NSW 对象级 holdout 协议，写入 CSV、JSON、图和 Markdown 表。 |
| scripts/run_partial_identification_experiment.py | 阶段 9 脚本 | 运行多种子部分识别实验，写入 CSV、JSON、图和 Markdown 表。 |
| scripts/run_sanity_check.py | 阶段 1 脚本 | 生成最小 DGP 并执行 Assumption 3.1--3.5 的快速校验。 |
| src/causal_atlas_sim/__init__.py | 包接口 | 集中导出 DGP、方法、实验、报告和论文产物的公开 API。 |
| src/causal_atlas_sim/calibration_experiment.py | 阶段 6 源码 | 定义证书校准场景、策略、汇总指标和图表生成。 |
| src/causal_atlas_sim/bridge_experiment.py | 阶段 11 源码 | 定义 bridge 候选、VoI 直径代理、causal/semantic/random 策略和多种子汇总。 |
| src/causal_atlas_sim/comparison.py | 阶段 3 源码 | 定义共享重复下的方法比较协议及其汇总。 |
| src/causal_atlas_sim/dgp.py | 阶段 1 源码 | 定义最小机制空间、随机试验数据、真实效应、AIPW 证书及假设校验。 |
| src/causal_atlas_sim/experiments.py | 阶段 4 源码 | 定义主参数扫描、固定重复、长表汇总和主实验图表。 |
| src/causal_atlas_sim/formal_experiment.py | 阶段 5 源码 | 定义预注册式多种子场景、消融估计器、Wilson 区间和正式汇总。 |
| src/causal_atlas_sim/methods.py | 方法源码 | 实现 Causal ATLAS、拒绝规则、证书分解、权重优化和各基线方法。 |
| src/causal_atlas_sim/minimax_experiment.py | 阶段 10 源码 | 实现 Theorem 5.5 几何与统计二点子模型、下界常数、代表性估计器和多种子汇总。 |
| src/causal_atlas_sim/monte_carlo.py | 阶段 2 源码 | 实现独立种子重复、oracle 对照和 Monte Carlo 指标汇总。 |
| src/causal_atlas_sim/nsw_experiment.py | 阶段 12 源码 | 实现 NSW 数据校验、局部对比对象、blind reconstruction、证书与多种子汇总。 |
| src/causal_atlas_sim/paper_artifacts.py | 阶段 8 源码 | 从已保存结果渲染论文写作稿和 LaTeX 表，禁止重新抽样。 |
| src/causal_atlas_sim/partial_identification.py | 阶段 9 源码 | 实现 Theorem 5.4 权重区间交集、oracle 凸包评价和多种子协议。 |
| src/causal_atlas_sim/reporting.py | 阶段 7 源码 | 验证结果行数，渲染最终报告和摘要表，计算产物 SHA-256 清单。 |
| tests/test_calibration_experiment.py | 阶段 6 测试 | 检验校准场景、策略、行数和固定协议的确定性。 |
| tests/test_bridge_experiment.py | 阶段 11 测试 | 检验候选库、直径代理单调性、固定协议确定性和 Stage 11 产物清单。 |
| tests/test_comparison.py | 阶段 3 测试 | 检验共享随机重复、方法集合和比较结果的确定性。 |
| tests/test_dgp.py | 阶段 1 测试 | 检验最小 DGP、五条假设、随机化一致性和证书界。 |
| tests/test_experiments.py | 阶段 4 测试 | 检验主扫描行数、固定种子和语义失配的机制范围。 |
| tests/test_formal_experiment.py | 阶段 5 测试 | 检验多种子协议、消融集合、汇总行数和 Wilson 区间。 |
| tests/test_methods.py | 方法测试 | 检验权重优化、候选筛选、证书分解、拒绝消融和基线输出。 |
| tests/test_minimax_experiment.py | 阶段 10 测试 | 检验二点曲面的边界、信息量公式、固定协议确定性和 Stage 10 产物清单。 |
| tests/test_monte_carlo.py | 阶段 2 测试 | 检验 oracle 参考、重复种子、确定性和覆盖率。 |
| tests/test_nsw_experiment.py | 阶段 12 测试 | 检验原始数据哈希、局部对象有效性、target 防泄漏、确定性和正式产物。 |
| tests/test_paper_artifacts.py | 阶段 8 测试 | 检验论文写作稿、LaTeX 数值和清单中第 8 步产物的存在。 |
| tests/test_partial_identification.py | 阶段 9 测试 | 检验失败概率分配、区间交集、覆盖、凸包距离和协议确定性。 |
| tests/test_reporting.py | 阶段 7 测试 | 检验结果行数、最终报告、摘要表和清单哈希。 |
| tests/test_repository_file_map.py | 维护测试 | 检验本表覆盖全部受跟踪或待提交项目文件，防止未来更新遗漏对照说明。 |
