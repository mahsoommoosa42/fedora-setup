#!/usr/bin/env bash
section "10 · NVIDIA Drivers, CUDA, Vulkan & FFmpeg"

# ── GPU detection ─────────────────────────────────────────────────────────────
if has_nvidia; then
    info "NVIDIA GPU detected"
else
    warn "No NVIDIA GPU detected — skipping NVIDIA drivers and CUDA"
fi

# ── RPM Fusion ────────────────────────────────────────────────────────────────
info "Enabling RPM Fusion repositories..."
FEDORA_VER=$(rpm -E %fedora 2>/dev/null || echo "41")
dnf_install \
    "https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-${FEDORA_VER}.noarch.rpm" \
    "https://mirrors.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-${FEDORA_VER}.noarch.rpm"
dnf_group_update core

# ── NVIDIA Drivers (native only — WSL2 uses the Windows host driver) ──────────
if has_nvidia; then
    if is_wsl; then
        warn "WSL: skipping akmod-nvidia (WSL2 uses the Windows NVIDIA driver directly)"
    else
        info "Installing NVIDIA drivers via akmod (RPM Fusion)..."
        dnf_install \
            akmod-nvidia \
            xorg-x11-drv-nvidia \
            xorg-x11-drv-nvidia-libs \
            xorg-x11-drv-nvidia-libs.i686

        info "Building NVIDIA kernel module (may take a few minutes)..."
        if [[ "${DRY_RUN:-0}" == "1" ]]; then
            echo "DRY_RUN: sudo akmods --force && sudo dracut --force"
        else
            sudo akmods --force
            sudo dracut --force
        fi
        success "NVIDIA drivers installed — reboot required to activate"
    fi
fi

# ── CUDA Toolkit ──────────────────────────────────────────────────────────────
if has_nvidia; then
    # Clean existing CUDA configuration
    clean_shell_init "CUDA PATH"
    clean_shell_init "WSL CUDA lib"

    info "Installing CUDA toolkit directly from NVIDIA..."
    # Get latest CUDA version from NVIDIA
    CUDA_VERSION="12.6.2"
    CUDA_RUN_FILE="cuda_${CUDA_VERSION}_linux.run"

    if [[ "${DRY_RUN:-0}" == "1" ]]; then
        echo "DRY_RUN: Would download and install CUDA ${CUDA_VERSION} from NVIDIA"
        echo "DRY_RUN: Download URL: https://developer.download.nvidia.com/compute/cuda/${CUDA_VERSION}/local_installers/${CUDA_RUN_FILE}"
        echo "DRY_RUN: Install options: --toolkit --silent --override"
    else
        info "Downloading CUDA ${CUDA_VERSION} installer from NVIDIA..."
        local tmp_dir
        tmp_dir=$(mktemp -d)
        cd "$tmp_dir"

        if command -v wget &>/dev/null; then
            wget "https://developer.download.nvidia.com/compute/cuda/${CUDA_VERSION}/local_installers/${CUDA_RUN_FILE}"
        elif command -v curl &>/dev/null; then
            curl -O "https://developer.download.nvidia.com/compute/cuda/${CUDA_VERSION}/local_installers/${CUDA_RUN_FILE}"
        else
            die "Neither wget nor curl available to download CUDA installer"
        fi

        info "Installing CUDA toolkit (this may take several minutes)..."
        chmod +x "$CUDA_RUN_FILE"
        sudo ./"$CUDA_RUN_FILE" --toolkit --silent --override

        cd - > /dev/null
        rm -rf "$tmp_dir"
    fi

    append_to_shell_init "CUDA PATH" \
'# CUDA toolkit
export CUDA_HOME=/usr/local/cuda
export PATH="$CUDA_HOME/bin:$PATH"
export LD_LIBRARY_PATH="$CUDA_HOME/lib64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"'

    if is_wsl; then
        # WSL2: the NVIDIA Windows driver exposes CUDA stubs under /usr/lib/wsl/lib
        append_to_shell_init "WSL CUDA lib" \
'# WSL2 CUDA stubs (provided by the Windows NVIDIA driver)
export LD_LIBRARY_PATH="/usr/lib/wsl/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"'
        info "WSL: added /usr/lib/wsl/lib to LD_LIBRARY_PATH for CUDA stubs"
    fi

    success "CUDA toolkit ${CUDA_VERSION} installed from NVIDIA"
    info "Note: cuDNN must be installed separately from https://developer.nvidia.com/cudnn"
fi

# ── Vulkan ────────────────────────────────────────────────────────────────────
info "Installing Vulkan runtime, tools and development headers..."
# glslc is provided by shaderc; spirv-headers has no -devel suffix on Fedora
dnf_install \
    vulkan-loader vulkan-loader-devel \
    vulkan-tools vulkan-validation-layers \
    spirv-tools spirv-headers \
    glslang shaderc \
    mesa-vulkan-drivers \
    mesa-libGL-devel mesa-libEGL-devel

clean_shell_init "Vulkan ICD path"

if is_wsl; then
    info "WSL: Vulkan via WSLg — NVIDIA ICD omitted from path"
    append_to_shell_init "Vulkan ICD path" \
'# Vulkan ICD loader — WSL2 (WSLg, AMD/Intel)
export VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/radeon_icd.x86_64.json:/usr/share/vulkan/icd.d/intel_icd.x86_64.json'
else
    append_to_shell_init "Vulkan ICD path" \
'# Vulkan ICD loader — covers NVIDIA, AMD, and Intel
export VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/nvidia_icd.json:/usr/share/vulkan/icd.d/radeon_icd.x86_64.json:/usr/share/vulkan/icd.d/intel_icd.x86_64.json'
fi

success "Vulkan installed — verify after reboot with: vulkaninfo --summary"

# ── FFmpeg ────────────────────────────────────────────────────────────────────
info "Installing FFmpeg with hardware acceleration support..."
# Remove the codec-limited stub that Fedora ships by default
dnf_remove ffmpeg-free

# Full FFmpeg from RPM Fusion nonfree
dnf_install ffmpeg ffmpeg-devel ffmpeg-libs

if has_nvidia; then
    dnf_install nv-codec-headers \
        || warn "nv-codec-headers not found — NVENC/NVDEC headers unavailable"
fi

# VA-API and VDPAU work on AMD/Intel too
dnf_install \
    libva libva-utils libva-devel \
    libvdpau libvdpau-va-gl \
    gstreamer1-vaapi

success "FFmpeg installed — verify with: ffmpeg -version && ffmpeg -hwaccels"
