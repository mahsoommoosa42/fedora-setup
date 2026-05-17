"""Module 10 · NVIDIA drivers, CUDA, Vulkan, FFmpeg."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from .. import colors, detect, runner, shell_init
from ..context import Context

CUDA_VERSION = "12.6.2"


def _fedora_version() -> str:
    if shutil.which("rpm"):
        try:
            result = subprocess.run(
                ["rpm", "-E", "%fedora"],
                capture_output=True,
                text=True,
                check=False,
            )
            value = result.stdout.strip()
            if value and value != "%fedora":
                return value
        except OSError:
            pass
    return "41"


def _install_rpm_fusion(ctx: Context) -> None:
    fedora_ver = _fedora_version()
    runner.dnf_install(
        ctx,
        f"https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-{fedora_ver}.noarch.rpm",
        f"https://mirrors.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-{fedora_ver}.noarch.rpm",
    )
    runner.dnf_group_update(ctx, "core")


def _install_nvidia_drivers(ctx: Context) -> None:
    if detect.is_wsl():
        colors.warn(
            "WSL: skipping akmod kernel module — WSL2 uses the Windows NVIDIA driver"
        )
        return

    colors.info("Installing NVIDIA drivers via akmod (RPM Fusion)...")
    runner.dnf_install(
        ctx,
        "akmod-nvidia",
        "xorg-x11-drv-nvidia",
        "xorg-x11-drv-nvidia-libs",
        "xorg-x11-drv-nvidia-libs.i686",
    )

    colors.info("Building NVIDIA kernel module (may take a few minutes)...")
    runner.akmods_dracut(ctx)
    colors.success("NVIDIA drivers installed — reboot required to activate")


def _install_cuda_toolkit(ctx: Context) -> None:
    shell_init.clean_shell_init(ctx, "CUDA PATH")
    shell_init.clean_shell_init(ctx, "WSL CUDA lib")

    colors.info("Installing CUDA toolkit directly from NVIDIA...")
    cuda_run = f"cuda_{CUDA_VERSION}_linux.run"
    cuda_url = (
        "https://developer.download.nvidia.com/compute/cuda/"
        f"{CUDA_VERSION}/local_installers/{cuda_run}"
    )

    if ctx.dry_run:
        print(f"DRY_RUN: Would download and install CUDA {CUDA_VERSION} from NVIDIA")
        print(f"DRY_RUN: Download URL: {cuda_url}")
        print("DRY_RUN: Install options: --toolkit --silent --override")
    else:
        colors.info(f"Downloading CUDA {CUDA_VERSION} installer from NVIDIA...")
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            installer = tmp_path / cuda_run
            runner.download_file(ctx, cuda_url, installer)
            colors.info("Installing CUDA toolkit (this may take several minutes)...")
            installer.chmod(0o755)
            runner.run_sudo_script(ctx, installer, "--toolkit", "--silent", "--override")

    shell_init.append_to_shell_init(
        ctx,
        "CUDA PATH",
        '# CUDA toolkit\n'
        'export CUDA_HOME=/usr/local/cuda\n'
        'export PATH="$CUDA_HOME/bin:$PATH"\n'
        'export LD_LIBRARY_PATH="$CUDA_HOME/lib64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"',
    )

    if detect.is_wsl():
        shell_init.append_to_shell_init(
            ctx,
            "WSL CUDA lib",
            '# WSL2 CUDA stubs (provided by the Windows NVIDIA driver)\n'
            'export LD_LIBRARY_PATH="/usr/lib/wsl/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"',
        )
        colors.info("WSL: added /usr/lib/wsl/lib to LD_LIBRARY_PATH for CUDA stubs")

    colors.success(f"CUDA toolkit {CUDA_VERSION} installed from NVIDIA")
    colors.info("Note: cuDNN must be installed separately from https://developer.nvidia.com/cudnn")


def _install_vulkan(ctx: Context) -> None:
    colors.info("Installing Vulkan runtime, tools and development headers...")
    runner.dnf_install(
        ctx,
        "vulkan-loader", "vulkan-loader-devel",
        "vulkan-tools", "vulkan-validation-layers",
        "spirv-tools", "spirv-headers-devel",
        "glslang", "libshaderc-devel",
        "mesa-vulkan-drivers",
        "mesa-libGL-devel", "mesa-libEGL-devel",
    )

    shell_init.clean_shell_init(ctx, "Vulkan ICD path")

    if detect.is_wsl():
        colors.info("WSL: Vulkan via WSLg — NVIDIA ICD omitted from path")
        shell_init.append_to_shell_init(
            ctx,
            "Vulkan ICD path",
            '# Vulkan ICD loader — WSL2 (WSLg, AMD/Intel)\n'
            'export VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/radeon_icd.x86_64.json:'
            '/usr/share/vulkan/icd.d/intel_icd.x86_64.json',
        )
    else:
        shell_init.append_to_shell_init(
            ctx,
            "Vulkan ICD path",
            '# Vulkan ICD loader — covers NVIDIA, AMD, and Intel\n'
            'export VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/nvidia_icd.json:'
            '/usr/share/vulkan/icd.d/radeon_icd.x86_64.json:'
            '/usr/share/vulkan/icd.d/intel_icd.x86_64.json',
        )

    colors.success("Vulkan installed — verify after reboot with: vulkaninfo --summary")


def _install_ffmpeg(ctx: Context) -> None:
    colors.info("Installing FFmpeg with hardware acceleration support...")
    runner.dnf_remove(ctx, "ffmpeg-free")
    # --allowerasing lets dnf replace Fedora's *-free codec packages with the
    # full RPM Fusion builds that include hardware-acceleration support.
    runner.dnf_install(ctx, "ffmpeg", "ffmpeg-devel", "ffmpeg-libs", allowerasing=True)

    if detect.has_nvidia():
        try:
            runner.dnf_install(ctx, "nv-codec-headers")
        except subprocess.CalledProcessError:
            colors.warn("nv-codec-headers not found — NVENC/NVDEC headers unavailable")

    runner.dnf_install(
        ctx,
        "libva", "libva-utils", "libva-devel",
        "libvdpau",
        "gstreamer1-vaapi",
    )
    colors.success("FFmpeg installed — verify with: ffmpeg -version && ffmpeg -hwaccels")


def run(ctx: Context) -> None:
    colors.section("10 · NVIDIA Drivers, CUDA, Vulkan & FFmpeg")

    if detect.has_nvidia():
        colors.info("NVIDIA GPU detected")
    else:
        colors.warn("No NVIDIA GPU detected — skipping NVIDIA drivers and CUDA")

    colors.info("Enabling RPM Fusion repositories...")
    _install_rpm_fusion(ctx)

    if detect.has_nvidia():
        _install_nvidia_drivers(ctx)
        _install_cuda_toolkit(ctx)

    _install_vulkan(ctx)
    _install_ffmpeg(ctx)
