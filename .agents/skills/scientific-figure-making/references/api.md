# API Reference

Use a semantic publication palette and consistent matplotlib style.

```python
PALETTE = {
    "blue_main": "#0F4D92",
    "blue_secondary": "#3775BA",
    "green_1": "#DDF3DE", "green_2": "#AADCA9", "green_3": "#8BCF8B",
    "red_1": "#F6CFCB", "red_2": "#E9A6A1", "red_strong": "#B64342",
    "neutral": "#CFCECE", "highlight": "#FFD700",
    "teal": "#42949E", "violet": "#9A4D8E",
}
```

Recommended conceptual helpers: `apply_publication_style`, `create_subplots`, `finalize_figure`, `make_grouped_bar`, `annotate_bars`, `make_trend`, `make_heatmap`, and `make_scatter`.

Validate dimensions and lengths before plotting. Save under stable project figure paths. Prefer vector formats for paper figures and 300 DPI or higher for raster exports.
