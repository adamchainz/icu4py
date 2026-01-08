from __future__ import annotations

import sys

from setuptools import Extension, setup

if sys.platform == "win32":
    libraries = ["icuin", "icuuc", "icudt"]
else:
    libraries = ["icui18n", "icuuc", "icudata"]

if sys.platform == "win32":
    extra_compile_args = ["/Zc:wchar_t", "/EHsc", "/std:c++17"]
else:
    extra_compile_args = ["-std=c++17"]

extra_link_args: list[str] = []

# On macOS, add rpath to find versionless Homebrew install location
if sys.platform == "darwin":
    extra_link_args = [
        "-Wl,-rpath,/opt/homebrew/opt/icu4c/lib",
        "-Wl,-rpath,/usr/local/opt/icu4c/lib",
    ]

setup(
    ext_modules=[
        Extension(
            "icu4py.messageformat",
            sources=["src/icu4py/messageformat.cpp"],
            libraries=libraries,
            extra_compile_args=extra_compile_args,
            extra_link_args=extra_link_args,
            language="c++",
        )
    ],
)
