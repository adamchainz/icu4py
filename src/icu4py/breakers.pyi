from collections.abc import Iterator

from typing_extensions import disjoint_base

from icu4py.locale import Locale

@disjoint_base
class BaseBreaker:
    def segments(self) -> Iterator[tuple[int, int]]: ...
    def __iter__(self) -> Iterator[str]: ...

class WordBreaker(BaseBreaker):
    def __init__(self, text: str, locale: str | Locale) -> None: ...

class LineBreaker(BaseBreaker):
    def __init__(self, text: str, locale: str | Locale) -> None: ...

class CharacterBreaker(BaseBreaker):
    def __init__(self, text: str, locale: str | Locale) -> None: ...

class SentenceBreaker(BaseBreaker):
    def __init__(self, text: str, locale: str | Locale) -> None: ...
