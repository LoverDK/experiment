# 09：从一条 CSV 记录到正文图和附录表

本章讲展示代码，不重新生成实验。主要源码：[paper_figures.py](../../../src/causal_atlas_sim/paper_figures.py)、[figure_style.py](../../../src/causal_atlas_sim/figure_style.py)、[build_extension_artifacts.py](../../../scripts/build/build_extension_artifacts.py)、[build_validation_v3.py](../../../scripts/build/build_validation_v3.py)、[restructure_appendix_b.py](../../../scripts/build/restructure_appendix_b.py)。

## 1. 四类文件不能混读

records CSV：一行通常对应一个任务、方法或区间设置。summary CSV：对一组 records 计算均值、比例、SD/SE。图表文件：将数值格式化展示。论文 tex：决定选用哪些资产以及如何描述。

原始 `certificate_diagnostics_summary.csv` 是逐目标记录，这是命名例外。原始 formal/PI/minimax/bridge 的 records 保存在运行时内存，runner 通常只保存 pooled 和 seed summary。因此“核心函数创建 records”不代表磁盘一定有同名 records CSV。

本目录 [examples/trace_saved_results.py](examples/trace_saved_results.py) 可以从保存记录重新算正文基准的一行、强基线配对差、v3 选择、nuisance、相关性、真实数据和 bridge 核心数字；它只打印，不写回任何结果。

## 2. Pandas groupby 的真实意思

`for key,g in df.groupby(['surface','change','method'])` 把三个标签完全相同的记录分为一组。key 是三个标签，g 是该组小表。`len(g)` 是行数，不一定是独立重复数；`g.replicate.nunique()` 才数不同重复编号。

`g.error.mean()` 默认忽略 NaN；当所有值都 NaN，结果仍 NaN。无穷不是缺失，会使均值无穷。`pd.to_numeric(errors='coerce')` 把无法解析的字符串变成 NaN，因此应核对是否发生了意料外的缺失。

v3 `summarize` 先对每个指标求总体平均，再对 replicate 分组求均值。模拟场景 MCSE=这些 replicate 均值的 SD/根号重复数；real=True 的 NSW 则报告拆分 SD。

## 3. 发布条件均值的分母是随机的

`ratio_se(df,value,select)` 中 x 是指标，w 是 0/1 发布指示。

```python
ratio = (x*w).sum()/w.sum() if w.sum() else np.nan
influence = (x-ratio)*w
```

ratio 是总发布误差/总发布数。先按独立 replicate 把 influence 和 w 求和；再用 cluster influence 的 SD/根号 cluster 数，除以每 cluster 平均发布数，得到这个比值的近似标准误。

教学例子：第 1 次发布 1 个目标误差 1，第 2 次发布 3 个目标误差都为 0。总发布均值是 1/4=.25；两次“各自发布均值”的简单平均是 (1+0)/2=.5。两种算法给不同估计目标，不能随意替换。

v2 NSW 半合成条件发布指标采用同类 cluster ratio 计算。v3 排序选择的不确定性还要重新排序，见第 6 章，不应只套这个固定标记公式。

## 4. v2 强基线 builder 的核验先于画图

build_extension_artifacts 的 main 读取 synthetic、NSW real/semi、bridge checks/sets，检查正式行数 9600/16200/3072、两个人员池无交集，并把 v2 nominal 与原 certificate 记录按 seed 对齐核查。

这说明少量 repetitions 生成的 smoke 文件不满足正式 builder 输入。它会断言失败；不要删掉断言让不完整数据变成正式论文表。

随后 wide=group.pivot(index='seed',columns='method',values='absolute_error')，每行一个共同目标。按列平均是各方法全目标 MAE；`errors-wide.atlas_no_rejection` 先在同一行作差，再算均值和 SE。配对运算包含协方差，和两个独立均值 SE 相加不同。

真实 NSW bootstrap 先按 bootstrap 编号平均六目标的 signed gap，再取有效重复分位；半合成先按 replicate 平均六目标绝对误差，再算 MCSE。表注必须对应各自流程。

## 5. Matplotlib 基础语句逐个认识

`fig,axes=plt.subplots(2,2,figsize=(13.2,9.2))` 创建一个画布和四个坐标区；figsize 是英寸。`axes[0,1]` 指第一行第二列面板。`ax.plot(xs,ys)` 按对应位置连线；scatter 画点；bar 画柱；imshow 把矩阵数值映射颜色；step 画经验分布阶梯。

`color` 决定颜色，`marker` 决定点形状，`linewidth` 决定线粗，`alpha` 决定透明度，`zorder` 决定前后层。它们改变可读性，不应该改变底层实验值。

