# 论文级实验扩展：表示、证书与最终图表

本扩展遵守一个硬边界：不修改 `algorithm1.py`、`methods.py` 中已经审查的可部署
估计逻辑。新增内容只位于合成评价、目标级诊断和论文展示层。

## 1. 二维表示敏感性

网格为隐藏调节偏移 `0, 0.2, 0.4, 0.6, 0.8` 与代理不确定性
`0.05, 0.10, 0.20, 0.30, 0.40`。每个单元格使用 3 个固定基础种子，每个种子
100 次重复，共 7,500 个目标。

ATLAS 使用四维公开表示；semantic forced 只使用 `(s1, s2)`，两者共享相同目标。
主要量为：

\[
\Delta_{rep}=MAE_{semantic}-MAE_{ATLAS,no\ rejection}.
\]

它隔离表示本身的经验增益。另报
`ATLAS no-rejection MAE - ATLAS accepted MAE`，但只把它称为选择性风险诊断，
不声称两项构成严格可加的因果分解。

当代理不确定性固定为 0.10 时，隐藏偏移从 0 增至 0.8，`Delta_rep` 从 0.1232
增至 0.6035；发布率从 0.8867 降至 0.2600。表示可帮助预测并不等于该目标拥有
足够证书支持可以发布。

## 2. evaluation-only oracle

`fit_oracle_latent_support` 只在合成评价中把公开表示 `r(e)` 替换为真实机制
`m(e)`。archive 效应估计、标准误、设计过滤、单纯形约束、方差惩罚和证书协议
保持一致，并强制在共同目标集上评价。

这个 oracle 不得用于可部署候选检索、权重、接受/拒绝或 bridge 选择。它在
`synthetic_benchmark_summary.csv` 中明确标记为 evaluation-only；300 个目标上的
MAE 为 0.1350，只应解释为当前 DGP 下潜在机制完全可见时的评价参考。

## 3. 证书与实际误差

`certificate_diagnostics_summary.csv` 对 300 个共同目标保存：证书总半径、表示项、
曲率项、隐藏调节项、偏差项、统计项、发布状态、实际绝对误差和六方法误差。

证书半径与实际绝对误差的 Spearman 相关为 0.2716；经验上没有目标的实际误差
超过证书半径。由于图中逐目标误差事件与定理概率事件的完全等价没有另行证明，
该比例称为 `error exceeds certificate rate`，不称“定理违反率”。

## 4. 最终论文图表

- Figure 2：语义几何、六方法误差 ECDF、表示优势热图、隐藏偏移压力测试；证书与实际
  误差散点移至 Appendix B.4。
- Figure 3：risk--coverage、coverage--width、证书分量和失配边界。
- Figure 4：拒绝点 PI 直径、bridge 预算路径、evaluation-only 真机制凸包距离和
  greedy/ex-post exhaustive value ratio；主图不显示 exact-set match rate，避免把集合命中率
  误读为性能准确率。
- Figure 5：NSW PCA archive map、全量 raw reconstruction 和全量绝对误差 ECDF；证书与
  实际误差散点移至 Appendix B.8。Table 3 同时报告 all-target MAE 与从 target-level records 汇总的
  released-only MAE。
- Table 1：六方法合成主表，含 evaluation-only oracle 脚注。
- Table 2：支持恶化、拒绝与部分识别汇总。

运行顺序：

```powershell
python scripts/run/run_representation_sensitivity.py
python scripts/run/run_certificate_diagnostics.py
python scripts/run/run_bridge_budget_path_experiment.py
python scripts/run/run_nsw_experiment.py
python scripts/build/build_paper_figures.py
```

最后一个构建器只读取既有 CSV/JSON。以后修改字体、panel 布局或图注时，不必重新
运行 Monte Carlo；旧图仍在 `results/figures/legacy_layout_*` 中保留。
