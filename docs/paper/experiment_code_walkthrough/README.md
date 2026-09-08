# 从 Python 代码读懂 Causal ATLAS 的全部实验

这套文档写给第一次接触 Python、但需要自己核查论文实验的读者。阅读对象是 `01_causal_atlas_bridge.tex` 所对应的代码与结果。讲解覆盖正文实验、当前附录 B 的五个板块，以及支撑它们的历史实验。理论和附录 A 没有在本次文档工作中修改。

这里的“完整”是指从入口、数据构造、拟合、重复抽样、评价、落盘到论文展示的调用链完整。公共代码在前面的专章细讲，后面的实验章明确链接回去；不会在每个实验里重复解释同一段 `import`。核心计算给出源码片段，按语句解释；绘图、文件写入和记录类也有对应说明。完整源码始终以链接指向的 `.py` 文件为准。

## 阅读顺序

| 顺序 | 文档 | 读完应能回答 |
| --- | --- | --- |
| 0 | [Python 与仓库基础](00_python_and_repository_basics.md) | 一条命令如何找到函数？数组、对象、字典分别是什么？ |
| 1 | [合成数据逐步生成](01_synthetic_data.md) | 一次模拟的 8 个源实验和 1 个目标如何生成？真值在哪里？ |
| 2 | [ATLAS 核心代码](02_atlas_core.md) | 权重怎么求？五项证书怎么算？为什么拒绝？ |
| 3 | [正文合成实验与原始诊断](03_main_synthetic_experiments.md) | 主结果、消融、风险曲线、校准和表示敏感性如何计算？ |
| 4 | [部分识别、minimax 与 bridge](04_partial_identification_and_bridge.md) | 拒绝后如何形成区间？如何选择下一项实验？ |
| 5 | [NSW 与真实协变量实验](05_nsw_real_and_semisynthetic.md) | 真实数据怎样变成 archive？真值和参考估计如何区分？ |
| 6 | [更强基线与选择审计](06_baselines_and_selection.md) | ridge、kernel、历史阈值、同发布率比较如何实现？ |
| 7 | [机制、nuisance、相关性与常数](07_robustness_and_failure_boundaries.md) | 附录 B.2 的每一项压力测试究竟改了什么？ |
| 8 | [真实数据稳定性与 bridge 扩展](08_real_data_and_bridge_stability.md) | NSW 切分、Hillstrom、bridge 积分敏感性如何运行？ |
| 9 | [CSV 到论文图表](09_results_figures_tables_paper.md) | 一条记录怎样变成图中的点和附录里的表格？ |
| 10 | [运行、调试与核验](10_running_and_debugging.md) | 怎样从单次实验开始？怎样不误覆盖正式结果？ |
| 11 | [逐文件源码导航](11_source_inventory.md) | 每个 runner、核心模块和构建脚本应接着读哪里？ |

## 从论文倒着找代码

| 论文位置 | 本导读的位置 | 主要源码 |
| --- | --- | --- |
| 正文合成基准、表示与误差 | 1、2、3 | `dgp.py`、`methods.py`、`certificate_diagnostics.py` |
| 正文选择性发布与区间校准 | 3、6 | `risk_coverage.py`、`calibration_curve.py`、`validation_v3.py` |
| 正文拒绝、部分识别、bridge | 4 | `partial_identification.py`、`algorithm1.py`、`bridge_experiment.py` |
| 正文 NSW | 5 | `nsw_experiment.py` |
| B.1 Experimental Protocols and Evaluation Quantities | 0、1、3、9、10 | 配置类、runner、汇总器 |
| B.2 Robustness and Failure Boundaries | 3、7 | `representation_sensitivity.py`、`validation_v3.py` |
| B.3 Comparator and Selection Audit | 6 | `extension_baselines.py`、`selection_intervals()`、bootstrap builder |
| B.4 Real-Data Construction and Stability | 5、8 | `extension_nsw.py`、`nsw_stability()`、`hillstrom()` |
| B.5 Scope and Stability of Bridge Evidence | 4、8 | `extension_bridge.py`、`bridge_stability()` |

各章源码链接从本目录退回四级到仓库根目录。文件内函数名称可在 GitHub 或编辑器中搜索。固定的代码位置可用 `rg -n '^def 函数名' 路径` 查询，避免代码移动后纸面行号失效。

## 读文档时的三个约定

1. 标成“源码”的片段来自现存实现；省略部分会明确说明。标成“教学例子”的片段仅帮助理解，不是论文结果。标成“等价展开”的片段把紧凑语法写成多行，不改变计算意思。
2. 数字结果以已提交 CSV 为依据。本次是在解释已有实现，没有为写教程重跑论文规模实验，也没有把教学样本当成正式结果。
3. 原始、v2、v3 是不同协议和抽样批次。即使两个表都叫 MAE，也须先核对目标集合、是否筛选、真值/参考值、重复单位和区间类型。

实验路径总表仍可在[原工作流汇总](../experiment_workflow_summary.md)查阅。它适合查命令和资产，本目录用于理解代码。建议第一次按 0 到 10 顺序阅读，以后从上面的论文映射表跳转。

实验结构总图见[实验地图](experiment_map.md)，它把每个实验小块、正文图表、附录表和结论作用放在同一张图中。
