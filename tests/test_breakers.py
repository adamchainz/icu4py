from __future__ import annotations

import pytest

from icu4py.breakers import (
    BaseBreaker,
    CharacterBreaker,
    LineBreaker,
    SentenceBreaker,
    WordBreaker,
)
from icu4py.locale import Locale


class TestBaseBreaker:
    def test_cannot_init_directly(self):
        with pytest.raises(TypeError, match="Cannot instantiate BaseBreaker directly"):
            BaseBreaker("hello", "en")


class TestCharacterBreaker:
    def test_simple_characters(self):
        breaker = CharacterBreaker("Hello", "en_GB")
        chars = list(breaker)
        assert chars == ["H", "e", "l", "l", "o"]

    def test_segments(self):
        breaker = CharacterBreaker("Hello", "en_GB")
        segments = list(breaker.segments())
        assert segments == [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)]

    def test_combining_characters(self):
        text = "é"
        breaker = CharacterBreaker(text, "en_GB")
        chars = list(breaker)
        assert chars == ["é"]

    def test_emoji_sequences(self):
        text = "👨‍👩‍👧‍👦"
        breaker = CharacterBreaker(text, "en_GB")
        chars = list(breaker)
        assert chars == ["👨‍👩‍👧‍👦"]

    def test_emoji_with_skin_tone(self):
        text = "👋🏽"
        breaker = CharacterBreaker(text, "en_GB")
        chars = list(breaker)
        assert chars == ["👋🏽"]

    def test_empty_string(self):
        breaker = CharacterBreaker("", "en_GB")
        chars = list(breaker)
        assert chars == []

    def test_unicode_text(self):
        breaker = CharacterBreaker("Café", "en_GB")
        chars = list(breaker)
        assert chars == ["C", "a", "f", "é"]

    def test_with_locale_object(self):
        locale = Locale("en", "GB")
        breaker = CharacterBreaker("Hello", locale)
        chars = list(breaker)
        assert chars == ["H", "e", "l", "l", "o"]


class TestWordBreaker:
    def test_simple_words(self):
        breaker = WordBreaker("Hello World", "en_GB")
        words = list(breaker)
        assert words == ["Hello", " ", "World"]

    def test_segments(self):
        breaker = WordBreaker("Hello World", "en_GB")
        segments = list(breaker.segments())
        assert segments == [(0, 5), (5, 6), (6, 11)]

    def test_punctuation(self):
        breaker = WordBreaker("Hello, World!", "en_GB")
        words = list(breaker)
        assert words == ["Hello", ",", " ", "World", "!"]

    def test_contractions(self):
        breaker = WordBreaker("I'm here", "en_GB")
        words = list(breaker)
        assert words == ["I'm", " ", "here"]

    def test_numbers(self):
        breaker = WordBreaker("There are 42 items", "en_GB")
        words = list(breaker)
        assert words == ["There", " ", "are", " ", "42", " ", "items"]

    def test_hyphenated_words(self):
        breaker = WordBreaker("self-contained", "en_GB")
        words = list(breaker)
        assert words == ["self", "-", "contained"]

    def test_empty_string(self):
        breaker = WordBreaker("", "en_GB")
        words = list(breaker)
        assert words == []

    def test_single_word(self):
        breaker = WordBreaker("Hello", "en_GB")
        words = list(breaker)
        assert words == ["Hello"]

    def test_unicode_text(self):
        breaker = WordBreaker("Café résumé", "en_GB")
        words = list(breaker)
        assert words == ["Café", " ", "résumé"]

    def test_emoji(self):
        breaker = WordBreaker("Hello 👋 World", "en_GB")
        words = list(breaker)
        assert words == ["Hello", " ", "👋", " ", "World"]

    def test_with_locale_object(self):
        locale = Locale("en", "GB")
        breaker = WordBreaker("Hello World", locale)
        words = list(breaker)
        assert words == ["Hello", " ", "World"]

    def test_japanese_text(self):
        breaker = WordBreaker("これは日本語です", "ja_JP")
        words = list(breaker)
        assert words == ["これ", "は", "日本語", "です"]

    def test_multiple_spaces(self):
        breaker = WordBreaker("Hello  World", "en_GB")
        words = list(breaker)
        assert words == ["Hello", "  ", "World"]


