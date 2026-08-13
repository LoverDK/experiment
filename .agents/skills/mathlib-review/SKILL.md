---
name: mathlib-review
description: Review guidelines for Mathlib PRs. Use when reviewing pull requests, checking code quality, or assessing whether a PR is ready to merge.
---

# Mathlib PR Review

## Attributes and API

- New definitions should come with associated lemmas and appropriate attributes (`@[simp]`, `@[ext]`, etc.).
- Watch for instance diamonds.
- Prefer bundled morphisms, `FunLike` API for morphism classes, `SetLike` API for subobject classes.

## Style Points

- Do not squeeze terminal `simp` unless there is a measured performance problem.
- Prefer established normal forms.
- Needing `erw`, or `rfl` after `simp`/`rw`, usually indicates missing API lemmas.
- Consider splitting files over ~1000 lines or with multiple topics.
