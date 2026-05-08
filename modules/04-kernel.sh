#!/usr/bin/env bash
section "4 · Kernel Development Tools"

if is_wsl; then
    warn "WSL: skipping kernel module (WSL uses the Windows kernel; kernel-devel not applicable)"
    return 0 2>/dev/null || exit 0
fi

info "Installing kernel dev packages..."
# pahole is provided by the dwarves package — do not install separately
dnf_install \
    kernel-devel kernel-headers \
    dwarves elfutils-libelf-devel \
    openssl-devel flex bison bc \
    bpftrace bpftool trace-cmd \
    crash systemtap \
    qemu-kvm libvirt virt-manager virt-install

info "Enabling libvirtd..."
systemctl_enable libvirtd

info "Adding user to kvm and libvirt groups..."
usermod_groups kvm,libvirt "${USER:-$(whoami)}"

info "Installing cross-compilers..."
dnf_install \
    gcc-aarch64-linux-gnu \
    gcc-arm-linux-gnu \
    binutils-aarch64-linux-gnu

success "Kernel dev tooling ready (qemu-kvm, bpftrace, cross-compilers)"
