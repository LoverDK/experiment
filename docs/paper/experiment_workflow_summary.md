# Causal ATLAS 子论文实验汇总与复现流程

本文对应 `01_causal_atlas_bridge.tex`，以提交 `88f8a41` 中的五板块附录 B 为组织基准。整理日期：2026-09-07。本次工作只汇总实验与文件关系，没有重新生成实验结果，也没有改动论文或理论。

所有路径均相对于仓库根目录。下列命令在仓库根目录执行。正文图表和附录采用同一组实验时，只运行一次，通过下面的对应表定位其用途。

## 1. 阅读入口与版本范围

| 材料 | 完整仓库路径 | 用途 |
| --- | --- | --- |
| 当前论文源稿 | [docs/paper/overleaf/01_causal_atlas_bridge.tex](overleaf/01_causal_atlas_bridge.tex) | 判断实验是否入文、采用何种表述；不要用旧 PDF 推断当前附录内容 |
| 当前附录模板 | [docs/paper/appendix_B_template.tex](appendix_B_template.tex) | 五板块文字、实验解释和表格插入位置 |
| v2 执行协议 | [docs/paper/extension_protocol_v2.md](extension_protocol_v2.md) | 强基线、NSW 独立参考与半合成、冻结规划分布 bridge |
| v2 结果解释 | [docs/paper/extension_results_v2.md](extension_results_v2.md) | v2 完整结果与复现说明 |
| v3 执行协议 | [docs/paper/validation_v3_protocol.md](validation_v3_protocol.md) | 九类补充问题、预设样本量与评价规则 |
| v3 执行差异 | [docs/paper/validation_v3_deviations.md](validation_v3_deviations.md) | 必须与协议一起读，尤其 propensity 的实际 DGP 与失败记录处理 |
| v3 完整数值 | [docs/paper/validation_v3_tables.md](validation_v3_tables.md) | 各汇总表的完整 CSV 阅读版 |
| v3 结果说明 | [docs/paper/validation_v3_results_and_inclusion.md](validation_v3_results_and_inclusion.md) | 结果与局限；其中入文建议是重构前记录，当前位置以本文为准 |
| 当前图表依赖清单 | [docs/paper/revision_evidence/appendix_B_asset_audit.json](revision_evidence/appendix_B_asset_audit.json) | 当前 01 的引用文件，以及整理时观测到的 Overleaf 未引用文件 |

原始 `docs/stages/`、旧 README 和早期结果稿中的附录编号属于历史版本。当前附录为 B.1 协议、B.2 稳健性与失效边界、B.3 比较与选择审查、B.4 真实数据构造与稳定性、B.5 bridge 证据范围。`docs/paper/overleaf/01_causal_atlas_bridge.pdf` 是较早留档；本轮五板块版本的 54 页编译证据在 `docs/paper/revision_evidence/appendix_B_overleaf_compile_dom.txt`。

## 2. 公共环境、数据和评价规则

### 2.1 软件与运行方式

运行脚本自行把 `src/` 加入 Python 搜索路径，无需安装本仓库为 Python 包。代码使用 NumPy、Pandas 和 Matplotlib；建议 Python 3.10 及以上。已有运行的具体 Python/NumPy/Pandas 版本见各 `*_metadata.json`。仓库目前没有统一锁定的依赖文件，下面是安装入口，不构成跨版本逐字节复现承诺。

```powershell
python -m pip install numpy pandas matplotlib
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
```

`scripts/run/` 重新产生实验数据，默认写入固定结果目录；重复运行会覆盖相应产物。复现时应保留已提交基线，在新分支或工作副本中运行，并提交配置、失败记录和结果差异。`scripts/build/` 使用已保存记录；其中 `build_validation_v3.py` 还会对这些记录进行固定种子的 bootstrap，但不会重新生成 DGP 样本。

### 2.2 数据入口

| 数据 | 文件与校验位置 | 使用方式 |
| --- | --- | --- |
| 合成档案 | `src/causal_atlas_sim/dgp.py` 中 `SimulationConfig`、`generate_minimal_archive` | 通常为 8 个源实验、每实验 400 个单位；场景覆盖这些默认值时，以下分项另行说明 |
| NSW 随机样本 | `data/nsw_dw.dta`；校验常量在 `src/causal_atlas_sim/nsw_experiment.py` | 445 人，185 treated、260 control；1978 收入除以 1000，误差与宽度单位为千美元 |
| Hillstrom 随机试验 | `data/external/hillstrom.csv`；来源与 SHA-256 在 `data/external/hillstrom_provenance.json` | 原始 64,000 人，选 Men's Email/No Email 的 42,613 人；效应单位为百分点 |

数据已在仓库留档。Hillstrom runner 读取并校验本地 CSV，不负责重新下载数据；原始研究链接、镜像 URL、压缩文件 MD5 和 CSV SHA-256 均在 provenance 文件中。

### 2.3 公共计算流程

1. 生成源实验或构造真实数据对象，记录设计、公开表示、效应估计和标准误。
2. 只使用源信息检索、兼容性过滤、调参、选择支持权重。合成真值与真实目标参考效应只在评价阶段使用。
3. 计算点预测、证书半径、释放状态；必要时计算部分识别区间及 bridge 策略。
4. 保存逐目标或逐重复记录，再按预设场景汇总。早期 runner 中部分模块只保存汇总，不能把其 `summary.csv` 当作逐目标原始数据。
5. 从已保存结果构建论文图表。对没有释放目标的单元格保留缺失值；对失败档案、空交集和无限区间分别标记。

