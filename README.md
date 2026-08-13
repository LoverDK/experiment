# Causal ATLAS 仿真实验

本仓库实现重点论文 `Rejectable Causal Atlas` 的合成仿真、理论边界数值实验和
NSW 真实数据分析。当前 12 个阶段是项目开发与验证阶段，不是论文 Algorithm 1
的 12 个步骤。Algorithm 1 的唯一端到端代码入口是
`src/causal_atlas_sim/algorithm1.py::run_algorithm1`，逐行对照见
[`docs/algorithm1_alignment.md`](docs/algorithm1_alignment.md)。

仓库每个文件的职责和生成关系见
[`docs/repository_file_map.md`](docs/repository_file_map.md)。新增、删除、移动文件
或改变职责时，必须在同一提交中更新该表。

## Algorithm 1 主流程

1. 按式 (4.2) 对 archive 实验效应去偏，保存公开表示、设计与假设档案、AIPW
   效应估计、AIPW 分数样本方差和样本量。
2. 用语义和元数据检索候选，再删除设计或识别假设不兼容的实验。
3. 按式 (4.3) 学习非负且和为 1 的支持权重。
4. 按 Theorem 5.1 计算支持、曲率、隐藏调节、nuisance 和统计证书。
5. 若证书不超过科学容忍度，返回点预测和 Corollary 5.2 诚实区间。
6. 若证书超过容忍度，不发布点预测，改为构造 Theorem 5.4 部分识别区间。
7. 在当前已选 bridge 集合条件下，逐轮选择期望部分识别直径缩减最大的候选。
8. 返回部分识别区间、bridge 集合、每轮边际价值和直径路径。

接受和拒绝两个分支互斥：接受时不构造部分识别、不选择 bridge；拒绝时
`point_estimate=None`。空的部分识别交集按 Lemma 5.1 记录为证书不一致，绝不
当作直径为 0。

## 论文算法与项目阶段

| 项目阶段 | 对应论文或职责 | 肉眼可见产出 |
| --- | --- | --- |
| 1 最小 DGP | Assumption 3.1--3.5；Algorithm 1 第 1 行 | 8 个 archive、target、AIPW 估计和五条假设报告 |
| 2 Monte Carlo | 误差分解基础设施校验 | 200 次 oracle 重复的误差与覆盖率 JSON |
| 3 方法比较 | 式 (4.3)、Theorem 5.1、Corollary 5.2；第 2--7 行 | ATLAS/基线的接受率、误差、覆盖与证书分量 |
| 4 主扫描 | 第 2--7 行的单因素压力测试 | 60 行 CSV、两张扫描图和元数据 |
| 5 正式实验 | 多种子基准与消融 | 42 行合并表、126 行逐种子表和总览图 |
| 6 校准 | 证书与拒绝的失效边界 | 正确/不拒绝/低报平滑界的覆盖与发布率 |
| 7 最终报告 | 从已保存 CSV 生成报告与清单 | 中文报告、摘要表、SHA-256 manifest |
| 8 论文产物 | 从已保存 CSV 生成写作稿 | 中文结果段和 LaTeX 表 |
| 9 部分识别 | Definition 5.1、Theorem 5.4；第 8--9 行 | 拒绝率、部分识别覆盖与宽度 |
| 10 minimax 下界 | Theorem 5.5；解释为什么不能强制外推 | 8 个下界场景的解析与经验风险 |
| 11 bridge 设计 | Definition 5.2、Theorem 5.6；第 10--15 行 | 3,600 条策略路径、直径缩减和不一致诊断 |
| 12 NSW | Section 6.2 与 Appendix B 的真实数据扩展 | 8,400 条方法级评价记录和五方法主表 |

Algorithm 1 的核心实现跨阶段 1、3、9、11；其余阶段用于验证、压力测试、理论
下界、结果生成或真实数据扩展。

## 严格实现要点

### 式 (4.2) 的 archive 方差

每个实验的 `variance_proxy` 是 AIPW 分数的无偏样本方差：

\[
\widehat v_i=\frac1{n_i-1}\sum_\ell
(\phi_{i\ell}-\widehat\tau_i)^2,
\qquad s_i^2=\widehat v_i/n_i.
\]

