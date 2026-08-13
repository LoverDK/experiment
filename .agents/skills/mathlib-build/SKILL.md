---
name: mathlib-build
description: Building Mathlib
---

# Building Mathlib

Fetch the Mathlib olean cache before build:

```bash
lake exe cache get
```

Use `lake exe cache get!` to force re-download if corrupt.

Build with reduced verbosity:

```bash
lake build -q --log-level=info
```

For small fixes build only affected files. For a thorough build, use `lake build Mathlib MathlibTest Archive Counterexamples && lake exe runLinter`.
