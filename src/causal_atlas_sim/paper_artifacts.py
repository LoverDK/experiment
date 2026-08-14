"""Paper-facing results artifacts derived from committed simulation tables."""

from __future__ import annotations

from .reporting import ResultBundle


_NOMINAL_METHODS = (
    "atlas",
    "atlas_no_rejection",
    "atlas_no_variance_penalty",
    "atlas_top4_candidates",
    "semantic_forced",
    "nearest_semantic",
    "global_mean",
)

_METHOD_LABELS = {
    "atlas": "Causal ATLAS",
    "atlas_no_rejection": "ATLAS without rejection",
    "atlas_no_variance_penalty": "ATLAS without variance penalty",
    "atlas_top4_candidates": "ATLAS with top-4 candidates",
    "semantic_forced": "Semantic forced composition",
    "nearest_semantic": "Nearest semantic neighbor",
    "global_mean": "Global mean",
}

_STRESS_SCENARIOS = (
    "strong_semantic_mismatch",
    "severe_semantic_mismatch",
)

_SCENARIO_LABELS = {
    "strong_semantic_mismatch": "Strong mismatch",
    "severe_semantic_mismatch": "Severe mismatch",
}

_POLICIES = (
    "certified_atlas",
    "no_rejection",
    "understated_smoothness",
)

_POLICY_LABELS = {
    "certified_atlas": "Certified ATLAS",
    "no_rejection": "No rejection",
    "understated_smoothness": "Understated bounds",
}


