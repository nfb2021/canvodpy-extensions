"""Atmospheric refraction correction for reflector-height retrieval.

Wraps gnssrefl's own `refraction.py` directly rather than reimplementing
Landskron & Böhm (2018) or any other refraction model from scratch —
gnssrefl is the community-established baseline here, and re-deriving its
logic independently risks a silent divergence for no correctness benefit.
This module contains a translation layer only: canvodpy-shaped inputs in,
gnssrefl's `station_config` dict built and passed through, its output
translated back out. No refraction geodesy is written here.

gnssrefl's own refraction model (verified by reading `refraction.py` in
full) is not real-time/NWM-driven VMF3 — it's a one-time-downloaded
static 1°x1° grid (`gpt_1wA.pickle`, an older GPT2w-generation model)
evaluated with a built-in annual+semiannual harmonic for "time variation."
There is no live network dependency at correction time.

`RefractionMethod`/`RefractionStrategyConfig` (see `config.py`) expose
this as four named methods crossed with a `time_varying` flag, replacing
gnssrefl's numbered `refr_model` (1-6) with names — gnssrefl's own CLI
already lets users type "NITE"/"MPF" for models 5/6 but not names for
1-4; this extends that same idea uniformly.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date

import numpy as np
import numpy.typing as npt
from canvod.gnssgeodesy.config import RefractionStrategyConfig


@dataclass(frozen=True)
class RefractionResult:
    """Runtime return value, not a config — deliberately a plain
    dataclass, not pydantic: numpy arrays don't belong in a
    YAML-round-trippable model."""

    corrected_elevation_deg: npt.NDArray[np.floating]
    valid_mask: npt.NDArray[np.bool_]


class RefractionCorrector(ABC):
    """Extension point. v1 ships exactly one implementation, backed
    directly by gnssrefl's own refraction.py. A later, literature-
    motivated alternative (e.g. a live/periodically-refreshed
    VMF3-operational-grid corrector instead of gnssrefl's static-grid-
    plus-harmonic model) plugs in here as a second subclass, with zero
    changes to call sites."""

    def __init__(self, config: RefractionStrategyConfig) -> None:
        self._config = config

    @abstractmethod
    def correct(
        self,
        elevation_deg: npt.NDArray[np.floating],
        *,
        epoch: date,
        station_id: str,
        station_lat_deg: float,
        station_lon_deg: float,
        station_height_m: float,
    ) -> RefractionResult: ...


class GnssreflRefractionCorrector(RefractionCorrector):
    """v1's only implementation. A thin translation layer: builds the
    `station_config` dict gnssrefl.refraction.correct_elevations()
    expects, calls it unmodified, wraps its `(corrected_ele, valid_mask)`
    tuple back into RefractionResult. No gnssrefl logic is reimplemented,
    altered, or ported — this class contains zero geodesy, only
    translation."""

    def correct(
        self,
        elevation_deg: npt.NDArray[np.floating],
        *,
        epoch: date,
        station_id: str,
        station_lat_deg: float,
        station_lon_deg: float,
        station_height_m: float,
    ) -> RefractionResult:
        # optional dep (`gnssrefl` extra) — imported lazily so the rest of
        # canvod-gnssgeodesy works with the extra uninstalled
        from gnssrefl.refraction import correct_elevations

        station_config = {
            "station": station_id,
            "lat": station_lat_deg,
            "lon": station_lon_deg,
            "ht": station_height_m,
            "refraction": self._config.enabled,
            "refr_model": self._config.to_gnssrefl_model_id(),
            "apriori_rh": self._config.apriori_rh_m,
        }
        corrected, valid_mask = correct_elevations(
            elevation_deg,
            station_config,
            epoch.year,
            epoch.timetuple().tm_yday,
            verbose=False,
        )
        return RefractionResult(corrected_elevation_deg=corrected, valid_mask=valid_mask)


def build_refraction_corrector(config: RefractionStrategyConfig) -> RefractionCorrector:
    """Factory — today always returns GnssreflRefractionCorrector. This
    is the seam a future dynamic-source corrector registers into;
    callers only ever depend on the RefractionCorrector ABC, never the
    concrete class."""
    return GnssreflRefractionCorrector(config)
