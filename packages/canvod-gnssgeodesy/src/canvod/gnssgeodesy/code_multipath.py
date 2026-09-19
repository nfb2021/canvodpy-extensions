"""Code/pseudorange multipath — MP1 -> MP1rms -> NMRI.

The one product family in this package that is a genuine from-scratch,
literature-sourced implementation rather than a wrapped community-trusted
core. gnssrefl never implements MP1/NMRI in code at all — its own
`computemp1mp2.py` shells out to the deprecated `teqc` binary and parses
its text log output. There is nothing to wrap; this module is built
directly from Larson & Small (2014, IEEE JSTARS) and Small, Larson &
Smith (2014).

Formula: `estimateSignalDelays()`'s MP1 combination (gnssmultipath,
verified by reading the function directly) depends on exactly one
physical quantity, `alpha = carrier_freq1**2 / carrier_freq2**2` — no
GPS-specific constant appears anywhere in the function itself. What does
NOT transfer across constellations/band-pairs is the *literature
calibration* (elevation mask, baseline fraction): a closely-spaced pair
(e.g. Galileo E5a/E5b) amplifies phase noise via the `2/(alpha-1)`
coefficient far more than a widely-spaced one (GPS L1/L2), so calibration
is keyed per band-pair via `AlphaCalibration` below, not merely per
constellation. GPS L1/L2 is the only registered entry in v1; the
formula's own generality is preserved so a future Galileo/BeiDou entry is
a registry addition, not a code change.

Elevation-mask/baseline-fraction resolution: `NmriStrategyConfig.
min_elev_deg`/`max_elev_deg`/`baseline_top_fraction` are `None`-defaults
that fall back to `get_alpha_calibration(constellation).
elevation_mask_deg`/`baseline_top_fraction` — an explicit config value
always overrides the literature-sourced default. Resolution happens once,
before `detect_arcs()` is called, against the active constellation.

Normalization: per-`sv` (satellite), not pooled across satellites —
pooling would mix different elevation/geometry multipath regimes into a
single threshold. `NMRI = (MP1max - MP1rms) / MP1max`, computed per `sv`
per day. `NMRI` goes negative on the very days that define `MP1max`
itself (the baseline days' own `MP1rms` sit at or above `MP1max`) — an
expected property of the normalization, not a bug.

NMRI baseline (`MP1max`): a two-tier policy, not a single frozen or
ever-recomputed window.

- Tier 1 (record shorter than `NmriStrategyConfig.climatology_min_years`,
  default 2): `MP1max` = mean of the top `baseline_top_fraction` of that
  satellite's `MP1rms` history across the *entire available record so
  far* — Larson & Small's literal definition, honestly provisional
  (shifts as more data arrives).
- Tier 2 (record at or past `climatology_min_years`): `MP1max` is frozen
  over an explicit `baseline_from` climatology window, set manually by a
  caller — never an automatic transition. This is what makes NMRI
  eligible for `io.py`'s append/dedup write mechanism at all (a per-day-
  independent value), instead of needing a whole-series overwrite on
  every run.
- `climatology_min_years=2` is this package's own engineering judgment
  (the literature is silent on this exact operational question) — the
  floor at which "climatology" stops being numerically identical to the
  raw record: with only one year of data there is nothing independent to
  average over.
- Revisiting a Tier 2 station's frozen window as decades of data
  accumulate is an explicit, deliberate stub (see
  `raise_climatology_revision_not_implemented` below) — likely a future
  moving/rolling window, cadence and mechanism unresolved. The one
  related case that *is* handled, because it's a discontinuity rather
  than a moving-window problem: a station hardware change (antenna,
  radome, receiver swap) must split the baseline into separate eras.

Output: `xr.Dataset`, dims `(epoch, sv)` (GPS-only in v1, so always a `G`
prefix), one timestamp per day. Vars `MP1rms`, `NMRI`, `MP1max` (the
normalizer itself is always an output variable), `nmri_baseline_n_days`,
`nmri_baseline_confidence` (both per-`sv`). No `station` dim — see
`io.py`. A separate per-day rollup (`sv` -> scalar) feeds the
GNSS-VOD-facing use case, same pattern as `snr_multipath.py`'s `sid` ->
scalar rollup.
"""

from __future__ import annotations

from dataclasses import dataclass

import xarray as xr
from canvod.gnssgeodesy.arcs import Arc
from canvod.gnssgeodesy.config import NmriStrategyConfig


