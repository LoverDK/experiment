# 01 基础校验、早期 Monte Carlo 与方法演示

## 1. Assumption 3.1--3.5 自动校验

### 正文覆盖状态

Section 6.1 已经说明机制空间、随机化、样本量和隐藏调节代理，但没有说明仓库还会
自动检查五条假设构造。它不是新的性能实验，而是 DGP 的有效性检查。

### 对应文件

| 文件 | 作用 |
| --- | --- |
| `docs/stages/minimal_dgp.md` | 五条假设的构造、数学解释和校验口径 |
| `src/causal_atlas_sim/dgp.py` | DGP、AIPW 方差和假设证书实现 |
| `scripts/run/run_sanity_check.py` | 生成一份 archive-target 并打印五条校验结果 |
| `tests/test_dgp.py` | 自动检查随机化、平滑界、代理证书和隐藏偏移边界 |

### 建议

正文最多增加一句，不应把测试输出写成一张实验表。它的价值是证明后续实验确实运行在
声明的模型类中，而不是提供方法性能证据。

### 候选正文

> Before evaluating transport performance, we verified programmatically that every synthetic configuration used in the nominal experiments satisfies the experiment-level identification, design-normalization, smoothness, uncertainty-certificate, and moderator-proxy conditions stated in Assumptions 3.1--3.5.

## 2. 200 次 oracle-support Monte Carlo 管线校验

### 做了什么

阶段 2 使用 DGP 内部真实凸组合权重，不学习 ATLAS 权重。它比较 noise-only 区间和
加入曲率、隐藏调节项后的 certified 区间。固定 200 次演示中，noise-only coverage
为 `0.4150`，certified coverage 为 `1.0000`，完整区间平均宽度为 `3.2708`。

### 对应文件

| 文件 | 作用 |
| --- | --- |
| `docs/stages/monte_carlo.md` | 实验目的、公式、结果与边界 |
| `src/causal_atlas_sim/monte_carlo.py` | oracle-support 重复和覆盖率计算 |
| `scripts/run/run_monte_carlo.py` | 运行后输出 JSON，不写正式结果文件 |
| `tests/test_monte_carlo.py` | 固定种子、覆盖与曲率界测试 |

### 遗漏判断

这项工作正文完全未写，但不建议补入正文。它是开发期管线检查，且已被 Section 6.3
更严格的共同目标校准实验取代。若再写 `0.415` 与 `1.000`，会和 Figure 3 的正式
Wald/honest 比较形成重复，还可能让读者误以为 oracle 权重可以部署。

### 仅在需要解释开发验证时使用的文本

> A preliminary oracle-support simulation was used only to validate the error-decomposition pipeline: intervals based on sampling noise alone undercover, whereas adding curvature and moderator uncertainty restores conservative coverage. Because this check uses simulated oracle weights, it is not treated as a deployable-method result.

## 3. 200 次早期五方法比较

### 做了什么

阶段 3 在共享的 200 个 target 上比较 ATLAS、no-rejection 和三种语义/全局基线。
它验证候选过滤、权重、拒绝和区间代码能共同工作，但不保存正式 CSV。

### 对应文件

| 文件 | 作用 |
| --- | --- |
| `docs/stages/method_comparison.md` | 五种方法、信息边界和演示结果 |
| `src/causal_atlas_sim/comparison.py` | 共享 target 的比较协议 |
| `scripts/run/run_method_comparison.py` | 输出 200 次演示 JSON |
| `tests/test_comparison.py` | 共享随机流和方法集合测试 |

### 遗漏判断

不要补正文。它已经被 `synthetic_benchmark_summary.csv` 的 300 个共同目标、六方法
正式基准完全取代。正文 Table 1 应保持唯一主基准，避免同时出现两套略有差异的
ATLAS、semantic 和 nearest 数字。

## 4. 不属于实验结果的仓库工作

以下内容虽然在仓库中可运行，但不应列为“正文遗漏实验”：

- `run_algorithm1.py`：一条算法路径演示；
- `build_final_report.py`、`build_paper_artifacts.py`、`build_paper_figures.py`：产物构建；
- `experiment_manifest.json`：文件完整性与哈希清单；
- 单元测试：实现正确性验证。

它们应进入复现说明，而不是 Section 6 的科学结果。
