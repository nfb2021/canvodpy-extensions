"""Phase 0.5 verification: are raw GPS P1/L1/L2 obtainable at the precision
canvod-gnssgeodesy needs, from both readers, on real ROSA (Rosalia) fixtures?

Checks, each printed pass/fail with evidence:
1. RINEX: Pseudorange/Phase/LLI present, dtype, GPS-only slice.
2. SBF: Pseudorange_raw/Phase_raw present (vs corrected Pseudorange/Phase),
   dtype, and whether they actually differ numerically (proving "raw" is
   really unsmoothed/uncorrected, not just a renamed copy).
3. freq_center dtype/units claim (float32, MHz) vs a hypothetical
   frequency_hz field (should not exist).
4. theta/phi range/units sanity on real data.

Referenced as evidence throughout PLAN.md §3 and RATIONALE.md §16 — kept
here (not in an ephemeral scratchpad) so the claims it produced remain
independently re-runnable and re-checkable.
"""

from pathlib import Path

import numpy as np
from canvod.readers.rinex.v3_04 import Rnxv3Obs
from canvod.readers.sbf.reader import SbfReader

TEST_DATA = Path("/Users/nfb/Developer/GNSS/canvodpy/packages/canvod-readers/tests/test_data")
RINEX_FILE = (
    TEST_DATA
    / "valid/rinex_v3_04/01_Rosalia/02_canopy/01_GNSS/01_raw/25001/ROSA01TUW_R_20250010000_15M_05S_AA.rnx"
)
SBF_FILE = (
    TEST_DATA / "valid/sbf/01_Rosalia/01_reference/25001/ROSR01TUW_R_20250010000_15M_05S_AA.sbf"
)


def hr(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


# ---------------------------------------------------------------------
hr("1. RINEX v3.04 — Pseudorange/Phase/LLI availability & dtype")
if not RINEX_FILE.exists():
    print(f"SKIP — file not found: {RINEX_FILE}")
else:
    r = Rnxv3Obs(fpath=RINEX_FILE)
    ds = r.to_ds(keep_data_vars=["SNR", "Pseudorange", "Phase", "LLI"])
    print("data_vars:", list(ds.data_vars))
    for v in ["Pseudorange", "Phase", "LLI", "SNR"]:
        if v in ds.data_vars:
            da = ds[v]
            print(
                f"  {v}: dtype={da.dtype}, shape={da.shape}, "
                f"n_finite={int(np.isfinite(da.values.astype(float)).sum()) if da.dtype.kind == 'f' else 'n/a (int)'}"
            )
        else:
            print(f"  {v}: MISSING")
    print("sid coord dtype check (freq_center / claimed frequency_hz):")
    for c in ["freq_center", "freq_min", "freq_max", "frequency_hz"]:
        if c in ds.coords:
            print(f"  {c}: EXISTS, dtype={ds.coords[c].dtype}, sample={ds.coords[c].values[:3]}")
        else:
            print(f"  {c}: does not exist")
    # GPS-only slice sanity
    gps_sids = [s for s in ds.sid.values if str(s).startswith("G")]
    print(f"GPS SIDs present: {len(gps_sids)} (sample: {gps_sids[:5]})")

# ---------------------------------------------------------------------
hr("2. SBF — Pseudorange_raw/Phase_raw vs corrected Pseudorange/Phase")
if not SBF_FILE.exists():
    print(f"SKIP — file not found: {SBF_FILE}")
else:
    reader = SbfReader(fpath=SBF_FILE)
    # BUG FOUND: to_ds_and_auxiliary() calls validate_dataset(obs_ds, required_vars=keep_data_vars)
    # at reader.py:2490, BEFORE the store_raw_observables block (~2876-2930) that actually
    # creates Pseudorange_raw/Phase_raw/SNR_raw/Pseudorange_unsmoothed. Passing those names in
    # keep_data_vars therefore always raises "Missing required data variables" even though
    # store_raw_observables=True would have created them moments later. The documented
    # "keep_data_vars: data variables to retain" contract cannot select the raw variables.
    # Workaround: pass keep_data_vars=None (validates against the default ["SNR"] only, and
    # skips the post-hoc drop-filter entirely, since that filter is also gated on
    # `if keep_data_vars is not None`) and subset manually afterward.
    try:
        ds_raw, aux = reader.to_ds_and_auxiliary(
            keep_data_vars=None,
            pad_global_sid=False,
            strip_fillval=False,
            store_raw_observables=True,
        )
        print("data_vars:", list(ds_raw.data_vars))
        for v in ["Pseudorange", "Pseudorange_raw", "Phase", "Phase_raw"]:
            if v in ds_raw.data_vars:
                da = ds_raw[v]
                print(f"  {v}: dtype={da.dtype}, shape={da.shape}")
            else:
                print(f"  {v}: MISSING")
        if "Pseudorange" in ds_raw.data_vars and "Pseudorange_raw" in ds_raw.data_vars:
            diff = (ds_raw["Pseudorange"] - ds_raw["Pseudorange_raw"]).values
            finite = diff[np.isfinite(diff)]
            print(
                f"  Pseudorange - Pseudorange_raw: n_finite_diffs={finite.size}, "
                f"max_abs={np.nanmax(np.abs(finite)) if finite.size else 'n/a'}, "
                f"mean_abs={np.nanmean(np.abs(finite)) if finite.size else 'n/a'}"
            )
            print(
                "  (non-zero difference proves 'raw' is genuinely distinct from the corrected/smoothed variable)"
            )
        if "Phase" in ds_raw.data_vars and "Phase_raw" in ds_raw.data_vars:
            diff = (ds_raw["Phase"] - ds_raw["Phase_raw"]).values
            finite = diff[np.isfinite(diff)]
            print(
                f"  Phase - Phase_raw: n_finite_diffs={finite.size}, "
                f"max_abs={np.nanmax(np.abs(finite)) if finite.size else 'n/a'}"
            )
    except Exception as e:
        print(f"ERROR requesting corrected+raw together: {type(e).__name__}: {e}")
        raise

    # Also confirm LLI is genuinely absent (per plan claim) and cum_loss_cont exists in metadata
    try:
        ds_lli = reader.to_ds(
            keep_data_vars=["SNR", "LLI"], pad_global_sid=False, strip_fillval=False
        )
        print("Requesting LLI on SBF did NOT raise — unexpected, re-check plan claim.")
    except Exception as e:
        print(f"Requesting LLI on SBF raised as expected: {type(e).__name__}: {e}")

    meta_ds = aux["sbf_obs"]
    print("sbf_obs metadata data_vars:", list(meta_ds.data_vars))
    for v in ["cum_loss_cont", "mp_correction_m", "car_mp_corr_cycles", "smoothing_corr_m"]:
        if v in meta_ds.data_vars:
            print(f"  {v}: dtype={meta_ds[v].dtype}, shape={meta_ds[v].shape}")
        else:
            print(f"  {v}: MISSING from metadata")

# ---------------------------------------------------------------------
hr(
    "3. theta/phi geometry convention sanity (needs VOD-side ephemeris augmentation — may not be available from a bare reader)"
)
print(
    "Bare reader output has no theta/phi (those are added by ephemeris augmentation downstream of the reader)."
)
print(
    "This check is deferred to an integration test once ephemeris augmentation is wired in Phase 1."
)
