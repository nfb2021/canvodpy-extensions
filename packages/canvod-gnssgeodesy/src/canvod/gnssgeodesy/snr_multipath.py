"""Reflector height (RH) retrieval — the reflectometry (GNSS-IR) family.

Per arc:
1. `SNR` dB-Hz -> linear: `A = 10**(SNR/20)`. A fixed physical
   conversion, not gnssrefl-specific.
2. Detrend: plain polynomial fit (`np.polyfit`/`np.polyval`) against
   elevation-in-degrees, over `detrend_window_deg`, order
   `detrend_poly_order` (both `RhStrategyConfig` fields, gnssrefl's own
   defaults). This step stays canvod-native — it's textbook, not
   gnssrefl-proprietary geodesy — computed directly over canvodpy's own
   xarray-shaped arc data rather than routed through gnssrefl's on-disk
   multi-column SNR-file convention.
3. Lomb-Scargle periodogram and peak-pick: call gnssrefl's
   `strip_compute()` directly via `GnssreflRhComputer` below, passing the
   detrended residual from step 2 plus the per-satellite/frequency
   wavelength scale factor (also sourced from gnssrefl,
   `gnssrefl.gnss_frequencies.get_scale_factor`).
4. Noise floor / peak-to-noise stays canvod-native, computed on top of
   `strip_compute()`'s returned periodogram: `noise_region_m` (config)
   marks an RH range known to be past any real reflector;
   `peak2noise = amplitude / mean(periodogram_power in that window)`.
   There is no gnssrefl default for the noise region (its own
   `nr1`/`nr2` are `None` unless station-supplied) — require it
   explicitly per station, never invent one.
5. Refraction correction via `refraction.py` (not this module) — applied
   to elevation before arc detrending/LSP, not after.
6. Nyquist / maximum-resolvable-RH guard: `max_height_m` must be checked
   against the station's actual sampling interval at run time — a
   canvod-native sanity check on the config values themselves, not a
   call-through to anything gnssrefl computes.

QC (see `qc.py`): elevation-range compliance, arc duration bounds,
amplitude threshold, peak-to-noise ratio. Lomb-Scargle False Alarm
Probability (FAP) via the closed-form Baluev/Scargle formula is the sole
FAP path — astropy's own `LombScargle.false_alarm_probability()` requires
a fully-constructed `LombScargle` object holding internal state this
module never builds (it only ever sees `strip_compute()`'s returned
`(px, pz)` arrays); reconstructing that object would mean re-deriving
gnssrefl's internal transform, exactly the divergence risk wrapping
`strip_compute()` exists to avoid.

Daily aggregation: per-satellite (per-`sid`), not pooled across
satellites. Within each satellite's own arcs for the day, reject arcs
whose RH deviates from that satellite's day-median RH by more than a
configurable metres threshold, then report the mean (not median) of
survivors, plus a minimum-accepted-track count.

Output: `xr.Dataset`, dims `(epoch, sid)`, one timestamp per day.
Vars `RH`, `amplitude`, `peak2noise`, `n_arcs_used`. No `station` dim —
station is an Icechunk group-path routing parameter (`io.py`), never a
Dataset dimension. A separate per-day rollup (sample-count-weighted mean
of `RH` across available `sid`s that day, dims `(epoch,)`) feeds the
GNSS-VOD use case — see `io.py`.

Performance: the LSP step is inherently per-arc (astropy/scipy don't
batch irregular per-arc frequency grids in one call); the throughput
lever is `joblib` arc-level fan-out (`parallel` extra), never
`dask.delayed`/`dask.bag` — this project's convention is `joblib` for
parallel compute, `dask` only for lazy-array storage (Icechunk/zarr).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt
import xarray as xr
from canvod.gnssgeodesy.arcs import Arc
from canvod.gnssgeodesy.config import RhStrategyConfig


@dataclass(frozen=True)
class RhResult:
    """Runtime return value, not a config — numpy arrays don't belong in
    a YAML-round-trippable model."""

    rh_m: float
    amplitude: float
    elevation_min_observed_deg: float
    elevation_max_observed_deg: float
    rise_or_set: int  # gnssrefl's own convention kept as-is: 1 rise, -1 set
    periodogram_rh_m: npt.NDArray[np.floating]
    periodogram_power: npt.NDArray[np.floating]


class RhComputer:
    """Extension point mirroring RefractionCorrector. v1's only
    implementation wraps gnssrefl's gps.py:strip_compute() directly for
    the LSP peak-pick — the actual correctness-sensitive geodesy. A
    future alternative RH-retrieval method plugs in here as a second
    subclass, without touching call sites."""

    def __init__(self, config: RhStrategyConfig) -> None:
        self._config = config

    def compute(
        self,
        elevation_deg: npt.NDArray[np.floating],
        detrended_snr_linear: npt.NDArray[np.floating],
        *,
        frequency_code: int,
        satellite_number: int,
    ) -> RhResult:
        raise NotImplementedError


# gnssrefl's own strip_compute() takes lsp_method='fast'/'scipy' — 'fast' is
# just its chosen sentinel for "use astropy" (the branch condition is
# literally `if lsp_method == 'scipy': ... else: <astropy>`). RhStrategyConfig
# .lsp_backend names the actual library instead of reusing that internal
# shorthand; this dict is the one place the translation happens.
_GNSSREFL_LSP_METHOD: dict[str, str] = {"astropy": "fast", "scipy": "scipy"}


class GnssreflRhComputer(RhComputer):
    """v1's only implementation. Looks up gnssrefl's own wavelength scale
    factor, calls strip_compute() unmodified, wraps its 7-tuple return
    into RhResult. No LSP math is reimplemented, altered, or ported."""

    def compute(
        self,
        elevation_deg: npt.NDArray[np.floating],
        detrended_snr_linear: npt.NDArray[np.floating],
        *,
        frequency_code: int,
        satellite_number: int,
    ) -> RhResult:
        # optional dep (`gnssrefl` extra) — imported lazily so the rest of
        # canvod-gnssgeodesy works with the extra uninstalled
        from gnssrefl.gnss_frequencies import get_scale_factor
        from gnssrefl.gps import strip_compute

        cf = get_scale_factor(frequency_code, satellite_number)
        maxF, maxAmp, eminObs, emaxObs, riseSet, px, pz = strip_compute(
            elevation_deg,
            detrended_snr_linear,
            cf,
            self._config.max_height_m,
            self._config.desired_precision_m,
            self._config.min_height_m,
            lsp_method=_GNSSREFL_LSP_METHOD[self._config.lsp_backend],
        )
        return RhResult(
            rh_m=maxF,
            amplitude=maxAmp,
            elevation_min_observed_deg=eminObs,
            elevation_max_observed_deg=emaxObs,
            rise_or_set=riseSet,
            periodogram_rh_m=px,
            periodogram_power=pz,
        )


def build_rh_computer(config: RhStrategyConfig) -> RhComputer:
    """Factory — today always returns GnssreflRhComputer. Same seam as
    build_refraction_corrector: callers depend on the RhComputer ABC,
    never the concrete class."""
    return GnssreflRhComputer(config)


def compute_rh_for_station(
    ds: xr.Dataset,
    arcs: list[Arc],
    config: RhStrategyConfig,
    *,
    station_id: str,
) -> xr.Dataset:
    """Entry point: detrend + RH retrieval + refraction + daily
    per-`sid` aggregation, over every arc for one station.

    Not yet implemented (Phase 3) — steps 1/2/4/6 in the module
    docstring above are canvod-native and still need writing; step 3
    (`GnssreflRhComputer`) and step 5 (`refraction.py`) already exist
    and are wired here once the surrounding pipeline is built.
    """
    raise NotImplementedError(
        "snr_multipath.compute_rh_for_station: Phase 3, not yet "
        "implemented. RhComputer/GnssreflRhComputer above are complete; "
        "the detrend -> compute -> refraction -> daily-aggregate pipeline "
        "around them is not."
    )
