=====
Usage
=====

.. currentmodule:: icu

.. autoclass:: MessageFormat

  A wrapper around ICU’s |MessageFormat class|__.

  .. |MessageFormat class| replace:: ``MessageFormat`` class
  __ https://unicode-org.github.io/icu-docs/apidoc/released/icu4c/classicu_1_1MessageFormat.html

  Construct an instance with a message pattern and locale, then call :meth:`format` with a dictionary of values to format the message.

  :param pattern: The message pattern string.
  :param locale: The locale to use, as a string like ``"en_US"``.

  .. automethod:: format

    Format the message with the given values.

    :param values: A dictionary of names to values to format the message with.

      Currently supported value types are ``int``, ``float``, and ``str``.
      ICU supports more types, like dates, which can be added in the future.

    :return: The formatted message string.
    :rtype: str

    Example usage:

    .. code-block:: pycon

       >>> from icu import MessageFormat
       >>> pattern = "{count, plural, one {# file} other {# files}}"
       >>> fmt = MessageFormat(pattern, "en_US")
       >>> fmt.format({"count": 1})
       '1 file'
       >>> fmt.format({"count": 5})
       '5 files'

    A more complex example:

    .. code-block:: pycon

      >>> from icu import MessageFormat
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
      ```
