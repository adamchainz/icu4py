from typing import overload

from typing_extensions import disjoint_base

@disjoint_base
class Locale:
    @overload
    def __init__(self, language: str) -> None: ...
    @overload
    def __init__(
        self,
        language: str,
        country: str,
        variant: str | None = None,
        extensions: dict[str, str] | None = None,
    ) -> None: ...
    @property
    def bogus(self) -> bool: ...
    @property
    def language(self) -> str: ...
    @property
    def country(self) -> str: ...
    @property
    def variant(self) -> str: ...
    @property
    def extensions(self) -> dict[str, str]: ...
