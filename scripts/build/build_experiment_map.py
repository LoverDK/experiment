"""Build a visual map of the Causal ATLAS experiments and paper assets."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/paper/experiment_code_walkthrough/figures"
INK, MUTED = "#1F2933", "#5B6570"
BLUE, TEAL, GOLD, GREEN = "#0F4D92", "#2F7F86", "#A56800", "#3F7F52"
BLUE_LIGHT, TEAL_LIGHT, GOLD_LIGHT, GREEN_LIGHT = "#E8F0FA", "#E7F4F3", "#FFF4D6", "#EAF5EC"


def box(ax, x, y, w, h, text, face, edge, *, size=7.5, bold=False, center=False):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, transform=ax.transAxes, clip_on=False,
        boxstyle="round,pad=0.012,rounding_size=0.018",
        linewidth=1.15, edgecolor=edge, facecolor=face,
    ))
    ax.text(x + (w / 2 if center else 0.014), y + h / 2, text,
            transform=ax.transAxes, ha="center" if center else "left", va="center",
            color=INK, fontsize=size, fontweight="bold" if bold else "normal", linespacing=1.15)


def arrow(ax, a, b, color, rad=0.0):
    ax.add_patch(FancyArrowPatch(a, b, transform=ax.transAxes, arrowstyle="-|>",
                                 mutation_scale=8, linewidth=1.05, color=color,
                                 connectionstyle=f"arc3,rad={rad}", shrinkA=3, shrinkB=3))


def main():
    plt.rcParams.update({"font.family": "DejaVu Sans", "pdf.fonttype": 42,
                         "svg.fonttype": "none", "savefig.facecolor": "white"})
    fig, ax = plt.subplots(figsize=(22, 16), dpi=180)
    ax.set_axis_off()
    ax.text(0.02, 0.975, "Causal ATLAS experiment map: from question to evidence",
            transform=ax.transAxes, fontsize=19, fontweight="bold", color=INK, va="top")
    ax.text(0.02, 0.948, "Left to right: research question -> experiment block -> paper display -> bounded interpretation.",
            transform=ax.transAxes, fontsize=9.5, color=MUTED, va="top")
    columns = [(0.02, 0.18, "Research question", BLUE), (0.235, 0.31, "Experiment block", TEAL),
               (0.565, 0.28, "Paper display", GOLD), (0.865, 0.115, "What it establishes", GREEN)]
    for x, w, label, color in columns:
        ax.text(x, 0.915, label, transform=ax.transAxes, fontsize=10.5,
                fontweight="bold", color=color, va="bottom")
        ax.plot([x, x + w], [0.908, 0.908], transform=ax.transAxes, color=color, lw=2.2)

    questions = [(0.80, "Q1  Can causal support improve composition over semantic similarity?"),
                 (0.67, "Q2  When should the method release, reject, or widen uncertainty?"),
                 (0.54, "Q3  What can be learned after rejection, and which bridge is useful?"),
                 (0.39, "Q4  Do conclusions survive nuisance, dependence, and representation stress?"),
                 (0.21, "Q5  How does the workflow behave on randomized real-data settings?")]
    for y, text in questions:
        box(ax, 0.02, y, 0.18, 0.085, text, BLUE_LIGHT, BLUE, size=8.1, bold=True)

    blocks = [(0.825, "E1  Setup and controlled DGP\n8 source experiments; known truth; AIPW; fixed seeds\n[B.1 protocol]"),
              (0.715, "E2  Certified composition\nATLAS, no-rejection, semantic, nearest, global mean, latent oracle\n[Main synthetic]"),
              (0.605, "E3  Selective release and intervals\nRisk--coverage, calibration, certificate components\n[Main uncertainty]"),
              (0.495, "E4  Rejection, PI, minimax\nSupport deterioration; interval intersection; two-point checks\n[PI evidence]"),
              (0.385, "E5  Bridge design\nCausal greedy, semantic greedy, random, exhaustive benchmark\n[Bridge evidence]"),
              (0.275, "E6  Comparators and selection audit\nRidge, RBF, IVW, nearest; equal release fractions; ablations\n[B.3 audit]"),
              (0.165, "E7  Robustness and failure boundaries\nSurfaces, nuisance, overlap, dependence, constants, calibration\n[B.2 stress]"),
              (0.055, "E8  NSW and Hillstrom stability\nReal reconstruction, disjoint references, semisynthetic truth, cell LOO\n[B.4 stability]")]
    for y, text in blocks:
        box(ax, 0.235, y, 0.31, 0.095, text, TEAL_LIGHT, TEAL, size=7.4, bold=True)

    assets = [(0.825, "FIG 2  Synthetic validation\nTable 1  Main synthetic\napp_formal_nominal / stress_a / stress_b\napp_representation_grid"),
              (0.715, "FIG 3  Selective uncertainty\napp_risk_coverage\napp_calibration_levels\napp_certificate_components\napp_failure_boundary"),
              (0.605, "FIG 4  Rejection and bridge\nTable 2  Main partial ID\napp_partial_id_full\napp_minimax\napp_bridge_all_scenarios / optimality"),
              (0.495, "app_b_surfaces\napp_b_nuisance\napp_b_dependence\napp_b_constants\napp_b_calibration"),
              (0.385, "app_b_selection\napp_b_ablation\napp_paired_comparison\napp_stronger_baselines\napp_stronger_paired"),
              (0.275, "FIG 5  NSW reconstruction\nTable 3  Main NSW\napp_nsw_construction / seedwise\napp_nsw_reference / calibration\napp_nsw_semisynthetic"),
              (0.165, "app_b_nsw_stability\napp_b_hillstrom_error\napp_b_hillstrom_interval\nextension_nsw_validation.pdf"),
              (0.055, "app_bridge_retained\napp_b_bridge_retained\nbridge_checks_8192\noperational monotonicity stays in repository")]
    for y, text in assets:
        box(ax, 0.565, y, 0.28, 0.095, text, GOLD_LIGHT, GOLD, size=7.15)

    claims = [(0.825, "Representation and\ncomposition claim"), (0.715, "Selective risk and\nhonest uncertainty"),
              (0.605, "Rejection widens the\nidentified set; bridge\nshrinks it"), (0.495, "Assumptions define the\nvalidity boundary"),
              (0.385, "Accuracy depends on\ninformation access"), (0.275, "Real-data evidence is\ndescriptive and noisy"),
              (0.165, "Stability varies with\ndesign choices"), (0.055, "Bridge diagnostic is\nconditional on its\nfixed-law objective")]
    for y, text in claims:
        box(ax, 0.865, y, 0.115, 0.095, text, GREEN_LIGHT, GREEN, size=7.25, bold=True, center=True)

    for yq, yb in [(0.80, 0.825), (0.67, 0.715), (0.54, 0.605), (0.54, 0.495),
                   (0.54, 0.385), (0.39, 0.275), (0.39, 0.165), (0.21, 0.055)]:
        arrow(ax, (0.20, yq + 0.04), (0.235, yb + 0.047), BLUE)
    for y in [0.825, 0.715, 0.605, 0.495, 0.385, 0.275, 0.165, 0.055]:
        arrow(ax, (0.545, y + 0.047), (0.565, y + 0.047), TEAL)
        arrow(ax, (0.845, y + 0.047), (0.865, y + 0.047), GOLD)
    ax.text(0.02, 0.018, "Blue = question   Teal = experiment   Gold = display or archived table   Green = interpretation",
            transform=ax.transAxes, fontsize=8.2, color=MUTED, va="bottom")
    ax.text(0.98, 0.018, "Names are repository basenames; app_* denotes appendix assets.",
            transform=ax.transAxes, fontsize=8.2, color=MUTED, va="bottom", ha="right")
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / "causal_atlas_experiment_map.png", dpi=300, bbox_inches="tight", pad_inches=0.12)
    fig.savefig(OUT / "causal_atlas_experiment_map.pdf", bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)
    print(OUT / "causal_atlas_experiment_map.png")
    print(OUT / "causal_atlas_experiment_map.pdf")


if __name__ == "__main__":
    main()
