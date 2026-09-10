# 从零复现实验并重建论文结论

这是一份可执行的端到端复现流程。目标是从干净仓库开始，重新生成正文实验、附录 B 实验、CSV 汇总、图、LaTeX 表，并逐项核对论文文字结论。所有命令均在仓库根目录 `experiment/` 执行。

正式 runner 会写入 `results/`，部分 builder 会覆盖汇总和图表；建议使用新分支或新工作副本。不要在含有个人临时文件的目录直接运行正式规模实验。

## 1. 准备环境并确认基线

### 1.1 获取代码和数据

```powershell
git clone https://github.com/LoverDK/experiment.git
cd experiment
git checkout main
git status --short
```

工作区最好为空。当前实验论文源稿是 `docs/paper/overleaf/01_causal_atlas_bridge.tex`；不要用旧 PDF 推断附录结构。仓库已包含合成代码、NSW 快照、Hillstrom 数据及 provenance 文件。

### 1.2 安装依赖

```powershell
python --version
python -m pip install numpy pandas matplotlib pillow
python -m pip show numpy pandas matplotlib pillow
```

建议 Python 3.10 或以上。脚本会自行把 `src/` 加入 Python 搜索路径，不需要先安装本仓库。想逐数值复现时，应查看 `results/*_metadata.json` 中记录的版本；更换版本要保存为一次新的复现实验。

### 1.3 先跑只读教学例子

```powershell
python docs/paper/experiment_code_walkthrough/examples/inspect_one_archive.py
python docs/paper/experiment_code_walkthrough/examples/trace_saved_results.py
```

第一个脚本在内存中生成一个八源档案，重算 AIPW、ATLAS 权重、五项证书和部分识别端点；第二个脚本从已保存 CSV 重算正文和附录的代表数字；二者都不写文件。

### 1.4 运行代码级测试

```powershell
python -m py_compile docs/paper/experiment_code_walkthrough/examples/inspect_one_archive.py docs/paper/experiment_code_walkthrough/examples/trace_saved_results.py
python -m unittest discover -s tests -v
```

算法、固定种子、表图输入和数据构造测试应通过。文件索引测试可能因本地未跟踪临时文件失败；应记录文件名，不要把临时文件加入正式索引。

### 1.5 固定评价口径

1. 合成和已知真值半合成的 coverage 针对潜在效应；NSW/Hillstrom 的 inclusion 针对带噪声随机化参考值。
2. `released MAE` 只在发布目标上算，`all-target MAE` 包含所有目标。
3. NSW 多次划分衡量同一总体的设计敏感性，不是独立试验重复。
4. 空交集、失败档案和无限宽区间保留特殊状态，不能改成零或普通缺失。

## 2. 按依赖顺序运行正文和附录实验

