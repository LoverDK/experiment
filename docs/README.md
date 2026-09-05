# 文档导航

## `stages/`：按实验阶段学习

从 `minimal_dgp.md` 开始，依次阅读 Monte Carlo、方法比较、主扫描、正式实验、
校准、部分识别、minimax、bridge 和 NSW。每份文档说明该阶段做了什么、为什么做、
运行哪个脚本以及得到哪些肉眼可见的产物。

## `paper/`：面向论文写作

- `overleaf/`：已在 Overleaf 编译的 01 论文最终源稿、PDF 和全部引用图表。
- `overleaf_revision_20260906.md`：本次修改范围、在线版本来源、编译与核验记录。
- `revision_evidence/`：修改前在线源稿、最终编译日志和理论及数值一致性审计。
- `paper_experiment_extension.md`：Oracle、二维表示敏感性、证书诊断和 Figure 2--5
  的新增协议、信息边界与解释。
- `final_experiment_report.md`：全部合成阶段的中文总报告。
- `paper_results_section.md`：可继续改写成论文 Section 6 的结果稿。
- `main_text_gap_catalog/`：逐项对照仓库实验与当前 Section 6，列出正文遗漏、
  需修正的解释、对应证据文件、推荐插入位置和英文候选正文；当前只处理正文取舍。
- `original_experiment_artifacts.md`：把原论文 Figure 2--3、Table 1--3 映射到
  当前固定实验协议生成的兼容图表，并说明旧数值不得与新协议混用。

## `reference/`：维护与对照

- `algorithm1_alignment.md`：论文 Algorithm 1 与代码入口逐行对应。
- `repository_file_map.md`：所有受 Git 跟踪文件的职责、输入输出和维护关系。

仓库总体入口和完整命令在根目录 `README.md`；脚本分区见 `scripts/README.md`。
