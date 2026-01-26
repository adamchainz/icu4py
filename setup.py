from __future__ import annotations

import sys
from functools import partial

from setuptools import Extension, setup

libraries = [
    "icudt" if sys.platform == "win32" else "icudata",
    "icuin" if sys.platform == "win32" else "icui18n",
    "icuio",
    "icuuc",
]

if sys.platform == "win32":
    extra_compile_args = ["/Zc:wchar_t", "/EHsc", "/std:c++17"]
else:
    extra_compile_args = ["-std=c++17"]

extra_link_args: list[str] = []

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
