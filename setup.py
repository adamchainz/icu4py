from __future__ import annotations

import os
import sys
from functools import partial
from pathlib import Path

from setuptools import Extension, setup

libraries = [
    "icudt" if sys.platform == "win32" else "icudata",
    "icuin" if sys.platform == "win32" else "icui18n",
    "icuio",
    "icuuc",
]

if sys.platform == "win32":
    extra_compile_args = ["/Zc:wchar_t", "/EHsc", "/std:c++17"]
    icu_root = Path(os.environ.get("ICU_ROOT", "C:/icu/icu"))
    include_dirs = [str(icu_root / "include")]
    library_dirs = [str(icu_root / "lib")]
else:
    extra_compile_args = ["-std=c++17"]
    include_dirs: list[str] = []
    library_dirs: list[str] = []

extra_link_args: list[str] = []

ext = partial(
    Extension,
    libraries=libraries,
    include_dirs=include_dirs,
    library_dirs=library_dirs,
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
            "icu4py.breakers",
            sources=["src/icu4py/breakers.cpp"],
        ),
        ext(
            "icu4py._version",
            sources=["src/icu4py/_version.cpp"],
        ),
    ],
)