def render_paper_results_section(bundle: ResultBundle) -> str:
    """Render a Chinese, paper-facing discussion linked to saved figures."""

    nominal = _formal_row(bundle, "nominal", "atlas")
    no_rejection = _formal_row(bundle, "nominal", "atlas_no_rejection")
    semantic_baseline = _formal_row(bundle, "nominal", "semantic_forced")
    nearest_baseline = _formal_row(bundle, "nominal", "nearest_semantic")
    mismatch = _formal_row(bundle, "semantic_mismatch_025", "atlas")
    hidden = _formal_row(bundle, "hidden_radius_040", "atlas")
    strong_certified = _calibration_row(
        bundle, "strong_semantic_mismatch", "certified_atlas"
    )
    strong_no_rejection = _calibration_row(
        bundle, "strong_semantic_mismatch", "no_rejection"
    )
    severe_understated = _calibration_row(
        bundle, "severe_semantic_mismatch", "understated_smoothness"
    )
    partial_severe = next(
        row
        for row in bundle.partial_identification_rows
        if row["scenario_key"] == "severe_mismatch"
    )
    bridge_severe = next(
        row
        for row in bundle.bridge_rows
        if row["scenario_key"] == "severe"
        and row["policy_key"] == "causal_greedy"
    )
    risk_nominal = _find_one(bundle.risk_coverage_rows, threshold="1.65")
    risk_relaxed = _find_one(bundle.risk_coverage_rows, threshold="2.0")
    risk_no_rejection = _find_one(bundle.risk_coverage_rows, threshold="inf")
    curve_low = _find_one(
        bundle.calibration_curve_rows,
        confidence_level="0.8",
        policy="honest_atlas",
    )
    curve_high = _find_one(
        bundle.calibration_curve_rows,
        confidence_level="0.975",
        policy="honest_atlas",
    )
    bridge_optimality = [
        _find_one(bundle.bridge_optimality_rows, budget=budget)
        for budget in ("1", "2", "3")
    ]

    lines = [
        "# 论文实验结果写作稿",
        "",
        "本文件由已提交的结果 CSV 自动生成，供论文的仿真实验章节直接改写和引用。",
        "数值均保留四位小数；不重新运行仿真，也不读取目标实验的真实效应。",
        "",
        "## 实验设计与报告原则",
        "",
        "所有实验使用满足 Assumption 3.1--3.5 的最小数据生成机制。正式基准实验",
        "按论文 Algorithm 1 的统一入口运行：接受时报告 Corollary 5.2 区间，拒绝时",
        "才进入 Theorem 5.4 部分识别和 Definition 5.2 bridge 设计。",
        "包含 6 个预先定义的情景、3 个独立基准种子，以及每个种子 100 次重复。",
        "对每个 target，所有比较方法共享同一份 archive-target 抽样；目标真值仅在",
        "方法输出后用于评价。可拒绝方法同时报告发布率和已发布点上的误差，避免把拒绝",
        "当作无代价的性能提升。",
        "",
        "## 主结果：受控参数扫描",
        "",
        "![主实验参数扫描](../../results/figures/main_experiment_mae.png)",
        "",
        "图 1 展示四个单因素扫描中的已发布点 MAE。随着语义失配从 0 增至 0.25，",
        f"Causal ATLAS 的发布率从 {_f(_main_row(bundle, 'semantic_shift_fraction', '0.0'), 'acceptance_rate')} "
        f"降至 {_f(_main_row(bundle, 'semantic_shift_fraction', '0.25'), 'acceptance_rate')}，"
        "而已发布点 MAE 仍保持在较低水平。样本量从 100 增至 1000 时，发布率从 "
        f"{_f(_main_row(bundle, 'sample_size', '100.0'), 'acceptance_rate')} 升至 "
        f"{_f(_main_row(bundle, 'sample_size', '1000.0'), 'acceptance_rate')}。"
        "这与证书半径随统计与表征不确定性变化而调整的设计一致。",
        "",
        "## 正式多种子比较与消融",
        "",
        "![正式多种子基准与消融](../../results/figures/formal_experiment_overview.png)",
        "",
        "在名义情景中，Causal ATLAS 的发布率为 "
        f"{_f(nominal, 'acceptance_rate')}，已发布点 MAE 为 {_f(nominal, 'accepted_mae')}；"
        "去除拒绝规则后，所有点均被发布，MAE 上升至 "
        f"{_f(no_rejection, 'accepted_mae')}。语义强制组合和最近语义邻居的 MAE 分别为 "
        f"{_f(semantic_baseline, 'accepted_mae')} 与 {_f(nearest_baseline, 'accepted_mae')}，"
        "说明仅使用语义距离不足以替代设计兼容性和证书筛选。"
        "在语义失配 0.25 时，ATLAS 发布率为 "
        f"{_f(mismatch, 'acceptance_rate')}；当隐藏调节不确定性半径为 0.40 时，"
        f"发布率为 {_f(hidden, 'acceptance_rate')}，即方法对证据不足的 target 选择拒绝。",
        "",
        "## 证书校准与失效边界",
        "",
        "![证书校准与失效边界](../../results/figures/calibration_experiment_overview.png)",
        "",
        "在强语义失配下，正确证书的 ATLAS 仅发布 "
        f"{_f(strong_certified, 'release_rate')} 的点，已发布区间覆盖率为 "
        f"{_f(strong_certified, 'released_interval_coverage')}。相同场景下，"
        "无拒绝策略发布全部点，其中 "
        f"{_f(strong_no_rejection, 'released_above_tolerance_rate')} 的点的证书半径超过科学容忍度。"
        "作为故意违反理论前提的反例，严重失配且低报平滑界时，发布区间覆盖率降至 "
        f"{_f(severe_understated, 'released_interval_coverage')}。"
        "因此，这个边界实验支持的结论是：证书有用的前提是其上界确实有效，"
        "而不是任何数值化的置信区间都会自动保证可靠发布。",
        "",
        "## Risk--coverage 与 coverage--width",
        "",
        "![Risk--coverage frontier](../../results/figures/risk_coverage_curve.png)",
        "",
        "风险--覆盖率曲线在同一批 target 上同时报告发布率与已发布点条件 MAE。"
        f"阈值 1.65 时发布率为 {_f(risk_nominal, 'acceptance_rate')}、条件 MAE 为 "
        f"{_f(risk_nominal, 'conditional_mae')}；将阈值放宽到 2.00 时，"
        f"发布率升至 {_f(risk_relaxed, 'acceptance_rate')}、条件 MAE 为 "
        f"{_f(risk_relaxed, 'conditional_mae')}；无拒绝端点的 MAE 为 "
        f"{_f(risk_no_rejection, 'conditional_mae')}。",
        "",
        "![Coverage--width calibration](../../results/figures/calibration_curve.png)",
        "",
        "正确证书的经验覆盖率在 0.80--0.975 名义水平下均为 1.0000，但平均宽度约为 "
        f"{_f(curve_low, 'mean_width')}--{_f(curve_high, 'mean_width')}；"
        "因此覆盖率和区间宽度必须联合报告。",
        "",
        "## 拒绝后的部分识别与 bridge",
        "",
        "严重失配时，ATLAS 拒绝率为 "
        f"{_f(partial_severe, 'rejection_rate')}，拒绝分支的平均 Theorem 5.4 "
        f"区间宽度为 {_f(partial_severe, 'mean_partial_id_width_on_rejected')}，"
        f"覆盖率为 {_f(partial_severe, 'partial_id_coverage_on_rejected')}。"
        "在 Definition 5.2 bridge 实验中，完整因果 greedy 把平均直径从 "
        f"{_f(bridge_severe, 'mean_initial_diameter')} 降至 "
        f"{_f(bridge_severe, 'mean_final_diameter')}，缩减 "
        f"{_f(bridge_severe, 'shrinkage_fraction')}，并在全部路径用满预算。",
        "小规模穷举基准中，预算 1、2、3 的 greedy/optimal bridge value 比例分别为 "
        + "、".join(
            _f(row, "greedy_to_optimal_value_ratio") for row in bridge_optimality
        )
        + "；这只是当前候选库上的事后效率比较，不是弱次模性证明。",
        "",
        "## 可引用结论与限制",
        "",
        "当前结果支持：在这个满足理论假设的合成 DGP 中，拒绝机制会优先保留较低误差的",
        "点预测，并在高不确定性区域减少发布；完整证书在预设情景下保持保守覆盖。",
        "它们不支持对真实世界的泛化结论，也不能说明当前区间宽度最优。真实数据应用仍需",
        "单独处理表征误差、设计不兼容和 nuisance estimation 误差。NSW 阶段是 real-data",
        "reconstruction stress test；held-out local contrast 是带噪评价参考，不是 causal ground truth。",
        "",
        "LaTeX 表格位于 results/tables/paper_results_tables.tex，其中仅使用已保存的",
        "正式多种子、失效边界和新增 risk--coverage/校准结果。",
    ]
    return "\n".join(lines) + "\n"


