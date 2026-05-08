# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Bash script suite that configures a Fedora developer workstation (native KDE Plasma or WSL2). `setup.sh` sources 13 numbered modules in order, each adding a toolchain layer (base tools, C++, Python, JS, Rust, GPU/CUDA/Vulkan, editors, shell, etc.).

## Running

```bash
./setup.sh                  # real install (requires Fedora, non-root)
DRY_RUN=1 ./setup.sh        # preview — prints what would run, touches nothing
```

## Tests

```bash
# All fast tests (bats unit + pytest+Docker integration)
uv run python tests/run_tests.py

# Bats unit tests only
bats tests/unit/

# Single bats file
bats tests/unit/test_detect.bats

# Integration tests only (requires Docker Desktop running)
uv run python tests/run_tests.py --integration

# Include slow real-install tests (~30 min, needs network)
uv run python tests/run_tests.py --slow

# Run a single module in dry-run for quick iteration
DRY_RUN=1 IS_WSL=0 HAS_NVIDIA=0 bash tests/unit/run_module.sh 04-kernel
```

Python test dependencies are managed with `uv` inside `tests/` (see `tests/pyproject.toml`). Bats must be installed separately (`dnf install bats`).

## Architecture

### Execution flow

`setup.sh` → sources `lib/{colors,detect,utils}.sh` → `source`s each `modules/NN-*.sh` in the same shell process. Modules are not subshells — they share state with each other and with `setup.sh`.

### lib/

- **`colors.sh`** — ANSI color vars + logging functions (`info`, `success`, `warn`, `die`, `section`).
- **`detect.sh`** — Environment predicates: `is_wsl`, `has_nvidia`, `has_systemd`. Each checks an override env var first (`IS_WSL`, `HAS_NVIDIA`, `SYSTEMD_DIR_OVERRIDE`) so tests can mock without touching the filesystem.
- **`utils.sh`** — All side-effecting operations (dnf, systemctl, cargo, curl-pipe-bash, etc.) are wrapped here. Every wrapper checks `DRY_RUN=1` and prints what it would do instead of acting. `append_if_missing` writes shell config idempotently using a marker string.

### modules/

Numbered 01–13, sourced in sequence. Each calls only functions from `lib/` — no raw `dnf`, `sudo`, or `curl` calls. WSL-only and native-only sections are gated on `is_wsl`.

### tests/

- **`tests/unit/`** — Bats tests. `helpers.bash` provides `mock_wsl`, `mock_native`, `mock_nvidia`, `make_temp_home`, etc. `run_module.sh` is a thin harness that sources libs + one module so modules can be tested in isolation with `DRY_RUN=1`.
- **`tests/integration/`** — pytest suite running commands inside a `fedora:41` Docker container (defined in `tests/Dockerfile.fedora`). `conftest.py` manages three session-scoped containers: native, WSL, and WSL+NVIDIA. `helpers.exec_in()` runs commands and returns `(exit_code, output)`.
- **`tests/stubs/`** — Fake executables (`dnf`, `sudo`, `systemctl`, `lspci`, `rpm`, `kwriteconfig6`) prepended to `PATH` during bats tests to intercept side effects.

## Key conventions

- **All side effects go through `lib/utils.sh` wrappers** — never call `dnf`, `sudo`, `systemctl`, etc. directly in a module.
- **Testability via env vars** — `detect.sh` functions check override vars before touching the real system. New detection logic must follow the same pattern.
- **Idempotence** — use `append_if_missing <marker> <content>` for any shell config additions; the marker string is what's checked for existence.
- **DRY_RUN coverage** — every new side-effecting wrapper must print a `DRY_RUN: ...` line and return 0 when `DRY_RUN=1`.
