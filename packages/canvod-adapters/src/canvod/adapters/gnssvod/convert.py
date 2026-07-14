"""Pure-format conversion between canvodpy and gnssvod data shapes.

No dependency on ``canvod-store`` or the real ``gnssvod`` package — this
module only matches gnssvod's documented data shape, verified against
gnssvod's own ``io/io.py::Observation.to_xarray()`` and
``io/exporters.py::export_as_nc()``.

Coordinate conventions
-----------------------
canvodpy:
    theta = polar angle from zenith, [0, pi/2] rad (0=zenith, pi/2=horizon)
    phi   = azimuth from North clockwise, [0, 2*pi) rad

gnssvod:
    Elevation = angle from horizon, [0, 90] degrees (0=horizon, 90=zenith)
    Azimuth   = angle from North clockwise, [0, 360) degrees

Mapping:
    Elevation = 90 - degrees(theta)
    Azimuth   = degrees(phi) mod 360

Originally built for ``canvod-audit``'s Tier-3 comparison
(``audit_vs_gnssvod``); extracted here so it's reusable outside the audit
suite. ``GnssvodAdapter``/``detect_band_map``/``BAND_MAP``/
``gnssvod_merge_codes``/``gnssvod_df_to_xarray`` are unchanged from that
origin. ``to_gnssvod_dataset``/``from_gnssvod_dataset`` are new: they
operate on an already-computed, multi-band canvodpy VOD dataset (the shape
written to the VOD Icechunk store — variables ``VOD``, ``delta_snr``,
``phi``, ``theta``), merging/splitting across every band in one call,
rather than the single-band-at-a-time comparison use in ``GnssvodAdapter``.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import TYPE_CHECKING

import numpy as np
import xarray as xr

if TYPE_CHECKING:
    import pandas as pd

# ---------------------------------------------------------------------------
# Band configuration
# ---------------------------------------------------------------------------

#: Default band map — (canvodpy band|code suffix, gnssvod SNR column, gnssvod VOD column).
BAND_MAP: list[tuple[str, str, str | None]] = [
    ("L1|C", "S1C", "VOD1"),
    ("L2|W", "S2W", "VOD2"),
    ("L5|Q", "S5Q", None),  # L5 VOD not standard in gnssvod
]


def detect_band_map(
    ds_canvod: xr.Dataset,
    ds_gnssvod: xr.Dataset,
) -> list[tuple[str, str, str | None]]:
    """Auto-detect band mapping from available variables.

    Scans canvodpy SIDs and gnssvod columns to find matching bands.
    Returns list of (canvodpy_band_suffix, gnssvod_snr_col, gnssvod_vod_col).
    """
    # Detect bands in canvodpy SIDs
    all_sids = [str(s) for s in ds_canvod.sid.values]
    canvod_bands: dict[str, set[str]] = {}  # band_num -> set of tracking codes
    for sid in all_sids:
        parts = sid.split("|")
        if len(parts) == 3:
            band = parts[1]  # e.g. "L1"
            code = parts[2]  # e.g. "C"
            band_num = band[1:]  # e.g. "1"
            canvod_bands.setdefault(band_num, set()).add(code)

    # Match against gnssvod SNR columns (S1C, S2W, etc.)
    gnssvod_var_names = [str(c) for c in ds_gnssvod.data_vars]
    gnssvod_snr_cols = [c for c in gnssvod_var_names if c.startswith("S") and len(c) == 3]

    # VOD column mapping: band 1 -> VOD1, band 2 -> VOD2, etc.
    gnssvod_vod_cols = {c[-1]: c for c in gnssvod_var_names if c.startswith("VOD")}

    band_map = []
    for band_num, codes in sorted(canvod_bands.items()):
        # Find which gnssvod SNR columns exist for this band
        matching_snr = [c for c in gnssvod_snr_cols if c[1] == band_num]
        if not matching_snr:
            continue

        # Match canvodpy code to the gnssvod SNR column's tracking code
        snr_col = None
        primary_code = None
        for mc in matching_snr:
            gnssvod_code = mc[2]  # e.g. "C" from "S1C"
            if gnssvod_code in codes:
                snr_col = mc
                primary_code = gnssvod_code
                break
        if snr_col is None:
            # Fallback: lex-first code with first matching gnssvod column
            primary_code = sorted(codes)[0]
            snr_col = matching_snr[0]

        vod_col = gnssvod_vod_cols.get(band_num)
        band_suffix = f"L{band_num}|{primary_code}"

        band_map.append((band_suffix, snr_col, vod_col))

    return band_map


# ---------------------------------------------------------------------------
# Single-band adapter (canvodpy -> gnssvod)
# ---------------------------------------------------------------------------


class GnssvodAdapter:
    """Project a canvodpy (epoch, sid) dataset into gnssvod variable space.

    Transforms canvodpy's SID-indexed data into PRN-indexed data with
    gnssvod-compatible variable names and units. One adapter instance
    handles one frequency band.

    Parameters
    ----------
    ds : xarray.Dataset
        canvodpy dataset with (epoch, sid) dims and variables: SNR, phi,
        theta, and optionally VOD.
    band_filter : str
        SID band suffix to select, e.g. ``"L1|C"`` or ``"L2|W"``.
    snr_col : str
        gnssvod column name for SNR at this band (e.g. ``"S1C"``).
    vod_col : str or None
        gnssvod column name for VOD at this band (e.g. ``"VOD1"``).
    """

    def __init__(
        self,
        ds: xr.Dataset,
        band_filter: str,
        snr_col: str,
        vod_col: str | None = None,
    ):
        # Select SIDs matching this band
        all_sids = [str(s) for s in ds.sid.values]
        band_sids = [s for s in all_sids if s.endswith(f"|{band_filter}")]
        if not band_sids:
            raise ValueError(
                f"No SIDs match band filter '|{band_filter}'. Available: {all_sids[:10]}"
            )

        self.ds = ds.sel(sid=band_sids)
        self.band_filter = band_filter
        self.snr_col = snr_col
        self.vod_col = vod_col

        # Map SIDs to PRNs
        self.prns = [s.split("|")[0] for s in band_sids]
        if len(self.prns) != len(set(self.prns)):
            dupes = {k: v for k, v in Counter(self.prns).items() if v > 1}
            raise ValueError(
                f"Duplicate PRNs after SID->PRN mapping for band {band_filter}: "
                f"{dupes}. Input was not trimmed to one code per band."
            )

    def to_gnssvod_dataset(self) -> xr.Dataset:
        """Convert to a gnssvod-shaped dataset with PRN sids.

        Returns dataset with variables named like gnssvod output:
        - ``{snr_col}`` (e.g. S1C): SNR in dB-Hz (unchanged)
        - ``Azimuth``: degrees from North, clockwise [0, 360)
        - ``Elevation``: degrees from horizon [0, 90]
        - ``{vod_col}`` (e.g. VOD1): VOD (unchanged) if present

        Coordinates: epoch (datetime), sid (PRN strings like "G01").
        """
        data_vars = {}

        # SNR: same units (dB-Hz), just rename
        if "SNR" in self.ds.data_vars:
            data_vars[self.snr_col] = (["epoch", "sid"], self.ds["SNR"].values)

        # Azimuth: phi (rad, from North CW) -> degrees
        if "phi" in self.ds.data_vars:
            az_deg = np.degrees(self.ds["phi"].values) % 360.0
            data_vars["Azimuth"] = (["epoch", "sid"], az_deg)

        # Elevation: theta (rad, polar angle) -> 90 - degrees(theta)
        if "theta" in self.ds.data_vars:
            el_deg = 90.0 - np.degrees(self.ds["theta"].values)
            data_vars["Elevation"] = (["epoch", "sid"], el_deg)

        # VOD: same units, just rename
        if self.vod_col and "VOD" in self.ds.data_vars:
            data_vars[self.vod_col] = (["epoch", "sid"], self.ds["VOD"].values)

        return xr.Dataset(
            data_vars,
            coords={
                "epoch": self.ds.epoch.values,
                "sid": self.prns,
            },
        )


# ---------------------------------------------------------------------------
# gnssvod fillna merge replication
# ---------------------------------------------------------------------------


def gnssvod_merge_codes(
    ds: xr.Dataset,
    band_num: str,
    snr_var: str = "SNR",
) -> xr.Dataset:
    """Replicate gnssvod's fillna merge for a given band.

    gnssvod merges multiple tracking codes per band using fillna in
    lexicographic order (determined by ``numpy.intersect1d`` sorting).
    For example, with S1C and S1W both present:
    - S1C values used where available
    - S1W fills remaining NaN gaps

    .. note::

        In gnssvod (``vod_calc.py``), the fillna merge operates on
        **per-code VOD values**, not raw SNR. Each code's VOD is
        computed independently first::

            VOD_code = -ln(10^((grn - ref) / 10)) * cos(90 - elev)

        Then ``band_VOD.fillna(code_VOD)`` cascades in lex order.
        This function merges raw variable values (SNR, phi, theta)
        instead, which is equivalent for SNR (a direct observable)
        but **not** equivalent for VOD. For correct VOD merging,
        compute VOD per code first, then call this function on the
        VOD variable.

    Parameters
    ----------
    ds : xarray.Dataset
        canvodpy dataset with (epoch, sid) dims.
    band_num : str
        Band number to merge, e.g. ``"1"`` for L1, ``"2"`` for L2.
    snr_var : str
        SNR variable name in the dataset.

    Returns
    -------
    xarray.Dataset
        Dataset with one SID per PRN for this band (merged), sid
        values replaced with PRN strings.
    """
    # Find all SIDs for this band: e.g. "G01|L1|C", "G01|L1|W"
    band_prefix = f"|L{band_num}|"
    all_sids = [str(s) for s in ds.sid.values]
    band_sids = [s for s in all_sids if band_prefix in s]
    if not band_sids:
        raise ValueError(f"No SIDs match band L{band_num}")

    # Group SIDs by PRN, sort codes lexicographically (matching gnssvod)
    prn_groups: dict[str, list[str]] = defaultdict(list)
    for sid in band_sids:
        prn = sid.split("|")[0]
        prn_groups[prn].append(sid)
    for prn in prn_groups:
        prn_groups[prn].sort()  # lexicographic = gnssvod order

    # Merge: for each PRN, fillna across codes in sorted order
    prns = sorted(prn_groups.keys())
    merged_data = {}

    for var in ds.data_vars:
        merged_arrays = []
        for prn in prns:
            sids_for_prn = prn_groups[prn]
            # Start with NaN, fillna in lex order
            merged = np.full(len(ds.epoch), np.nan)
            for sid in sids_for_prn:
                vals = ds[var].sel(sid=sid).values.astype(np.float64)
                nan_mask = np.isnan(merged)
                merged[nan_mask] = vals[nan_mask]
            merged_arrays.append(merged)
        merged_data[var] = (["epoch", "sid"], np.column_stack(merged_arrays))

    return xr.Dataset(
        merged_data,
        coords={"epoch": ds.epoch.values, "sid": prns},
    )


# ---------------------------------------------------------------------------
# gnssvod DataFrame -> xarray conversion
# ---------------------------------------------------------------------------


def gnssvod_df_to_xarray(
    df: pd.DataFrame,
    *,
    epoch_col: str = "Epoch",
    sid_col: str = "SV",
    value_cols: list[str] | None = None,
) -> xr.Dataset:
    """Convert a gnssvod pandas DataFrame to an xarray Dataset.

    gnssvod outputs DataFrames with MultiIndex (Epoch, SV) and columns
    for each observation type (S1C, S2W, ...) plus Azimuth, Elevation,
    and VOD bands (VOD1, VOD2, ...).

    Parameters
    ----------
    df : pandas.DataFrame
        Output from gnssvod (with or without MultiIndex).
    epoch_col : str
        Column or index level name for the time axis.
    sid_col : str
        Column or index level name for the satellite identifier.
    value_cols : list of str, optional
        Data columns to include. If not given, uses all numeric columns.

    Returns
    -------
    xarray.Dataset
        With dimensions (epoch, sid).
    """
    import pandas as pd

    # Reset MultiIndex if present
    if isinstance(df.index, pd.MultiIndex):
        df = df.reset_index()

    if value_cols is None:
        value_cols = [
            c
            for c in df.columns
            if c not in (epoch_col, sid_col) and np.issubdtype(df[c].dtype, np.number)
        ]

    epochs = sorted(df[epoch_col].unique())
    sids = sorted(df[sid_col].unique())

    data_vars = {}
    for col in value_cols:
        # Use pivot (not pivot_table) to raise on duplicates instead of
        # silently averaging them
        try:
            pivoted = df.pivot(index=epoch_col, columns=sid_col, values=col)
        except ValueError:
            # Fallback if there are true duplicates (shouldn't happen with
            # trimmed RINEX, but be defensive)
            pivoted = df.pivot_table(index=epoch_col, columns=sid_col, values=col)
        pivoted = pivoted.reindex(index=epochs, columns=sids)
        data_vars[col] = (["epoch", "sid"], pivoted.values)

    return xr.Dataset(
        data_vars,
        coords={"epoch": epochs, "sid": [str(s) for s in sids]},
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _normalize_dims(ds: xr.Dataset) -> xr.Dataset:
    """Rename gnssvod's native `Epoch`/`SV` dims to canvodpy's `epoch`/`sid`."""
    rename = {}
    if "Epoch" in ds.dims and "epoch" not in ds.dims:
        rename["Epoch"] = "epoch"
    if "SV" in ds.dims and "sid" not in ds.dims:
        rename["SV"] = "sid"
    return ds.rename(rename) if rename else ds


# ---------------------------------------------------------------------------
# Multi-band conversion (canvodpy VOD store <-> gnssvod), new
# ---------------------------------------------------------------------------


def to_gnssvod_dataset(
    vod_ds: xr.Dataset,
    band_map: list[tuple[str, str, str | None]] | None = None,
) -> xr.Dataset:
    """Merge all bands of a canvodpy VOD dataset into one gnssvod-shaped dataset.

    Unlike ``GnssvodAdapter`` (single band, used for the per-band Tier-3
    comparison), this merges every band declared in ``band_map`` into one
    combined ``xr.Dataset`` — matching gnssvod's own NetCDF layout, where
    ``S1C``/``Azimuth``/``Elevation``/``VOD1``/``VOD2``/... are sibling
    variables in a single per-station file.

    Parameters
    ----------
    vod_ds : xarray.Dataset
        A canvodpy VOD dataset as written to the VOD Icechunk store: dims
        ``(epoch, sid)``, variables ``VOD``, ``delta_snr`` (optional),
        ``phi``, ``theta``. Must contain exactly one tracking code per
        band (raises ``ValueError`` otherwise — pre-merge with
        ``gnssvod_merge_codes`` or trim upstream first).
    band_map : list of (band_suffix, snr_col, vod_col), optional
        Defaults to ``BAND_MAP``.

    Returns
    -------
    xarray.Dataset
        dims ``(epoch, sid)`` (sid holding PRN strings, e.g. ``"G01"``),
        variables ``Azimuth``, ``Elevation``, ``VOD1``/``VOD2``/... (per
        band with a configured ``vod_col``), and ``dSNR1``/``dSNR2``/...
        (canvodpy's ``delta_snr``, per band — **not** renamed to
        gnssvod's ``S1C``-style columns, since ``delta_snr`` is a
        canopy-minus-reference difference, not the raw per-receiver SNR
        those columns represent in real gnssvod output).

    Raises
    ------
    ValueError
        If no band in ``band_map`` matches any SID, or if a band has
        more than one tracking code (ambiguous PRN mapping).
    """
    if band_map is None:
        band_map = BAND_MAP

    all_sids = [str(s) for s in vod_ds.sid.values]
    band_datasets: list[xr.Dataset] = []

    for band_suffix, _snr_col, vod_col in band_map:
        band_positions = [i for i, s in enumerate(all_sids) if s.endswith(f"|{band_suffix}")]
        if not band_positions:
            continue

        # Positional (not label-based) selection: a malformed/duplicated
        # input dataset may have non-unique sid labels, which would make
        # .sel() raise a low-level pandas index error before the
        # duplicate-PRN check below ever runs.
        sub = vod_ds.isel(sid=band_positions)
        band_sids = [all_sids[i] for i in band_positions]
        prns = [s.split("|")[0] for s in band_sids]
        if len(prns) != len(set(prns)):
            dupes = {k: v for k, v in Counter(prns).items() if v > 1}
            raise ValueError(
                f"Duplicate PRNs after SID->PRN mapping for band {band_suffix}: "
                f"{dupes}. Pass a dataset trimmed to one code per band, or "
                "pre-merge codes with gnssvod_merge_codes()."
            )

        band_num = band_suffix.split("|")[0][1:]  # "L1|C" -> "1"
        dvars: dict[str, tuple] = {}
        if "phi" in sub.data_vars:
            dvars["Azimuth"] = (
                ["epoch", "sid"],
                np.degrees(sub["phi"].values) % 360.0,
            )
        if "theta" in sub.data_vars:
            dvars["Elevation"] = (
                ["epoch", "sid"],
                90.0 - np.degrees(sub["theta"].values),
            )
        if vod_col and "VOD" in sub.data_vars:
            dvars[vod_col] = (["epoch", "sid"], sub["VOD"].values)
        if "delta_snr" in sub.data_vars:
            dvars[f"dSNR{band_num}"] = (["epoch", "sid"], sub["delta_snr"].values)

        if not dvars:
            continue

        band_datasets.append(xr.Dataset(dvars, coords={"epoch": sub.epoch.values, "sid": prns}))

    if not band_datasets:
        raise ValueError(
            "No bands in band_map matched any SIDs in the input dataset. "
            f"Available SIDs (sample): {all_sids[:10]}"
        )

    # outer join: union of PRNs across bands, NaN-filled where a band lacks
    # a given PRN; compat="override" -- Azimuth/Elevation are (near-)identical
    # across bands for the same satellite/epoch, first band wins on overlap
    # rather than requiring bit-identical equality across bands.
    return xr.merge(band_datasets, join="outer", compat="override")


def from_gnssvod_dataset(
    gnssvod_ds: xr.Dataset,
    band_map: list[tuple[str, str, str | None]] | None = None,
) -> xr.Dataset:
    """Convert a gnssvod-shaped dataset into a canvodpy VOD dataset.

    Reverse of :func:`to_gnssvod_dataset`. Accepts either that function's
    own output or a real gnssvod NetCDF export (dims ``Epoch``/``SV`` or
    ``epoch``/``sid``; variables ``S1C``/``Azimuth``/``Elevation``/
    ``VOD1``/...).

    Parameters
    ----------
    gnssvod_ds : xarray.Dataset
        gnssvod-shaped dataset, dims ``(epoch|Epoch, sid|SV)``.
    band_map : list of (band_suffix, snr_col, vod_col), optional
        Defaults to ``BAND_MAP``. Only bands with a non-``None`` ``vod_col``
        present in ``gnssvod_ds`` are reconstructed.

    Returns
    -------
    xarray.Dataset
        dims ``(epoch, sid)``, SID format ``"{PRN}|{band_suffix}"``
        (e.g. ``"G01|L1|C"``), variables ``VOD`` (always), ``phi``/
        ``theta`` (if Azimuth/Elevation present), ``delta_snr`` (if a
        matching SNR/dSNR column is present). Sets attrs
        ``vod_reconstructed_code_ambiguous=True``: gnssvod merges
        multiple tracking codes per band via fillna before it ever
        exports data, so the per-code identity of ``VOD``/SNR is lost —
        reconstructed SIDs use ``band_map``'s declared code as a
        placeholder, not an observed value.

    Raises
    ------
    ValueError
        If no band in ``band_map`` has a matching VOD column in
        ``gnssvod_ds``.
    """
    if band_map is None:
        band_map = BAND_MAP

    ds = _normalize_dims(gnssvod_ds)
    prns = [str(s) for s in ds.sid.values]

    az = ds["Azimuth"].values if "Azimuth" in ds.data_vars else None
    el = ds["Elevation"].values if "Elevation" in ds.data_vars else None

    sid_labels: list[str] = []
    vod_chunks: list[np.ndarray] = []
    phi_chunks: list[np.ndarray] = []
    theta_chunks: list[np.ndarray] = []
    dsnr_chunks: list[np.ndarray] = []

    for band_suffix, snr_col, vod_col in band_map:
        if vod_col is None or vod_col not in ds.data_vars:
            continue

        band_num = band_suffix.split("|")[0][1:]
        band_sids = [f"{prn}|{band_suffix}" for prn in prns]
        sid_labels.extend(band_sids)
        vod_chunks.append(ds[vod_col].values)

        if az is not None:
            phi_chunks.append(np.radians(az) % (2 * np.pi))
        if el is not None:
            theta_chunks.append(np.radians(90.0 - el))

        dsnr_col = f"dSNR{band_num}"
        if snr_col in ds.data_vars:
            dsnr_chunks.append(ds[snr_col].values)
        elif dsnr_col in ds.data_vars:
            dsnr_chunks.append(ds[dsnr_col].values)

    if not sid_labels:
        raise ValueError(
            "No VOD column in the input dataset matched any band in "
            f"band_map. Available variables: {sorted(ds.data_vars)}"
        )

    data_vars: dict[str, tuple] = {"VOD": (["epoch", "sid"], np.concatenate(vod_chunks, axis=1))}
    if len(phi_chunks) == len(vod_chunks):
        data_vars["phi"] = (["epoch", "sid"], np.concatenate(phi_chunks, axis=1))
    if len(theta_chunks) == len(vod_chunks):
        data_vars["theta"] = (["epoch", "sid"], np.concatenate(theta_chunks, axis=1))
    if len(dsnr_chunks) == len(vod_chunks):
        data_vars["delta_snr"] = (
            ["epoch", "sid"],
            np.concatenate(dsnr_chunks, axis=1),
        )

    out = xr.Dataset(
        data_vars,
        coords={"epoch": ds.epoch.values, "sid": sid_labels},
    )
    out.attrs["vod_reconstructed_code_ambiguous"] = True
    return out
