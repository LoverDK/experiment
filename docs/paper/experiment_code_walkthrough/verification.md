# 本次导读的验证记录

日期：2026-09-07。此记录只验证本目录新增的代码导读和教学脚本；没有重跑论文规模的随机实验、重建论文图表或编译 Overleaf。

## 已执行的检查

1. 对 `examples/inspect_one_archive.py` 和 `examples/trace_saved_results.py` 运行 `python -m py_compile`，两份教学脚本均可被 Python 解析。
2. 运行 `inspect_one_archive.py`。脚本生成一个固定种子的合成 archive，确认其包含 8 个源实验、每个源实验有 400 个单位和 4 维公开表示；重算首个源实验的 AIPW 估计 `-0.838615` 和标准误 `0.095755`，并核对 simplex 权重、原始点估计及五项证书之和。随后以 `scientific_tolerance=0` 走入部分识别分支，核对区间 `[-2.056888, 2.248484]` 的交集端点且真值在其中。脚本不写文件。
3. 运行 `trace_saved_results.py`。脚本从已保存 CSV 重算并核对主文合成结果：300 个目标中 139 个发布，发布 MAE 为 `0.110919`，所有目标的 ATLAS 无拒绝 MAE 为 `0.138699`。它还核对 v2 名义 ridge 配对差 `0.002479`（MCSE `0.001483`）、v3 moderate 50% 的三种排序 MAE、机制和 nuisance 汇总、相关性/常数分组、NSW 半合成的聚类 MCSE、112 个有效加 8 个失败的 NSW 设计、Hillstrom 的无限宽 95% LOO 规则及 retained bridge 的 72 项检查。脚本不写文件。
4. 检查本目录 Markdown 中的相对链接、教学脚本中的仓库相对路径和所指向文件都存在。
5. 运行 `git diff --check`，检查本次文本改动没有空白字符错误。
6. 运行 `python -m unittest discover -s tests -v`：95 项中 94 项通过。唯一失败是文件索引测试发现用户未跟踪的 `results/appendix_b_build/` 下 10 个临时编译文件尚未列入维护表；新增导读文件本身均已列入，其他实验和代码测试通过。

## 检查边界

两份脚本使用已有结果，所以验证的是“文档对实现和保存口径的描述能被实际数据复算”，并不重新验证随机模拟本身。论文的历史编译状态、54 页和零错误/警告的证据位于 `docs/paper/revision_evidence/appendix_B_overleaf_compile_dom.txt`；本次未改动 `.tex`，也没有重新声称线上编译。

仓库完整测试命令是：

```powershell
python -m unittest discover -s tests -v
```

其中 `test_repository_file_map.py` 还会检查未忽略的未跟踪文件。因此在工作区存在用户临时材料时，完整文件索引测试可能报告这些材料没有列入受 Git 跟踪的维护表。本次会将新增导读文件加入 `docs/reference/repository_file_map.md`，但不会删除、暂存或改写用户的临时文件。
