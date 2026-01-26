from __future__ import annotations

import pytest

from icu4py.locale import Locale


class TestLocale:
    def test_c_locale_string(self):
        locale = Locale("en")
        assert not locale.bogus
        assert locale.language == "en"
        assert locale.country == ""
        assert locale.variant == ""
        assert locale.extensions == {}

    def test_c_locale_string_country(self):
        locale = Locale("en_GB")
        assert not locale.bogus
        assert locale.language == "en"
        assert locale.country == "GB"
        assert locale.variant == ""
        assert locale.extensions == {}

    def test_c_locale_string_with_params(self):
        locale = Locale("de_DE@collation=phonebook")
        assert not locale.bogus
        assert locale.language == "de"
        assert locale.country == "DE"
        assert locale.variant == ""
        assert locale.extensions == {"collation": "phonebook"}

    def test_language_country(self):
        locale = Locale("en", "GB")
        assert not locale.bogus
        assert locale.language == "en"
        assert locale.country == "GB"
        assert locale.variant == ""
        assert locale.extensions == {}

    def test_language_country_three_letter_language(self):
        locale = Locale("eng", "GB")
        assert not locale.bogus
        assert locale.language == "en"
        assert locale.country == "GB"
        assert locale.variant == ""
        assert locale.extensions == {}

    def test_language_country_variant(self):
        locale = Locale("en", "GB", "POSIX")
        assert not locale.bogus
        assert locale.language == "en"
        assert locale.country == "GB"
        assert locale.variant == "POSIX"
        assert locale.extensions == {}

    def test_language_country_variant_double(self):
        locale = Locale("es", "ES", "Traditional_POSIX")
        assert not locale.bogus
        assert locale.language == "es"
        assert locale.country == "ES"
        assert locale.variant == "TRADITIONAL_POSIX"
        assert locale.extensions == {}

    def test_language_country_variant_empties(self):
        locale = Locale("es", "", "")
        assert not locale.bogus
        assert locale.language == "es"
        assert locale.country == ""
        assert locale.variant == ""
        assert locale.extensions == {}

    def test_language_country_variant_extensions(self):
        locale = Locale("en", "GB", None, {"collation": "phonebook"})
        assert not locale.bogus
        assert locale.language == "en"
        assert locale.country == "GB"
        assert locale.variant == ""
        assert locale.extensions == {"collation": "phonebook"}

    def test_language_country_extensions(self):
        locale = Locale("en", "GB", extensions={"collation": "phonebook"})
        assert not locale.bogus
        assert locale.language == "en"
        assert locale.country == "GB"
        assert locale.variant == ""
        assert locale.extensions == {"collation": "phonebook"}

    def test_language_country_extensions_empty(self):
        locale = Locale("en", "GB", extensions={})
        assert not locale.bogus
        assert locale.language == "en"
        assert locale.country == "GB"
        assert locale.variant == ""
        assert locale.extensions == {}

    def test_language_country_extensions_multiple(self):
        locale = Locale(
            "en", "GB", extensions={"collation": "phonebook", "currency": "USD"}
        )
        assert not locale.bogus
        assert locale.language == "en"
        assert locale.country == "GB"
        assert locale.variant == ""
        assert locale.extensions == {"collation": "phonebook", "currency": "USD"}

    def test_bogus_locale_string(self):
        locale = Locale("x" * 100)
        assert locale.bogus is True

    @pytest.mark.parametrize(
        "lang,country",
        [
            ("en", "GB"),
            ("fr", "FR"),
            ("de", "DE"),
            ("ja", "JP"),
            ("zh", "CN"),
            ("es", "ES"),
        ],
    )
    def test_bogus_common_locale(self, lang, country):
        locale = Locale(lang, country)
        assert locale.bogus is False

    def test_inheritance(self):
        class CustomLocale(Locale):
            def __init__(self, language: str) -> None:
                assert language in ("en_GB", "fr_FR")
                super().__init__(language)

        locale = CustomLocale("en_GB")
        assert not locale.bogus

        locale2 = CustomLocale("fr_FR")
        assert not locale2.bogus

        with pytest.raises(AssertionError):
            CustomLocale("de_DE")

    def test_repr_simple(self):
        locale = Locale("en")
        assert repr(locale) == "Locale('en')"

    def test_repr_with_country(self):
        locale = Locale("en", "GB")
        assert repr(locale) == "Locale('en_GB')"

    def test_repr_with_variant(self):
        locale = Locale("en", "GB", "POSIX")
        assert repr(locale) == "Locale('en_GB_POSIX')"

    def test_repr_with_extensions(self):
        locale = Locale("de", "DE", extensions={"collation": "phonebook"})
        assert repr(locale) == "Locale('de_DE@collation=phonebook')"

    def test_repr_with_multiple_extensions(self):
        locale = Locale(
            "en", "GB", extensions={"collation": "phonebook", "currency": "USD"}
        )
        repr_str = repr(locale)
        assert repr_str.startswith("Locale('en_GB@")
        assert "collation=phonebook" in repr_str
        assert "currency=USD" in repr_str
