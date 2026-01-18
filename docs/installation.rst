============
Installation
============

Requirements
------------

Python 3.10 to 3.14 supported, including free-threaded variants from Python 3.13 onwards.

Only CPython is supported at this time because ICU uses its C API.

Installation
------------

Install this package, for example with **pip**:

.. code-block:: sh

    python -m pip install icu4py

Wheels are provided for Linux and macOS.
The Windows build has unresolved errors, as tracked in `Issue #11 <https://github.com/adamchainz/icu4py/issues/11>`__.

Wheels embed a recent version of ICU.
Right now, that is at least ICU 78 on most platforms, but for older Linux distributions it is ICU 72.
`Issue #16 <https://github.com/adamchainz/icu4py/issues/16>`__ tracks using a consistent version across all platforms.
