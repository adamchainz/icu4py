from __future__ import annotations

import sys
from functools import partial

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

ext = partial(
    Extension,
    libraries=libraries,
    extra_compile_args=extra_compile_args,
    extra_link_args=extra_link_args,
    language="c++",
)

setup(
    ext_modules=[
        ext(
            "icu4py.locale",
            sources=["src/icu4py/locale.cpp"],
        ),
        ext(
            "icu4py.messageformat",
            sources=["src/icu4py/messageformat.cpp"],
        ),
        ext(
            "icu4py._version",
            sources=["src/icu4py/_version.cpp"],
        ),
    ],
)
