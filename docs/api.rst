===
API
===

``icu4py``
==========

.. currentmodule:: icu4py

.. data:: icu_version
  :type: str

  A string representing the ICU version, for example ``"78.2"``.

.. data:: icu_version_info
  :type: tuple[int, int, int, int]

  A tuple of four integers representing the ICU version in the format ``(major, minor, patch, build)``, for example, ``(78, 2, 0, 0)``.

``icu4py.locale``
=================

This module wraps ICU's `locale functionality`__.

__ https://unicode-org.github.io/icu/userguide/locale/

.. currentmodule:: icu4py.locale

.. class:: Locale(language: str, country: str | None = None, variant: str | None = None, extensions: dict[str, str] | None = None)

  A wrapper around ICU's |Locale class|__.

  .. |Locale class| replace:: ``Locale`` class
  __ https://unicode-org.github.io/icu-docs/apidoc/released/icu4c/classicu_1_1Locale.html#details

  Represents a specific geographical, political, or cultural region.

  :param language: A valid **ISO Language Code**: one of the lower-case two-letter codes as defined by ISO-639, like ``"en"``. Find a full list of these codes `on Wikipedia <https://en.wikipedia.org/wiki/List_of_ISO_639_language_codes>`__.

  Alternatively, this parameter may be provided as an **ICU style C locale string**, such as ``"en_GB"`` or ``"de_DE@collation=phonebook"``. In this case, the other parameters should be left as ``None``.

  :param country: A valid **ISO Country Code**: one of the upper-case two-letter (A-2) codes as defined by ISO-3166, like ``GB"``. Find a full list of these codes `on Wikipedia <https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes>`__.

  :param variant: A **Variant**: variant codes are vendor and browser-specific.

  :param extensions: A dictionary of Unicode locale extensions, such as ``{"collation": "phonebook", "currency": "euro"}`` (optional).

  Per ICU’s behaviour, the ``Locale`` constructor performs no validation of the provided locale data. Operations use a best-match approach for locales. However, if input data is completely invalid, the locale is marked as “bogus”, which can be checked with the :attr:`bogus` attribute.

  Example usage:

  .. code-block:: pycon

     >>> from icu4py.locale import Locale
     >>> locale = Locale("en", "GB")
     >>> locale.bogus
     False
     >>> locale.language
     'en'
     >>> locale.country
     'GB'

  .. attribute:: bogus
     :type: bool

     Whether the locale is bogus (definitely invalid). Returns ``True`` if the locale is bogus, ``False`` if it is valid.

  .. attribute:: language
     :type: str

     The locale's ISO Language Code, like ``"en"`` for English.

     Note that ICU canonicalizes the language code. For instance, a ``Locale`` constructed with the three-letter code ``"eng"`` will return ``"en"``.

  .. attribute:: country
     :type: str

     The locale's ISO Country Code, like ``"GB"`` for the United Kingdom.

     Returns an empty string if no country code was specified.

  .. attribute:: variant
     :type: str

     The locale's variant code. Variant codes are vendor and browser-specific, such as ``"POSIX"``.

     Returns an empty string if no variant was specified. Note that ICU uppercases variant codes.

  .. attribute:: extensions
     :type: dict[str, str]

     A dictionary of the locale's keywords and values (extensions). For example, ``{"collation": "phonebook", "currency": "USD"}``.

     Returns an empty dictionary if no extensions were specified.

``icu4py.messageformat``
========================

This module wraps ICU’s `MessageFormat V1 functionality`__.

__ https://unicode-org.github.io/icu/userguide/format_parse/messages/

.. currentmodule:: icu4py.messageformat

.. class:: MessageFormat(pattern: str, locale: str | Locale)

  A wrapper around ICU’s version 1 |MessageFormat class|__.

  .. |MessageFormat class| replace:: ``MessageFormat`` class
  __ https://unicode-org.github.io/icu-docs/apidoc/released/icu4c/classicu_1_1MessageFormat.html#details

  Construct an instance with a message pattern and locale, then call :meth:`format` with a dictionary of values to format the message.

  :param pattern: The message pattern string.
  :param locale: The locale to use, as either a string (an ICU style C locale) or a :class:`~icu4py.locale.Locale` object.

  .. method:: format(values: dict[str, Any]) -> str

    Format the message with the given values.

    :param values: A dictionary of names to values to format the message with.

      Currently supported value types are ``int``, ``float``, ``str``, |Decimal|__, |date|__, and |datetime|__.

      .. |Decimal| replace:: ``decimal.Decimal``
      __ https://docs.python.org/3/library/decimal.html#decimal.Decimal
      .. |date| replace:: ``datetime.date``
      __ https://docs.python.org/3/library/datetime.html#datetime.date
      .. |datetime| replace:: ``datetime.datetime``
      __ https://docs.python.org/3/library/datetime.html#datetime.datetime

    :return: The formatted message string.
    :rtype: str

    Example usage:

    .. code-block:: pycon

       >>> from icu4py.messageformat import MessageFormat
       >>> pattern = "{count,plural,one {# file} other {# files}}"
       >>> fmt = MessageFormat(pattern, "en_GB")
       >>> fmt.format({"count": 1})
       '1 file'
       >>> fmt.format({"count": 5})
       '5 files'

    A more complex example:

    .. code-block:: pycon

      >>> from icu4py.messageformat import MessageFormat
      >>> pattern = (
      ...     "{num_guests,plural,offset:1 "
      ...     "=0 {{host} does not throw a party.}"
      ...     "=1 {{host} invites {guest} to the party.}"
      ...     "=2 {{host} invites {guest} and one other person to the party.}"
      ...     "other {{host} invites {guest} and # other people to the party.}}"
      ... )
      >>> fmt = MessageFormat(pattern, "en_GB")
      >>> fmt.format({"num_guests": 0, "host": "Alice", "guest": "Bob"})
      'Alice does not throw a party.'
      >>> fmt.format({"num_guests": 1, "host": "Alice", "guest": "Bob"})
      'Alice invites Bob to the party.'
      >>> fmt.format({"num_guests": 5, "host": "Alice", "guest": "Bob"})
      'Alice invites Bob and 4 other people to the party.'

    Formatting a ``datetime``:

    .. code-block:: pycon

      >>> import datetime as dt
      >>> from icu4py.messageformat import MessageFormat
      >>> fmt = MessageFormat("We gotta go back to {when,date,full}", "en_GB")
      >>> fmt.format({"when": dt.datetime(1985, 10, 26, 1, 24)})
      'We gotta go back to Saturday, 26 October 1985'

