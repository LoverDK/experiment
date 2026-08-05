# Causal ATLAS 仿真实验

本仓库用于逐步实现和记录重点论文 **Rejectable Causal Atlas** 的仿真实验。

## 当前进度

- [x] 创建 GitHub 仓库并连接本地目录
- [x] 建立仿真实验说明文档
- [x] 实现最小化数据生成机制（sanity check）
- [x] 加入统计噪声并重复 Monte Carlo 实验
- [ ] 实现目标方法和基线方法
- [ ] 完成主实验、消融实验和敏感性分析

## 仿真实验总流程

仿真用于在“真实答案已知”的受控环境中检验理论结论。整体流程为：

1. **明确理论命题**：确定本轮实验要验证的具体结论，例如语义相似是否足以保证因果效应可迁移，或拒绝机制是否能识别不可靠预测。
2. **定义实验机制**：为每个实验生成可观察语义特征、隐藏调节变量和设计特征，记为
   \[
   m_i=(s_{i1},s_{i2},h_i,q_i).
   \]
3. **定义真实效应**：通过预先指定的效应函数计算真实因果效应
   \[
   \tau_i=\mu(m_i).
   \]
4. **模拟观测误差**：加入与样本量相关的统计噪声，得到旧实验中可观察的估计值
   \[
   \hat\tau_i=\tau_i+\varepsilon_i.
   \]
5. **划分 archive 和 target**：方法只能使用旧实验信息预测目标实验；目标实验的真实效应只用于最后评价，避免信息泄漏。
6. **运行比较方法**：比较完整的 Causal ATLAS、语义基线、最近邻基线、全局均值、不带拒绝机制的版本，以及必要时的 oracle 参考方法。
7. **评价结果**：报告 MAE、RMSE、Bias、方向准确率、区间覆盖率、区间宽度和拒绝率等指标。
8. **重复和扩展**：通过 Monte Carlo 重复获得稳定结果，再进行消融实验和敏感性分析。
9. **理论解释**：每张表和每幅图都要对应一个理论命题，说明实验现象支持或不支持什么结论。

## 实验记录原则

- 每轮实验固定随机种子并保存参数；
- 主实验、消融实验和敏感性分析使用独立配置；
- 不把目标实验真实效应传给预测方法；
- 对可拒绝方法同时报告接受率、拒绝率和接受预测上的误差；
- 每完成一个阶段，更新本 README 和对应实验记录，并提交到 GitHub。

## 已实现：最小化数据生成机制

第一阶段的实现位于 [`src/causal_atlas_sim/dgp.py`](src/causal_atlas_sim/dgp.py)。它生成 archive experiments、一个 held-out target 以及每个实验的单位级记录、AIPW 效应估计和不确定性证书。

该实现将 target 机制构造为 archive 机制的凸组合，用于验证机制空间、真实效应、支持残差和误差证书的基础链路；构造权重只作为 oracle sanity check 元数据保存，后续方法不可访问。

生成器满足论文 Assumption 3.1--3.5 的方式如下：

| 假设 | 最小实现中的保证 |
| --- | --- |
| 3.1 可识别性 | 独立单位、已知 Bernoulli 随机化、\(\pi=0.5\)、一致性生成规则和真值 nuisance functions。 |
| 3.2 设计兼容性 | 所有实验使用同一个 `DesignProfile` 和共同的标准化 ATE 尺度。 |
| 3.3 局部平滑性 | \(\mathcal M=[-1,1]^4\)；使用论文的平滑非线性 \(\mu\)，并记录 \(L=2.61\)、\(H=1.80\) 的保守解析界。 |
| 3.4 不确定性证书 | 通过已知随机化的 AIPW score 生成 \(\hat\tau=\tau+\xi+0\)，并为每个实验记录 \(s_i^2=v_i/n_i\)。 |
| 3.5 隐藏调节变量证书 | 公开有界噪声的 \(h\) 代理，保留真实 \(h\) 仅作 oracle 评价，并按 \(R_{\mathrm{hid}}=L_h(\delta_*+\sum_j\alpha_j\delta_j)\) 生成证书。 |

更完整的数学构造、边界来源和运行方式见 [`docs/minimal_dgp.md`](docs/minimal_dgp.md)。自动校验位于 [`tests/test_dgp.py`](tests/test_dgp.py)，快速运行入口为 [`scripts/run_sanity_check.py`](scripts/run_sanity_check.py)。

## 已实现：Monte Carlo 重复运行框架

第二阶段位于 [`src/causal_atlas_sim/monte_carlo.py`](src/causal_atlas_sim/monte_carlo.py)。它使用独立子随机种子重复最小 DGP，并以真实支持权重组合构造一个 oracle 参考结果，检查误差、偏差、方向准确率和区间覆盖率。该 oracle 只用于验证重复运行和理论误差分解，不能当作完整 Causal ATLAS 方法的性能结果。