统一解释规则：合成数据和已知效应的半合成数据可报告真值覆盖率；NSW/Hillstrom 报告带噪声参考纳入率。全目标 MAE、释放条件 MAE和相同释放比例下的策略风险是不同指标。共享单位或重叠邻域不能作为独立重复；NSW 多次划分衡量设计敏感性。经验覆盖率不自动构成有限样本证书。

v3 随机种子由 `src/causal_atlas_sim/validation_v3.py::seed` 统一生成：`SeedSequence([20260906, 300 + block, scenario, rep])`。分项参数和种子同时保存在该模块与逐条结果中；运行命令、源文件哈希和软件版本在 `results/validation_v3/<block>_metadata.json`。

## 3. B.1 实验协议与评价量

本板块集中定义 DGP、表示、拟合、评价口径及复现规则，不重复陈列后面各板块的性能结果。

### 3.1 基础 DGP、oracle Monte Carlo 与方法演示

| 实验 | 入口与核心实现 | 固定流程及产物 |
| --- | --- | --- |
| DGP 检查 | `scripts/run/run_sanity_check.py`；`src/causal_atlas_sim/dgp.py` | 种子 20260805，生成档案、目标与声明条件诊断；JSON 打印到终端，没有固定结果 CSV |
| oracle Monte Carlo | `scripts/run/run_monte_carlo.py`；`src/causal_atlas_sim/monte_carlo.py` | 种子 20260805，200 次；检查估计误差与覆盖；JSON 打印到终端 |
| 三类方法演示 | `scripts/run/run_method_comparison.py`；`src/causal_atlas_sim/comparison.py`、`src/causal_atlas_sim/methods.py` | 种子 20260805，200 次；比较 ATLAS、拒绝消融及语义方法；JSON 打印到终端 |
| 完整算法路径 | `scripts/run/run_algorithm1.py`；`src/causal_atlas_sim/algorithm1.py::run_algorithm1` | 一次完整接受或拒绝后的 PI/bridge 执行演示；不替代正式策略实验 |

```powershell
python scripts/run/run_sanity_check.py
python scripts/run/run_monte_carlo.py
python scripts/run/run_method_comparison.py
python scripts/run/run_algorithm1.py
```

DGP 中机制为 `(s1,s2,h,q)`，公开表示包括有误差的隐藏调节变量代理。源效应经 AIPW 估计；分数样本方差除以样本量形成运行中的方差估计。声明条件检查可以核对已知模拟构造，但不能据此证明估计方差是有限样本 sub-Gaussian 上界。详细构造见 `docs/stages/minimal_dgp.md`；算法对照见 `docs/reference/algorithm1_alignment.md`，其旧定理编号需对照当前源稿标签理解。

## 4. B.2 稳健性与失效边界

### 4.1 原始单因素扫描与表示敏感性

入口：`scripts/run/run_main_experiment.py` 和 `scripts/run/run_representation_sensitivity.py`。核心实现分别为 `src/causal_atlas_sim/experiments.py`、`src/causal_atlas_sim/representation_sensitivity.py`。

流程：主扫描以种子 20260806 为基础，每设置 200 次，四因素分别为 semantic shift（0/.10/.25）、隐藏半径（.20/.40/.60）、源样本量（100/400/1000）和科学容忍度（1.25/1.65/2.05）；表示实验在 5×5 隐藏偏移/代理不确定性网格上，每格使用种子 20260901、20260902、20260903 各 100 次。共享场景中比较 full representation 与 semantic composition，并把表示增益和释放带来的选择效应分别计算。

输出：`results/main_experiment_summary.csv`、`results/main_experiment_metadata.json`；`results/representation_sensitivity_summary.csv`、`results/representation_sensitivity_metadata.json`。主扫描 60 行，表示网格 25 个单元格。前者的详细协议见 `docs/stages/main_experiment.md`。

论文用途：Figure 2 的表示敏感性及偏移诊断；B.1/B.2 提供构造和解释。完整扫描留在仓库，不再逐张放入附录。

### 4.2 原始证书校准、覆盖与宽度

入口：`scripts/run/run_calibration_experiment.py`、`scripts/run/run_calibration_curve_experiment.py`。实现：`src/causal_atlas_sim/calibration_experiment.py`、`src/causal_atlas_sim/calibration_curve.py`。

流程：前者用种子 20260831、20260901、20260902，各 100 次，考察正确界、低报平滑界、拒绝及相关消融；后者用 20260841、20260842、20260843，各 100 次，对相同目标改变名义区间水平，并与 Wald-only 等规则比较。覆盖、宽度和释放比例共同汇总。

输出：`results/calibration_experiment_summary.csv`、`results/calibration_experiment_seed_summary.csv`、`results/calibration_experiment_metadata.json`；`results/calibration_curve_summary.csv`、`results/calibration_curve_metadata.json`。

结果定位：正确界的区间较保守，Wald-only 在该构造中明显欠覆盖。数据进入 Figure 3；详细单元格保留在结果 CSV。不要将本组与 v3 不同种子的历史校准实验直接拼成同一统计比较。

### 4.3 多效应曲面与假设外压力测试

命令：`python scripts/run/run_validation_v3.py mechanisms`。实现：`src/causal_atlas_sim/validation_v3.py::mechanism_benchmark`、`transform`、`surface_value`；种子 block=4。

流程：原始、仿射、振荡、阈值、Friedman #2 五种曲面，每种交叉九种设置，各 100 个档案。设置包括基准、严重偏移、n=100、源档案大小 4/24、噪声标准差 3、t3 汇总误差、遗漏 h/q 表示信息和较大代理误差。相同档案比较五种方法，保存全目标误差、区间与释放信息。

输出：`results/validation_v3/mechanism_records.csv`（22,500 条方法记录）、`results/validation_v3/mechanism_summary.csv`、`results/validation_v3/mechanisms_metadata.json`。

