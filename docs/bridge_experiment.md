# Stage 11：Bridge experiment design

## 理论目标

本阶段对应论文 Definition 5.2、Algorithm 1 和 Theorem 5.6。拒绝点组合后，
bridge 的价值不是文本新颖性，而是目标部分识别区域的期望直径缩减：

\[
\operatorname{VoI}_{\mathcal A}(b)
=
\operatorname{diam}\{\Theta_{\mathcal A}(e^\star)\}
-
\mathbb E_b\!left[
\operatorname{diam}\{\Theta_{\mathcal A\cup\{b\}}(e^\star)\}
\right].
\]

对候选集合 \(S\)，论文记

\[
F(S)=\operatorname{diam}\{\Theta_{\mathcal A}(e^\star)\}
-\mathbb E\!left[
\operatorname{diam}\{\Theta_{\mathcal A\cup S}(e^\star)\}
\right].
\]

如果 \(F\) 单调、\(F(\varnothing)=0\)，并且是 \(\gamma\)-weakly submodular，
同时 greedy 使用的边际价值误差统一不超过 \(\varepsilon_{\mathrm{est}}\)，则预算
\(B\) 下 Theorem 5.6 给出

\[
F(S_B)
\ge
(1-e^{-\gamma})F(S^\star)
-\frac{2B\varepsilon_{\mathrm{est}}}{\gamma}.
\]

该定理是条件保证，不声明所有 bridge 目标天然满足 weak submodularity。本实验
比较三种选择策略的直径缩减，不把数值结果当作上述条件或近似系数的证明。

## 可计算的直径代理

在 bridge outcome 尚未观测时，完整的 \(\Theta_{\mathcal A\cup\{b\}}\) 依赖未知
结果。本阶段使用一个可审计的 design-time support-diameter certificate：

\[
D_{\mathcal A}
=2\min\left\{
M,
L\rho_\star(\alpha)
+\frac{H}{2}\operatorname{Disp}(\alpha)
+R_{\mathrm{hid}}(\alpha)
+\sqrt{2\log(2/\zeta)\sum_j\alpha_j^2s_j^2}
\right\}.
\]

它沿用 Theorem 5.1 的 support、curvature、hidden-moderator 和 statistical 四个
证书分量，使用 \(L=2.61\)、\(H=1.80\)、\(M=3.88\) 和 \(\zeta=0.05\)。
权重在单纯形上同时降低公开表示的 support residual 和方差集中度。

候选尚未运行时，策略用该候选的公开表示、moderator radius 和已知设计标准误
计算 singleton certificate，作为边际价值估计；候选选中后，再把它加入 archive，
重新求完整权重和完整直径。边际估计额外加入绝对值不超过 0.01 的均匀误差，
与 Theorem 5.6 的统一误差条件相对应。

bridge effect 按论文附录的非线性曲面生成，并加入标准误为 0.10 的高斯测量误差。
该 outcome 不进入选择策略；在设计时，它只通过已知标准误影响期望宽度。真实
bridge effect、target 真值和真实机制只用于仿真评估。

## 候选库与策略

每个 target 的公开表示附近生成 12 个候选：

1. 4 个 `causal_full`：在语义、隐藏调节代理和设计坐标上都接近 target；
2. 4 个 `semantic_trap`：在 \((s_1,s_2)\) 上很近，但在隐藏调节和设计坐标上远；
3. 4 个 `mixed`：在四个坐标上中等幅度变化。

三种策略共享完全相同的 archive、target、候选和 bridge outcomes：

| 策略 | 设计时允许读取的信息 | 选择规则 |
| --- | --- | --- |
| causal-support greedy | 完整公开表示 \((s_1,s_2,h_{proxy},q)\) | 每步最大化估计直径缩减 |
| semantic-only greedy | 仅 \((s_1,s_2)\) | 每步最大化语义空间直径缩减 |
| random bridge | 候选索引 | 从剩余候选均匀随机选择 |

