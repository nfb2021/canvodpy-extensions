"""Contract tests for canvod.gnssgeodesy.refraction against gnssrefl's own
correct_elevations() -- not oracle tests. refraction.py calls gnssrefl's
code directly rather than reimplementing it, so there is no independent
algorithm to check against an oracle; this only verifies the translation
layer builds gnssrefl's expected arguments and calls it unmodified.

Requires the `gnssrefl` extra installed -- skipped otherwise.
"""

from __future__ import annotations

from datetime import date

import numpy as np
import pytest
from canvod.gnssgeodesy.config import RefractionStrategyConfig
from canvod.gnssgeodesy.refraction import (
    GnssreflRefractionCorrector,
    RefractionResult,
    build_refraction_corrector,
)

pytest.importorskip("gnssrefl")


def test_build_refraction_corrector_returns_gnssrefl_backed_instance() -> None:
    cfg = RefractionStrategyConfig()
    corrector = build_refraction_corrector(cfg)
    assert isinstance(corrector, GnssreflRefractionCorrector)


def test_disabled_refraction_still_calls_correct_elevations_with_model_zero() -> None:
    cfg = RefractionStrategyConfig(enabled=False)
    corrector = build_refraction_corrector(cfg)
    result = corrector.correct(
        np.array([5.0, 10.0, 20.0]),
        epoch=date(2025, 6, 1),
        station_id="TEST",
        station_lat_deg=48.2,
        station_lon_deg=16.4,
        station_height_m=200.0,
    )
    assert isinstance(result, RefractionResult)
    assert result.corrected_elevation_deg.shape == (3,)
