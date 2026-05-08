# Fedora Developer Workstation Setup

Automated configuration tool for setting up a complete Fedora development
environment on native KDE Plasma or WSL2. All logic is implemented in
**Python 3** (which Fedora ships out of the box); `setup.sh` and `cleanup.sh`
are thin shell wrappers that exec into the `fedora_setup` Python package.

## Features

- **Python-first**: every module is a `def run(ctx): ...` function in the
  `fedora_setup.modules` package — easy to test, type-check, and extend.
- **Modular Design**: 13 independent configuration modules for fine-grained
  control.
- **Environment Detection**: auto-detects WSL2 vs native Fedora, GPU
  availability, and systemd presence.
- **Safe Testing**: `DRY_RUN` mode previews every change without touching
  the system.
- **Clean Installs**: `CLEAN_INSTALL` removes existing fedora-setup
  configuration before reinstalling.
- **NVIDIA CUDA Support**: direct download from NVIDIA (no Fedora repo
  compatibility issues).
- **WSL2 Optimized**: skips WSL-incompatible tools while keeping full
  GPU/CUDA support.
- **Idempotent**: safe to run multiple times — only adds what's missing.

## Prerequisites

- **Fedora Linux** (native KDE Plasma or WSL2).
- **Python 3.11+** (preinstalled on Fedora; the entry-point script will
  print a clear error if missing).
- **Non-root user** with sudo privileges.
- **Internet connection** for downloading packages.
- For **NVIDIA GPU support**: NVIDIA drivers installed (native) or WSL2
  with GPU passthrough.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/mahsoommoosa42/fedora-setup.git
cd fedora-setup

# Preview what will be installed (safe, no changes)
DRY_RUN=1 ./setup.sh

# Run the actual installation
./setup.sh

