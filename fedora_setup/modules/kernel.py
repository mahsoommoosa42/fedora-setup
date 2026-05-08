"""Module 04 · Kernel development tools (skipped on WSL)."""

from __future__ import annotations

import os

from .. import colors, detect, runner
from ..context import Context


def run(ctx: Context) -> None:
    colors.section("4 · Kernel Development Tools")

    if detect.is_wsl():
        colors.warn(
            "WSL: skipping kernel module — WSL uses the Windows kernel"
        )
        return

    colors.info("Installing kernel dev packages...")
    # pahole is provided by the dwarves package — do not install separately
    runner.dnf_install(
        ctx,
        "kernel-devel", "kernel-headers",
        "dwarves", "elfutils-libelf-devel",
        "openssl-devel", "flex", "bison", "bc",
        "bpftrace", "bpftool", "trace-cmd",
        "crash", "systemtap",
        "qemu-kvm", "libvirt", "virt-manager", "virt-install",
    )

    colors.info("Enabling libvirtd...")
    runner.systemctl_enable(ctx, "libvirtd")

    colors.info("Adding user to kvm and libvirt groups...")
    user = os.environ.get("USER") or os.popen("whoami").read().strip() or "user"
    runner.usermod_groups(ctx, "kvm,libvirt", user)

    colors.info("Installing cross-compilers...")
    runner.dnf_install(
        ctx,
        "gcc-aarch64-linux-gnu",
        "gcc-arm-linux-gnu",
        "binutils-aarch64-linux-gnu",
    )

    colors.success("Kernel dev tooling ready (qemu-kvm, bpftrace, cross-compilers)")
