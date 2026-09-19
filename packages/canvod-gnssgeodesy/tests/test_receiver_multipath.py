"""Tests for canvod.gnssgeodesy.receiver_multipath -- Phase 4 stub."""

from __future__ import annotations

import pytest
import xarray as xr
from canvod.gnssgeodesy.receiver_multipath import compute_receiver_multipath_for_station


def test_compute_receiver_multipath_for_station_not_yet_implemented() -> None:
    with pytest.raises(NotImplementedError):
        compute_receiver_multipath_for_station(xr.Dataset(), station_id="TEST")
