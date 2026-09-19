"""Shared, threshold-based arc/day-level quality control.

RH (`snr_multipath.py`): elevation-range compliance, arc duration bounds,
amplitude threshold, peak-to-noise ratio, reject-if-too-close-to-search-
bounds. Two strategies:

- **Default (gnssrefl-compatible)**: `peak2noise_min`, `req_amp_min`,
  `delT_max_min`, `ediff_deg` -- all sourced from gnssrefl's own
  `gnssir_input.py` defaults (see `config.py`'s `RhStrategyConfig`).
- **Improved (opt-in)**: Lomb-Scargle False Alarm Probability (FAP) via
  the closed-form Baluev/Scargle formula (Scargle 1982; VanderPlas 2018;
  Baluev 2008), not gnssrefl's ad hoc peak/noise-region thresholds, and
  not astropy's `LombScargle.false_alarm_probability()` either -- that
  method needs a fully-constructed `LombScargle` object holding internal
  state this package never builds (only `strip_compute()`'s returned
  `(px, pz)` arrays are available). The closed-form formula is computable
  from data already owned outright: the arc's own point count `N`, plus
  `strip_compute()`'s own `(px, pz)` for the peak height and
  frequency-grid span.

NMRI (`code_multipath.py`): MAD-based outlier filter on daily `MP1rms`,
not a plain 3-sigma filter -- multipath residuals are right-skewed, and a
symmetric cutoff would systematically over-reject the high tail, which is
exactly the vegetation signal being measured.
"""

from __future__ import annotations

import numpy as np
import numpy.typing as npt


def compute_fap_baluev(
    periodogram_power: npt.NDArray[np.floating],
    periodogram_frequency: npt.NDArray[np.floating],
    n_points: int,
) -> float:
    """Closed-form Baluev/Scargle False Alarm Probability for the
    periodogram's peak, given only what `strip_compute()` already
    returns plus the arc's own point count -- no `LombScargle` object
    reconstruction required.

    Not yet implemented (Phase 3).
    """
    raise NotImplementedError("qc.compute_fap_baluev: Phase 3, not yet implemented.")


def mad_outlier_mask(
    values: npt.NDArray[np.floating],
    *,
    threshold: float,
) -> npt.NDArray[np.bool_]:
    """Median-absolute-deviation outlier mask (`True` = keep), for
    filtering daily `MP1rms` before baseline/NMRI computation.

    Not yet implemented (Phase 2).
    """
    raise NotImplementedError("qc.mad_outlier_mask: Phase 2, not yet implemented.")