论文：B.2，生成表 `app_b_surfaces.tex`，label `tab:b-surfaces`。基准振荡曲面下 ATLAS 覆盖率 0.90；阈值违反光滑性前提。Friedman #2 被转用为效应曲面；t3 改动发生于汇总误差层。原始 release 分数尺度不同，公平等释放率比较见 B.3。

### 4.4 拟合 nuisance、交叉拟合与弱重叠

命令：`python scripts/run/run_validation_v3.py nuisance`。实现：`src/causal_atlas_sim/validation_v3.py::nuisance_experiment`、`fitted_aipw`；种子 block=3。

流程：n=100/400，各档案八个源实验，每设置 200 个档案；单位协变量在 [-1,1] 均匀分布，响应含线性/二次项。平衡与弱重叠场景使用已知 propensity .5/.1，比较 oracle、二次拟合和线性拟合；logistic 场景真值为 expit(2x)，比较 oracle、拟合 logistic 和错误截距模型。采用两折交叉拟合，训练折样本不足的完整档案记为失败。

先记录单实验效应 bias/RMSE/SE/普通区间覆盖，再用完整有效档案做目标组合，记录覆盖、宽度与释放。已执行 propensity 与最初协议文字不同，详见 `docs/paper/validation_v3_deviations.md`。

输出：`results/validation_v3/nuisance_records.csv`、`nuisance_summary.csv`、`nuisance_effect_records.csv`、`nuisance_effect_summary.csv`、`nuisance_failures.csv`、`nuisance_failed_partial_effects.csv`、`nuisance_metadata.json`，均位于 `results/validation_v3/`。

论文：B.2 的 `app_b_nuisance.tex`，label `tab:b-nuisance`。n=100、p=.1 时，线性和二次拟合分别失败 170/200、198/200；失败不能从分母中悄然移除。未知 propensity 的零 nuisance 偏差界是未认证的 plug-in 设置。

### 4.5 档案相关性与协方差处理

命令：`python scripts/run/run_validation_v3.py dependence`。实现：`src/causal_atlas_sim/validation_v3.py::dependence_experiment`；种子 block=5。

流程：常数和原始曲面，相关系数 0/.3/.7，每格 300 个档案。加入边际 SE=.6 的等相关高斯汇总误差；固定同一组预测权重，分别采用对角方差、真实协方差以及 40 个独立校准噪声向量估计的协方差。同时评价统计项和完整区间，避免几何项掩盖噪声失准。

输出：`results/validation_v3/dependence_records.csv`、`results/validation_v3/dependence_summary.csv`、`results/validation_v3/dependence_metadata.json`。

论文：B.2 的 `app_b_dependence.tex`，label `tab:b-dependence`。常数曲面 rho=.7 时三种处理覆盖率为 .6067/.9600/.9500。真实矩阵为 oracle 对照，估计矩阵结果为经验诊断。

### 4.6 科学常数与历史校准迁移

入口一：`python scripts/run/run_validation_v3.py constants`；实现 `src/causal_atlas_sim/validation_v3.py::constants_experiment`，种子 block=9。原设定、严重偏移和代理误差低报各 300 个档案，保持点估计权重不变，把 L/H/hidden 界一起乘 .1/.25/.5/1/2，评价覆盖、宽度和释放。

输出：`results/validation_v3/constant_records.csv`、`results/validation_v3/constant_summary.csv`、`results/validation_v3/constants_metadata.json`。B.2 表 `app_b_constants.tex`，label `tab:b-constants`。严重偏移 factor=.1 时覆盖 .40，factor=1 时覆盖 1.00、释放约 .0033；这是联合敏感性，不能分别识别三个常数的作用。

入口二与 B.3 共享 `python scripts/run/run_validation_v3.py selection`。先产生各场景 150 个历史校准档案及 300 个测试档案，再用带噪声历史目标参考的标准化残差构建 .8/.9/.95 区间，分别采用同场景校准及原设定校准跨场景迁移。真值只用于最后评价。

输出：`results/validation_v3/interval_records.csv`、`results/validation_v3/interval_summary.csv`。B.2 表 `app_b_calibration.tex`，label `tab:b-calibration`；严重偏移中原设定历史校准覆盖 .6333。

补充流程：`scripts/build/build_validation_v3.py` 从 `results/validation_v3/selection_predictions.csv` 提取原设定历史校准残差，应用到 `constant_records.csv` 的 factor=1 档案，生成 `results/validation_v3/constant_nominal_calibration_records.csv` 和 `results/validation_v3/constant_nominal_calibration_summary.csv`。这批严重偏移覆盖 .6867，使用另一组测试种子，不能与 .6333 当作同批结果。

### 4.7 部分识别与 minimax 数值说明

PI 入口：`scripts/run/run_partial_identification_experiment.py`；实现 `src/causal_atlas_sim/partial_identification.py`。种子 20260911、20260912、20260913，各 100 次；偏移 0/.25/.60/.80。先判断拒绝，再构造支持优化区间与保留 singleton 证书的交集；去除重复权重、按独立证书数量分配错误概率。空交集记为不一致，不能记成零宽度。

输出：`results/partial_identification_summary.csv`、`results/partial_identification_seed_summary.csv`、`results/partial_identification_metadata.json`。正文 `main_partial_id.tex`、Figure 4 和 B.2 使用本组；四场景交集较单区间缩窄约 2.74%、5.14%、11.43%、11.25%。

下界入口：`scripts/run/run_minimax_experiment.py`；实现 `src/causal_atlas_sim/minimax_experiment.py`。种子 20261011、20261012、20261013，各 100 次，标准误 .35/1.20 和 hull distance 0/.25/.60/1.00 共八格；计算二点构造的解析下界和代表性估计器经验风险。

