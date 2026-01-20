=========
Changelog
=========

* Add :data:`.icu_version` and :data:`.icu_version_info` to expose the ICU library version.

* Add :class:`.Locale` class and extend :class:`.MessageFormat` to accept it.

* Expand :meth:`.MessageFormat.format` to support ``decimal.Decimal``, ``date``, and ``datetime`` values.

* Make :meth:`.MessageFormat.format` support large integers that would overflow ``int64``, rather than raising an error.

  `PR #38 <https://github.com/adamchainz/icu4py/issues/38>`__.

* Allow :class:`.MessageFormat` to be subclassed.

0.1.0 (2026-01-09)
------------------

* First release on PyPI.
