# 07：附录 B.2 的每一项压力测试改了哪些代码

源码统一在 [validation_v3.py](../../../src/causal_atlas_sim/validation_v3.py)，入口为 [run_validation_v3.py](../../../scripts/run/run_validation_v3.py)。本章按函数完整解释 mechanisms、nuisance、dependence、constants 四个 block。历史校准 block 见第 6 章。

## 1. runner 如何选择实验、记录失败

入口的 functions 字典把命令名称映射到函数，例如 `'nuisance':v.nuisance_experiment`。`argparse` 的 choices 限制合法名称。`functions[args.block]()` 先按字符串查出函数，再用括号调用。

运行之前保存 command、Python/NumPy/Pandas 版本、当前 Git HEAD、所有核心 `.py` 及协议 SHA-256。try 成功写 status=completed；异常写 failed 与 repr(ex)，并重新抛出；finally 总会记耗时和 metadata。

每个 block 默认正式规模固定，没有统一 `--repetitions` 参数。想快速学习应单独调用小函数，不要想当然在命令后加不支持的选项。

## 2. mechanisms：五种曲面的定义

`surface_value(m,kind)` 把四维 m 转为 x。original 保留 `effect_surface`；另外四种：

- affine：`.5+x0+.6*x1+.8*x2-.3*x3`，线性加截距。
- oscillatory：`sin(4*x0)+cos(3*x1)+.8*x2*x3`，更快振荡并含交互。
- threshold：`1.5*(x2>0)-1.2*(x0*x1>.15)+.4*x3`，条件为真时产生跳跃。
- friedman2：先把四坐标变换到指定正值尺度 a/b/c/d，再算 `sqrt(a*a+(b*c-1/(b*d))**2)/500`。

这里更换曲面没有为各曲面重新证明 L/H/L_h。原常数被继续传给方法，因此新曲面的区间是失配压力诊断。threshold 本身不连续，更不能归入原始光滑假设成立的验证。

## 3. `transform` 如何改摘要而保持结构

先把 source 与 target 合成一个迭代序列：`(*g.archive,g.target)`。对每个对象：取原真值或新 surface_value；取原估计误差 `estimated_effect-true_effect`；选择是否替换噪声；复制 observed 表示。

```python
if noise == 't3':
    err = rng.standard_t(3)/np.sqrt(3)*obj.standard_error_certificate
```

自由度 3 的 t 分布方差为 3，所以除 sqrt(3) 调整至单位方差，再乘 SE。此操作直接改 effect estimate 的噪声，是摘要层 heavy-tail 压力测试；并未从头生成一组服从 t 噪声的受试者结果并重新计算整个 AIPW。

`proxy=True` 把公开 h 代理改为真实 h 加 uniform(-.5,.5) 后截断，声明半径仍旧。`omit=True` 将公开表示最后两维用无关随机值替换，保留数组维数四维。这里“omit”是用无信息坐标替换，不是删除数组列。

`delta=新真值-旧真值`，随后 replace 更新 true_effect、estimated_effect、observed_representation；给 Y(1)、观测处理组 Y、AIPW 分数各加相应 delta。这些字段在基准重心是摘要评价；t3 改写后的摘要误差不保证仍等于存储 aipw_scores 的均值误差。

## 4. mechanisms 的完整网格

九个 change：baseline、shift=.8、small_n=100、archive4、archive24、high_noise=3、t3、omit、proxy。5 曲面×9 设置×100 重复×5 方法=22500 条方法记录。

small_n 在 settings 中仅改变 `n_units_per_experiment`，目标人数仍默认 400；这一点与原始主扫描源目标一起改不同。原始目标真值不受目标样本噪声影响，但参考值精度会受人数设定影响。

每条记录含 surface、change、replicate、seed，随后是 predictor_rows 的各字段，另加 width、released、covered。默认 `released=score<=1.65` 对五方法都计算；ridge/RBF score 为启发式分数，所以不能称所有方法都通过统一理论证书。

输出 `results/validation_v3/mechanism_records.csv`。builder 按 surface/change/method 汇总，论文表选 baseline 五曲面，其他扰动保留全记录和汇总。没有写入表不等于没有运行。

## 5. nuisance：单个人的数据怎样生成