def render_paper_results_tables(bundle: ResultBundle) -> str:
    """Render two LaTeX tables from the formal and calibration result tables."""

    nominal_rows = [
        _formal_row(bundle, "nominal", method) for method in _NOMINAL_METHODS
    ]
    stress_rows = [
        _calibration_row(bundle, scenario, policy)
        for scenario in _STRESS_SCENARIOS
        for policy in _POLICIES
    ]
    lines = [
        "% Generated by scripts/build/build_paper_artifacts.py; do not edit by hand.",
        "% Requires: \\usepackage{booktabs}",
        "",
        "\\begin{table}[t]",
        "\\centering",
        "\\caption{Nominal multi-seed benchmark (three seeds, 100 repetitions per seed).}",
        "\\label{tab:causal-atlas-nominal}",
        "\\begin{tabular}{lrrrrr}",
        "\\toprule",
        "Method & Release & MAE & RMSE & Coverage & Width \\\\",
        "\\midrule",
        *[
            f"{_METHOD_LABELS[row['estimator_key']]} & "
            f"{_f(row, 'acceptance_rate')} & {_f(row, 'accepted_mae')} & "
            f"{_f(row, 'accepted_rmse')} & {_f(row, 'interval_coverage')} & "
            f"{_f(row, 'mean_interval_width')} \\\\"
            for row in nominal_rows
        ],
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{table}",
        "",
        "\\begin{table}[t]",
        "\\centering",
        "\\caption{Failure-boundary comparison under semantic mismatch.}",
        "\\label{tab:causal-atlas-failure-boundary}",
        "\\begin{tabular}{llrrrr}",
        "\\toprule",
        "Scenario & Policy & Release & Released MAE & Coverage & Above tolerance \\\\",
        "\\midrule",
        *[
            f"{_SCENARIO_LABELS[row['scenario_key']]} & "
            f"{_POLICY_LABELS[row['policy_key']]} & "
            f"{_f(row, 'release_rate')} & {_f(row, 'released_mae')} & "
            f"{_f(row, 'released_interval_coverage')} & "
            f"{_f(row, 'released_above_tolerance_rate')} \\\\"
            for row in stress_rows
        ],
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{table}",
        "",
    ]
    return "\n".join(lines)


def _formal_row(
    bundle: ResultBundle, scenario_key: str, estimator_key: str
) -> dict[str, str]:
    return _find_one(
        bundle.formal_rows,
        scenario_key=scenario_key,
        estimator_key=estimator_key,
    )


def _calibration_row(
    bundle: ResultBundle, scenario_key: str, policy_key: str
) -> dict[str, str]:
    return _find_one(
        bundle.calibration_rows,
        scenario_key=scenario_key,
        policy_key=policy_key,
    )


def _main_row(
    bundle: ResultBundle, sweep_key: str, level: str
) -> dict[str, str]:
    return _find_one(
        bundle.main_rows,
        sweep_key=sweep_key,
        level=level,
        method="atlas",
    )


def _find_one(
    rows: tuple[dict[str, str], ...], **criteria: str
) -> dict[str, str]:
    matches = [
        row
        for row in rows
        if all(row.get(field) == expected for field, expected in criteria.items())
    ]
    if len(matches) != 1:
        raise ValueError(f"Expected one result row for {criteria}, found {len(matches)}.")
    return matches[0]


def _f(row: dict[str, str], field: str) -> str:
    value = row.get(field, "")
    return "NA" if value == "" else f"{float(value):.4f}"
