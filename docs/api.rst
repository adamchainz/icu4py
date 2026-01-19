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

``icu4py.messageformat``
========================

This module wraps ICU’s MessageFormat V1 functionality.

.. currentmodule:: icu4py.messageformat

.. class:: MessageFormat(pattern: str, locale: str)

  A wrapper around ICU’s version 1 |MessageFormat class|__.

  .. |MessageFormat class| replace:: ``MessageFormat`` class
  __ https://unicode-org.github.io/icu-docs/apidoc/released/icu4c/classicu_1_1MessageFormat.html

  Construct an instance with a message pattern and locale, then call :meth:`format` with a dictionary of values to format the message.

  :param pattern: The message pattern string.
  :param locale: The locale to use, as a string like ``"en_US"``.

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
       >>> pattern = "{count, plural, one {# file} other {# files}}"
       >>> fmt = MessageFormat(pattern, "en_US")
       >>> fmt.format({"count": 1})
       '1 file'
       >>> fmt.format({"count": 5})
       '5 files'

    A more complex example:

    .. code-block:: pycon

      >>> from icu4py.messageformat import MessageFormat
      >>> pattern = (
      ...     "{num_guests, plural, offset:1 "
      ...     "=0 {{host} does not throw a party.}"
      ...     "=1 {{host} invites {guest} to the party.}"
      ...     "=2 {{host} invites {guest} and one other person to the party.}"
      ...     "other {{host} invites {guest} and # other people to the party.}}"
      ... )
      >>> fmt = MessageFormat(pattern, "en_US")
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
