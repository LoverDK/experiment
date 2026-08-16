# 原论文实验图表的当前协议复现

## 1. 核对结论

`../main_direction_Causal_ATLAS_7papers.pdf` 的实验部分包含两张四面板图和三张表：

| 原论文产物 | 原论文位置 | 当前仓库对应产物 |
| --- | --- | --- |
| Figure 2：synthetic validation | PDF 第 14 页 | `results/figures/legacy_layout_synthetic_validation.{png,pdf}` |
| Figure 3：NSW local-contrast validation | PDF 第 16 页 | `results/figures/legacy_layout_nsw_validation.{png,pdf}` |
| Table 1：synthetic reconstruction | PDF 第 14 页 | `results/tables/legacy_layout_table1_synthetic.{md,tex}` |
| Table 2：bridge-design ablation | PDF 第 15 页 | `results/tables/legacy_layout_table2_bridge.{md,tex}` |
| Table 3：NSW reconstruction | PDF 第 15 页 | `results/tables/legacy_layout_table3_nsw.{md,tex}` |

工作区的历史临时目录曾保留 `synthetic_atlas_validation` 和
`real_nsw_archive_validation` 两张旧图，但它们使用远古实验协议，不属于本 GitHub
仓库，也不能作为当前论文数值来源。

## 2. 两张兼容图如何复现旧版优点

### 合成实验图

兼容图保留原 Figure 2 的四条视觉主线：

1. 语义近邻可能具有不同隐藏调节量；
2. 六种方法的完整误差分布，而不只比较均值；
3. 三种 bridge 策略随预算增加的部分识别直径路径；
4. 隐藏调节偏移与代理不确定性的二维表示敏感性。

数值分别来自 `certificate_diagnostics_summary.csv`、
`bridge_budget_path_summary.csv` 和 `representation_sensitivity_summary.csv`。

### NSW 图

兼容图保留原 Figure 3 的四条视觉主线：

1. 112 个 local objects 的机制表示地图，并标出一组固定 holdout 的接受/拒绝；
2. 五种方法各 1,680 个共享 holdout 的绝对误差分布、中位数与四分位区间；
3. ATLAS 重建值与 noisy held-out local contrast 的校准散点；
4. 支持证书分量、区间宽度与重建误差之间的关系。

数值来自 `nsw_archive_map_summary.csv`、`nsw_method_error_records.csv` 和
`nsw_diagnostics_summary.csv`。B 面板的 violin 使用全部逐目标误差，叠加散点只是
固定的可视化抽样，不参与中位数或四分位数计算。

## 3. 与原论文旧数值的关系

这些文件复现的是**旧版图表布局和论证结构**，不是旧数值。所有点、曲线、表格均
从当前固定三种子协议的已提交 CSV/JSON 生成，因此与现在的 README、阶段文档和
Section 6 结果口径一致。旧论文的 Table 1--3 数值不得与这些新图表混用。

合成图中的 ATLAS 误差分布只使用实际发布目标；no-rejection 和其他强制发布方法
使用全部 target。NSW 的 ATLAS 与 no-rejection 使用相同点权重，所以它们的点误差
指标按构造相同，区别在拒绝和证书区间。

## 4. 生成命令

```powershell
python scripts/build/build_paper_figures.py
```

构建器只读取 `results/*.csv` 和 metadata JSON，不调用 DGP，也不重新运行仿真。
输出同时包含 300 DPI PNG、矢量 PDF、Markdown 表和可供 LaTeX/Overleaf 输入的 TeX 表。
