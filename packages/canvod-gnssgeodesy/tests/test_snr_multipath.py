"""Tests for canvod.gnssgeodesy.snr_multipath.

GnssreflRhComputer needs the `gnssrefl` extra installed to actually run
-- see test_refraction.py for the same skip convention. The
pipeline-level entry point is a Phase 3 stub.
"""

from __future__ import annotations

import pytest
import xarray as xr
from canvod.gnssgeodesy.config import RhStrategyConfig
from canvod.gnssgeodesy.snr_multipath import build_rh_computer, compute_rh_for_station

pytest.importorskip("gnssrefl")


def test_build_rh_computer_returns_gnssrefl_backed_instance() -> None:
    from canvod.gnssgeodesy.snr_multipath import GnssreflRhComputer

    cfg = RhStrategyConfig(noise_region_m=(6.0, 8.0), max_gap_epochs=5)
    computer = build_rh_computer(cfg)
    assert isinstance(computer, GnssreflRhComputer)


def test_compute_rh_for_station_not_yet_implemented(reader_shaped_ds: xr.Dataset) -> None:
    cfg = RhStrategyConfig(noise_region_m=(6.0, 8.0), max_gap_epochs=5)
    with pytest.raises(NotImplementedError):
        compute_rh_for_station(reader_shaped_ds, [], cfg, station_id="TEST")
