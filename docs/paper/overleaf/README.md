# Compiled Overleaf snapshot

This directory contains the final paper-01 source and its 53-page PDF from
Overleaf project `6a3410d137fc160e82dd884e`, archived on 2026-09-06.
It is the authoritative delivery snapshot for this revision.

Set `01_causal_atlas_bridge.tex` as the main document and select XeLaTeX.
The project was verified with TeX Live 2025 on Overleaf. All six referenced
figure PDFs and seventeen table inputs are included under
`experiments/causal_atlas_bridge/figures/` and `tables/`.

For an installation with the required LaTeX packages, compile from this
directory:

```sh
latexmk -xelatex -interaction=nonstopmode -halt-on-error 01_causal_atlas_bridge.tex
```

The compile log and protected-text audit are in `../revision_evidence/`.
The experimental changes, provenance, and validation details are recorded in
`../overleaf_revision_20260906.md`. Figure generators and saved numerical
results remain in the repository's `src/`, `scripts/`, and `results/` trees.
