# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Python tool that configures a Fedora developer workstation (native KDE
Plasma or WSL2). The entry-point shell scripts (`setup.sh`, `cleanup.sh`,
`kickstart/*.sh`) are thin wrappers; **all logic lives in the
`fedora_setup` Python package**. `setup.sh` execs `python3 -m
fedora_setup`, which loads 13 numbered modules in order, each adding a
toolchain layer (base tools, C++, Python, JS, Rust, GPU/CUDA/Vulkan,
editors, shell, etc.).

## Running

```bash
./setup.sh                       # real install (requires Fedora, non-root)
DRY_RUN=1 ./setup.sh             # preview — prints what would run, touches nothing
python3 -m fedora_setup --dry-run    # same thing without the shell wrapper
python3 -m fedora_setup --clean-install
```

## Tests

```bash
# All fast tests (pytest unit + pytest+Docker integration)
uv run python tests/run_tests.py

# Unit tests only (no Docker required)
(cd tests && uv run pytest unit -v)

# Single unit-test file
(cd tests && uv run pytest unit/test_detect.py -v)

# Integration tests only (requires Docker daemon)
uv run python tests/run_tests.py --integration

# Include slow real-install tests (~30 min, needs network)
uv run python tests/run_tests.py --slow
```

Python test dependencies are managed with `uv` inside `tests/` (see
`tests/pyproject.toml`). The unit tests are pure pytest — no `bats`
required anymore.

## Architecture

### Execution flow

`setup.sh` → `python3 -m fedora_setup` → `fedora_setup.__main__:main()`.
`main()` parses `DRY_RUN` / `CLEAN_INSTALL` env vars and CLI flags,
builds a `Context`, runs pre-flight checks (not root, on Fedora), seeds
the shell-init plumbing, then iterates over `MODULE_ORDER` and calls
each module's `run(ctx)` in sequence. All modules share state through
the `Context` object — they are not subshells and do not import from
each other.

### `fedora_setup/`

- **`colors.py`** — ANSI color constants + logging functions (`info`,
  `success`, `warn`, `die`, `section`).
- **`context.py`** — `Context` dataclass holding `dry_run`,
  `clean_install`, `script_dir`, `home`, `bashrc`, and
  `shell_init_path`. Replaces the global shell variables of the old
  Bash port.
- **`detect.py`** — environment predicates: `is_wsl()`, `has_nvidia()`,
  `has_systemd()`, `is_interactive()`, `get_fedora_versions()`. Each
  detection function checks an override env var first (`IS_WSL`,
  `HAS_NVIDIA`, `SYSTEMD_DIR_OVERRIDE`) so tests can mock without
  touching the real filesystem.
- **`runner.py`** — every side-effecting operation (dnf, systemctl,
  cargo, curl-pipe-bash, rpm imports, sudo-tee writes, usermod, …) is
  wrapped here. Each wrapper checks `ctx.dry_run` and prints
  `DRY_RUN: ...` instead of executing when true. Modules **must** go
  through these wrappers — never call `subprocess.run()` directly.
- **`shell_init.py`** — marker-based, idempotent management of the
  centralized shell-init file at `~/.config/fedora-setup/shell-init.sh`.
  Provides `ensure_shell_init`, `append_to_shell_init`,
  `clean_shell_init`, `append_if_missing`, `clean_config`, and
  `remove_file`. The user's `.bashrc` / `.zshrc` / `.bash_profile` only
  contains a single `source` line — cleanup just removes that line and
  deletes the shell-init file.
- **`cleanup.py`** — entry point for `python3 -m fedora_setup.cleanup`.
  Supports `--dry-run`, `--remove-packages`, `--help`.

### `fedora_setup/modules/`

Thirteen modules, each with a single `def run(ctx): ...` function.
`fedora_setup/modules/__init__.py` exposes `MODULE_ORDER`, an ordered
list of `(name, module)` tuples. Module names use the `NN-name`
convention (`01-base`, `02-cli`, …, `13-shell`) so the existing
integration tests still match the expected output format. Each module
calls only `runner.py` / `shell_init.py` helpers and gates WSL-only or
native-only branches behind `is_wsl()`.

### `fedora_setup/kickstart/`

- **`download_iso.py`** — interactive Fedora ISO browser & SHA-256
  verifier (`python3 -m fedora_setup.kickstart.download_iso`).
- **`prepare_ks.py`** — interactive kickstart generator
  (`python3 -m fedora_setup.kickstart.prepare_ks`). Hashes the user
  password via `crypt`, with `openssl` / `mkpasswd` fallbacks.

The `kickstart/*.sh` scripts are tiny shims that exec into the Python
modules.

### `tests/`

- **`tests/unit/`** — pytest unit tests covering `detect`, `runner`,
  `shell_init`, and every module's `run()` in DRY_RUN mode. Uses
  `monkeypatch` for env vars and `tmp_path` for temp filesystems.
- **`tests/integration/`** — pytest suite running commands inside a
  `fedora` Docker container (defined in `tests/Dockerfile.fedora`).
  `conftest.py` manages session-scoped containers (native, WSL,
  WSL+NVIDIA). `helpers.exec_in()` runs commands and returns
  `(exit_code, output)`. The integration tests still drive `setup.sh`
  end-to-end, but the script now execs into Python under the hood.
- **`tests/run_tests.py`** — unified runner that dispatches to pytest
  for both unit and integration suites.

## Key conventions

- **All side effects go through `runner.py` wrappers** — never call
  `subprocess.run()`, `dnf`, `sudo`, `systemctl`, etc. directly in a
  module.
- **Testability via env vars** — `detect.py` functions check override
  variables before touching the real system. New detection logic must
  follow the same pattern.
- **Idempotence** — use `append_if_missing(ctx, marker, content, file)`
  or `append_to_shell_init(ctx, marker, content)` for any shell config
  additions; the marker string is what's checked for existence.
- **DRY_RUN coverage** — every new side-effecting wrapper must emit a
  `DRY_RUN: ...` line and return without doing work when
  `ctx.dry_run` is true.
- **CLEAN_INSTALL coverage** — when `ctx.clean_install` is true,
  modules call `clean_shell_init` / `clean_config` first to wipe any
  prior fedora-setup blocks before re-appending them.
- **Type hints** — annotate all function signatures. Avoid `Any`,
  `getattr`, `setattr`; understand the type and access it directly.
- **Imports at top** — no nested imports inside functions or methods.