# Reload your shell
source ~/.bashrc
```

You can also call the Python package directly without the shell wrapper:

```bash
python3 -m fedora_setup --dry-run
python3 -m fedora_setup --clean-install
```

## Configuration Options

### Dry Run Mode
Preview changes without modifying your system:
```bash
DRY_RUN=1 ./setup.sh
# or
python3 -m fedora_setup --dry-run
```

### Clean Install Mode
Remove existing fedora-setup configuration before installing:
```bash
CLEAN_INSTALL=1 ./setup.sh
# or
python3 -m fedora_setup --clean-install
```

### Combined Options
```bash
DRY_RUN=1 CLEAN_INSTALL=1 ./setup.sh
```

## What Gets Installed

### Base Tools
- Git, curl, wget, htop, btop, ripgrep, fd, fzf, jq, bat, eza, zoxide
- tmux, stow, man-pages, bash-completion

### Development Toolchains

**C++**
- GCC, Clang, CMake, Ninja, Meson, Make
- ccache, mold, bear, gdb, lldb, valgrind
- Boost, fmt, Abseil, Catch2, Google Benchmark, OneTBB

**Python**
- uv (modern Python package manager)
- Python 3.13, ruff, mypy, ipython, pytest, httpie

**JavaScript/TypeScript**
- Bun runtime and package manager
- TypeScript, tsx, ESLint, Prettier, ni

**Rust**
- rustup, cargo, rust-analyzer, clippy, rustfmt
- cargo-watch, cargo-expand, cargo-nextest, cargo-audit, cargo-bloat
- bandwhich, hexyl, dust, sd

### GPU & Acceleration

**CUDA (NVIDIA GPU only)**
- CUDA Toolkit 12.6.2 (direct from NVIDIA)
- cuDNN (manual install required — see notes below)
- WSL2 CUDA library paths configured automatically

**Vulkan**
- Vulkan runtime, tools, validation layers
- SPIRV tools, glslang, shaderc
- Mesa Vulkan drivers

**FFmpeg**
- Full FFmpeg with NVENC/NVDEC support
- VA-API and VDPAU acceleration

### Editors & AI

**Native Fedora only:**
- Visual Studio Code
- Windsurf AI editor
- KDE font configuration

**All environments:**
- Claude Code CLI
- Lazygit (Git TUI)
- git-delta (diff pager)

### Shell & Productivity
- Starship prompt (with nerd-font preset)
- Zoxide (smart cd), FZF, Eza, Bat
- Enhanced shell history

### Fonts
- JetBrains Mono / FiraCode / CascadiaCode / Meslo Nerd Fonts

## WSL2 vs Native Fedora

### WSL2 Specific Behavior
- Skips kernel development tools (uses Windows kernel)
- Skips NVIDIA driver installation (uses Windows driver)
- Skips KDE-specific configurations (no display server)
- Skips GUI editors (VS Code, Windsurf)
- Configures WSL2 CUDA library paths for GPU access
- Uses WSLg for Vulkan support

### Native Fedora Specific Behavior
- Installs kernel development packages and headers
- Installs NVIDIA drivers via akmod
- Configures KDE fonts and Konsole profiles
- Installs GUI editors (VS Code, Windsurf)
- Installs libvirt/KVM for virtualization
- Requires reboot after NVIDIA driver installation

## Manual Installation Steps

### cuDNN Installation
After running the script, manually install cuDNN from NVIDIA:
1. Visit https://developer.nvidia.com/cudnn
2. Download cuDNN for CUDA 12.x
3. Extract and copy to `/usr/local/cuda/` directories

### Starship Configuration
The script creates a default starship config with the nerd-font preset at
`~/.config/starship.toml`. To customize:
```bash
nano ~/.config/starship.toml
# or pick a different preset
starship preset tokyo-night > ~/.config/starship.toml
```

## Automated Installation with Kickstart

Two helper CLIs (also implemented in Python) automate kickstart-based installs.

### Step 1: Generate Kickstart File
```bash
./kickstart/prepare-ks.sh
# or
python3 -m fedora_setup.kickstart.prepare_ks
```
The wizard prompts for username, password, hostname, timezone, disk
layout, and the URL of `setup.sh`, and writes `kickstart/fedora-dev.ks`.

### Step 2: Download Fedora ISO
```bash
./kickstart/download-iso.sh
# or
python3 -m fedora_setup.kickstart.download_iso
```
Browse the official mirror, pick an ISO, download with progress, and verify
the SHA-256 checksum.

### Step 3: Bake Kickstart into ISO
```bash
sudo dnf install lorax  # if not already installed
mkksiso --ks kickstart/fedora-dev.ks \
        ~/Downloads/Fedora-ISOs/Fedora-*.iso \
        ~/Downloads/Fedora-ISOs/fedora-dev-custom.iso
```

### Step 4: Write to USB and Boot
```bash
sudo dd if=~/Downloads/Fedora-ISOs/fedora-dev-custom.iso \
        of=/dev/sdX bs=4M status=progress oflag=sync
```
Boot from the USB. Anaconda runs unattended through user creation, package
installation, and the `%post` script that downloads and runs `setup.sh`.

## Cleanup and Revert

```bash
# Preview what would be removed (safe)
./cleanup.sh --dry-run

# Remove all configurations (requires confirmation)
./cleanup.sh

# Remove configurations AND installed packages (dangerous)
./cleanup.sh --remove-packages
```

The cleanup tool removes:
- The source line from shell configs (`.bashrc`, `.zshrc`, `.bash_profile`)
- The shell-init file (`~/.config/fedora-setup/shell-init.sh`) which
  contains all tool configurations
- Tool configuration files (`~/.config/starship.toml`,
  `~/.ccache/ccache.conf`, etc.)
- Optionally, installed packages (with `--remove-packages`)

## Troubleshooting

### NVIDIA GPU Not Detected in WSL2
```bash
nvidia-smi                    # confirm GPU access
HAS_NVIDIA=1 ./setup.sh       # force detection
```

### Permission Denied on Script
```bash
chmod +x setup.sh cleanup.sh
```

### Cleanup After Failed Installation
```bash
CLEAN_INSTALL=1 ./setup.sh
```

### Module-Specific Iteration
```bash
python3 -c "
from fedora_setup.context import Context
from fedora_setup.modules import MODULE_ORDER
ctx = Context(dry_run=True)
next(mod for n, mod in MODULE_ORDER if n == '10-gpu').run(ctx)
"
```

## Testing

The project ships pytest-based unit and integration tests:

```bash
# Run all fast tests (unit + integration)
uv run python tests/run_tests.py

