# Monte Carlo 重复运行框架

本阶段把已通过 Assumption 3.1--3.5 校验的单次 DGP 重复运行，但暂时不实现 Causal ATLAS 的权重学习。唯一的比较对象是 `oracle-support composition`：使用 DGP 内部保存的真实凸组合权重 \(\alpha\) 组合 archive 效应估计，作为后续方法和评价管线的参考，不代表可部署方法。

## 每次重复

对每个独立子随机种子：

1. 生成一批 archive experiments 和一个 target；
2. 读取 archive 的估计效应和方差证书；
3. 用 oracle \(\alpha\) 计算
   \[
   \widehat\theta_{\mathrm{oracle}}=\sum_j\alpha_j\widehat\tau_j;
   \]
4. 记录 target 真值、signed error、absolute error 和方向是否正确；
5. 计算只含统计噪声的区间；
6. 加入 Assumption 3.3 的曲率项和 Assumption 3.5 的 \(R_{\mathrm{hid}}\) 后，计算保守证书区间。

## 为什么同时报告两种区间？

由于 \(\mu\) 是非线性的，即使 target 机制在 archive 的凸包内，也有

\[
\mu(m_\star)\ne\sum_j\alpha_j\mu(m_j).
\]

因此只使用 \(z\sqrt{\sum_j\alpha_j^2s_j^2}\) 的 noise-only interval 不能覆盖曲率偏差和隐藏调节变量误差。第二种 certified interval 加入

\[
\frac{H}{2}\sum_j\alpha_j\|m_j-\bar m_\alpha\|^2
+R_{\mathrm{hid}}(\alpha)
+z\sqrt{\sum_j\alpha_j^2s_j^2},
\]

它是对理论组合不等式的直接数值化。这个阶段的目的，是确认误差分解和指标实现正确；不能把 oracle 结果当作完整方法的性能结论。

## 输出指标

脚本输出 JSON 汇总：

- `mean_absolute_error`、`rmse`、`bias`；
- `sign_accuracy`；
- `noise_only_coverage` 与 `certified_coverage`；
- 两种区间的平均宽度；
- 平均曲率界、平均隐藏调节变量证书；
- `mean_support_residual`；
- 曲率界违反率。

运行：

```powershell
& 'C:\Users\Qiutian\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts/run_monte_carlo.py
```

默认运行 200 次，不会把生成的数据或结果文件写入仓库。后续正式实验应为每种方法使用相同的重复数据和随机种子，并保存配置与结果表。