@dataclass(frozen=True)
class AlphaCalibration:
    """One literature-validated (constellation, band-pair) combination
    for code_multipath. Named after `alpha = carrier_freq1**2 /
    carrier_freq2**2` — the one physical quantity
    `estimateSignalDelays()` actually depends on — because everything
    else here (`elevation_mask_deg`, `baseline_top_fraction`) is a number
    the literature derived *for that specific alpha*, not a
    constellation-level constant."""

    constellation: str  # sv's leading letter, e.g. "G", "E", "C", "R"
    band_pair: tuple[str, str]  # e.g. ("L1", "L2"), ("E1", "E5a")
    carrier_freq1_hz: float  # float64, exact — precision matters, see module docstring
    carrier_freq2_hz: float
    range_codes: tuple[str, str]  # (range1_Code, range2_Code) passed to estimateSignalDelays()
    elevation_mask_deg: tuple[float, float]
    baseline_top_fraction: float
    citation: str  # literature source for elevation_mask_deg/baseline_top_fraction specifically

    @property
    def alpha(self) -> float:
        return (self.carrier_freq1_hz / self.carrier_freq2_hz) ** 2


_ALPHA_CALIBRATION_REGISTRY: dict[str, AlphaCalibration] = {
    "G": AlphaCalibration(
        constellation="G",
        band_pair=("L1", "L2"),
        carrier_freq1_hz=1575.42e6,
        carrier_freq2_hz=1227.60e6,
        # PBO's Trimble NetRS receivers have no P-code access, so "P1" in the
        # classic MP1 formula is populated by C/A-code C1 in practice; "C2W"
        # is required by estimateSignalDelays()'s signature but only gates
        # missing-obs completeness.
        range_codes=("C1C", "C2W"),
        elevation_mask_deg=(
            10.0,
            15.0,
        ),  # classic teqc MP1 mask / Larson & Small 2014-family convention
        baseline_top_fraction=0.05,
        citation=(
            "Larson & Small 2014 (IEEE JSTARS); Small, Larson & Smith 2014; "
            "Small, Larson & Braun 2010 (GRL); classic teqc MP1 convention "
            "(Estey & Meertens 1999)"
        ),
    ),
    # Architecturally pluggable, not registered in v1: Galileo E1/E5a and
    # BeiDou B1I/B3I are the most plausible next entries (both widely-spaced
    # pairs); GLONASS is additionally blocked independent of calibration by
    # its FDMA channel-dependent frequencies.
}


def get_alpha_calibration(constellation: str) -> AlphaCalibration:
    """Raises, does not silently fall back to GPS — the single
    enforcement point for this package's GPS-only-in-v1 restriction."""
    try:
        return _ALPHA_CALIBRATION_REGISTRY[constellation]
    except KeyError:
        raise NotImplementedError(
            f"No AlphaCalibration registered for constellation {constellation!r}. "
            "estimateSignalDelays()'s formula itself is constellation-generic "
            "(alpha-only dependency) — what's missing is a literature-sourced "
            "(or internally noise-floor-characterized) elevation_mask_deg/"
            "baseline_top_fraction for this constellation/band-pair, not a "
            "code change."
        ) from None


def raise_climatology_revision_not_implemented(station_id: str, sv: str) -> None:
    """Explicit stub, not a bug. Called wherever a Tier 2 station's
    `baseline_from` would otherwise need automatic revision as new years
    of data accumulate. How this should work (most likely a
    periodically-revised trailing window, in the spirit of meteorological
    climate-normal revisions) is a deliberately deferred design question
    — cadence, overlap handling, and how to avoid retroactively rewriting
    already-published `NMRI` values are all unresolved. The only
    supported path today is an operator setting a new `baseline_from`
    explicitly, same as the initial Tier 1 -> Tier 2 transition."""
    raise NotImplementedError(
        f"Automatic climatology revision is not implemented (station={station_id!r}, "
        f"sv={sv!r}). A Tier 2 station's baseline_from must be updated manually; "
        "see code_multipath.py's module docstring and RATIONALE.md §33 before "
        "attempting to implement this."
    )


def compute_nmri_for_station(
    ds: xr.Dataset,
    arcs: list[Arc],
    config: NmriStrategyConfig,
    *,
    station_id: str,
    exclude_days: xr.DataArray | None = None,
) -> xr.Dataset:
    """Entry point: elevation/fraction resolution against
    `AlphaCalibration`, MP1 computation (`gnssmultipath`'s
    `estimateSignalDelays()`), per-`sv` MP1rms/MP1max/NMRI aggregation,
    per the two-tier baseline policy in this module's docstring.

    `exclude_days` is a runtime argument, not a config field — an
    `xr.DataArray` in a pydantic model needs `arbitrary_types_allowed`
    and breaks YAML round-tripping.

    Not yet implemented (Phase 2).
    """
    raise NotImplementedError(
        "code_multipath.compute_nmri_for_station: Phase 2, not yet "
        "implemented. AlphaCalibration/get_alpha_calibration above are "
        "complete; the MP1 computation and per-sv aggregation pipeline "
        "around them is not."
    )
