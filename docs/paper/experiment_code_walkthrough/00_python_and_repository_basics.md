# 00：先学会读这份仓库里的 Python

本章围绕实际入口 [run_main_experiment.py](../../../scripts/run/run_main_experiment.py) 和 [run_validation_v3.py](../../../scripts/run/run_validation_v3.py) 讲语法。你暂时不需要安装编辑器插件，也不需要理解机器学习框架。

## 1. 在哪里输入命令

Windows PowerShell 中：

```powershell
Set-Location 'D:\study\zzh科研\experiment'
python --version
python scripts/run/run_main_experiment.py
```

第一行切换当前目录。第二行显示解释器版本。第三行让 Python 从指定文件顶部往下执行。第三行会运行正式规模实验并覆盖对应输出，初学时先读第 10 章的小例子。

相对路径 `scripts/run/...` 从当前目录出发。文件名里的 `/` 在这里也可以用于 Windows。终端里敲的是 PowerShell 命令；`.py` 文件里写的是 Python 代码，两者不能直接混写。

## 2. 入口顶部的代码究竟干什么

源码：

```python
from pathlib import Path
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
from causal_atlas_sim.experiments import MainExperimentConfig, run_main_experiment
```

逐句理解：

- `from pathlib import Path`：从 Python 自带的 `pathlib` 模块取出路径类 `Path`。
- `import sys`：取得 Python 运行环境的信息与设置。
- `__file__`：当前脚本自身的文件路径。
- `.resolve()`：把路径解析成绝对路径。
- `.parents[0]` 是 `scripts/run`，`[1]` 是 `scripts`，`[2]` 是仓库根目录。Python 下标从 0 开始。
- `PROJECT_ROOT / "src"`：此处 `/` 是 Path 定义的路径拼接运算，得到仓库的 `src` 子目录。
- `str(...)`：转成普通字符串。
- `sys.path.insert(0, ...)`：把 `src` 放在模块搜索路径的第一位。
- 最后一句才从仓库代码导入配置类和实验函数。导入函数不会自动跑完整实验；调用函数才会执行它的函数体。

因此，把命令放在仓库根目录运行最清楚。入口通过自身位置找到项目，无需你把源码文件复制到 runner 旁边。

## 3. 函数、调用、返回值

源码中的核心两行：

```python
def main() -> None:
    result = run_main_experiment(MainExperimentConfig())
```

`def` 定义函数，`main` 是名称，括号里为空表示调用时不传参数。冒号后的缩进属于这个函数。`-> None` 是类型提示，表示 main 主要通过写文件或打印产生效果，没有需要交回调用者的值。

右边从内向外执行：先 `MainExperimentConfig()` 创建一份默认配置；再把配置传给 `run_main_experiment`；最后把返回对象绑定到变量 `result`。变量名是对对象的引用，不是自动生成的文件。

入口末尾：

```python
if __name__ == "__main__":
    main()
```

直接运行此脚本时，Python 把它的 `__name__` 设置成 `"__main__"`，于是调用 main。别的文件 import 这个脚本时不会进入这个条件。这使脚本既可运行，也可被测试导入。

## 4. 配置为什么是一种 class

[dgp.py](../../../src/causal_atlas_sim/dgp.py) 中有：

```python
@dataclass(frozen=True)
class SimulationConfig:
    n_archive: int = 8
    n_units_per_experiment: int = 400
```

`class` 定义一种对象类型。这里一份配置有两个示例字段，实际还有其他字段。`int` 提示整数；`= 8` 是默认值。`@dataclass` 自动生成接收这些字段的构造方法；`frozen=True` 禁止直接重新赋值字段。

教学例子：

```python
from dataclasses import replace
cfg = SimulationConfig()
small = replace(cfg, n_units_per_experiment=100)
print(cfg.n_units_per_experiment)    # 400
print(small.n_units_per_experiment)  # 100
```

`cfg.字段名` 用点号访问字段。`replace` 产生新的配置，原配置仍是 400。实验中大量使用它，是为了只改变指定因素。注意 frozen 是对字段赋值的限制，并不使字段内部的 NumPy 数组自动变成不可修改数组。

`field(default_factory=SimulationConfig)` 表示每次创建外层配置时，单独生成一份默认内层配置。`__post_init__` 在创建对象之后检查参数是否合法，抛出 `ValueError` 说明配置不符合代码要求。

## 5. 本仓库最常见的容器

| 写法 | 含义 | 实验中的用途 |
| --- | --- | --- |
| `[a, b]` | list，可追加 | 积累结果 `records` |
| `(a, b)` | tuple，固定顺序 | 源实验集合 `archive`、种子组 |
| `{"method": "atlas", "error": 0.2}` | dict，键对应值 | 一条 CSV 记录 |
| `{1, 2}` | set，不重复元素 | 已选目标 ID、集合审计 |
| `np.array([1., 2.])` | NumPy 数组 | 向量化数值计算 |
| `pd.DataFrame(rows)` | Pandas 二维表 | 多条字典变成行列 |

