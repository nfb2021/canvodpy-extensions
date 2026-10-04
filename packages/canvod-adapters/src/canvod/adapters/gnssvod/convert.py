"""Conversion between canvodpy and gnssvod (Humphrey et al.) data.

gnssvod
    Observations: dims ``(Epoch, SV)``, one variable per RINEX observation
    code (``S1C``, ``C1C``, ``L1C``, ``D1C``; RINEX 2: ``S1``, ``P2``, ...),
    plus ``Azimuth`` and ``Elevation`` in degrees (``Observation`` objects,
    ``gnssvod.preprocess``). VOD: dims ``(Epoch, SV)``, one variable per
    band named in the ``bands`` argument of ``gnssvod.calc_vod``, which
    merges the band's observation codes present in the data in sorted
    order (``numpy.intersect1d``), each filling the gaps of the previous.

canvodpy
    dims ``(epoch, sid)``, sid ``"SV|BAND|CODE"`` with the coordinates
    ``sv``, ``system``, ``band``, ``code`` and the band frequencies;
    ``SNR``, ``Pseudorange``, ``Phase``, ``Doppler``, ``VOD``; ``theta``
    (polar angle from zenith) and ``phi`` (azimuth from North, clockwise)
    in radians.

Signal IDs and observation codes are mapped with
:func:`canvod.readers.gnss_specs.obs_codes.sid_for_obs_code` and
:func:`~canvod.readers.gnss_specs.obs_codes.obs_code_for_sid`, the rules of
canvodpy's RINEX readers. Angles: ``Elevation = 90 - degrees(theta)``,
``Azimuth = degrees(phi) mod 360``.
"""

from __future__ import annotations

import numpy as np
import xarray as xr
from canvod.readers import SignalID, sid_coords
from canvod.readers.gnss_specs.obs_codes import obs_code_for_sid, sid_for_obs_code
from canvod.readers.gnss_specs.signals import SignalIDMapper

#: canvodpy observable -> RINEX observation type.
OBS_TYPES: dict[str, str] = {
    "SNR": "S",
    "Pseudorange": "C",
    "Phase": "L",
    "Doppler": "D",
}

