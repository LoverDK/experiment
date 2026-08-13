---
name: mathlib-pr
description: PR conventions for leanprover-community/mathlib4. Use when creating pull requests, writing commit messages, or managing labels for Mathlib contributions.
---

# Mathlib PR Conventions

PR titles follow `<type>(<scope>): <subject>` with standard conventional types. Scope is the module path with the `Mathlib/` prefix stripped. Subject uses imperative present tense, no initial capital, no trailing period.

## Workflow

- PRs must come from forks.
- Run `lake exe mk_all` when adding/removing files.
- Dependencies use `- [ ] depends on: #XXXX`.
- Comment `!bench` for performance benchmarking.

## Merge Process

Reviewer approval + `maintainer-merge`, then maintainer adds `ready-to-merge`; Bors merges. Delegated authors can comment `bors merge`.

Before submitting, follow Mathlib naming, code style, documentation style, and PR lifecycle guides.
