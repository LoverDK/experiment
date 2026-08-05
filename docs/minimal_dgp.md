# 最小化数据生成机制

本阶段只实现可验证理论前提的数据生成器，不实现候选检索、权重优化、拒绝规则或基线比较。生成器的任务是产生一组 archive experiments 和一个 target experiment，并使 Assumption 3.1--3.5 在构造上成立。

## 机制与真实效应

真实机制位于紧且凸的空间：

\[
\mathcal M=[-1,1]^4,
\qquad m=(s_1,s_2,h,q).
\]

其中 \(s_1,s_2\) 是语义坐标，\(h\) 是真实但未完全观测的调节变量，\(q\) 是设计坐标。真实效应采用论文附录中的曲面：

\[
\mu(m)=1.15\sin(1.1s_1)+0.65s_2+1.10h+0.45s_1h-0.28q^2+0.25\cos(s_2+q).
\]

archive 中的机制独立从 \(\mathcal M\) 抽取；target 机制由 archive 机制的非负权重凸组合构造。这个权重只保留为 sanity check 的 oracle 元数据，后续估计方法不可使用它。于是 target 的因果支持残差在数值精度内为零。

## Assumption 3.1：实验层面效应可识别

每个实验生成独立单位记录：

\[
X_\ell\sim N(0,I),\qquad A_\ell\sim\operatorname{Bernoulli}(0.5),
\]

且 \(A_\ell\) 独立于 \(X_\ell,Y_\ell(0),Y_\ell(1)\)。已知倾向概率为 \(\pi(X)=0.5\)，满足声明的重叠下界 \(\pi_0=0.1\)。观测结果严格由

\[
Y=A Y(1)+(1-A)Y(0)
\]

生成，因此一致性和随机化下的可忽略性在构造上成立。

## Assumption 3.2：设计兼容性与归一化

所有 archive 和 target 共用同一个不可变 `DesignProfile`：相同处理版本、无处理对照、标准化连续结果差、固定结果时间窗、无干扰暴露映射、相同抽样框，以及共同 estimand \(\operatorname{ATE}=E[Y(1)-Y(0)]\)。效果尺度已经标准化，归一化为恒等变换。

## Assumption 3.3：局部平滑性

\(\mu\) 是 \(\mathcal M\) 上连续可微函数。实现中记录了保守的全局证书：

\[
\|\nabla\mu(m)\|\le L=2.61,
\qquad
\|\nabla^2\mu(m)\|_{\mathrm{op}}\le H=1.80.
\]

前者来自四个偏导绝对值上界 \((1.715,0.90,1.55,0.81)\) 的欧氏范数；后者由 Hessian 的 Frobenius 范数上界给出。测试会在随机机制点上重新检查解析梯度和 Hessian。

## Assumption 3.4：不确定性证书

生成器使用已知随机化概率和真实 nuisance functions 计算 AIPW score。单位层面残差是独立正态变量，因此实验级估计满足

\[
\widehat\tau_i=\tau_i+\xi_i+b_i,
\qquad b_i=0,
\]

其中 \(\xi_i\) 是均值零次高斯误差，方差代理证书取为

\[
s_i^2=\frac{v_i}{n_i},
\qquad
v_i=\frac{\sigma^2}{\min\{\pi,1-\pi\}^2}.
\]

默认 \(\pi=0.5\) 时，该界为 \(v_i=4\sigma^2\)。每个实验使用独立随机流，所以协方差证书为对角形式。

## Assumption 3.5：观测表示与隐藏调节变量证书

算法公开的表示为

\[
r=(s_1,s_2,h_{\mathrm{proxy}},q).
\]

代理误差被限制为 \(|h-h_{\mathrm{proxy}}|\le0.10\)。声明的敏感性半径为 \(\delta=0.20\)，它覆盖同一 proxy-compatible 集合中任意两个 \(h\) 值的最大距离。由于

\[
\left|\frac{\partial\mu}{\partial h}\right|
=|1.10+0.45s_1|\le L_h=1.55,
\]

对任意设计兼容的单纯形权重 \(\alpha\)，使用讲义给出的证书：

\[
R_{\mathrm{hid}}(\alpha)
=L_h\left(\delta_\star+\sum_j\alpha_j\delta_j\right).
\]

代码会检查 target 与 archive 的实际 true-versus-proxy 组合差不超过这个证书。

## 运行与校验

```powershell
& 'C:\Users\Qiutian\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts/run_sanity_check.py
& 'C:\Users\Qiutian\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest discover -s tests -v
```

这些校验只证明实现遵守了所声明的数学构造；真实数据分析中的随机化审计、平衡检验、重叠图、负对照和敏感性曲线将在后续步骤实现。
