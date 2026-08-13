---
name: lean4-setup
description: Set up a lean4 repository clone with proper elan toolchains. 
---

# Lean 4 Repository Setup

The first time you build in a lean4 repository clone, run:
```bash
cmake --preset release
make -j -C build/release
```

The `cmake` command is not needed on subsequent builds.

## Tests

Single test:
```bash
cd tests/lean/run
./test_single.sh example_test.lean
```

Full suite:
```bash
make -j -C build/release test ARGS="-j$(nproc)"
```

New tests go in `tests/lean/run/`; use `#guard_msgs` to check specific messages.

## Interactive repository setup

After the initial build, link stage1 and stage0 with `elan toolchain link`, then set `lean-toolchain` files appropriately. Verify from `tests/lean/run` that `lean --version` reports the clone commit. Remove custom toolchains with `elan toolchain uninstall` when done.
