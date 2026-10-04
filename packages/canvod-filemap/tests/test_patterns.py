"""Tests for canvod.filemap.patterns."""

import pytest
from canvod.filemap.patterns import hour_letter_to_int, resolve_year_from_yy


class TestHourLetterToInt:
    def test_a_is_zero(self):
        assert hour_letter_to_int("a") == 0

    def test_x_is_23(self):
        assert hour_letter_to_int("x") == 23

    def test_zero_char_is_zero(self):
        assert hour_letter_to_int("0") == 0

    def test_invalid_raises(self):
        with pytest.raises(ValueError, match="Invalid hour letter"):
            hour_letter_to_int("z")

    def test_uppercase_accepted(self):
        assert hour_letter_to_int("B") == 1


class TestResolveYearFromYy:
    def test_year_00(self):
        assert resolve_year_from_yy(0) == 2000

    def test_year_25(self):
        assert resolve_year_from_yy(25) == 2025

    def test_year_79(self):
        assert resolve_year_from_yy(79) == 2079

    def test_year_80(self):
        assert resolve_year_from_yy(80) == 1980

    def test_year_99(self):
        assert resolve_year_from_yy(99) == 1999
