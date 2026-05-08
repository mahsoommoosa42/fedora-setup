# Fedora Developer Workstation Setup

Automated configuration script for setting up a complete Fedora development environment on native KDE Plasma or WSL2. This script installs and configures toolchains for C++, Python, JavaScript, Rust, GPU/CUDA/Vulkan development, and more.

## Features

- **Modular Design**: 13 independent configuration modules for fine-grained control
- **Environment Detection**: Automatically detects WSL2 vs native Fedora, GPU availability, and systemd presence
- **Safe Testing**: `DRY_RUN` mode to preview changes without modifying your system
- **Clean Installs**: `CLEAN_INSTALL` option to remove existing configurations before installing
- **NVIDIA CUDA Support**: Direct installation from NVIDIA (no Fedora repo compatibility issues)
- **WSL2 Optimized**: Skips WSL-incompatible tools while maintaining full GPU/CUDA support
- **Idempotent**: Safe to run multiple times - only adds what's missing

## Prerequisites

- **Fedora Linux** (native KDE Plasma or WSL2)
- **Non-root user** with sudo privileges
- **Internet connection** for downloading packages
- For **NVIDIA GPU support**: NVIDIA drivers installed (native) or WSL2 with GPU passthrough

## Quick Start

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/fedora-setup.git
cd fedora-setup

# Preview what will be installed (safe, no changes)
DRY_RUN=1 ./setup.sh

# Run the actual installation
./setup.sh

# Reload your shell
source ~/.bashrc
```

## Configuration Options

### Dry Run Mode
Preview changes without modifying your system:
```bash
DRY_RUN=1 ./setup.sh
```

### Clean Install Mode
Remove existing configurations before installing:
```bash
CLEAN_INSTALL=1 ./setup.sh
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
- cuDNN (manual install required - see notes below)
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
- Zoxide (smart cd)
- FZF (fuzzy finder)
- Eza (modern ls)
- Bat (better cat)
- Enhanced shell history

### Fonts

- JetBrains Mono Nerd Font
- FiraCode Nerd Font
- CascadiaCode Nerd Font
- Meslo Nerd Font

## WSL2 vs Native Fedora

### WSL2 Specific Behavior
- ✅ Skips kernel development tools (uses Windows kernel)
- ✅ Skips NVIDIA driver installation (uses Windows driver)
- ✅ Skips KDE-specific configurations (no display server)
- ✅ Skips GUI editors (VS Code, Windsurf)
- ✅ Configures WSL2 CUDA library paths for GPU access
- ✅ Uses WSLg for Vulkan support

### Native Fedora Specific Behavior
- ✅ Installs kernel development packages and headers
- ✅ Installs NVIDIA drivers via akmod
- ✅ Configures KDE fonts and Konsole profiles
- ✅ Installs GUI editors (VS Code, Windsurf)
- ✅ Installs libvirt/KVM for virtualization
- ✅ Requires reboot after NVIDIA driver installation

## Manual Installation Steps

### cuDNN Installation
After running the script, manually install cuDNN from NVIDIA:
1. Visit https://developer.nvidia.com/cudnn
2. Download cuDNN for CUDA 12.x
3. Extract and copy to `/usr/local/cuda/` directories

### Starship Configuration
The script creates a default starship config with the nerd-font preset at `~/.config/starship.toml`. To customize:
```bash
# Edit the config file
nano ~/.config/starship.toml

# Or choose a different preset
starship preset tokyo-night > ~/.config/starship.toml
```

## Automated Installation with Kickstart

For a completely automated Fedora installation (e.g., on a new machine), you can use the provided kickstart configuration:

### Step 1: Generate Kickstart File
Run the interactive wizard to create a customized kickstart file:
```bash
./kickstart/prepare-ks.sh
```
This prompts for:
- Username and password
- Full name and hostname
- Timezone
- Disk layout (automatic LVM, automatic Btrfs, or manual)
- GitHub URL for the setup script

The wizard generates `kickstart/fedora-dev.ks` with all your settings.

### Step 2: Download Fedora ISO
Use the interactive browser to download the Fedora ISO:
```bash
./kickstart/download-iso.sh
```
Navigate through the mirror directory tree to select the desired Fedora version and edition (Workstation, KDE, etc.).