最终评价对三种策略统一使用完整四维公开表示的证书直径。另报告真实机制到扩展
archive 凸包的 oracle 距离，但该距离不参与选择。

## 固定实验协议

- support 场景：shift fraction 为 0、0.25、0.60、0.80；
- archive 数量：8；
- bridge 候选数：12；
- bridge 预算：4；
- bridge 标准误：0.10；
- 边际估计统一误差上界：0.01；
- 独立基准种子：20261111、20261112、20261113；
- 每个种子、每个场景重复 100 次；
- 总 target 重复数：4 × 3 × 100 = 1,200；
- 总策略路径：1,200 × 3 = 3,600。

## 结果

| 场景 | 策略 | 初始直径 | 最终直径 | 缩减 | 缩减比例 | 初始 oracle 距离 | 最终 oracle 距离 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| supported | causal greedy | 3.3559 | 2.5332 | 0.8228 | 0.2452 | 0.0000 | 0.0000 |
| supported | semantic greedy | 3.3559 | 2.8771 | 0.4788 | 0.1427 | 0.0000 | 0.0000 |
| supported | random | 3.3559 | 2.8250 | 0.5309 | 0.1582 | 0.0000 | 0.0000 |
| moderate | causal greedy | 3.9344 | 2.0668 | 1.8676 | 0.4747 | 0.1246 | 0.0051 |
| moderate | semantic greedy | 3.9344 | 2.7369 | 1.1975 | 0.3044 | 0.1246 | 0.0100 |
| moderate | random | 3.9344 | 2.6335 | 1.3009 | 0.3307 | 0.1246 | 0.0062 |
| strong | causal greedy | 6.1000 | 1.7765 | 4.3236 | 0.7088 | 0.6446 | 0.0148 |
| strong | semantic greedy | 6.1000 | 2.4289 | 3.6711 | 0.6018 | 0.6446 | 0.0271 |
| strong | random | 6.1000 | 2.3967 | 3.7033 | 0.6071 | 0.6446 | 0.0306 |
| severe | causal greedy | 7.0338 | 1.7817 | 5.2521 | 0.7467 | 1.0015 | 0.0153 |
| severe | semantic greedy | 7.0338 | 2.1808 | 4.8529 | 0.6899 | 1.0015 | 0.0155 |
| severe | random | 7.0338 | 2.3104 | 4.7234 | 0.6715 | 1.0015 | 0.0389 |

![Bridge design 实验总览](../results/figures/bridge_experiment_overview.png)

causal greedy 在全部四个场景中取得最小最终证书直径。支持缺口越大，bridge 的
绝对价值越大：严重失配下平均缩减 5.2521，而 supported 场景缩减 0.8228。
supported 场景的 oracle hull distance 已接近 0，但统计、曲率和隐藏调节证书仍
非零，因此新实验仍能通过增加局部精度来缩短直径。

semantic greedy 在 strong 和 severe 场景中也能把若干候选的真实机制凸包扩展到
target 附近，但这些候选在隐藏调节和设计坐标上分散，导致 curvature 和完整证书
直径更大。因此，仅报告最终 oracle hull distance 会漏掉设计风险；bridge 必须按
完整证书而不只是“能否几何到达 target”评价。

## 限制

本阶段没有穷举预算 4 的全局最优候选集合，也没有估计 weak-submodularity 参数
\(\gamma\)，所以不能验证理论近似比例。singleton marginal 是候选尚未测量时的
可计算代理，不等于完整 outcome-dependent VoI。候选库由受控偏移构造，结果不能
外推到任意真实科学候选库。

下一阶段的 NSW 真实数据实验会把 bridge 设计留在合成部分，不会把真实数据的
held-out local contrast 误称为无噪声 ground truth。

## 复现

```powershell
python scripts/run_bridge_experiment.py
python -m unittest discover -s tests -v
```

结果位于 `results/bridge_experiment_*.csv`、对应 metadata JSON、
`results/tables/bridge_experiment_tables.md` 和
`results/figures/bridge_experiment_overview.png`。