输出：`results/minimax_experiment_summary.csv`、`results/minimax_experiment_seed_summary.csv`、`results/minimax_experiment_metadata.json`。B.2 文字概述，完整结果在仓库；该实验不建立完整算法的匹配最优性。

## 5. B.3 比较方法与选择机制审查

### 5.1 六方法共同目标比较、证书诊断与配对差

入口：`scripts/run/run_certificate_diagnostics.py`；实现 `src/causal_atlas_sim/certificate_diagnostics.py`、`src/causal_atlas_sim/evaluation_baselines.py`。种子 20260811、20260812、20260813，各 100 次。

流程：对同一批目标比较 ATLAS、no-rejection、semantic forced、semantic nearest、global mean 和仅供评价的 latent oracle。保存真值、预测、绝对误差、释放与五个证书分量。oracle 的真实机制不进入可部署预测或 bridge 选择。

输出：`results/certificate_diagnostics_summary.csv`（本文件实际包含 300 条目标级诊断）、`results/synthetic_benchmark_summary.csv`、`results/certificate_diagnostics_metadata.json`。正文 Figure 2、Figure 3 和 `main_synthetic.tex` 使用本组。

配对表构建：`python scripts/build/build_paired_comparison_table.py`，读取目标级诊断，对每个 comparator 计算相对 no-rejection ATLAS 的绝对误差差，采用配对 MC SE；输出 `docs/paper/overleaf/experiments/causal_atlas_bridge/tables/app_paired_comparison.tex` 和 `docs/paper/revision_evidence/paired_comparison_audit.json`。B.3 保留此表，label `tab:v1-app-paired-comparison`。

结果定位：共同目标的 no-rejection MAE 约 .1387，semantic forced .2493，latent oracle .1350；释放条件下 ATLAS MAE .1109，不能直接拿它与基线全目标 MAE 当作公平的纯预测比较。

### 5.2 正式多场景基准与消融

入口：`scripts/run/run_formal_experiment.py`；实现 `src/causal_atlas_sim/formal_experiment.py`。种子 20260811、20260812、20260813，各场景每种子 100 次；六场景与七种方法/消融共 42 个汇总单元，逐种子 126 行。

流程：固定场景与种子，运行方法、删除 variance penalty 和限制 top-4 候选等消融，分别汇总全目标与释放条件指标及 MC SE。输出：`results/formal_experiment_summary.csv`、`results/formal_experiment_seed_summary.csv`、`results/formal_experiment_metadata.json`。

论文：B.3 从原设定提取三种组合变体，生成 `app_b_ablation.tex`，label `tab:b-ablation`。ATLAS 释放 .463、释放 MAE .111；top-4 释放 .320、MAE .123。该同方差设定删除 variance penalty 效果较小；相同 hidden radius 项在 simplex 上为常数，不能据此声称已识别其权重贡献。

### 5.3 强基线全目标比较（v2）

命令：`python scripts/run/run_requested_extensions.py synthetic --repetitions 100`。实现：该 runner 的 `synthetic` 与 `src/causal_atlas_sim/extension_baselines.py::archive_baselines`。

流程：原设定、偏移 .25、偏移 .8、高噪声四场景，种子 20260811、20260812、20260813 各 100 次。基线使用相同源效应、标准误和完整表示；ridge/RBF 只用源对象 LOO 调参。各方法在所有共同目标上评价，点预测基线不人为附加原生置信区间。

输出：`results/extensions/synthetic_baselines_records.csv`、`results/extensions/synthetic_metadata.json`。之后运行 `scripts/build/build_extension_artifacts.py` 生成 `results/extensions/synthetic_summary.csv`、`results/extensions/synthetic_paired_summary.csv` 及 `docs/paper/overleaf/experiments/causal_atlas_bridge/tables/app_stronger_baselines.tex`。

论文：B.3 外部表 `app_stronger_baselines.tex`，label `tab:ext-baselines`；正文也引用。严重偏移全目标 MAE 为 ATLAS .707、ridge .328、RBF .396，保留强基线胜出的结果。旧 `app_stronger_paired.tex` 不再被当前 01 引用。

### 5.4 单方法风险前沿与多方法等释放率（v3）

原始前沿入口：`scripts/run/run_risk_coverage_experiment.py`；实现 `src/causal_atlas_sim/risk_coverage.py`。种子 20260821、20260822、20260823，各 100 次；同一批目标改变证书阈值，输出 `results/risk_coverage_summary.csv` 和 `results/risk_coverage_metadata.json`，进入 Figure 3。

多方法入口：`python scripts/run/run_validation_v3.py selection`；实现 `src/causal_atlas_sim/validation_v3.py::selection_intervals`，种子 block=1。四场景各 150 历史校准档案、300 测试档案。ATLAS、IVW、nearest、ridge、RBF 只用源信息构建分数，选择最低分数的 25%/50%/75%/100%，并保存由历史分数学得的阈值。相同释放比例允许选中不同目标，评价各方法自己的选择策略风险。

原始输出：`results/validation_v3/selection_predictions.csv`、`results/validation_v3/selection_records.csv`、`results/validation_v3/selection_thresholds.csv`、`results/validation_v3/selection_metadata.json`；同一 runner 还产生 B.2 的 `interval_records.csv`。

构建：`scripts/build/build_validation_v3.py` 生成 `results/validation_v3/selection_summary.csv` 与 `results/validation_v3/selection_rank_bootstrap.csv`。后者用 1,000 次目标配对 bootstrap，每次重新排序；随机种子为 2026090731 加场景排序索引。应使用它评价排序策略的不确定性，普通 summary 的 MC SE 不包含重排变异。