# Unit tests only (no Docker required)
(cd tests && uv run pytest unit -v)

# Integration tests only (requires Docker Desktop running)
uv run python tests/run_tests.py --integration

# Include slow real-install tests (~30 min, needs network)
uv run python tests/run_tests.py --slow
```

Test dependencies are managed with `uv` inside `tests/` (see
`tests/pyproject.toml`).

## Project Structure

```
fedora-setup/
├── setup.sh                          # Thin shell wrapper for python3 -m fedora_setup
├── cleanup.sh                        # Thin shell wrapper for python3 -m fedora_setup.cleanup
├── fedora_setup/                     # Python package with all the logic
│   ├── __init__.py
│   ├── __main__.py                   # Entry-point orchestrator
│   ├── colors.py                     # ANSI color constants & log helpers
│   ├── context.py                    # Context dataclass (dry_run, clean_install, paths)
│   ├── detect.py                     # is_wsl(), has_nvidia(), has_systemd(), …
│   ├── runner.py                     # DRY_RUN-aware wrappers (dnf, systemctl, cargo, …)
│   ├── shell_init.py                 # Marker-based idempotent shell-init management
│   ├── cleanup.py                    # python3 -m fedora_setup.cleanup
│   ├── modules/                      # 13 modules, each with def run(ctx)
│   │   ├── __init__.py               # MODULE_ORDER registry
│   │   ├── base.py                   # 01 · System update & base tools
│   │   ├── cli_tools.py              # 02 · Extra CLI tools, lazygit, starship
│   │   ├── cpp.py                    # 03 · C++ toolchain
│   │   ├── kernel.py                 # 04 · Kernel dev (native only)
│   │   ├── python_setup.py           # 05 · Python via uv
│   │   ├── js.py                     # 06 · JavaScript via Bun
│   │   ├── claude.py                 # 07 · Claude Code CLI
│   │   ├── fonts.py                  # 08 · Nerd Fonts + KDE/Konsole
│   │   ├── rust.py                   # 09 · Rust via rustup
│   │   ├── gpu.py                    # 10 · NVIDIA, CUDA, Vulkan, FFmpeg
│   │   ├── editors.py                # 11 · Neovim, VS Code, Windsurf
│   │   ├── git_config.py             # 12 · Git defaults
│   │   └── shell_qol.py              # 13 · Shell aliases, history, prompts
│   └── kickstart/                    # Kickstart helpers
│       ├── __init__.py
│       ├── download_iso.py           # Interactive Fedora ISO browser/verifier
│       └── prepare_ks.py             # Interactive kickstart generator
├── kickstart/
│   ├── prepare-ks.sh                 # Thin wrapper → fedora_setup.kickstart.prepare_ks
│   ├── download-iso.sh               # Thin wrapper → fedora_setup.kickstart.download_iso
│   └── fedora-dev.ks.template        # Template kickstart file
├── tests/
│   ├── unit/                         # Pytest unit tests
│   ├── integration/                  # Pytest integration tests (Docker)
│   ├── Dockerfile.fedora             # Image used by integration tests
│   ├── pyproject.toml                # uv-managed test deps
│   └── run_tests.py                  # Unified test runner
├── CLAUDE.md                         # Claude Code guidance
└── README.md                         # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality (pytest under `tests/unit`)
5. Ensure all tests pass
6. Submit a pull request

## License

This project is provided as-is for personal and educational use.
