"""Tests for canvod.gnssgeodesy.provenance -- fully implemented."""

from __future__ import annotations

from datetime import UTC, datetime

from canvod.gnssgeodesy.config import RhStrategyConfig
from canvod.gnssgeodesy.provenance import build_provenance_attrs


def test_build_provenance_attrs_rh() -> None:
    cfg = RhStrategyConfig(noise_region_m=(6.0, 8.0), max_gap_epochs=5)
    ts = datetime(2025, 1, 1, tzinfo=UTC)
    attrs = build_provenance_attrs("rh", "TEST_STATION", cfg, timestamp=ts)

    assert attrs["retrieval_algorithm"] == "lomb_scargle_snr_multipath"
    assert "Larson" in attrs["retrieval_paper_reference"]
    assert attrs["station"] == "TEST_STATION"
    assert attrs["retrieval_timestamp"] == ts.isoformat()
    assert isinstance(attrs["strategy_config_hash"], str)
    assert len(attrs["strategy_config_hash"]) == 64  # sha256 hex digest


def test_strategy_config_hash_is_deterministic_and_sensitive() -> None:
    cfg_a = RhStrategyConfig(noise_region_m=(6.0, 8.0), max_gap_epochs=5)
    cfg_b = RhStrategyConfig(noise_region_m=(6.0, 8.0), max_gap_epochs=5)
    cfg_c = RhStrategyConfig(noise_region_m=(7.0, 9.0), max_gap_epochs=5)

    attrs_a = build_provenance_attrs("rh", "S", cfg_a)
    attrs_b = build_provenance_attrs("rh", "S", cfg_b)
    attrs_c = build_provenance_attrs("rh", "S", cfg_c)

    assert attrs_a["strategy_config_hash"] == attrs_b["strategy_config_hash"]
    assert attrs_a["strategy_config_hash"] != attrs_c["strategy_config_hash"]


def test_build_provenance_attrs_unknown_package_version_does_not_raise() -> None:
    cfg = RhStrategyConfig(noise_region_m=(6.0, 8.0), max_gap_epochs=5)
    attrs = build_provenance_attrs("nmri", "S", cfg)
    assert isinstance(attrs["canvod_gnssgeodesy_version"], str)
