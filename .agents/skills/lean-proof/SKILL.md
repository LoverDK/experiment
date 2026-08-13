---
name: lean-proof
description: Use when asked to prove something in Lean. Covers one-step-at-a-time proving, error priority, working on the hardest case first, proof cleanup, and handling dependent type rewriting issues.
---

# Lean Proof Methodology

These are non-negotiable constraints for writing Lean proofs correctly.

## One Step at a Time

Write one tactic, check diagnostics (use `done` to see unsolved goals), repeat. Never write multiple tactics before checking.

**`by sorry` is acceptable**: For placeholders you're not actively working on.
**`done` is required**: When you expect there to be next steps in an active proof.

## Error Priority

Fix errors in this order — higher-priority errors make lower-priority ones unreliable:

1. **Syntax errors** → 2. **Type errors** → 3. **Unsolved goals / tactic failures** → 4. **Linter warnings**

Stop writing tactics after any error.

## Work on the Hardest Case First

Go directly to the target theorem. Don't fill in `sorry`s in helper lemmas first — Lean treats `sorry` as an axiom, so dependent theorems still work. Within a proof, sorry the easy cases and work on the hardest one first.

## Proof Cleanup

After getting a proof to work, clean it up immediately:
- Combine redundant steps
- Test if `simp` can handle more
- Find the truly minimal proof

## Dependent Type Rewriting Issues

When rewriting a term that appears in dependent types fails with motive errors, prove a generalized statement for an arbitrary parameter, then instantiate it with `convert`.

## Verification

Never declare a proof complete while `sorry` placeholders or error diagnostics remain.
