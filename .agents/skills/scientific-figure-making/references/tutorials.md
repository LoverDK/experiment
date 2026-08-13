# Tutorials: End-to-End Publication Figures

Implement/adapt publication helpers in project code. Use `matplotlib.use("Agg")` for unattended scripts when appropriate and finish with stable PDF/SVG/PNG exports.

## Grouped bar chart

Use shared categories, aligned series, a restrained semantic palette, readable labels, and y-limits that reveal meaningful differences without misleading scale choices. Export at publication quality.

## Multi-panel trend with shared legend

Keep panel styling consistent. When legends are large, dedicate a subplot to the legend instead of covering data. Use uncertainty bands where justified.

## Heatmap

Prepare a 2D matrix with clear row/column labels and a colorbar. Choose a perceptually appropriate colormap and export at publication quality.

For other chart types, follow `demos.md`, `common-patterns.md`, and `design-theory.md`.
