============
Installation
============

Requirements
------------

Python 3.10 to 3.14 supported, including free-threaded variants from Python 3.13 onwards.

Only CPython is supported at this time because ICU uses its C API.

Installation
------------

1. Install ICU4C:

   * **On macOS:** ``brew install icu4c``

   * **On Ubuntu/Debian:** ``apt-get install libicu-dev``

   * **On RHEL/CentOS:** ``yum install libicu-devel``

   * **On Windows:** ``vcpkg install icu``

   Version 78+ supported.

2. Install this package, for example with **pip**:

   .. code-block:: sh

      python -m pip install icu4py

   Wheels are provided for Linux and macOS.
   The Windows build has unresolved errors, as tracked in `Issue #11 <https://github.com/adamchainz/icu4py/issues/11>`__.
