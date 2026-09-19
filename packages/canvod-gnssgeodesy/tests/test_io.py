"""Tests for canvod.gnssgeodesy.io -- skipped unless the `store` extra is
installed, same convention as canvod-adapters' test_io.py.

Both functions currently raise NotImplementedError unconditionally: the
canvodpy-core touch points they depend on (a dedicated `geodesy_store`,
`write_or_append_geodesy_group()` in canvod-store) don't exist yet as of
this package's initial scaffold. These tests document that state
honestly rather than mocking around it.
"""

from __future__ import annotations

import pytest
import xarray as xr

pytest.importorskip("canvod.store")

from canvod.gnssgeodesy.io import read_geodesy_group, write_or_append_geodesy_group


def test_write_or_append_geodesy_group_not_yet_implemented() -> None:
    with pytest.raises(NotImplementedError, match="canvodpy-core touch points"):
        write_or_append_geodesy_group(
            None, "code_multipath/nmri/default", xr.Dataset(), {}, {}, "nmri"
        )


def test_read_geodesy_group_not_yet_implemented() -> None:
    with pytest.raises(NotImplementedError, match="canvodpy-core touch points"):
        read_geodesy_group(None, "TEST_STATION", "code_multipath", "default")