`annotate(label,(x,y),xytext=...,textcoords='offset points')` 将说明文字相对真实点偏移；偏移的是文字位置。`set_xlim/ylim` 设轴范围，读图仍应留意是否截掉范围之外的数据。

`twinx()` 创建共用 x、独立右 y 轴，用于同面板表示不同单位。颜色和轴标签应对应，不能从两条线的视觉高度直接比较量级。

## 6. Figure 2 的四个面板逐一追源

函数 `_build_synthetic_overview` 读 certificate_diagnostics_summary 与 representation_sensitivity_summary。

A：对目标与最近语义源的隐藏 h 差，除以前两维语义距离+.03，降序取 36 对作示意。圆是源、三角是目标、颜色是真实 h。这个面板是有意挑选突出语义/隐藏差别的示意，不是随机抽 36 对估计总体发生率。总体误差证据来自后面面板。

B：逐方法取误差，atlas 筛 accepted，其他取全部；排序 values；纵轴 `arange(1,n+1)/n`。例如五个误差排序后对应 .2/.4/.6/.8/1，这就是经验 CDF。它不拟合平滑概率模型。

C：从敏感性行取 hidden_shift_fraction 与 proxy_uncertainty 的去重排序值，建立二维 matrix；每格填 representation_advantage。红蓝色界限对称于 0，表示优势正负。

D：仅取 proxy_uncertainty=.10 的切片，按 hidden shift 排序；左轴表示优势，右轴 ATLAS 发布率。它是 C 网格的一个固定切片，不是额外生成的实验。

输出 `results/figures/figure2_synthetic_validation.pdf/png`，另复制兼容别名 synthetic_composability_overview。

## 7. Figure 3 的四个面板

`_build_selective_uncertainty` 读四类结果。

A：risk_coverage_summary 中非空 conditional_mae，按 acceptance_rate 排序，画发布率-条件误差；annotate 标有限阈值和 no rejection。

B：calibration_curve_summary 按 policy 分组、confidence_level 排序，以 mean_width 为 x、empirical_coverage 为 y，连接四个置信水平。标注置信水平的文字作错位，不改变点坐标。

C：certificate_diagnostics 按 atlas_accepted 分 released/rejected，对 representation、curvature、hidden、statistical 四分量分别求平均，用并排柱展示。bias 默认 0，未作为单独一组柱。

D：calibration_experiment 的 strong=.60 与 severe=.80，横轴 release_rate，纵轴 released_interval_coverage。颜色线型代表策略，点形代表场景。它的纵轴是发布条件覆盖，不能用 B 中全体 empirical coverage 代替。

先输出 selective_uncertainty_overview，再复制 figure3_selective_uncertainty 别名。旧图名带 v2 的文件是否使用，以当前 tex 的引用为准。

## 8. Figure 4 的四个面板与两个样本规模

A：partial_identification_summary 按 mean_oracle_hull_distance 排序，画拒绝目标 PI 宽度。x 是真实机制评价量，拟合时不知道它。

B：bridge_budget_path_summary 的 severe 三策略路径，通常由 focused runner 每策略 90 路径汇总；同时叠加 bridge_optimality_summary 的事后穷举点，后者来自另一个 30 次协议。

C：bridge_experiment_summary 四场景每策略 300 次的初始/最终真实 hull distance，y 轴用 log。真实机制只作事后评价。

D：optimality 的平均收益比，budget 1/2/3。一个图内来源不同，不能把 oracle 点与路径当成同 90 个目标逐次配对的结果。

## 9. Figure 5 的三面板

A：nsw_archive_map_summary 的 pc1、pc2，颜色是每个局部对象在重复留出时的发布频率。这是把高维表示压成二维作地图；方法本身仍在原表示空间拟合。PCA 数据由 `nsw_archive_map_rows` 用表示矩阵的 SVD 得到。

B：nsw_diagnostics_summary 横轴 heldout_local_contrast，纵轴 raw reconstructed_contrast，按 accepted 区分符号，虚线是 y=x。两轴比较的是参考重建，不是已知真实 ATE。

C：nsw_method_error_records 对所有 raw reconstruction error 画 ECDF。这里 ATLAS 不筛 released，标签也去掉 conditional on release，因此 ATLAS 与 no_rejection raw 误差可重合。不能套用 Figure 2B 的条件筛选口径。

## 10. 图片如何导出

figure_style 选择 Agg 后端，无需弹出桌面绘图窗口。apply_publication_style 设字体、轴线、去顶部/右边框、PDF 字体类型等。

