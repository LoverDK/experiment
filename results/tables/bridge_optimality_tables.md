# Bridge greedy 与小规模穷举最优

在严重支持失配场景中，候选库固定为 12 个，分别枚举预算 1、2、3 的所有
组合。穷举最优使用已经观测到的 bridge 结果，故只能作为事后评价基准；
causal greedy 仍按照 Algorithm 1 的公开信息约束选择。这个实验不估计弱次模
参数，也不证明 Theorem 5.6 的近似系数。

| budget | repetitions | exhaustive sets | greedy final diameter | optimal final diameter | greedy/optimal value | same-set rate |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 30 | 12 | 2.6933 | 2.6763 | 0.9957 | 0.6667 |
| 2 | 30 | 66 | 2.1307 | 2.0284 | 0.9776 | 0.3333 |
| 3 | 30 | 220 | 1.9323 | 1.8647 | 0.9857 | 0.4333 |
