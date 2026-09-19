"""Tests for canvod.gnssgeodesy.code_multipath.

AlphaCalibration/get_alpha_calibration/raise_climatology_revision_not_implemented
are fully implemented; compute_nmri_for_station is a Phase 2 stub.
"""

from __future__ import annotations

import pytest
import xarray as xr
from canvod.gnssgeodesy.code_multipath import (
    compute_nmri_for_station,
    get_alpha_calibration,
    raise_climatology_revision_not_implemented,
)
from canvod.gnssgeodesy.config import NmriStrategyConfig


def test_gps_alpha_calibration_registered() -> None:
    calib = get_alpha_calibration("G")
    assert calib.band_pair == ("L1", "L2")
    assert calib.elevation_mask_deg == (10.0, 15.0)
    assert calib.baseline_top_fraction == 0.05
    # alpha = (carrier_freq1 / carrier_freq2) ** 2 -- verified against
    # estimateSignalDelays.py's own definition, not re-derived here.
    expected_alpha = (1575.42e6 / 1227.60e6) ** 2
    assert calib.alpha == pytest.approx(expected_alpha)


def test_unregistered_constellation_raises_not_silently_falls_back() -> None:
    with pytest.raises(NotImplementedError, match="No AlphaCalibration registered"):
        get_alpha_calibration("E")


def test_climatology_revision_stub_raises() -> None:
    with pytest.raises(NotImplementedError, match="climatology revision"):
        raise_climatology_revision_not_implemented("TEST_STATION", "G01")


def test_compute_nmri_for_station_not_yet_implemented(reader_shaped_ds: xr.Dataset) -> None:
    cfg = NmriStrategyConfig(max_gap_epochs=5, min_segment_epochs=10)
    with pytest.raises(NotImplementedError):
        compute_nmri_for_station(reader_shaped_ds, [], cfg, station_id="TEST")