论文：B.3 的 `app_b_selection.tex`，label `tab:b-selection`，显示 50% 操作点，其他比例留档。中等偏移 ATLAS MAE .1612，ridge .1909、RBF .1829；严重偏移则为 .5931/.3058/.3654。回归分数是 heuristic；不声称相同分数意味着相同置信度。区间历史校准所需的额外参考数据必须单列说明。

## 6. B.4 真实数据构造与稳定性

### 6.1 原始 NSW 局部对象重建

入口：`scripts/run/run_nsw_experiment.py`；实现 `src/causal_atlas_sim/nsw_experiment.py`；输入 `data/nsw_dw.dta`。

流程：标准化八个基线协变量，构造 50-neighbor 局部对比，修剪中心范数/半径的极端对象，按覆盖保留 112 个对象。种子 20261201、20261202、20261203，各 20 次拆分，每次留出 28 个对象。五方法共享目标，目标对比与标准误在预测阶段隐藏。保存局部地图、重建误差与区间诊断。

输出：`results/nsw_experiment_summary.csv`、`nsw_experiment_seed_summary.csv`、`nsw_diagnostics_summary.csv`、`nsw_archive_map_summary.csv`、`nsw_method_error_records.csv`、`nsw_experiment_metadata.json`，均位于 `results/`。其中 1,680 条 ATLAS 目标诊断、8,400 条五方法误差记录。

论文：正文 `main_nsw.tex`、Figure 5；B.4 解释构造。全目标 ATLAS 参考 MAE .8615 千美元。邻域共享单位，该重建协议是描述性评价，不是独立研究迁移或潜在真实效应覆盖验证。

### 6.2 NSW 独立单位参考与联合 bootstrap（v2）

命令：`python scripts/run/run_requested_extensions.py nsw --repetitions 100 --bootstrap 200`。实现 `src/causal_atlas_sim/extension_nsw.py::read_data`、`fixed_design`、`real_reference`；输入 `data/nsw_dw.dta`。

流程：种子 2026090601，按处理组把人分为 296 个源单位、149 个参考单位，彼此不重叠。固定 24 个源锚点和六个目标锚点，在各自池中构造 50-neighbor 对象，每臂至少八人。预测只见源信息；之后对参考池随机化对比评分。种子 2026090602，处理分层地独立 bootstrap 两池 200 次，联合重建各池中共享单位的邻域，记录失败和有符号 gap。

输出：`results/extensions/nsw_design.json`、`nsw_real_records.csv`、`nsw_real_failures.csv`、`nsw_metadata.json`，均位于 `results/extensions/`。由 `scripts/build/build_extension_artifacts.py` 生成 `results/extensions/nsw_real_summary.csv`、`results/extensions/nsw_calibration_summary.csv`。

论文：正文补充段和 B.4 文字说明；原 `app_nsw_reference.tex`、`app_nsw_calibration.tex` 及 `extension_nsw_validation.pdf` 已不再单独引用。196/200 bootstrap 有效；ATLAS 平均预测减参考的区间约 [-3.978,3.032] 千美元，不能据此建立等价或一致性。

### 6.3 NSW 已知真值半合成（v2，与 6.2 同一命令）

实现：`src/causal_atlas_sim/extension_nsw.py::semisynthetic`；保留上面的协变量、源/参考池与锚点，独立生成 Bernoulli(.5) 处理及噪声标准差 3 的结局。constant、smooth、interaction 三种效应曲面，种子 2026090611、2026090612、2026090613，各 100 次。

目标真值为该目标邻域的平均 tau(X)。比较源汇总方法及可访问源单位数据的 ridge T-learner，标注后者的额外信息。按独立重复聚类计算 MC SE，释放条件统计采用比值的聚类影响函数。

输出：`results/extensions/nsw_semisynthetic_records.csv`、`results/extensions/nsw_semisynthetic_failures.csv`；builder 生成 `results/extensions/nsw_semisynthetic_summary.csv` 和 `docs/paper/overleaf/experiments/causal_atlas_bridge/tables/app_nsw_semisynthetic.tex`。

论文：B.4 外部表 `app_nsw_semisynthetic.tex`，label `tab:ext-semi`；正文概述。ATLAS 释放约 .915-.947，释放覆盖 .995-.998，宽度约 4.248-4.373 千美元；T-learner 三曲面平均误差均更低。半合成结果不等同于真实潜在效应的验证。

### 6.4 NSW 邻域、锚点和划分稳定性（v3）

命令：`python scripts/run/run_validation_v3.py nsw`。实现 `src/causal_atlas_sim/validation_v3.py::nsw_stability`、`nsw_objects`；种子 block=6；输入 `data/nsw_dw.dta`。

流程：20 个处理分层、源/参考单位分离的拆分；每次比较 k=35/50/75 和 farthest/random 两种锚点，24 源、六目标，两臂最少八人。保存成员索引与全部失败设计。性能条件于有效设计，重复拆分不解释为新增独立样本。

输出：`results/validation_v3/nsw_stability_records.csv`、`nsw_stability_failures.csv`、`nsw_stability_designs.json`、`nsw_stability_summary.csv`、`nsw_metadata.json`，均位于 `results/validation_v3/`。

论文：B.4 的 `app_b_nsw_stability.tex`，label `tab:b-nsw-stability`。120 个设计中 112 个有效；不同 k 改变估计目标与精度，不能把 MAE 随 k 降低单独归因于算法改进。

### 6.5 Hillstrom 第二个真实随机试验（v3）

