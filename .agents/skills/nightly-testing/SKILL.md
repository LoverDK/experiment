---
name: nightly-testing
description: Understanding the Lean/Mathlib nightly testing infrastructure. Use when working on toolchain bumps, adaptation PRs, or investigating nightly CI failures.
---

# Nightly Testing

Lean 4 publishes nightly toolchain builds from `master`. Batteries and Mathlib maintain nightly-testing branches and tags to validate new toolchains.

Mathlib nightly testing lives in `leanprover-community/mathlib4-nightly-testing`, not the main mathlib4 repository.

Key branches include `nightly-testing`, `nightly-with-mathlib`, `bump/v4.X.Y`, and `lean-pr-testing-NNNN`. Consult the Lean Zulip nightly-testing channel and the canonical tags-and-branches documentation when working on these branches.
