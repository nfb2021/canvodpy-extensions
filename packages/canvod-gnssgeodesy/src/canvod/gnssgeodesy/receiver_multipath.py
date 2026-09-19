"""SBF firmware-reported multipath — diagnostic only, SBF-only.

Reads firmware `mp_correction_m`/`car_mp_corr_cycles` from the SBF
reader's **metadata** dataset (`metadata/sbf_obs`, not the main
observation group — a different read path than `snr_multipath.py`/
`code_multipath.py`). Both source variables are dims `["epoch", "sid"]`
at raw (per-observation-epoch) resolution (verified directly against two
call sites in `sbf/reader.py` that emit the same fields with identical
dims).

Aggregates to a daily per-`sid` mean/std — `sid`, not `sv`: unlike
MP1/NMRI, these are true per-observable firmware corrections (one value
per band/code, not a value that mixes two observation codes into a
single per-satellite number), so `snr_multipath.py`'s per-`sid`
resolution is the right model here, not `code_multipath.py`'s per-`sv`
collapse.

Output dims `(epoch, sid)`, one timestamp per day. No `station` dim (see
`io.py`). No station-level rollup — if ever wanted, that's a downstream
consumer's job across this module's per-file output, not something this
module computes itself.

**Not an independent QC cross-check against `code_multipath.py`.** On SBF
the firmware multipath correction is already subtracted from the
corrected `Pseudorange`/`Phase` that a naive `code_multipath` run would
otherwise use; once `code_multipath.py` is fixed to require raw
observables, the two signals are correlated by construction, not
independent. Useful as a diagnostic ("does our from-scratch MP1 estimate
track the firmware's own estimate in trend, on days both are available"),
never as validation.
"""

from __future__ import annotations

import xarray as xr


def compute_receiver_multipath_for_station(
    metadata_ds: xr.Dataset,
    *,
    station_id: str,
) -> xr.Dataset:
    """Entry point: daily per-`sid` mean/std of `mp_correction_m`/
    `car_mp_corr_cycles`, read from the SBF metadata dataset.

    Not yet implemented (Phase 4).
    """
    raise NotImplementedError(
        "receiver_multipath.compute_receiver_multipath_for_station: Phase 4, not yet implemented."
    )
