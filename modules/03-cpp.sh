#!/usr/bin/env bash
section "3 · C++ Toolchain"

info "Installing C/C++ compilers and build tools..."
# libasan and libubsan are bundled with gcc — no separate package needed
dnf_install \
    gcc gcc-c++ \
    clang clang-tools-extra llvm lld \
    cmake ninja-build meson make \
    bear gdb lldb valgrind \
    perf strace ltrace \
    ccache doxygen

info "Installing common C++ libraries..."
# tbb-devel was renamed to onetbb-devel in Fedora 36+
# google-benchmark-devel is the Fedora package for benchmark-devel
dnf_install \
    boost-devel fmt-devel abseil-cpp-devel \
    catch2-devel gtest-devel \
    google-benchmark-devel onetbb-devel

clean_config "ccache PATH"

append_if_missing "ccache PATH" \
'# ccache — compiler cache
export PATH="/usr/lib64/ccache:$PATH"'

success "C++ toolchain ready (gcc, clang, cmake, ninja, bear, ccache)"
