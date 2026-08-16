# 正文实验遗漏目录

## 1. 用途与范围

本目录比较两类材料：

1. GitHub 仓库提交 `aa1a918` 中已经完成的全部实验；
2. `../version1_work/main_experiments.fragment.tex` 中 Section 6 的修订正文（仓库同级目录）。

目标是找出“仓库已经做了、但正文没有写或只写了一部分”的内容，并判断它应当：

- **补入正文**：直接增强核心论证；
- **正文一句带过**：值得让读者知道，但不应展开；
- **保留附录**：主要用于审计、稳健性或复现；
- **不再引用**：已被正式多种子协议或新版共同目标实验取代。

本目录不直接修改论文，也不讨论附录排版。每个主题文件均给出仓库证据、遗漏判断、
建议插入位置和可直接改写的英文候选文本。

除遗漏外，核对还发现一处需要先修正的解释：正文把 ATLAS 与 no-rejection 的差异称为
“公平的表示比较”，但它们使用相同的表示和点权重，差别是拒绝规则；而且当前合成主表
分别报告已发布子集和全部 target 的 MAE。真正的表示比较应固定不拒绝，再比较完整表示
组合与 semantic forced。详见 [02](02_synthetic_sweeps_and_ablations.md)。

## 2. 证据层级

正文数字应按以下优先级核对：

1. `results/*.csv`：正式数值的唯一事实来源；
2. `results/*_metadata.json`：样本量、种子、场景、阈值和信息边界；
3. `results/figures/`、`results/tables/`：读者实际看到的图表；
4. `docs/stages/`、`docs/paper/`：实验目的和正确解释；
5. `src/`、`scripts/run/`：指标或协议仍不清楚时才回查实现。

早期演示脚本的终端输出不能覆盖正式 CSV。单种子筛查结果也不应替代多种子正式结果。

## 3. 全部遗漏项总表

| 仓库已完成内容 | 当前正文状态 | 建议 | 详细目录 |
| --- | --- | --- | --- |
| Assumption 3.1--3.5 自动校验 | 只写了 DGP，未写自动校验结果 | 正文一句或附录 | [01](01_foundational_checks.md) |
| 200 次 oracle-support Monte Carlo 管线校验 | 完全未写 | 已被正式校准实验取代，不补正文 | [01](01_foundational_checks.md) |
| 200 次早期五方法比较 | 完全未写 | 已被 300 共同目标基准取代，不补正文 | [01](01_foundational_checks.md) |
| 四个单因素筛查扫描 | 正文只覆盖阈值前沿和二维表示网格 | 正文引用正式多种子压力结果，筛查表留附录 | [02](02_synthetic_sweeps_and_ablations.md) |
| 正式多种子六场景压力实验 | 正文只使用名义主表和少量端点 | 建议补一段 | [02](02_synthetic_sweeps_and_ablations.md) |
| 去方差惩罚、Top-4 候选消融 | 正文未写 | 建议补一段 | [02](02_synthetic_sweeps_and_ablations.md) |
| 表示敏感性完整 5x5 数值 | 正文只有热图和一条切片 | 图已覆盖，完整数值留附录 | [02](02_synthetic_sweeps_and_ablations.md) |
| ATLAS/no-rejection 被误称为表示比较 | 正文解释不准确 | 落稿前必须修正 | [02](02_synthetic_sweeps_and_ablations.md) |
| 接受与拒绝目标的证书分量均值 | 正文只报相关系数 | 建议补一句或一段 | [03](03_certificate_diagnostics.md) |
| archive 隐藏半径异质性 | 正文未写 | 建议正文一句 | [03](03_certificate_diagnostics.md) |
| 完整校准策略和全部置信水平 | 正文只突出 honest 与 Wald | 保留附录 | [03](03_certificate_diagnostics.md) |
| 多权重交集相对单区间的宽度收缩 | 正文未写 | 可补一句 | [04](04_partial_identification_and_minimax.md) |
| oracle 凸包距离与非识别分离量 | 图中使用，正文未解释数值 | 正文一句，明确 evaluation-only | [04](04_partial_identification_and_minimax.md) |
| Theorem 5.5 minimax 数值实验 | 正文完全未写 | 建议补一段 | [04](04_partial_identification_and_minimax.md) |
| bridge 在 supported/moderate/strong 场景的正式结果 | 正文只写 severe | 建议补一段或一句 | [05](05_bridge_additional_evidence.md) |
| semantic bridge 规划不一致率 | 正文未写 | 建议补一句 | [05](05_bridge_additional_evidence.md) |
| bridge 对真实机制凸包距离的缩减 | 正文未写 | 可补一句，必须标 evaluation-only | [05](05_bridge_additional_evidence.md) |
| bridge 逐种子、候选族和测量误差诊断 | 正文未写 | 保留附录 | [05](05_bridge_additional_evidence.md) |
| NSW restricted/design-enriched 表示分工 | 正文未解释 | 建议补正文 | [06](06_nsw_additional_evidence.md) |
| NSW local object 完整构造参数 | 正文只有概述 | 正文一句，其余附录 | [06](06_nsw_additional_evidence.md) |
| NSW no-rejection 与 ATLAS 点指标相同的原因 | 表中可见，正文未解释 | 建议补一句 | [06](06_nsw_additional_evidence.md) |
| NSW 逐种子稳定性和数据哈希 | 正文未写 | 保留附录/复现材料 | [06](06_nsw_additional_evidence.md) |

## 4. 正文补充优先级

### P0：最值得补入正文

1. 先修正 ATLAS/no-rejection 的比较含义；
2. 正式多种子消融：去方差惩罚与 Top-4 候选；
3. Theorem 5.5 的 minimax 数值说明；
4. bridge 优势是否跨 support 场景成立，以及 semantic 规划不一致；
5. NSW 的 restricted 与 design-enriched 表示分工。

### P1：可用一句或短段增强解释

1. 接受/拒绝目标的证书分量差异；
2. 多权重部分识别交集带来的宽度收缩；
3. archive 隐藏半径异质性压力测试；
4. NSW no-rejection 点指标相同的原因。

### P2：不要挤入正文

1. 早期 200 次 Monte Carlo 和方法演示；
2. 单种子筛查的全部数值；
3. 每个基础种子的完整表；
4. 所有阈值、所有置信水平和所有候选组合；
5. SHA-256、完整命令和构建清单。

这些内容有审计价值，但正文继续展开会重复 Figure 2--5 已经表达的主结论。

## 5. 使用方式

写某个正文小节时，先打开本目录对应主题文件，只选择标记为“补入正文”的候选段落。
候选英文文本是论证骨架，不是最终措辞；落稿前仍应从列出的 CSV 重新核对数字，并与
正文上下文合并，避免把独立实验误写成同一批 target 的联合比较。
