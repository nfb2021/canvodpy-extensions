"""Shared arc segmentation: rise/set detection, azimuth-sector filtering.

Used by both `snr_multipath.py` (RH) and `code_multipath.py` (MP1/NMRI) —
the only genuinely shared geometry/segmentation logic between the two
product families. Nothing here is retrieval-algorithm-specific.

Implementation status: signatures and data shapes below are fixed by
design; `detect_arcs()`'s body is not yet implemented (Phase 1).
"""

from __future__ import annotations

from typing import NamedTuple

import numpy as np
import numpy.typing as npt
import xarray as xr

#: Per-band tracking-code selection policy. Deliberately a fixed,
#: explicit, user-overridable default — never auto-detected per
#: station/file. Many current receivers report L2C-based codes
#: ("L"/"X"/"Q") instead of legacy semi-codeless "W"; auto-discovery
#: would silently mix tracking methods with different, uncalibrated
#: noise floors across stations/days without the caller ever choosing
#: that. Verified against Larson & Small's own text, not an arbitrary or
#: gnssmultipath-docstring-derived choice.
DEFAULT_TRACKING_CODES: dict[str, str] = {"L1": "C", "L2": "W"}


class Arc(NamedTuple):
    """One rise-to-set (or set-to-rise) satellite pass, already sliced
    out of a station's full epoch axis.

    `epoch_index` is an index array, not a slice: arcs on a real,
    SID-padded grid can have interior NaN gaps (padding to the global SID
    universe reindexes with `fill_value=NaN`), which a plain slice can't
    represent. `elevation_deg`/`azimuth_deg` are derived from it rather
    than carried independently, so the two can never disagree.
    """

    sid: str
    satellite: str  # e.g. "G01"
    band: str  # e.g. "L1"
    tracking_code: str  # e.g. "C" vs "W" — see DEFAULT_TRACKING_CODES
    rise_set: int  # +1 rise, -1 set
    epoch_index: npt.NDArray[np.integer]  # integer indices into the parent Dataset's epoch axis
    azimuth_at_min_elev: (
        float  # summary value for output/QC/plotting only — see module docstring below
    )
    elevation_deg: npt.NDArray[np.floating]
    azimuth_deg: npt.NDArray[np.floating]


def detect_arcs(
    ds: xr.Dataset,
    *,
    min_elev_deg: float,
    max_elev_deg: float,
    azimuth_sectors: list[tuple[float, float]] | None,
    max_gap_epochs: int,
    theta_var: str = "theta",
    constellations: list[str] | None = None,
    tracking_codes: dict[str, str] | None = None,
) -> list[Arc]:
    """Segment a station's epoch axis into per-satellite, per-band rise/set arcs.

    Parameters
    ----------
    ds
        Reader/VOD-shaped Dataset. Must carry `theta_var`/`phi` in
        radians (`theta ∈ [0, π/2]` once below-horizon values are NaN'd
        out) — there is no bare `elevation`/`azimuth` variable on raw
        reader output; convert via
        `elevation_deg = 90 - np.degrees(theta)`,
        `azimuth_deg = np.degrees(phi) % 360`.
    min_elev_deg, max_elev_deg
        Elevation mask, degrees. Already-resolved, non-Optional values —
        callers using a `None`-means-defer-to-literature-default config
        field (e.g. `NmriStrategyConfig`) must resolve that *before*
        calling this function, not pass `None` through.
    azimuth_sectors
        Filters the full per-epoch `azimuth_deg` array, not
        `azimuth_at_min_elev` — matching gnssrefl's own behaviour
        (`window_data()`/`removeDC()` mask every sample by
        `(azi > az1) & (azi < az2)` against the full per-epoch array). A
        pass whose azimuth drifts across a sector boundary is therefore
        partially masked, not whole-arc accepted/rejected.
    max_gap_epochs
        Sampling-interval-relative gap tolerance before a pass is split
        into two arcs.
    theta_var
        Elevation-angle source variable name, in radians. NOT
        `"elevation"` — no such variable exists on raw reader/
        ephemeris-augmented output.
    constellations
        Leading-SID-character allowlist (e.g. `["G"]`). Defaults to
        GPS-only if not given.
    tracking_codes
        Per-band tracking-code selection (see `DEFAULT_TRACKING_CODES`).
        Defaults to the module-level default if not given.

    Returns
    -------
    list[Arc]

    Notes
    -----
    `azimuth_at_min_elev` is a single summary value per arc — the
    `azimuth_deg` sample at the arc's lowest-elevation endpoint (index
    `0` for a rising arc, `-1` for a setting arc, given `epoch_index` is
    time-ordered ascending). It exists for output/QC/plotting (a compact
    "where on the horizon" tag), not for filtering — see
    `azimuth_sectors` above.

    `theta` is float32; boundary detection by a raw sign-of-diff on
    elevation will chatter near the arc apex (elevation-rate approaches
    zero there) — use a smoothed gradient or hysteresis band, not a raw
    `diff` sign flip.
    """
    raise NotImplementedError(
        "arcs.detect_arcs: Phase 1, not yet implemented. Signature and "
        "data-shape contract above are fixed by design; segmentation "
        "algorithm (hysteresis-based rise/set boundary detection, "
        "per-epoch azimuth-sector masking, tracking-code resolution) is "
        "not yet written — do not guess at it without a design "
        "discussion first."
    )