`finalize_figure` 先创建父目录，再 `tight_layout(pad=1.2)`；分别保存 PNG/PDF，默认 dpi=300、bbox_inches='tight'；最后 close(fig) 释放内存。PDF 中向量线条可缩放，PNG 是栅格图。

builder 写 `results/figures`，并不会自动上传到 Overleaf。论文存档图目录是 `docs/paper/overleaf/experiments/causal_atlas_bridge/figures`；线上相对路径去掉前面的 docs/paper/overleaf。

## 11. 当前附录 B 的表如何生成

restructure_appendix_b 顶部声明 ROOT、PAPER、TABLES、TEMPLATE、EVIDENCE、BASE。read(name) 读取 v3 CSV 并将路径加入 used_sources；row(frame,**query) 按具名字段筛选，并断言恰好一行，防止误选/重复行悄悄入表。

num(value) 把 NaN 显示为 `--`、inf 显示为 LaTeX 无穷，其余保留三位小数。因此显示相同的 .100 不代表保存值完全相同。

table(...) 用 headers 决定列数和左右对齐，拼 caption、label、tabular、表头、正文、note，再写 `.tex`。表格单元格数字来自 dataframe；解释性表注是作者维护的文本，实验设计修改后也要同步检查。

## 12. 11 张新表的输入筛选逐项对照

| 生成表 | 数据输入与筛选 | 对应前章 |
| --- | --- | --- |
| app_b_surfaces | mechanism_summary，change=baseline，五曲面五方法 | 7 |
| app_b_nuisance | nuisance_effect_summary 的源效应误差；nuisance_summary 的完成数 | 7 |
| app_b_dependence | dependence_summary，surface=constant，三 rho、三规则 | 7 |
| app_b_constants | constant_summary，三场景五 factor | 7 |
| app_b_calibration | interval_summary，ATLAS、level=.95，原生/匹配历史/名义历史 | 6 |
| app_b_ablation | formal_experiment_summary 的名义消融 | 3 |
| app_b_selection | selection_rank_bootstrap，fraction=.5 | 6 |
| app_b_nsw_stability | nsw_stability_summary，ATLAS 的有效 replications 和六种设计 | 8 |
| app_b_hillstrom_error | hillstrom_summary 中固定区间口径的两结局全目标误差 | 8 |
| app_b_hillstrom_interval | hillstrom_summary 中 ATLAS native factor 敏感性 | 8 |
| app_b_bridge_retained | bridge_checks_8192，family=retained_certificates | 8 |

这 11 张生成表的内容被内嵌到 01，而不是都通过外部 input 读入。另有协议表内嵌，及三张外部表 app_paired_comparison、app_stronger_baselines、app_nsw_semisynthetic，总计当前附录 15 表。

## 13. 模板如何替换进论文，为什么不能随便重跑

main 从 Git 的 BASE=`cccf750` 读取基准源，使用 appendix_B_template 的占位符和生成表内容组成五板块附录。它找到 Experimental Details 起点与 bibliography 起点，用新 appendix 替换区间，另做指定的正文交叉引用替换。

保护检查比较理论区域、Discussion 到附录起点、附录 A 及参考文献；确认五个 subsection 且没有剩余 `@@` 占位符。最后写 PAPER 和 revision_evidence/appendix_B_restructure.json，记录输入 CSV、模板、生成表、保护区段和源稿哈希。

**这个脚本会修改本地论文**。浅克隆缺少 BASE 会失败；模板和已编辑正文不匹配也可能触发 assert。它不是一般性的无副作用检查命令。本次教学任务没有运行它，也没有改 Overleaf。

## 14. 历史兼容产物与真正入文资产

paper_figures 仍生成 legacy 图和旧编号 appendix 图，某些标题/注释保留旧 B.4、B.8 编号。当前五板块论文的引用来自现存 01，不由这些旧注释决定。

`build_paper_artifacts` 生成历史写作稿和汇总 LaTeX，`build_final_report` 生成中文阶段报告，它们不等于重建当前定稿。`integrate_requested_extensions.py` 是旧 v2 集成入口，不应再用于当前附录。

`audit_appendix_b_assets.py` 使用保存的线上 inventory 与编译日志作依赖审计，不会打开浏览器编译。`verify_overleaf_revision.py` 也应按其源稿/保存证据范围理解，不能把历史日志当成现在新编译的结果。

更新本地文件与更新线上是两个动作。用户手动上传后，必要的最终编译在 Overleaf 完成。纯粹阅读本教程和执行只读教学例子不需要重编译论文。