`nuisance_experiment` 外层 n=100/400，分组方式 balanced/weak/logistic，各 200 次。每次先生成基础 archive 的机制，然后逐源另造一维 x：

```python
x = rng.uniform(-1,1,n)
p = .5 if prop=='balanced' else (.1 if prop=='weak' else sigmoid(2*x))
a = rng.binomial(1,p,n)
y = 1+.8*x+1.2*x*x + a*e.true_effect + rng.normal(size=n)
```

p 可以是标量 .5/.1，也可以是每人不同的向量。`sigmoid(2*x)` 等于 expit(2X)。结果基线有二次项，所以仅线性结果回归会失配。真实 treatment effect 仍来自该源机制的 e.true_effect。

同一套 `(x,a,y,p)` 保存到 data，随后各种 nuisance mode 共用它，而不是每种 mode 重新抽结果。

## 6. `fitted_aipw` 的 oracle 分支

函数输入 x、a、y、tau、mode、propensity。`np.isscalar` 判断 p 是否单一概率，必要时复制成 n 个概率。oracle 直接使用真实 `mu0=1+.8*x+1.2*x*x`，返回与第 1 章同型的 AIPW 分数。

真实 tau 在 oracle 中是明确允许的生成知识。拟合的 modes 用观测结果训练条件均值，不能把 oracle 的性能当作普通学习算法的性能。

## 7. 两折 cross-fitting 的下标逐句读

```python
folds = np.arange(n)%2
scores = np.empty(n)
for fold in (0,1):
    train = folds != fold
    test = ~train
```

`arange(n)` 是 0..n-1，模 2 交替生成 0/1。第 0 折评价偶数下标，用奇数下标训练；第 1 折相反。`~` 对布尔数组取反。scores 预留 n 个位置，两轮分别填回各自 test。

这里交替分折没有再洗牌；原 x、分组、噪声是随机生成，固定下标分折与它们的抽样独立。评价折的 y 不参与训练其自身 nuisance。

## 8. 分别拟合两个处理臂的结果回归

`power=2` 用于 quadratic_known 和 logistic_fitted，其余拟合模式 power=1。`features=column_stack([x**k for k in range(power+1)])`。

power=2 时每行 `[1,x,x**2]`，power=1 时 `[1,x]`。第一个 1 用于截距。对 arm=0/1，`use=train&(a==arm)` 同时满足训练折和该分组。

```python
if use.sum() < power+2:
    raise ValueError('arm_minimum')
coef = np.linalg.lstsq(features[use], y[use], rcond=None)[0]
fitted.append(features[test] @ coef)
```

`lstsq` 返回最小二乘解及其他诊断，`[0]` 只取回归系数。拟合后对 test 所有人的 X 预测该 arm 的结果。这样得到 m0、m1，即使 test 中某人实际在另一臂，也能预测其条件均值。

组内最少数据要求随 power 改变：线性需至少 3，二次至少 4。弱处理概率 .1、n=100、两折训练时很容易不足；这正是失败记录的来源之一。

## 9. logistic propensity 怎样迭代

logistic_fitted 用 `z=[1,x]`，intercept_misspecified 用常数列。beta 初始 0，循环最多 30 次：预测 pp=sigmoid(z_train@beta)；构造 Hessian `z.T@(z*(pp*(1-pp))[:,None])+1e-6*I`；用 solve 求更新 step；beta+=step，步长范数很小则停止。

`[:,None]` 把每人的方差因子变成列，以便乘每行 z。`1e-6*I` 是数值稳定小正则。test 概率 clip 到 [.1,.9]，防止 AIPW 分母极小。线性/二次 known 模式直接用已知 p，不拟合 propensity。

两臂结果回归和 propensity 都准备好后，将 `m1-m0+a*(y-m1)/pp-(1-a)*(y-m0)/(1-pp)` 写到 test 位置。第二折完成才返回整条 scores。

## 10. nuisance 偏差界和失败怎样留痕

每个源 score 的均值与 SD/sqrt(n) 写回 ExperimentData，然后整个八源 archive 调 ATLAS。每个源误差先放 pending_effects。只有八源全部成功才将它们 extend 到 effects；中途失败时前面已完成源放 partial_effects，不混进完整 archive 的准确度统计。