### 2.1 正文合成实验

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
```

这些命令生成主合成比较、选择性发布、校准、表示敏感性和目标级证书诊断。Figure 2 主要读取 `certificate_diagnostics_summary.csv`、`representation_sensitivity_summary.csv`；Figure 3 读取 risk-coverage、calibration curve、calibration experiment 和 certificate diagnostics；Table 1 读取 `synthetic_benchmark_summary.csv` 等汇总。

验收：formal 使用 seeds `20260811/12/13`，共同目标诊断有 300 行；不能用一个小规模 seed 代替正式表。

### 2.2 部分识别、minimax 和 Bridge

```powershell
python scripts/run/run_partial_identification_experiment.py
python scripts/run/run_minimax_experiment.py
python scripts/run/run_bridge_experiment.py
python scripts/run/run_bridge_optimality_experiment.py
python scripts/run/run_bridge_budget_path_experiment.py
```

先生成拒绝目标的部分识别区间，再做 minimax 数值检查，最后运行正式 Bridge、事后穷举和 severe focused path。focused runner 会覆盖 `results/bridge_budget_path_summary.csv`，因此必须放在正式 Bridge 之后。

这些结果支撑 Figure 4、Table 2 以及附录的完整 PI、minimax、Bridge 场景和穷举表。事后穷举使用规划阶段不可用的信息，不能写成部署策略最优性的证明。

### 2.3 NSW 和 v2 扩展

```powershell
python scripts/run/run_nsw_experiment.py
python scripts/run/run_requested_extensions.py synthetic --repetitions 100
python scripts/run/run_requested_extensions.py nsw --repetitions 100 --bootstrap 200
python scripts/run/run_requested_extensions.py bridge --bridge-repetitions 12
```

第一条生成正文 NSW reconstruction；后三条生成强基线、分离源/参考池的 NSW 和已知真值半合成、冻结规划分布 Bridge。正式 builder 不能读取 `--repetitions 2` 之类 smoke 输出。

### 2.4 附录 B.2：稳健性与失效边界

```powershell
python scripts/run/run_validation_v3.py mechanisms
python scripts/run/run_validation_v3.py nuisance
python scripts/run/run_validation_v3.py dependence
python scripts/run/run_validation_v3.py constants
```

四个 block 分别改变效应曲面与表示、nuisance 与 overlap、摘要误差相关性、科学常数和历史校准。每个 block 都会写 metadata；失败记录也是结果的一部分。

### 2.5 附录 B.3：比较与选择审计

```powershell
python scripts/run/run_validation_v3.py selection
```

该 block 使用 calibration/test 分离档案比较 ATLAS、IVW、nearest、ridge 和 RBF，并在相同发布比例下重新排序、执行 1,000 次 paired bootstrap。重点是信息访问和选择规则的公平比较。

### 2.6 附录 B.4：真实数据构造与稳定性

```powershell
python scripts/run/run_validation_v3.py nsw
python scripts/run/run_validation_v3.py hillstrom
```

NSW block 运行 20 个分离单位划分、两种锚点和三种邻域大小；Hillstrom 留出 18 个非空随机试验单元，报告 visit 和 conversion。保留 NSW 失败设计和 Hillstrom 无限宽 95% source-LOO 区间。

### 2.7 附录 B.5：Bridge 稳定性

```powershell
python scripts/run/run_validation_v3.py bridge
```

该命令把参考积分从 v2 的 2,048 draws 增至 8,192 draws，检查 retained-certificate 固定目标的边际收益和下界；它依赖 v2 的 `results/extensions/bridge_set_values.csv`。operational bridge monotonicity 只留在仓库，不写入论文结论。

## 3. 汇总、生成论文资产并验收结论

### 3.1 生成汇总

```powershell
python scripts/build/build_final_report.py
python scripts/build/build_paper_artifacts.py
python scripts/build/build_paired_comparison_table.py
python scripts/build/build_extension_artifacts.py
python scripts/build/build_validation_v3.py
```

这些 builder 读取已保存记录，不重新生成 DGP。检查 `results/extensions/`、`results/validation_v3/` 中的 records、summary、failures 和 metadata 是否齐全。

### 3.2 生成 Figure 2--5

```powershell
python scripts/build/build_paper_figures.py
```

Figure 2 展示因果表示和组合误差；Figure 3 展示 risk-coverage、区间覆盖/宽度、证书分量和失配边界；Figure 4 展示拒绝后的识别区间及 Bridge 缩减；Figure 5 展示 NSW 局部对象、重建误差和 noisy reference inclusion。检查 `results/figures/` 下 PNG/PDF 均存在。

### 3.3 重建附录 B 表格

```powershell
python scripts/build/restructure_appendix_b.py
```

脚本读取 `docs/paper/appendix_B_template.tex` 和已保存 CSV，生成 `docs/paper/overleaf/experiments/causal_atlas_bridge/tables/app_b_*.tex`，并把五板块附录内嵌到本地 `01_causal_atlas_bridge.tex`。它会修改论文源稿，运行前应备份或使用新分支。

生成表的分组是：B.2 的 surfaces、nuisance、dependence、constants、calibration；B.3 的 selection、ablation；B.4 的 NSW stability、Hillstrom error、Hillstrom interval；B.5 的 retained bridge。B.1 协议表以及 B.3/B.4 的外部扩展表也必须保留，当前附录共 15 张表。

### 3.4 逐项核对论文文字

```powershell
python docs/paper/experiment_code_walkthrough/examples/trace_saved_results.py
```

1. Figure 2/Table 1：发布率、released MAE、all-target MAE、semantic forced 对照和 representation advantage 必须来自共同目标协议。
2. Figure 3：条件 MAE、发布率、honest coverage/width、证书分量和失配 coverage 必须分别来自对应 CSV。
3. Figure 4/Table 2：PI 宽度、Bridge 路径和 ex-post 穷举来自不同协议，不能混作同一批重复。
4. Figure 5/Table 3：NSW reference 是 noisy held-out local contrast，不能写成真实 subgroup ATE。
5. B.2：失败次数、相关误差覆盖下降、常数敏感性和校准迁移失败都要保留。
6. B.3：bootstrap 中必须重新排序；额外信息访问要在表注说明。
7. B.4：112/120 有效 NSW 设计、8 个失败设计、两个 Hillstrom 结局和无限宽 95% 区间都要保留。
8. B.5：72 个 retained checks 和 8,192-draw 稳定性不能扩展成 operational adaptive policy 的新定理。

### 3.5 编译和留痕

```powershell
git diff --check
python scripts/build/audit_appendix_b_assets.py
```

把图表上传到 Overleaf 对应的 `experiments/causal_atlas_bridge/figures/` 和 `tables/` 路径后重新编译，检查 0 errors、0 warnings、0 typesetting messages，并确认 Figure 2--7、Table 1--3 及附录表均无 missing file。历史编译日志不能冒充本次新编译证据。

一次正式复现至少保存每个 runner 的命令、日期、软件版本、git commit、metadata、CSV、图表、失败记录、论文源稿和编译日志。完整可追溯链是：runner 生成记录 → builder 生成汇总 → 图表 builder 生成展示 → LaTeX 引用展示 → 文字结论引用展示中的统计量。