`records.append(one)` 增加一个元素。`records.extend(many)` 把 many 里的元素逐个加进去。若 many 有五种方法的结果，extend 加五条；append 会加一个装着五条的列表，结构就不同了。

`None` 表示没有值，常用于拒绝后的已发布点估计。`float('nan')` 表示数值缺失/无效；`float('inf')` 表示正无穷，例如有效有限样本残差排序无法产生有限半径。三者都不等于数值 0。

## 6. 数组形状是理解实验的关键

基础 DGP 中：

| 对象 | 默认形状 | 一行/一项是什么 |
| --- | --- | --- |
| `experiment.x` | `(400, 2)` | 一位受试者的两个协变量 |
| `experiment.treatment` | `(400,)` | 每人的 0/1 分组 |
| `experiment.aipw_scores` | `(400,)` | 每人的 AIPW 分数 |
| `experiment.observed_representation` | `(4,)` | 一个实验的四个表示坐标 |
| `representations` | `(8, 4)` | 每行一个源实验 |
| `weights` | `(8,)` | 每个源实验的组合权重 |

`x[:, 0]` 取所有行的第 0 列。`x[mask]` 只保留 mask 为 True 的行。`x[:, None]` 对一维向量增加一个轴，得到一列矩阵。`np.vstack` 竖直堆叠向量，`np.column_stack` 横向拼列。

`*` 对 NumPy 数组通常逐元素相乘；`@` 是矩阵乘法。例如 `(8,) @ (8,4)` 得到 `(4,)`，正是加权平均后的实验表示。`weights**2` 把每个权重平方。`np.sum` 求和，`np.mean` 求平均，`np.linalg.norm` 默认求欧氏长度。

教学手算：

```python
weights = np.array([0.25, 0.75])
effects = np.array([1.0, 3.0])
print(weights @ effects)  # 0.25*1 + 0.75*3 = 2.5
```

## 7. 循环如何变成很多次实验

源码经常是：

```python
for replicate, sequence in enumerate(seed_sequences):
    seed = int(sequence.generate_state(1, dtype=np.uint32)[0])
    generated = generate_minimal_archive(dgp_config, seed=seed)
    for estimator in config.estimators:
        ...
```

外层每走一次，生成一套新的 archive 和 target。`enumerate` 同时给编号和对象，首个编号是 0。内层把所有方法应用于同一套数据。不能把内层每种方法当成新的独立数据重复。对同一目标比较两种方法时，应配对计算差值。

`[e.estimated_effect for e in archive]` 是列表推导式。等价展开：

```python
values = []
for e in archive:
    values.append(e.estimated_effect)
```

`zip(weights, archive, strict=True)` 并排取权重和源对象，长度不同会报错。`for _ in range(100)` 中 `_` 表示此次编号不用到；range(100) 是 0 到 99，共 100 次。

字典展开 `dict(seed=sd, **v)` 把字典 v 的键值加入新字典。函数调用里的 `SimulationConfig(**settings)` 把 settings 当作具名参数。`lambda item: item[0]` 是小型匿名函数，这里作为排序依据。

## 8. 随机种子究竟固定了什么

`np.random.default_rng(seed)` 创建随机数生成器。相同软件实现、相同 seed、相同调用顺序，才会得到相同随机序列。增加一次随机抽样可能使后续抽样整体移动。

`SeedSequence(...).spawn(k)` 创建 k 个子随机流，源实验和目标数据可使用分开的子流。v3 使用 `[基础种子, block, scenario, replicate]` 编码生成种子，使不同任务可分别重跑。种子不是日历日期，即使形如 20260841 也只是合法整数。

同一个 seed 在不同协议中不自动表示相同数据：DGP 参数、随机调用顺序、样本量都可能不同。

## 9. 代码怎样写出 CSV

原 runner 采用标准库：

```python
with output_path.open("w", newline="", encoding="utf-8") as output:
    writer = csv.DictWriter(output, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
```

`with` 在块结束时关闭文件。`"w"` 会覆盖旧文件。`fieldnames` 从第一条字典取列名，所以 rows 不能为空。writeheader 写表头，writerows 写每条记录。`newline=""` 避免 Windows 下多余空行。

v3 更短：`pd.DataFrame(rows).to_csv(path, index=False)`。`index=False` 不写 Pandas 自己的行号。读取标准库 CSV 时字段通常是字符串，`"False"` 直接用 bool 转换会得到 True，因为它是非空字符串；绘图器因此单独使用 `_boolean`。

## 10. 错误、测试、元数据

`try` 运行代码；`except` 接住特定异常；`finally` 无论成功失败都执行。v3 runner 在 finally 写 metadata，所以失败运行也应留下状态与耗时。不要仅凭 metadata 文件存在判断成功，要读 `status`。

`assert` 检查某个条件，不满足则停止。测试通过说明测试所覆盖的代码行为符合预期；它不是数学定理的证明，也不说明合成实验能覆盖所有真实场景。

下一章从一个随机种子开始，逐行追踪真正的数据生成过程。