命令：`python scripts/run/run_validation_v3.py hillstrom`。实现 `src/causal_atlas_sim/validation_v3.py::hillstrom`；输入 `data/external/hillstrom.csv` 和 `data/external/hillstrom_provenance.json`。

流程：按 recency 三个区间、此前 men's/women's purchase 指示和 new-customer 指示预设 24 个单元；18 个非空且全部保留。逐个完整单元留出；标准化、调参、预测只用剩余源单元。visit 是主结局，conversion 是次结局，全部报告。比较五种方法、原生常数 .5/1/2 倍及源单元 LOO 残差区间；内层 LOO 重新拟合 preprocessing。

输出：`results/validation_v3/hillstrom_records.csv`、`hillstrom_loo_records.csv`、`hillstrom_design.json`、`hillstrom_summary.csv`、`hillstrom_metadata.json`，均位于 `results/validation_v3/`。

论文：B.4 的 `app_b_hillstrom_error.tex`、`app_b_hillstrom_interval.tex`，labels `tab:b-hillstrom-error`、`tab:b-hillstrom-interval`。visit MAE 为 ATLAS 2.0364、ridge 1.6324、RBF 1.7580 个百分点；conversion 为 .5293/.7973/.6699。95% 残差区间秩 ceil(18×.95)=18，大于 17 个可用残差，按规则保存无限宽区间。该 LOO 评价不声称 split-conformal 保证，也不是多项独立研究构成的档案。

## 7. B.5 Bridge 证据的范围与稳定性

### 7.1 原始操作策略与预算路径

正式入口：`scripts/run/run_bridge_experiment.py`；实现 `src/causal_atlas_sim/bridge_experiment.py` 和 `src/causal_atlas_sim/algorithm1.py`。种子 20261111、20261112、20261113，各 100 次；四场景、causal greedy/semantic greedy/random 三策略，共 3,600 条策略轨迹。12 个候选、预算四、bridge SE=.10；各步按当前档案，用三点 Gauss-Hermite 求积计算条件期望 PI 直径缩减，再观测被选候选并更新。

输出：`results/bridge_experiment_summary.csv`、`results/bridge_experiment_seed_summary.csv`、`results/bridge_experiment_metadata.json`，以及 `results/bridge_budget_path_summary.csv`。前几个文件提供正式 300 次每策略每场景汇总。

Figure 4 聚焦路径入口：`scripts/run/run_bridge_budget_path_experiment.py`，同三个种子，每策略每种子 30 次，仅严重偏移，共 90 路径/策略。它覆盖 `results/bridge_budget_path_summary.csv`，并生成 `results/bridge_budget_path_metadata.json`；因此重跑时先正式策略、后 focused 路径。正式汇总仍以 `bridge_experiment_summary.csv` 为准。

论文：正文 Figure 4、bridge 小节和 B.5 操作流程说明。causal greedy 四场景平均直径缩减约 31.1%、45.4%、66.2%、73.0%。规划与评价空交集分别记录，不作为零直径收益。

### 7.2 小候选库事后穷举对照

入口：`scripts/run/run_bridge_optimality_experiment.py`；核心 `src/causal_atlas_sim/bridge_experiment.py::run_bridge_optimality_experiment`。种子 20261121，30 次；12 候选，预算 1/2/3 分别枚举 12/66/220 个集合。

流程：先运行可执行策略，再使用已实现的 bridge 结果评价事后最优集合，保存收益比。输出：`results/bridge_optimality_summary.csv`、`results/bridge_optimality_metadata.json`。Figure 4 和 B.5 使用此经验对照；约 .9957/.9776/.9857 的收益比不等于事前策略最优性或弱次模系数证明。

### 7.3 冻结规划分布与保留证书变体（v2）

命令：`python scripts/run/run_requested_extensions.py bridge --bridge-repetitions 12`。实现 `src/causal_atlas_sim/extension_bridge.py::bridge_checks`；种子 2026090621、2026090622，各 12 档案。

流程：moderate/severe 两场景，候选索引 0/1/4/5/8/9，枚举 64 子集、665 个严格扩展。初始源档案确定固定预测分布；参考 2,048 个联合 draws、规划 128 draws，子集间共享 outcome vectors。分别评价 operational 与 retained_certificates 两种证书族，记录空交集、比率、边际估计差和预算 1/2/3 的界。

输出：`results/extensions/bridge_checks.csv`、`bridge_set_values.csv`、`bridge_empty_intersections.csv`、`bridge_metadata.json`，均位于 `results/extensions/`；builder 生成 `results/extensions/bridge_summary.csv`。这组是下一项积分稳定性比较的输入。

### 7.4 增加参考积分样本（v3）

命令：`python scripts/run/run_validation_v3.py bridge`。实现 `src/causal_atlas_sim/validation_v3.py::bridge_stability`，调用同一 `extension_bridge.py::bridge_checks`。

流程：同一批 24 档案、六候选、全部子集，参考 draws 增至 8,192，规划仍为 128；读取 v2 的 `results/extensions/bridge_set_values.csv`，对比 192 条添加候选边/档案的边际符号和数值变化。参考随机流有共同前缀，本项衡量积分敏感性。

输出：`results/validation_v3/bridge_checks_8192.csv`、`bridge_sets_8192.csv`、`bridge_failures_8192.csv`、`bridge_edge_records.csv`、`bridge_edge_summary.csv`、`bridge_stability_summary.csv`、`bridge_metadata.json`，均位于 `results/validation_v3/`。

论文：B.5 从 `bridge_checks_8192.csv` 筛选 `family == retained_certificates`，生成 `app_b_bridge_retained.tex`，label `tab:ext-retained`。72 个档案×预算检查均 gamma=1、下界为正且不超过 greedy value；边际最大变化 .00749。

