# 阶段6：证书校准与失效边界

本阶段不是 Algorithm 1 的附加步骤，而是对第 5--7 行的证书、拒绝规则与诚实
区间做失效边界压力测试。它检验拒绝行为和区间覆盖是否像证书所声明的那样工作。实验包含4个场景、
3个独立基础种子，并在每个种子下重复100次。因此，每个“场景-策略”汇总行包含
300个 target。不同策略始终使用完全相同的生成记录，保证比较公平。

## 场景设置

| 场景 | 改变内容 |
| --- | --- |
| 名义场景 | 使用原始数据生成机制和正确证书上界 |
| 隐藏半径异质 | archive 敏感性半径从0.20逐渐增加到0.60 |
| 强语义失配 | target 失配比例为0.60 |
| 严重语义失配 | target 失配比例为0.80 |

隐藏半径异质场景仍然覆盖每个代理变量兼容集合：target 半径保持0.20，archive 半径
从0.20增加到0.60，公开代理噪声仍被0.10限制。因此这是一项保守证书压力测试，
不是对论文假设的破坏。

## 比较策略

- `certified_atlas`（正确证书 ATLAS）：使用解析上界 `L=2.61`、`H=1.80`，并以
  科学容忍度1.65执行拒绝规则；
- `no_rejection`（不拒绝）：使用相同的学习权重和正确证书区间，但始终发布点预测；
- `understated_smoothness`（低报平滑界）：故意向方法提供错误的 `L=0.20` 和
  `H=0.05`。该策略只用于展示证书上界无效时会发生什么。

## 评价指标

除了发布率和平均绝对误差，本阶段还记录：

- `released_interval_coverage`：已发布点预测对应区间的经验覆盖率；
- `released_interval_uncovered_rate`：已发布区间未覆盖真值的比例；
- `released_above_tolerance_rate`：已发布点中证书半径超过科学容忍度的比例；
- `overall_interval_coverage`：执行接受或拒绝以前，全部有限区间的覆盖率。

这些指标必须区分。不拒绝方法的区间可能仍然覆盖真值，但它可能同时发布大量证书
已经明确判定为不够可靠的点预测。

## 当前结果

使用正确上界时，ATLAS 在名义场景的发布率为0.4267；隐藏半径异质时为0.0300；
强失配时为0.0433；严重失配时为0.0067。四个场景的总体证书区间覆盖率均为1.0000。

在强失配和严重失配下，不拒绝策略仍发布所有点，但其中分别有0.9567和0.9933的
已发布点证书半径超过科学容忍度。正确 ATLAS 避免发布了这些高风险点预测。

故意低报平滑界的策略也发布所有点，但其已发布区间覆盖率在强失配下跌至0.8333，
在严重失配下进一步跌至0.7233。这就是本实验要展示的失效边界：数据生成机制仍然
有效，但方法接收了错误的平滑常数，所以证书不再可靠。

## 文件产出

- `results/calibration_experiment_summary.csv`：12行合并结果表；
- `results/calibration_experiment_seed_summary.csv`：36行逐种子结果表；
- `results/calibration_experiment_metadata.json`：完整实验配置；
- `results/tables/calibration_experiment_tables.md`：报告用结果表；
- `results/figures/calibration_experiment_overview.png`：发布率与覆盖率比较图。

### coverage--width 校准曲线

`run_calibration_curve_experiment.py` 在名义置信水平 0.80、0.90、0.95、0.975 下，
对同一批 target 同时报告经验覆盖率与平均区间宽度。它比较正确证书、Wald-only、
semantic forced、低报平滑界和取消隐藏调节膨胀。正确证书覆盖率为 1.0000 但区间较宽，
Wald-only 覆盖率为 0.2000--0.3367，说明论文必须联合报告 coverage 与 width。

新增产物：`results/calibration_curve_summary.csv`、metadata JSON、Markdown 表和 PNG 图。

运行命令：

```powershell
python scripts/run_calibration_experiment.py
python scripts/run_calibration_curve_experiment.py
```
