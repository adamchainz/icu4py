=========
Changelog
=========

* Embed ICU version 78.2 consistently in wheels across all platforms, via the custom ICU4C build repository, `icu4c-builds <https://github.com/adamchainz/icu4c-builds>`__.

  `PR #45 <https://github.com/adamchainz/icu4py/pull/45>`__.

* Stop shipping wheels for 32-bit platforms.

  `PR #47 <https://github.com/adamchainz/icu4py/pull/47>`__.

0.2.0 (2026-01-20)
------------------

* Add :data:`.icu_version` and :data:`.icu_version_info` to expose the ICU library version.

* Add :class:`.Locale` class and extend :class:`.MessageFormat` to accept it.

* Expand :meth:`.MessageFormat.format` to support ``decimal.Decimal``, ``date``, and ``datetime`` values.

* Make :meth:`.MessageFormat.format` support large integers that would overflow ``int64``, rather than raising an error.

  `PR #38 <https://github.com/adamchainz/icu4py/issues/38>`__.

* Allow :class:`.MessageFormat` to be subclassed.

0.1.0 (2026-01-09)
------------------

* First release on PyPI.