operational bridge 单调性诊断完整保存在上述 CSV，按用户取舍不写入论文。保留证书变体是单独的固定目标诊断，没有替换 Algorithm 1，也没有证明自适应 operational policy 满足定理前提。

## 8. 从结果到当前论文图表

### 8.1 正文图与外部输入表

当前 Overleaf 图目录为 `experiments/causal_atlas_bridge/figures/`；其仓库归档完整目录为 `docs/paper/overleaf/experiments/causal_atlas_bridge/figures/`。表目录对应替换为 `tables/`。

| 论文资产 | 主要结果输入（均相对仓库根目录） | 构建与归档关系 |
| --- | --- | --- |
| `figure2_synthetic_validation.pdf` | `results/certificate_diagnostics_summary.csv`；`results/representation_sensitivity_summary.csv` | `scripts/build/build_paper_figures.py` → `results/figures/`；当前 Overleaf 副本位于上述归档图目录 |
| `figure3_selective_uncertainty.pdf` | `results/risk_coverage_summary.csv`；`results/calibration_curve_summary.csv`；`results/calibration_experiment_summary.csv`；`results/certificate_diagnostics_summary.csv` | 同一 builder；`selective_uncertainty_overview` 的论文别名 |
| `figure4_rejection_bridge.pdf` | `results/partial_identification_summary.csv`；`results/bridge_budget_path_summary.csv`；`results/bridge_optimality_summary.csv`；`results/bridge_experiment_summary.csv` | 同一 builder；`rejection_bridge_overview` 的论文别名 |
| `figure5_nsw.pdf` | `results/nsw_archive_map_summary.csv`；`results/nsw_diagnostics_summary.csv`；`results/nsw_method_error_records.csv` | 同一 builder；`nsw_diagnostics_overview` 的论文别名 |
| `main_synthetic.tex` | `results/synthetic_benchmark_summary.csv` 与目标诊断 | 当前正文输入快照；paired 统计独立按 5.1 重建 |
| `main_partial_id.tex` | `results/partial_identification_summary.csv` | 当前正文输入快照 |
| `main_nsw.tex` | `results/nsw_experiment_summary.csv`；`results/nsw_method_error_records.csv` | 当前正文输入快照 |
| `app_paired_comparison.tex` | `results/certificate_diagnostics_summary.csv` | `scripts/build/build_paired_comparison_table.py` 直接写归档表目录 |
| `app_stronger_baselines.tex` | `results/extensions/synthetic_baselines_records.csv` | `scripts/build/build_extension_artifacts.py` 直接写归档表目录 |
| `app_nsw_semisynthetic.tex` | `results/extensions/nsw_semisynthetic_records.csv` | 同上 |

`build_paper_figures.py` 也生成 `results/tables/` 下的支持表和旧布局兼容表，不能假定它自动更新所有 `main_*.tex` 在线定稿快照。重跑后需要对照定稿的列定义、表注和统计口径，显式同步所需资产；修改本地文件不会自动同步 Overleaf。

### 8.2 当前附录内嵌表

统一构建入口：`scripts/build/restructure_appendix_b.py`。它读取 `docs/paper/appendix_B_template.tex`、提交 cccf750 的原始 DGP/半合成协议及下表中的保存结果，生成 11 个 `app_b_*.tex`，随后把表内容内嵌到本地 `docs/paper/overleaf/01_causal_atlas_bridge.tex`。生成表完整目录为 `docs/paper/overleaf/experiments/causal_atlas_bridge/tables/`。

| 板块 | 生成表文件 | 输入 |
| --- | --- | --- |
| B.2 | `app_b_surfaces.tex` | `results/validation_v3/mechanism_summary.csv` |
| B.2 | `app_b_nuisance.tex` | `results/validation_v3/nuisance_summary.csv`；`results/validation_v3/nuisance_effect_summary.csv` |
| B.2 | `app_b_dependence.tex` | `results/validation_v3/dependence_summary.csv` |
| B.2 | `app_b_constants.tex` | `results/validation_v3/constant_summary.csv` |
| B.2 | `app_b_calibration.tex` | `results/validation_v3/interval_summary.csv` |
| B.3 | `app_b_selection.tex` | `results/validation_v3/selection_rank_bootstrap.csv` |
| B.3 | `app_b_ablation.tex` | `results/formal_experiment_summary.csv` |
| B.4 | `app_b_nsw_stability.tex` | `results/validation_v3/nsw_stability_summary.csv` |
| B.4 | `app_b_hillstrom_error.tex` | `results/validation_v3/hillstrom_summary.csv` |
| B.4 | `app_b_hillstrom_interval.tex` | `results/validation_v3/hillstrom_summary.csv` |
| B.5 | `app_b_bridge_retained.tex` | `results/validation_v3/bridge_checks_8192.csv`，仅 retained_certificates |

此外，B.1 保留原始 DGP 参数内嵌表，B.3/B.4 保留上面的三个外部表，因此当前附录共 15 表。没有新增外部附录图。生成的 11 个文件是可维护中间产物，当前 Overleaf 编译直接使用 01 中的内嵌内容。

## 9. 完整执行顺序

### 9.1 从头重跑实验

下面命令遵循实际输入依赖。前四条为基础诊断，其余会写入结果目录。正式 bridge 及全部子集积分耗时较长；不能用少量 smoke test 替换论文固定规模结果。

