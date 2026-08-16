# 03 证书分量、异质隐藏半径与完整校准

## 1. 接受目标和拒绝目标的证书分量差异

### 正文覆盖状态

Section 6.2 已报告证书半径与实际绝对误差的 Spearman 相关系数为 0.272，并说明没有观察到实际误差超过证书半径。但正文没有回答一个更直观的问题：**到底是哪一个证书分量把目标推过了拒绝阈值？**

仓库的 300 个共同目标诊断给出了下表。这里的“接受”和“拒绝”由固定科学容忍度 1.65 决定；数值是各组目标的分量均值。

| 目标状态 | 数量 | 表示项 | 曲率项 | 隐藏调节项 | 统计项 | 总半径 | 绝对误差 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 接受 | 139 | 0.0087 | 0.7589 | 0.6200 | 0.1184 | 1.5061 | 0.1109 |
| 拒绝 | 161 | 0.0065 | 1.1314 | 0.6200 | 0.1126 | 1.8705 | 0.1627 |

在当前 DGP 中，接受组和拒绝组的隐藏调节项几乎相同，统计项也非常接近。主要差异来自曲率项从 0.759 增至 1.131。因此，这里的拒绝主要是在识别**组合后仍然离 target 机制较远的几何支持不足**，而不是简单挑出标准误较大的 target。

这个结论只适用于当前固定 DGP。不能据此声称隐藏调节不确定性或统计不确定性在一般问题中不重要；它们在本组实验中接近固定，因而没有成为区分接受与拒绝的主要来源。

### 对应文件

| 文件 | 提供的证据 |
| --- | --- |
| `results/certificate_diagnostics_summary.csv` | 300 个 target 的证书分量、接受状态和各方法绝对误差 |
| `results/certificate_diagnostics_metadata.json` | 固定种子、阈值和证书配置 |
| `src/causal_atlas_sim/certificate_diagnostics.py` | 分量记录与诊断汇总实现 |
| `scripts/run/run_certificate_diagnostics.py` | 诊断复现入口 |
| `results/figures/synthetic_composability_overview.pdf` | 正文 Figure 2D 使用的证书诊断图 |

### 是否进入正文

建议在 Section 6.2 最后一段、Figure 2D 的相关系数解释之后补一至两句。它比再加入一张表更有价值，因为它直接解释“拒绝规则在当前 DGP 中看到了什么”。完整分组表留到附录。

### 候选正文

> Decomposing the certificate clarifies what drives abstention in the nominal design. Among the 139 released targets, the mean curvature component is 0.759, compared with 1.131 among the 161 rejected targets, whereas the hidden-moderator and statistical components are nearly unchanged across the two groups. Thus, in this DGP, rejection is driven primarily by geometric support rather than by sampling noise alone.

## 2. Archive 隐藏半径异质性压力测试

### 做了什么

正式校准实验没有只使用统一的隐藏调节半径。它还构造了一个异质场景：target 半径保持 0.20，而八个 archive 的隐藏半径从 0.20 逐步增加到 0.60。公开代理噪声仍满足既定界，因此这不是故意破坏假设，而是在有效证书范围内增加 archive 间的不确定性差异。

正确证书 ATLAS 在这一场景中只发布 9/300 个 target，即发布率 0.0300；全部有限区间和已发布区间的经验覆盖率都为 1.0000。不拒绝版本发布全部 target，MAE 为 0.1835，但其中 97% 的证书半径超过固定科学容忍度。

### 正文覆盖状态与判断

Section 6.3 已写强、严重语义失配以及低报平滑常数的负对照，但完全没有写异质隐藏半径。这是一个有独立意义的压力测试，因为它说明拒绝不只会响应语义失配，也会响应 archive 声明的隐藏不确定性。

建议在 Section 6.3 负对照段之前补一句，不需要增加新图表。

### 对应文件

| 文件 | 提供的证据 |
| --- | --- |
| `results/calibration_experiment_summary.csv` | 异质隐藏半径场景的三策略汇总 |
| `results/calibration_experiment_seed_summary.csv` | 三个基础种子的稳定性 |
| `results/calibration_experiment_metadata.json` | 八个 archive 半径和实验协议 |
| `docs/stages/calibration_experiment.md` | 场景为何仍满足证书假设的解释 |
| `src/causal_atlas_sim/calibration_experiment.py` | 场景生成和策略实现 |
| `scripts/run/run_calibration_experiment.py` | 正式运行入口 |

### 候选正文

> The decision rule also responds to heterogeneous moderator uncertainty. When the archive-specific hidden radii range from 0.20 to 0.60, certified ATLAS releases only 0.030 of the targets while retaining empirical interval coverage of 1.000; forcing publication yields MAE 0.184 and publishes 0.970 of targets whose certificate radius exceeds the scientific tolerance.

## 3. 仓库中的完整校准政策

### 正文已写与未写

Section 6.3 已经写入了最重要的两组结果：四个置信水平下 honest 与 Wald-only 的 coverage--width 对比，以及低报平滑界的负对照。因此，仓库中下面这些额外策略属于**已做但不宜继续挤入正文**的证据：

- `semantic_forced` 的全置信水平 coverage 与 width；
- 取消隐藏调节膨胀的 `no_hidden_moderator_inflation`；
- 低报平滑界在四个置信水平下的完整曲线；
- 每个场景、策略、种子的发布率 Wilson 区间与跨种子标准差；
- 风险--发布率曲线上因没有任何目标发布而出现的空条件 MAE 单元。

这些结果适合附录或可复现材料。正文继续罗列会稀释 Figure 3 的核心论证：coverage 必须和 width 联合解释，且证书只有在声明的上界有效时才可信。

### 对应文件

| 文件 | 提供的证据 |
| --- | --- |
| `results/calibration_curve_summary.csv` | 4 个置信水平 × 5 个策略的完整曲线 |
| `results/calibration_curve_metadata.json` | 置信水平、策略和固定 target 协议 |
| `results/risk_coverage_summary.csv` | 固定 target 下的完整阈值前沿 |
| `results/risk_coverage_metadata.json` | 阈值网格及无拒绝端点说明 |
| `results/tables/calibration_curve_tables.md` | 完整 Markdown 表 |
| `results/tables/risk_coverage_tables.md` | 完整风险--发布率表 |
| `src/causal_atlas_sim/calibration_curve.py` | 校准曲线实现 |
| `src/causal_atlas_sim/risk_coverage.py` | 风险--发布率实现 |
| `scripts/run/run_calibration_curve_experiment.py` | 完整 coverage--width 曲线运行入口 |
| `scripts/run/run_risk_coverage_experiment.py` | 固定 target 风险--发布率前沿运行入口 |

## 4. 本主题的正文取舍

建议正文只补两项：证书分量的一句解释，以及异质隐藏半径的一句压力结果。完整分量表、五策略校准曲线、逐种子误差和空单元规则后续统一进入附录。这样可以增加机制解释，而不重复 Figure 3 已经完成的校准论证。
