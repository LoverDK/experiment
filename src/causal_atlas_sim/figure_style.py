"""Small publication-style layer shared by paper figure builders."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


PALETTE = {
    "blue_main": "#0F4D92",
    "blue_secondary": "#3775BA",
    "green": "#4F9D69",
    "green_light": "#AADCA9",
    "red": "#B64342",
    "red_light": "#E9A6A1",
    "neutral": "#767676",
    "neutral_light": "#CFCECE",
    "teal": "#42949E",
    "violet": "#9A4D8E",
    "gold": "#C58A00",
}


@dataclass(frozen=True)
class FigureStyle:
    font_size: int = 11
    axes_linewidth: float = 1.4


def apply_publication_style(style: FigureStyle | None = None) -> None:
    style = style or FigureStyle()
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": style.font_size,
            "axes.linewidth": style.axes_linewidth,
            "axes.spines.right": False,
            "axes.spines.top": False,
            "legend.frameon": False,
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "savefig.facecolor": "white",
        }
    )


def finalize_figure(
    fig,
    output_base: Path,
    *,
    formats: Iterable[str] = ("png", "pdf"),
    dpi: int = 300,
) -> tuple[Path, ...]:
    output_base = Path(output_base)
    output_base.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(pad=1.2)
    saved = []
    for extension in formats:
        path = output_base.with_suffix(f".{extension}")
        fig.savefig(path, dpi=dpi, bbox_inches="tight", pad_inches=0.06)
        saved.append(path)
    plt.close(fig)
    return tuple(saved)