class TestLineBreaker:
    def test_simple_line(self):
        breaker = LineBreaker("Hello World", "en_GB")
        segments = list(breaker.segments())
        assert segments == [(0, 6), (6, 11)]

    def test_long_text(self):
        text = "This is a long sentence that could be broken at multiple points."
        breaker = LineBreaker(text, "en_GB")
        segments = list(breaker.segments())
        assert segments == [
            (0, 5),
            (5, 8),
            (8, 10),
            (10, 15),
            (15, 24),
            (24, 29),
            (29, 35),
            (35, 38),
            (38, 45),
            (45, 48),
            (48, 57),
            (57, 64),
        ]

    def test_with_newlines(self):
        breaker = LineBreaker("Hello\nWorld", "en_GB")
        segments = list(breaker.segments())
        assert segments == [(0, 6), (6, 11)]

    def test_hyphenated_words(self):
        breaker = LineBreaker("self-contained", "en_GB")
        segments = list(breaker.segments())
        assert segments == [(0, 5), (5, 14)]

    def test_empty_string(self):
        breaker = LineBreaker("", "en_GB")
        segments = list(breaker.segments())
        assert segments == []

    def test_with_locale_object(self):
        locale = Locale("en", "GB")
        breaker = LineBreaker("Hello World", locale)
        segments = list(breaker.segments())
        assert segments == [(0, 6), (6, 11)]


class TestSentenceBreaker:
    def test_simple_sentences(self):
        text = "Hello. World."
        breaker = SentenceBreaker(text, "en_GB")
        sentences = list(breaker)
        assert sentences == ["Hello. ", "World."]

    def test_segments(self):
        text = "Hello. World."
        breaker = SentenceBreaker(text, "en_GB")
        segments = list(breaker.segments())
        assert segments == [(0, 7), (7, 13)]

    def test_abbreviations(self):
        text = "Dr. Smith is here."
        breaker = SentenceBreaker(text, "en_GB")
        sentences = list(breaker)
        assert sentences == ["Dr. ", "Smith is here."]

    def test_multiple_sentences(self):
        text = "First sentence. Second sentence! Third sentence?"
        breaker = SentenceBreaker(text, "en_GB")
        sentences = list(breaker)
        assert sentences == ["First sentence. ", "Second sentence! ", "Third sentence?"]

    def test_question_marks(self):
        text = "Are you there? Yes I am."
        breaker = SentenceBreaker(text, "en_GB")
        sentences = list(breaker)
        assert sentences == ["Are you there? ", "Yes I am."]

    def test_exclamation_marks(self):
        text = "Stop! Go now."
        breaker = SentenceBreaker(text, "en_GB")
        sentences = list(breaker)
        assert sentences == ["Stop! ", "Go now."]

    def test_empty_string(self):
        breaker = SentenceBreaker("", "en_GB")
        sentences = list(breaker)
        assert sentences == []

    def test_single_sentence(self):
        breaker = SentenceBreaker("Hello.", "en_GB")
        sentences = list(breaker)
        assert sentences == ["Hello."]

    def test_numbers_with_periods(self):
        text = "The value is 3.14. That's pi."
        breaker = SentenceBreaker(text, "en_GB")
        sentences = list(breaker)
        assert sentences == ["The value is 3.14. ", "That's pi."]

    def test_with_locale_object(self):
        locale = Locale("en", "GB")
        breaker = SentenceBreaker("Hello. World.", locale)
        sentences = list(breaker)
        assert sentences == ["Hello. ", "World."]


class TestLocaleHandling:
    def test_string_locale(self):
        breaker = WordBreaker("Hello", "en_GB")
        words = list(breaker)
        assert words == ["Hello"]

    def test_locale_object(self):
        locale = Locale("en", "GB")
        breaker = WordBreaker("Hello", locale)
        words = list(breaker)
        assert words == ["Hello"]

    def test_invalid_locale_type(self):
        with pytest.raises(TypeError, match="locale must be a string or Locale object"):
            WordBreaker("Hello", 123)  # type: ignore [arg-type]

    def test_different_locales(self):
        breaker_gb1 = WordBreaker("Hello", "en_GB")
        breaker_gb2 = WordBreaker("Hello", "en_GB")
        assert list(breaker_gb1) == list(breaker_gb2)


class TestEdgeCases:
    def test_very_long_text(self):
        text = "word " * 1000
        breaker = WordBreaker(text, "en_GB")
        words = list(breaker)
        assert len(words) == 2000

    def test_null_character(self):
        text = "Hello\x00World"
        breaker = WordBreaker(text, "en_GB")
        words = list(breaker)
        assert words == ["Hello", "\x00", "World"]

    def test_whitespace_only(self):
        breaker = WordBreaker("   ", "en_GB")
        words = list(breaker)
        assert words == ["   "]

    def test_newlines(self):
        breaker = WordBreaker("Hello\nWorld", "en_GB")
        words = list(breaker)
        assert words == ["Hello", "\n", "World"]

    def test_tabs(self):
        breaker = WordBreaker("Hello\tWorld", "en_GB")
        words = list(breaker)
        assert words == ["Hello", "\t", "World"]

    def test_mixed_scripts(self):
        text = "Hello 世界"
        breaker = WordBreaker(text, "en_GB")
        words = list(breaker)
        assert words == ["Hello", " ", "世界"]

    def test_rtl_text(self):
        text = "مرحبا"
        breaker = WordBreaker(text, "ar")
        words = list(breaker)
        assert words == ["مرحبا"]