### Step 3: Bake Kickstart into ISO
Embed the kickstart file into the ISO using `mkksiso`:
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
Boot from the USB. Anaconda will:
1. Run unattended through user creation, package installation, and configuration
2. Pause at disk partitioning (unless you selected automatic layout)
3. After installation, execute the `%post` script which downloads and runs `setup.sh`

The entire process results in a fully configured Fedora developer workstation with no manual intervention required.

## Cleanup and Revert

If you encounter issues or want to remove all configurations added by this script, use the cleanup tool:

```bash
# Preview what would be removed (safe)
./cleanup.sh --dry-run

# Remove all configurations (requires confirmation)
./cleanup.sh

# Remove configurations AND installed packages (dangerous)
./cleanup.sh --remove-packages
```

The cleanup script removes:
- The source line from shell configs (`.bashrc`, `.zshrc`, `.bash_profile`)
- The shell-init file (`~/.config/fedora-setup/shell-init.sh`) which contains all tool configurations
- Tool configuration files (`.config/starship.toml`, `.ccache/ccache.conf`, etc.)
- Optionally, installed packages (with `--remove-packages`)

**Note on shell configuration**: This script uses a centralized shell-init file at `~/.config/fedora-setup/shell-init.sh`. Your `.bashrc`, `.zshrc`, and `.bash_profile` simply source this file with a single line. This makes cleanup safe and simple — only the source line needs to be removed from your shell configs, and the entire shell-init file is deleted. No regex manipulation of your personal shell configs is performed.

## Troubleshooting

### NVIDIA GPU Not Detected in WSL2
If you have an NVIDIA GPU but the script doesn't detect it:
```bash
# Verify GPU access
nvidia-smi

# Force detection with environment variable
HAS_NVIDIA=1 ./setup.sh
```

### Permission Denied on Script
```bash
# Make script executable
chmod +x setup.sh
```

### Cleanup After Failed Installation
Use clean install mode to remove partial configurations:
```bash
CLEAN_INSTALL=1 ./setup.sh
```

### Module-Specific Issues
Run individual modules in isolation for debugging:
```bash
# Run specific module in dry-run mode
DRY_RUN=1 bash tests/unit/run_module.sh 10-gpu
```

## Testing

The project includes comprehensive tests:

```bash
# Run all fast tests (unit + integration)
uv run python tests/run_tests.py

# Run only unit tests
bats tests/unit/

# Run only integration tests (requires Docker)
uv run python tests/run_tests.py --integration

# Run specific module test
DRY_RUN=1 bash tests/unit/run_module.sh 02-cli
```

## Project Structure

```
fedora-setup/
├── setup.sh              # Main entry point
├── cleanup.sh            # Remove all configurations (for broken installs)
├── lib/
│   ├── colors.sh         # ANSI colors and logging
│   ├── detect.sh         # Environment detection
│   ├── fedora_releases.sh # Fedora version discovery from Bodhi API
│   └── utils.sh          # Utility functions (wrappers for side effects)
├── modules/
│   ├── 01-base.sh        # Base tools
│   ├── 02-cli.sh         # CLI tooling & starship
│   ├── 03-cpp.sh         # C++ toolchain
│   ├── 04-kernel.sh      # Kernel development (native only)
│   ├── 05-python.sh      # Python via uv
│   ├── 06-js.sh          # JavaScript via Bun
│   ├── 07-claude.sh      # Claude Code CLI
│   ├── 08-fonts.sh       # Nerd fonts
│   ├── 09-rust.sh        # Rust via rustup
│   ├── 10-gpu.sh         # NVIDIA, CUDA, Vulkan, FFmpeg
│   ├── 11-editors.sh     # VS Code, Windsurf (native only)
│   ├── 12-git.sh         # Git tools & lazygit
│   └── 13-shell.sh       # Shell aliases & productivity
├── kickstart/
│   ├── prepare-ks.sh     # Interactive kickstart file generator
│   ├── download-iso.sh   # Interactive Fedora ISO browser/downloader
│   └── fedora-dev.ks     # Kickstart template (generated by prepare-ks.sh)
├── tests/
│   ├── unit/             # Bats unit tests
│   ├── integration/      # Pytest integration tests
│   └── stubs/            # Fake executables for testing
├── CLAUDE.md             # Claude Code guidance
└── README.md             # This file
```

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is provided as-is for personal and educational use.

## Acknowledgments

- Inspired by various Fedora and WSL2 setup guides
- Uses excellent tools: starship, uv, bun, rustup, and many more
- Built with modularity and testability in mind