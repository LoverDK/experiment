---
name: lean-pr
description: PR conventions for the leanprover/lean4 repository. Use when creating pull requests, writing commit messages, or following project conventions for Lean contributions.
---

# Lean PR Conventions

## Commit Message Format

All PR titles must follow the format:

```
<type>: <subject>
```

**`<type>`** is one of:
- `feat` — feature
- `fix` — bug fix
- `doc` — documentation
- `style` — formatting
- `refactor`
- `test` — adding missing tests
- `chore` — maintenance
- `perf` — performance improvement

**`<subject>`**: imperative present tense, lowercase, no period.

For `feat`/`fix` PRs, begin the description with "This PR " — the first paragraph is automatically used in release notes.

## Changelog Labels

Every `feat` or `fix` PR must have a `changelog-*` label.

## Module System for `src/` Files

Files in `src/Lean/`, `src/Std/`, and `src/lake/Lake/` must have both `module` and `prelude` declarations. With `prelude`, nothing is auto-imported — you must explicitly import `Init.*` modules.

## Copyright Headers

New files in `src/` require a copyright header. Check recent files in the repository for the correct holder. Test files do not need copyright headers.

## PR Conventions

Keep descriptions concise: start with "This PR ...", omit unnecessary Summary/Test plan/Implementation details sections.