``icu4py.breakers``
===================

This module wraps ICU's |BreakIterator class|__ for finding boundaries in text.

.. |BreakIterator class| replace:: ``BreakIterator`` class
__ https://unicode-org.github.io/icu-docs/apidoc/released/icu4c/classicu_1_1BreakIterator.html#details

.. currentmodule:: icu4py.breakers

.. class:: BaseBreaker(text: str, locale: str | Locale)

  Base class for breaker subclasses, which cannot be instantiated directly.

  :param text: The text to analyze for boundaries.
  :param locale: The locale to use, as either a string (an ICU style C locale) or a :class:`~icu4py.locale.Locale` object.

  .. method:: __iter__() -> Iterator[str]

    Iterate over text segments split by boundaries.

    :return: An iterator of strings, each representing a segment of text between boundaries.

    Example usage:

    .. code-block:: pycon

       >>> from icu4py.breakers import WordBreaker
       >>> breaker = WordBreaker("Hello World", "en_GB")
       >>> list(breaker)
       ['Hello', ' ', 'World']

  .. method:: segments() -> Iterator[tuple[int, int]]

    Iterate over boundary positions as ``(start, end)`` tuples.

    :return: An iterator of ``(start, end)`` tuples representing boundary positions.

    Example usage:

    .. code-block:: pycon

       >>> from icu4py.breakers import WordBreaker
       >>> breaker = WordBreaker("Hello World", "en_GB")
       >>> list(breaker.segments())
       [(0, 5), (5, 6), (6, 11)]

.. class:: CharacterBreaker(text: str, locale: str | Locale)

  A wrapper around ICU's `character-break iterator`__.

  __ https://unicode-org.github.io/icu-docs/apidoc/released/icu4c/classicu_1_1BreakIterator.html#afffc1125b180a61857f698e147b1a668

  Finds character (grapheme cluster) boundaries, handling combining characters and emoji sequences as single units.

  Example usage:

  .. code-block:: pycon

     >>> from icu4py.breakers import CharacterBreaker
     >>> greeting = "👋🏽 hi"
     >>> list(greeting)  # splits by codepoints, emoji and skin tone are separate
     ['👋', '🏽', ' ', 'h', 'i']
     >>> breaker = CharacterBreaker(greeting, "en_GB")
     >>> list(breaker)  # splits by grapheme clusters, keeping emoji and skin tone together
     ['👋🏽', ' ', 'h', 'i']

.. class:: WordBreaker(text: str, locale: str | Locale)

  A wrapper around ICU's `word boundary iterator`__.

  __ https://unicode-org.github.io/icu-docs/apidoc/released/icu4c/classicu_1_1BreakIterator.html#a6aa1459cc086397bdb85ccd1bb3c5500

  Finds word boundaries in text, correctly handling punctuation, hyphenated words, and contractions.

  Example usage:

  .. code-block:: pycon

     >>> from icu4py.breakers import WordBreaker
     >>> exclamation = "A self-made rabbit."
     >>> list(WordBreaker(exclamation, "en_GB"))
     ['A', ' ', 'self', '-', 'made', ' ', 'rabbit', '.']

.. class:: LineBreaker(text: str, locale: str | Locale)

  A wrapper around ICU's `line-break iterator`__.

  __ https://unicode-org.github.io/icu-docs/apidoc/released/icu4c/classicu_1_1BreakIterator.html#aae588706df064825f1bccb2a9165169e

  Finds potential line-break positions in text, where text can be wrapped to the next line, correctly handling punctuation and hyphenated words.

  Example usage:

  .. code-block:: pycon

     >>> from icu4py.breakers import LineBreaker
     >>> review = "It’s quite thirst-quenching."
     >>> list(LineBreaker(review, "en_GB"))
     ['It’s ', 'quite ', 'thirst-', 'quenching.']

.. class:: SentenceBreaker(text: str, locale: str | Locale)

  A wrapper around ICU's `sentence-break iterator`__.

  __ https://unicode-org.github.io/icu-docs/apidoc/released/icu4c/classicu_1_1BreakIterator.html#ae161880c561882dad879112e15fde42b

  Finds sentence boundaries, correctly interpreting periods within numbers and abbreviations and any trailing punctuation marks.

  Example usage:

  .. code-block:: pycon

     >>> from icu4py.breakers import SentenceBreaker
     >>> tagline = 'You asked "Why?". We answered "Why not?"'
     >>> list(SentenceBreaker(tagline, "en_GB"))
     ['You asked "Why?". ', 'We answered "Why not?"']