本阶段同时报告只含统计噪声的区间，以及加入 Assumption 3.3 曲率项和 Assumption 3.5 隐藏调节变量证书后的保守区间。详细说明见 [`docs/monte_carlo.md`](docs/monte_carlo.md)，运行入口为 [`scripts/run_monte_carlo.py`](scripts/run_monte_carlo.py)。

## 已实现：可拒绝 Causal ATLAS 与基线比较

第三阶段实现位于 src/causal_atlas_sim/methods.py 和
src/causal_atlas_sim/comparison.py，包含：

1. 语义候选检索和设计兼容性过滤；
2. 单纯形约束下的投影梯度权重优化；
3. 可分解的传输证书，以及基于科学容忍度的接受或拒绝；
4. 使用相同权重的 no-rejection 消融；
5. semantic_forced、nearest_semantic 和 global_mean 三种基线；
6. 使用相同独立子随机种子的公平 Monte Carlo 方法比较。

所有估计器只读取观测表示、设计档案、历史效应估计和不确定性
证书。目标真值、真实机制和 oracle 权重仅在评价层使用，不能泄漏给
方法。数学构造、信息边界、输出指标和当前 200 次重复的结果见
docs/method_comparison.md。

## 已实现：主实验参数扫描与结果归档

第四阶段由 src/causal_atlas_sim/experiments.py 和
scripts/run_main_experiment.py 实现。它按固定随机种子逐一扫描语义失配、
隐藏调节变量证书半径、每实验样本量和科学容忍度；每个水平都让所有
方法使用相同的 archive-target 重复数据。

当前默认运行使用 200 次重复，生成 60 行长表、配置元数据和两张 PNG
图，均已保存到 results/。详细的因素定义、结果解释和空单元含义见
docs/main_experiment.md。

本阶段结果是对仿真协议和拒绝机制的筛查，不是对真实数据性能的结论。

## 已实现：多随机种子正式实验与消融

第五阶段位于 src/causal_atlas_sim/formal_experiment.py 和
scripts/run_formal_experiment.py。正式协议包含 6 个场景、3 个独立基准
种子和每种子 100 次重复，并在同一目标数据上公平比较完整 ATLAS、
no-rejection、无方差正则、top-4 候选消融及三种基线。

本阶段保存了 42 行合并结果、126 行逐种子结果、配置元数据、三张
论文式 Markdown 表和一张总览图。完整设置、统计不确定性和结果解释见
docs/formal_experiment.md，所有产物位于 results/。

## 已实现：证书校准与失效边界

第六阶段由 src/causal_atlas_sim/calibration_experiment.py 和
scripts/run_calibration_experiment.py 实现。它在异质隐藏半径、强语义
失配和故意低报平滑界的条件下，对比正确拒绝、no-rejection 和错误
证书策略。

正确证书在所有 300 次合并重复中保持完整区间覆盖，同时在压力情景下
大幅降低点预测发布率；no-rejection 则会发布绝大多数证书已经超过
科学容忍度的预测。若把 L 和 H 错误低报，强失配下的发布区间覆盖率
会从 1.0000 降至 0.8767，严重失配下进一步降至 0.7533。

完整设置、指标定义和三张结果表见 docs/calibration_experiment.md，产物
已保存到 results/。

## 已实现：最终报告与可复现清单

第七阶段使用 src/causal_atlas_sim/reporting.py 和
scripts/build_final_report.py 自动读取三张结果 CSV，验证其行数和关键
唯一键，并生成最终中文实验报告、统一摘要表和 SHA-256 产物清单。

最终报告位于 docs/final_experiment_report.md，摘要表位于
results/tables/final_summary_tables.md，所有结果文件、图表和文档的
校验值位于 results/experiment_manifest.json。该生成步骤不会重新抽样，
因此报告中的每个数值可追溯到已保存的原始结果表。

至此，当前合成数据下的最小 DGP、方法比较、主扫描、正式多种子实验、
消融、证书校准和失效边界实验均已完成。后续工作应由导师审核结果后，
决定是否扩展到新的 DGP、异质设计档案或真实数据应用。

## 已实现：论文图表与写作包

第八阶段通过 src/causal_atlas_sim/paper_artifacts.py 和
scripts/build_paper_artifacts.py 从已保存的 CSV 生成中文论文结果写作稿、
可直接输入论文的 LaTeX 表格，并把新增产物写入 SHA-256 清单。该阶段不重跑
仿真，不改变任何结果数值。

写作稿位于 docs/paper_results_section.md，其中链接主扫描、正式多种子比较和
证书校准三张图；表格位于 results/tables/paper_results_tables.tex。运行
python scripts/build_paper_artifacts.py 可重新生成两者及产物清单。