```powershell
python scripts/run/run_sanity_check.py
python scripts/run/run_monte_carlo.py
python scripts/run/run_method_comparison.py
python scripts/run/run_algorithm1.py
python scripts/run/run_main_experiment.py
python scripts/run/run_formal_experiment.py
python scripts/run/run_calibration_experiment.py
python scripts/run/run_risk_coverage_experiment.py
python scripts/run/run_calibration_curve_experiment.py
python scripts/run/run_representation_sensitivity.py
python scripts/run/run_certificate_diagnostics.py
python scripts/run/run_partial_identification_experiment.py
python scripts/run/run_minimax_experiment.py
python scripts/run/run_bridge_experiment.py
python scripts/run/run_bridge_optimality_experiment.py
python scripts/run/run_bridge_budget_path_experiment.py
python scripts/run/run_nsw_experiment.py
python scripts/run/run_requested_extensions.py synthetic --repetitions 100
python scripts/run/run_requested_extensions.py nsw --repetitions 100 --bootstrap 200
python scripts/run/run_requested_extensions.py bridge --bridge-repetitions 12
python scripts/run/run_validation_v3.py selection
python scripts/run/run_validation_v3.py mechanisms
python scripts/run/run_validation_v3.py nuisance
python scripts/run/run_validation_v3.py dependence
python scripts/run/run_validation_v3.py constants
python scripts/run/run_validation_v3.py nsw
python scripts/run/run_validation_v3.py hillstrom
python scripts/run/run_validation_v3.py bridge
```

### 9.2 只从保存记录重建结果汇总与图表

```powershell
python scripts/build/build_final_report.py
python scripts/build/build_paper_artifacts.py
python scripts/build/build_paper_figures.py
python scripts/build/build_paired_comparison_table.py
python scripts/build/build_extension_artifacts.py
python scripts/build/build_validation_v3.py
```

`build_extension_artifacts.py` 一次读取 synthetic、NSW 和 bridge 的 v2 结果，不能在只运行 synthetic 且没有其他保存文件的空目录中执行。`build_validation_v3.py` 一次汇总八个 block，并用 selection 数据校准 constants，所以须在全部原始记录就绪后执行。

以上构建器会重写各自汇总与旧展示产物；最终论文采用哪些文件，以第 8 节和当前源稿为准。

### 9.3 更新本地论文源稿与审计

```powershell
python scripts/build/restructure_appendix_b.py
python scripts/build/audit_appendix_b_assets.py
```

第一条会修改本地 01：重建附录 B，保留理论、附录 A 与参考文献，并修复预定义的正文实验交叉引用。它依赖本地 Git 历史中的 cccf750；浅克隆缺少该提交时需先取得对应历史。模板或数字有修改后，应同步源稿到 Overleaf 并重新编译。

第二条基于保存的 Overleaf 文件树与编译日志核对资产依赖；它不会发起新的在线编译，也不会重新读取当前线上编辑器。用户清理线上文件后，旧 inventory 仍是整理当时的快照。

当前版本不再使用 `scripts/build/integrate_requested_extensions.py` 进行附录集成，它属于 v2 历史流程。旧结果说明曾列出 `scripts/build/verify_validation_v3.py`，但当前提交没有这个脚本；不要将其写入可执行复现链。已有 `results/validation_v3/verification.json` 是当时核验结果留档，不能假定由现存 builder 自动更新。

## 10. 核验、留痕与材料边界

算法测试入口：`python -m unittest discover -s tests -v`。测试验证具体代码行为与实验接口，不构成数学证明。文件索引测试还会检查未忽略的未跟踪文件，临时工作材料可能导致该项失败；用于复现的工作副本应与所选提交一致。

| 留痕材料 | 内容与更新方式 |
| --- | --- |
| `results/experiment_manifest.json` | 原始实验产物清单，由相应结果/图表 builder 更新 |
| `results/extensions/artifact_manifest.json` | v2 输出、脚本、协议和资产哈希，由 `build_extension_artifacts.py` 更新 |
| `results/validation_v3/*_metadata.json` | 各 runner 的命令、软件版本、运行状态、源文件哈希和耗时 |
| `results/validation_v3/artifact_manifest.json` | 已完成 v3 的历史留档；当前 `build_validation_v3.py` 不重新生成此 manifest |
| `docs/paper/revision_evidence/appendix_B_restructure.json` | 当前附录输入 CSV、模板、生成表及论文源稿哈希 |
| `docs/paper/revision_evidence/01_before_appendix_B_online.tex` | 附录重构前在线源稿备份 |
| `docs/paper/revision_evidence/appendix_B_overleaf_compile_dom.txt` | 重构稿 54 页、0 errors、0 warnings、0 typesetting messages 的在线观察记录 |
| `docs/paper/revision_evidence/appendix_B_cleanup.md` | 当前 01 未引用资产与必须保留资产清单；不适用于其他子论文 |

附录 A 的检查另见 `docs/paper/appendix_A_proof_audit.md`、`scripts/run/audit_proof_counterexamples.py` 和 `results/validation_v3/proof_counterexamples.json`。这是理论审阅及数值反例材料，不属于性能实验，也不应把其输出解释为机器验证的证明。

维护本文件时，应同时更新 `docs/reference/repository_file_map.md`。新增实验要记录设计、命令、种子、输入数据哈希、完整成功/失败记录、汇总口径及入文位置；没有入文的实验继续保留在仓库。特别是 operational bridge 单调性诊断，只作仓库证据保留，不随本汇总写回论文。

本次文档核验：检查了文中明确路径、53 处脚本命令引用、具名函数和九个相对链接。全套既有测试共 95 项，94 项通过；文件索引测试报告上次附录重构的遗漏条目和本地未跟踪的临时构建文件。已补齐受 Git 跟踪文件的索引，并单独确认跟踪文件覆盖完整；未删除临时文件，也未声称工作区的完整索引测试已通过。本次没有重跑论文规模的实验或重建图表。
