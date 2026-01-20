from datetime import date, datetime
from decimal import Decimal

from typing_extensions import disjoint_base

from icu4py.locale import Locale

@disjoint_base
class MessageFormat:
    def __init__(self, pattern: str, locale: str | Locale) -> None: ...
    def format(
        self, params: dict[str, int | float | str | Decimal | date | datetime]
    ) -> str: ...
