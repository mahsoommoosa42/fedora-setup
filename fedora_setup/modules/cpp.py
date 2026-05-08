"""Module 03 · C++ toolchain."""

from __future__ import annotations

from .. import colors, runner, shell_init
from ..context import Context


def run(ctx: Context) -> None:
    colors.section("3 · C++ Toolchain")

    colors.info("Installing C/C++ compilers and build tools...")
    # libasan and libubsan are bundled with gcc — no separate package needed
    runner.dnf_install(
        ctx,
        "gcc", "gcc-c++",
        "clang", "clang-tools-extra", "llvm", "lld",
        "cmake", "ninja-build", "meson", "make",
        "bear", "gdb", "lldb", "valgrind",
        "perf", "strace", "ltrace",
        "ccache", "doxygen",
    )

    colors.info("Installing common C++ libraries...")
    # tbb-devel was renamed to onetbb-devel in Fedora 36+
    # google-benchmark-devel is the Fedora package for benchmark-devel
    runner.dnf_install(
        ctx,
        "boost-devel", "fmt-devel", "abseil-cpp-devel",
        "catch2-devel", "gtest-devel",
        "google-benchmark-devel", "onetbb-devel",
    )

    shell_init.clean_shell_init(ctx, "ccache PATH")

    shell_init.append_to_shell_init(
        ctx,
        "ccache PATH",
        '# ccache — compiler cache\n'
        'export PATH="/usr/lib64/ccache:$PATH"',
    )

    colors.success("C++ toolchain ready (gcc, clang, cmake, ninja, bear, ccache)")
