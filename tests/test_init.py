from __future__ import annotations

import pytest

import icu4py


class TestGetAttr:
    def test_getattr_unknown_attribute(self):
        with pytest.raises(AttributeError, match="has no attribute 'nonexistent'"):
            icu4py.nonexistent  # noqa: B018


class TestVersionInfo:
    def test_icu_version_is_string(self):
        assert isinstance(icu4py.icu_version, str)

    def test_icu_version_format(self):
        assert "." in icu4py.icu_version
        parts = icu4py.icu_version.split(".")
        assert len(parts) >= 2
        assert all(part.isdigit() for part in parts)

    def test_icu_version_info_is_tuple(self):
        assert isinstance(icu4py.icu_version_info, tuple)

    def test_icu_version_info_length(self):
        assert len(icu4py.icu_version_info) == 4

    def test_icu_version_info_contains_integers(self):
        assert all(isinstance(v, int) for v in icu4py.icu_version_info)

    def test_icu_version_info_matches_version_string(self):
        major, minor, patch, build = icu4py.icu_version_info
        version_str = icu4py.icu_version
        assert version_str.startswith(f"{major}.{minor}")
