icu4py documentation
====================

Python bindings to the `ICU (International Components for Unicode) library <https://icu.unicode.org/>`__ (ICU4C).

Let’s you do cool locale-aware things with text, like split it into sentences with :class:`~icu4py.breakers.SentenceBreaker`:
Split text into sentences with :class:`~icu4py.breakers.SentenceBreaker`:

.. doctest::

   >>> from icu4py.breakers import SentenceBreaker
   >>> text = 'You asked "Why?". We answered "Why not?"'
   >>> breaker = SentenceBreaker(text, "en_GB")
   >>> list(breaker)
   ['You asked "Why?". ', 'We answered "Why not?"']

…or format messages with variable pluralization using :class:`~icu4py.messageformat.MessageFormat`:

.. doctest::

   >>> from icu4py.messageformat import MessageFormat
   >>> pattern = "{count,plural,one {# file} other {# files}}"
   >>> fmt = MessageFormat(pattern, "en_GB")
   >>> fmt.format({"count": 1})
   '1 file'
   >>> fmt.format({"count": 5})
   '5 files'

Get started by following the installation instructions, and explore the API reference for more details.

.. toctree::
   :maxdepth: 1
   :caption: Contents:

   installation
   api
   changelog
