"""Helpers for the date and time fields of non-canonical filenames."""

from __future__ import annotations

# RINEX v2 hour letter: a-x = 0-23
_HOUR_LETTER_MAP: dict[str, int] = {chr(ord("a") + h): h for h in range(24)}
_HOUR_LETTER_MAP["0"] = 0  # '0' also means hour 0


def hour_letter_to_int(letter: str) -> int:
    """Convert a RINEX hour letter (a-x or '0') to an integer 0-23.

    Raises
    ------
    ValueError
        If the letter is not a valid RINEX hour code.
    """
    try:
        return _HOUR_LETTER_MAP[letter.lower()]
    except KeyError:
        raise ValueError(f"Invalid hour letter: {letter!r}") from None


def resolve_year_from_yy(yy: int) -> int:
    """Expand a 2-digit year to 4 digits (80-99 → 1980-1999, 00-79 → 2000-2079)."""
    if yy >= 80:
        return 1900 + yy
    return 2000 + yy