#: RINEX observation type -> canvodpy observable (RINEX 2 ``P`` is a
#: pseudorange).
_OBSERVABLES: dict[str, str] = {**{v: k for k, v in OBS_TYPES.items()}, "P": "Pseudorange"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _strings(values: np.ndarray) -> np.ndarray:
    """String coordinate values as ``str``, also from numpy ``StringDType``
    (how the VOD store returns them), which does not cast to ``str``."""
    return np.array([str(v) for v in values])


def _sv_of_sids(ds: xr.Dataset) -> np.ndarray:
    """The ``sv`` coordinate of a canvodpy dataset."""
    if "sv" not in ds.coords:
        msg = "The canvodpy dataset has no 'sv' coordinate on its sid dimension"
        raise ValueError(msg)
    return _strings(ds["sv"].values)


def _per_sv(da: xr.DataArray, svs: np.ndarray, sv_index: list[str]) -> np.ndarray:
    """``(epoch, sid)`` values of one satellite quantity as ``(epoch, SV)``.

    All sids of a satellite carry the same geometry; the first non-NaN value
    over its sids is taken.
    """
    values = np.asarray(da.values, dtype=np.float64)
    out = np.full((values.shape[0], len(sv_index)), np.nan)
    for j, sv in enumerate(sv_index):
        for col in np.flatnonzero(svs == sv):
            gap = np.isnan(out[:, j])
            out[gap, j] = values[gap, col]
    return out


def _gnssvod_dims(ds: xr.Dataset) -> xr.Dataset:
    """Require gnssvod's ``(Epoch, SV)`` dims."""
    missing = {"Epoch", "SV"} - set(ds.dims)
    if missing:
        msg = f"Not a gnssvod dataset: dims {sorted(missing)} missing"
        raise ValueError(msg)
    return ds


def _sids_of_code(svs: list[str], code: str, values: np.ndarray) -> dict[int, str]:
    """sid of each satellite column with data for one observation code.

    gnssvod's datasets hold every code for every satellite, so most columns
    are empty: an all-NaN column is no signal and gets no sid. Data for a
    satellite whose system has no band for the code is an error.
    """
    return {
        j: sid_for_obs_code(sv, code)
        for j, sv in enumerate(svs)
        if not np.all(np.isnan(values[:, j]))
    }


def _theta(elevation_deg: np.ndarray) -> np.ndarray:
    return np.radians(90.0 - elevation_deg)


def _phi(azimuth_deg: np.ndarray) -> np.ndarray:
    return np.radians(azimuth_deg) % (2 * np.pi)


def _angles_to_gnssvod(ds: xr.Dataset, svs: np.ndarray, sv_index: list[str]) -> dict[str, tuple]:
    out: dict[str, tuple] = {}
    if "phi" in ds.data_vars:
        out["Azimuth"] = (
            ("Epoch", "SV"),
            np.degrees(_per_sv(ds["phi"], svs, sv_index)) % 360.0,
        )
    if "theta" in ds.data_vars:
        out["Elevation"] = (
            ("Epoch", "SV"),
            90.0 - np.degrees(_per_sv(ds["theta"], svs, sv_index)),
        )
    return out


def _to_canvodpy(
    gnssvod_ds: xr.Dataset, columns: dict[str, dict[str, tuple[int, np.ndarray]]]
) -> xr.Dataset:
    """Assemble ``(epoch, sid)`` variables from per-sid columns.

    ``columns`` maps a canvodpy variable to ``{sid: (SV column, values)}``.
    ``theta``/``phi`` of each sid come from its satellite's
    ``Elevation``/``Azimuth``. The sid coordinates are canvodpy's
    (:func:`canvod.readers.sid_coords`).
    """
    sid_sv = {sid: col for per_sid in columns.values() for sid, (col, _) in per_sid.items()}
    sids = sorted(sid_sv)
    n_epoch = gnssvod_ds.sizes["Epoch"]
    data_vars: dict[str, tuple] = {}
    for name, per_sid in columns.items():
        arr = np.full((n_epoch, len(sids)), np.nan)
        for i, sid in enumerate(sids):
            if sid in per_sid:
                arr[:, i] = per_sid[sid][1]
        data_vars[name] = (("epoch", "sid"), arr)
    sv_cols = [sid_sv[sid] for sid in sids]
    if "Elevation" in gnssvod_ds.data_vars:
        el = np.asarray(gnssvod_ds["Elevation"].transpose("Epoch", "SV").values)
        data_vars["theta"] = (("epoch", "sid"), _theta(el[:, sv_cols]))
    if "Azimuth" in gnssvod_ds.data_vars:
        az = np.asarray(gnssvod_ds["Azimuth"].transpose("Epoch", "SV").values)
        data_vars["phi"] = (("epoch", "sid"), _phi(az[:, sv_cols]))
    signals = [SignalID.from_string(sid) for sid in sids]
    return xr.Dataset(
        data_vars,
        coords={
            "epoch": gnssvod_ds["Epoch"].values.astype("datetime64[ns]"),
            **sid_coords(signals, mapper=SignalIDMapper()),
        },
    )


# ---------------------------------------------------------------------------
# Observations
# ---------------------------------------------------------------------------


def to_gnssvod_observations(ds: xr.Dataset) -> xr.Dataset:
    """canvodpy observations as gnssvod observations.

    Parameters
    ----------
    ds : xarray.Dataset
        canvodpy receiver dataset: dims ``(epoch, sid)``, an ``sv``
        coordinate, any of ``SNR``/``Pseudorange``/``Phase``/``Doppler``,
        optionally ``theta``/``phi``.

    Returns
    -------
    xarray.Dataset
        dims ``(Epoch, SV)``: one variable per observation code with data,
        e.g. ``S1C``, for the satellites with data; ``Azimuth``/
        ``Elevation`` in degrees. All-NaN sids (canvodpy pads to a global
        sid set) are left out.

    Raises
    ------
    ValueError
        If two sids of a satellite map to the same observation code
        (RINEX 2 ``P2`` and ``C2`` are both ``C2`` in RINEX 3 terms).
    """
    ds = ds.transpose("epoch", "sid")
    svs = _sv_of_sids(ds)
    observables = [name for name in OBS_TYPES if name in ds.data_vars]
    has_data = np.zeros(ds.sizes["sid"], dtype=bool)
    for name in observables:
        has_data |= ~np.all(np.isnan(np.asarray(ds[name].values, dtype=np.float64)), axis=0)
    sv_index = sorted(set(svs[has_data]))
    sv_col = {sv: j for j, sv in enumerate(sv_index)}
    data_vars: dict[str, tuple] = {}
    for name, obs_type in OBS_TYPES.items():
        source: dict[tuple[str, str], str] = {}
        if name not in ds.data_vars:
            continue
        values = np.asarray(ds[name].values, dtype=np.float64)
        sids = _strings(ds["sid"].values)
        # canvodpy pads to a global sid set: an all-NaN sid is no signal
        for i in np.flatnonzero(~np.all(np.isnan(values), axis=0)):
            sid = sids[i]
            code = obs_code_for_sid(sid, obs_type)
            if (code, svs[i]) in source:
                msg = (
                    f"sids {source[code, svs[i]]!r} and {sid!r} both map to "
                    f"observation code {code!r}"
                )
                raise ValueError(msg)
            source[code, svs[i]] = sid
            if code not in data_vars:
                data_vars[code] = (
                    ("Epoch", "SV"),
                    np.full((values.shape[0], len(sv_index)), np.nan),
                )
            data_vars[code][1][:, sv_col[svs[i]]] = values[:, i]
    data_vars.update(_angles_to_gnssvod(ds, svs, sv_index))
    return xr.Dataset(
        data_vars,
        coords={"Epoch": ds["epoch"].values, "SV": np.array(sv_index, dtype=object)},
    )


def from_gnssvod_observations(gnssvod_ds: xr.Dataset) -> xr.Dataset:
    """gnssvod observations as canvodpy observations.

    Parameters
    ----------
    gnssvod_ds : xarray.Dataset
        gnssvod observations, dims ``(Epoch, SV)`` (e.g.
        ``Observation.observation.to_xarray()``).

    Returns
    -------
    xarray.Dataset
        dims ``(epoch, sid)`` with the sid coordinates; ``SNR``,
        ``Pseudorange``, ``Phase``, ``Doppler`` as present; ``theta``/``phi``
        if ``Elevation``/``Azimuth`` are present. Only satellite/code
        columns with data become sids.

    Raises
    ------
    ValueError
        If a satellite has data for a code its system has no band for.
    """
    ds = _gnssvod_dims(gnssvod_ds).transpose("Epoch", "SV")
    svs = [str(sv) for sv in ds["SV"].values]
    columns: dict[str, dict[str, tuple[int, np.ndarray]]] = {}
    for code in ds.data_vars:
        code = str(code)
        if len(code) not in (2, 3) or code[0] not in _OBSERVABLES:
            continue
        values = np.asarray(ds[code].values, dtype=np.float64)
        per_sid = columns.setdefault(_OBSERVABLES[code[0]], {})
        for j, sid in _sids_of_code(svs, code, values).items():
            per_sid[sid] = (j, values[:, j])
    return _to_canvodpy(ds, columns)


# ---------------------------------------------------------------------------
# VOD
# ---------------------------------------------------------------------------


def to_gnssvod_vod(vod_ds: xr.Dataset, bands: dict[str, list[str]]) -> xr.Dataset:
    """canvodpy VOD as gnssvod VOD, merged per band like ``gnssvod.calc_vod``.

    Parameters
    ----------
    vod_ds : xarray.Dataset
        canvodpy VOD dataset: dims ``(epoch, sid)``, an ``sv`` coordinate,
        ``VOD``, optionally ``theta``/``phi``.
    bands : dict[str, list[str]]
        gnssvod's ``bands`` argument: band name to the signal-strength
        observation codes it merges, e.g. ``{"VOD_L1": ["S1C", "S1W"]}``.

    Returns
    -------
    xarray.Dataset
        dims ``(Epoch, SV)``: one variable per band; ``Azimuth``/
        ``Elevation`` in degrees. canvodpy's angles are the canopy
        receiver's; ``calc_vod`` reports the reference receiver's.
    """
    obs = to_gnssvod_observations(vod_ds[["VOD"]].rename({"VOD": "SNR"}))
    data_vars: dict[str, tuple] = {}
    for band, codes in bands.items():
        merged = np.full((obs.sizes["Epoch"], obs.sizes["SV"]), np.nan)
        for code in np.intersect1d([str(v) for v in obs.data_vars], codes):
            gap = np.isnan(merged)
            merged[gap] = np.asarray(obs[code].values)[gap]
        data_vars[band] = (("Epoch", "SV"), merged)
    svs = _sv_of_sids(vod_ds)
    data_vars.update(
        _angles_to_gnssvod(
            vod_ds.transpose("epoch", "sid"), svs, [str(sv) for sv in obs["SV"].values]
        )
    )
    return xr.Dataset(data_vars, coords=obs.coords)


def from_gnssvod_vod(gnssvod_ds: xr.Dataset, bands: dict[str, str]) -> xr.Dataset:
    """gnssvod VOD as canvodpy VOD.

    Parameters
    ----------
    gnssvod_ds : xarray.Dataset
        gnssvod VOD, dims ``(Epoch, SV)`` (e.g. the ``calc_vod`` result
        converted with ``DataFrame.to_xarray()``).
    bands : dict[str, str]
        Band variable to the observation code its sids get. gnssvod merges
        the codes of a band, so give the RINEX 2 form for a merged band,
        e.g. ``{"VOD_L1": "S1"}``: the sid is ``"G01|L1|u"``, canvodpy's
        marker for a band whose tracking code is not known.

    Returns
    -------
    xarray.Dataset
        dims ``(epoch, sid)`` with the sid coordinates; ``VOD``;
        ``theta``/``phi`` if ``Elevation``/``Azimuth`` are present. Only
        satellite/band columns with data become sids.

    Raises
    ------
    ValueError
        If a band variable is missing, or a satellite has VOD for a band
        its system does not have.
    """
    ds = _gnssvod_dims(gnssvod_ds).transpose("Epoch", "SV")
    missing = [band for band in bands if band not in ds.data_vars]
    if missing:
        msg = f"Band variables {missing} not in the gnssvod dataset"
        raise ValueError(msg)
    svs = [str(sv) for sv in ds["SV"].values]
    per_sid: dict[str, tuple[int, np.ndarray]] = {}
    for band, code in bands.items():
        values = np.asarray(ds[band].values, dtype=np.float64)
        for j, sid in _sids_of_code(svs, code, values).items():
            per_sid[sid] = (j, values[:, j])
    return _to_canvodpy(ds, {"VOD": per_sid})