四个输出：`nuisance_records.csv` 迁移任务；`nuisance_effect_records.csv` 完整档案中的源效应；`nuisance_failures.csv` 失败；`nuisance_failed_partial_effects.csv` 失败档案中已经算出的部分源。

known propensity 分支的零偏差界有随机化/正确概率与 cross-fitting 的背景；logistic fitted 和 intercept 仍把 nuisance_bias_bound 置 0，记录 `bias_bound_status='uncertified_zero_plugin'`。这是诊断实现，不能宣称获得了估计 nuisance 误差的有效有限样本界。

附录 `app_b_nuisance.tex` 的 RMSE 和 coverage 来自 experiment-level 的 `nuisance_effect_summary`，不是迁移误差。完成数来自 `nuisance_summary`。小样本 weak 二次模式仅剩两套完整 archive，表里不将它们的准确度当作稳定结论。需要同时解释失败率。

## 11. dependence：显式加入源效应相关性

`sigma=.36*((1-corr)*eye(8)+corr*ones((8,8)))`。对角线恒 .36，故每源 SE=.6；非对角线=.36*rho。rho 取 0/.3/.7。

`rng.multivariate_normal(zeros(8),sigma)` 一次抽八维相关误差，加入各源真实效应。它是源摘要层误差模型，不是让八个基础 DGP 受试者数组自然共享个体。

跑 original 与 constant 两种曲面。constant 把源和目标真值设 0，L/H 设 1e-12、L_h=0，使几何项几乎消失，更容易暴露统计方差低估。原始曲面的大偏差界可能遮盖统计问题。

## 12. 三种方差规则保持相同点权重

ATLAS 先拟合一次取得 w，三规则只改变矩阵 mat：仅对角、已知 sigma、40 个额外独立八维误差向量的样本协方差。`rowvar=False` 表示每列一个源变量。

```python
se = np.sqrt(w @ mat @ w)
radius = bias + Z*se
```

教学例子：八源等权、rho=.7、每源 SE=.6，真实组合方差为 `.36*(.3/8+.7)=.2655`；只用对角则 `.36/8=.045`。忽略正相关可能明显低估标准误。

`statistical_covered` 检查 `abs(w@errors)<=Z*se`，隔离统计分量；covered 检查总预测误差<=radius。released 另使用浓度系数半径比较 1.65。三种规则共享预测与 w，能把变化归于方差计算。

每曲面×rho 300 次、三方差规则，共 5400 行 `dependence_records.csv`。B.2 展示 constant 场景；估计协方差额外使用 40 组校准误差，这是模拟中的额外信息条件。

## 13. constants：固定预测只改变界

`constants_experiment` 场景为 nominal、severe=.8、proxy_understated。每个 300 archive。factor=.1/.25/.5/1/2 联合乘 L、H、L_h。

虽然源码在 factor 循环内部重复调用默认 fit，但每次输入和默认配置相同，得到同一权重；随后仅用不同 config 调 compute_certificate。它没有使用缩放常数重新优化权重。

记录 error 固定；released 比较新的 certificate.radius 与 1.65；covered 使用新 bias+1.96*SE；certificate_violated 比较误差与浓度半径。共 `3*300*5=4500` 行 `constant_records.csv`。

同目标随 factor 增加宽度应扩张、发布更谨慎，这是公式造成的方向；实验更关心这些宽度对应的实际覆盖以及失配时的后果。不能用覆盖最高的 factor 作为无成本数据驱动科学常数估计。

## 14. nominal 历史校准为何依赖 selection

`build_validation_v3.py` 读取 selection_predictions 中 nominal calibration 的 atlas 行，求 `abs(estimate-reference)/score` 的 95% 秩分位 q。然后取 constants 的 factor=1 行，用 `q*score` 重建 width、covered，保存 `constant_nominal_calibration_records/summary.csv`。

这不是 constants runner 自己运行时产生的文件。复现必须先有 selection 和 constants，再执行 builder。此时 c 中 released 仍来自原 factor=1 规则，builder 没有按新历史区间宽重新定义发布，解释发布条件列时应保留这一点。

## 15. 读一行 summary 的检查表

先看来自哪一个 `_records`，再看 groupby keys，再确认 error 的真值、covered 的区间类型、released 的规则，最后看 replications 与失败数。同叫 coverage 的列可以分别是源效应区间、迁移区间或纯统计部分区间；这三种不能互相代替。
