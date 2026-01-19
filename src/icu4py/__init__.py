from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from icu4py._version import icu_version, icu_version_info
else:
    from typing import Any

    def __getattr__(name: str) -> Any:
        if name == "icu_version":
            from icu4py._version import icu_version

            return icu_version
        elif name == "icu_version_info":
            from icu4py._version import icu_version_info

            return icu_version_info
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["icu_version", "icu_version_info"]
