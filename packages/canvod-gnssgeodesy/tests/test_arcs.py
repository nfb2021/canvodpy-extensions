"""Tests for canvod.gnssgeodesy.arcs. detect_arcs() itself is a Phase 1
stub -- these tests only cover what's actually implemented so far."""

from __future__ import annotations

import pytest
import xarray as xr
from canvod.gnssgeodesy.arcs import DEFAULT_TRACKING_CODES, detect_arcs


def test_default_tracking_codes() -> None:
    assert DEFAULT_TRACKING_CODES == {"L1": "C", "L2": "W"}


def test_detect_arcs_not_yet_implemented(reader_shaped_ds: xr.Dataset) -> None:
    with pytest.raises(NotImplementedError):
        detect_arcs(
            reader_shaped_ds,
            min_elev_deg=5.0,
            max_elev_deg=25.0,
            azimuth_sectors=None,
            max_gap_epochs=5,
        )
