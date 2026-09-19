"""Tests for canvod.gnssgeodesy.config -- these models are fully
implemented (unlike most of this package's algorithmic modules), so
these are real correctness tests, not stubs."""

from __future__ import annotations

import pytest
from canvod.gnssgeodesy.config import (
    ArcStrategyConfig,
    NmriStrategyConfig,
    RefractionMethod,
    RefractionStrategyConfig,
    RhStrategyConfig,
)
from pydantic import ValidationError


def test_arc_strategy_config_defaults_tracking_codes() -> None:
    cfg = ArcStrategyConfig(min_elev_deg=5.0, max_elev_deg=25.0, max_gap_epochs=5)
    assert cfg.tracking_codes == {"L1": "C", "L2": "W"}


def test_arc_strategy_config_rejects_bad_elev_order() -> None:
    with pytest.raises(ValidationError):
        ArcStrategyConfig(min_elev_deg=25.0, max_elev_deg=5.0, max_gap_epochs=5)


def test_rh_strategy_config_defaults_match_gnssrefl() -> None:
    cfg = RhStrategyConfig(noise_region_m=(6.0, 8.0), max_gap_epochs=5)
    assert cfg.min_elev_deg == 5.0
    assert cfg.max_elev_deg == 25.0
    assert cfg.min_height_m == 0.5
    assert cfg.max_height_m == 8.0
    assert cfg.lsp_backend == "astropy"


def test_rh_strategy_config_rejects_bad_height_order() -> None:
    with pytest.raises(ValidationError):
        RhStrategyConfig(
            noise_region_m=(6.0, 8.0), max_gap_epochs=5, min_height_m=8.0, max_height_m=0.5
        )


@pytest.mark.parametrize(
    ("method", "time_varying", "expected_id"),
    [
        (RefractionMethod.BENNETT, False, 1),
        (RefractionMethod.BENNETT, True, 2),
        (RefractionMethod.ULICH, False, 3),
        (RefractionMethod.ULICH, True, 4),
        (RefractionMethod.NITE, True, 5),
        (RefractionMethod.MPF, True, 6),
    ],
)
def test_refraction_strategy_config_model_id_mapping(
    method: RefractionMethod, time_varying: bool, expected_id: int
) -> None:
    cfg = RefractionStrategyConfig(method=method, time_varying=time_varying)
    assert cfg.to_gnssrefl_model_id() == expected_id


def test_refraction_strategy_config_disabled_is_model_zero() -> None:
    cfg = RefractionStrategyConfig(enabled=False)
    assert cfg.to_gnssrefl_model_id() == 0


def test_refraction_strategy_config_rejects_nite_static() -> None:
    with pytest.raises(ValidationError):
        RefractionStrategyConfig(method=RefractionMethod.NITE, time_varying=False)


def test_nmri_strategy_config_elevation_defers_to_none() -> None:
    cfg = NmriStrategyConfig(max_gap_epochs=5, min_segment_epochs=10)
    assert cfg.min_elev_deg is None
    assert cfg.max_elev_deg is None
    assert cfg.baseline_top_fraction is None
    assert cfg.baseline_from is None
    assert cfg.climatology_min_years == 2


def test_nmri_strategy_config_allows_mixed_none_explicit_elev() -> None:
    # A None/non-None mix is allowed here -- each resolves independently
    # against AlphaCalibration at code_multipath.py's entry point.
    cfg = NmriStrategyConfig(max_gap_epochs=5, min_segment_epochs=10, min_elev_deg=12.0)
    assert cfg.min_elev_deg == 12.0
    assert cfg.max_elev_deg is None


def test_nmri_strategy_config_rejects_bad_explicit_elev_order() -> None:
    with pytest.raises(ValidationError):
        NmriStrategyConfig(
            max_gap_epochs=5,
            min_segment_epochs=10,
            min_elev_deg=20.0,
            max_elev_deg=10.0,
        )


def test_strict_models_reject_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        ArcStrategyConfig(
            min_elev_deg=5.0,
            max_elev_deg=25.0,
            max_gap_epochs=5,
            bogus_field=1,  # ty: ignore[unknown-argument]
        )