它不再使用手工指定的总体方差包络。

### 接受后的区间

Theorem 5.1 的完整有限样本证书负责接受或拒绝；接受后报告 Corollary 5.2 区间：

\[
\widehat\theta_\alpha\pm
\left\{\widehat D(\alpha)+z_{1-\zeta/2}\widehat V_\alpha^{1/2}\right\}.
\]

### bridge 的条件边际 VoI

bridge 不是按单候选距离排序。每轮对所有剩余候选计算“当前 Theorem 5.4 直径
减去加入候选后期望直径”，选中并观测结果后更新 archive，再计算下一轮。未来结果
期望使用公开声明的 plug-in 正态规划模型和 3 点 Gauss-Hermite 求积。真实 target
效应、真实机制和候选真实效应不进入选择。

## 当前关键结果

- 200 次方法演示中，ATLAS 接受率为 0.5300，接受点 MAE 为 0.1177；不拒绝版本
  MAE 为 0.1373。
- 正式名义场景中，ATLAS 接受率为 0.4633，接受点 MAE 为 0.1109；隐藏半径
  0.40 时全部拒绝。
- 部分识别的 1,200 个 target 中，所有拒绝分支交集均非空并覆盖真值；严重失配
  拒绝率为 0.9900，拒绝点平均区间宽度为 7.0760。
- 严重失配的 bridge 实验中，causal greedy 把平均直径从 6.9423 降至 1.8772，
  缩减 72.96%；四个场景均完成全部预算。语义策略出现 0.67%--6.00% 的规划证书
  不一致，均被明确记录而非当作零直径。
- NSW 描述性 holdout 中，ATLAS MAE 为 0.8615 千美元、覆盖率 0.9744、拒绝率
  0.2321；该阶段不声称逐数值复刻论文 Table 3。
- risk--coverage 补实验在同一批 300 个 target 上显示：阈值 1.65 时发布率
  0.5000、条件 MAE 0.1163；阈值 2.00 时发布率 0.9433、条件 MAE 0.1327；
  acceptance=1 的 no-rejection 端点 MAE 为 0.1365。
- coverage--width 曲线显示，正确证书在 0.80--0.975 名义水平下经验覆盖率均为
  1.0000、平均宽度为 3.2835--3.3667；Wald-only 对照覆盖率为 0.2000--0.3367，
  因此 coverage 不能脱离 width 解释。
- 12 候选 bridge 穷举中，预算 1、2、3 的 causal greedy/事后最优 bridge value
  比例为 0.9957、0.9776、0.9857。它是小规模经验效率对照，不估计弱次模参数，
  也不证明 Theorem 5.6 的近似系数。

## 运行入口

快速检查 Algorithm 1 一条完整拒绝路径：

```powershell
python scripts/run_algorithm1.py
python -m unittest tests.test_algorithm1 -v
```

按阶段运行：

```powershell
python scripts/run_sanity_check.py
python scripts/run_monte_carlo.py
python scripts/run_method_comparison.py
python scripts/run_main_experiment.py
python scripts/run_formal_experiment.py
python scripts/run_calibration_experiment.py
python scripts/run_risk_coverage_experiment.py
python scripts/run_calibration_curve_experiment.py
python scripts/run_partial_identification_experiment.py
python scripts/run_minimax_experiment.py
python scripts/run_bridge_experiment.py
python scripts/run_bridge_optimality_experiment.py
python scripts/run_nsw_experiment.py
python scripts/build_final_report.py
python scripts/build_paper_artifacts.py
```

阶段 11 的 3,600 路径严格 VoI 协议计算较慢；日常检查流程优先使用
`scripts/run_algorithm1.py`。完整测试：

```powershell
python -m unittest discover -s tests -v
```

各阶段的数学构造、协议、结果与限制位于 `docs/`；固定结果、图表、表格与
SHA-256 清单位于 `results/`。

新增评价产物：`results/risk_coverage_summary.csv` 和其 frontier 图；
`results/calibration_curve_summary.csv` 和 coverage--width 图；
`results/bridge_optimality_summary.csv` 和小规模穷举对照表。
