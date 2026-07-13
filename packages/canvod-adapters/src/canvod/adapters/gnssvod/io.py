"""Icechunk VOD store I/O convenience for the gnssvod adapter.

Requires the ``store`` extra (``canvod-adapters[store]``) — imports
``canvod-store`` lazily so the pure-format ``convert``/``provenance``
modules stay importable without it.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import xarray as xr
from canvod.adapters.gnssvod.convert import from_gnssvod_dataset, to_gnssvod_dataset
from canvod.adapters.gnssvod.provenance import build_provenance_attrs

if TYPE_CHECKING:
    from canvod.store import MyIcechunkStore


def _resolve_store(store_or_site: Any) -> MyIcechunkStore:
    """Accept a MyIcechunkStore, a site/manager object with a ``.vod_store``
    attribute, or a filesystem path — return a MyIcechunkStore instance.
    """
    try:
        from canvod.store import MyIcechunkStore
    except ImportError as e:
        raise ImportError(
            "canvod-store is required for VOD-store I/O. "
            "Install with: uv pip install 'canvod-adapters[store]'"
        ) from e

    if isinstance(store_or_site, MyIcechunkStore):
        return store_or_site
    if hasattr(store_or_site, "vod_store"):
        return store_or_site.vod_store
    return MyIcechunkStore(Path(store_or_site), store_type="vod_store")


def vod_store_to_gnssvod_nc(
    store_or_site: Any,
    analysis_name: str,
    out_path: Path | str,
    *,
    band_map: list[tuple[str, str, str | None]] | None = None,
    branch: str = "main",
) -> Path:
    """Read a canvodpy VOD analysis and export it as a gnssvod-shaped NetCDF.

    Parameters
    ----------
    store_or_site : MyIcechunkStore, site/manager object, or path
        Source of the VOD store. A site/manager object is used via its
        ``.vod_store`` attribute (matches ``GnssResearchSite``).
    analysis_name : str
        VOD analysis group to read (e.g. ``"canopy_01_vs_reference_01"``).
    out_path : Path or str
        Destination NetCDF file path.
    band_map : list of (band_suffix, snr_col, vod_col), optional
        Defaults to ``BAND_MAP`` (see ``canvod.adapters.gnssvod.convert``).
    branch : str, default "main"
        Icechunk branch to read from.

    Returns
    -------
    Path
        ``out_path``, for chaining.
    """
    store = _resolve_store(store_or_site)
    vod_ds = store.read_group(analysis_name, branch=branch).load()

    gnssvod_ds = to_gnssvod_dataset(vod_ds, band_map=band_map)
    gnssvod_ds.attrs.update(build_provenance_attrs("canvodpy_to_gnssvod", analysis_name))

    out_path = Path(out_path)
    gnssvod_ds.to_netcdf(out_path)
    return out_path


def gnssvod_nc_to_vod_store(
    nc_path: Path | str,
    store_or_site: Any,
    analysis_name: str,
    *,
    band_map: list[tuple[str, str, str | None]] | None = None,
    branch: str = "main",
    commit_message: str | None = None,
) -> bool:
    """Import a gnssvod NetCDF export into a canvodpy VOD Icechunk store.

    Parameters
    ----------
    nc_path : Path or str
        Path to a gnssvod-shaped NetCDF file (either a real gnssvod export,
        or one written by :func:`vod_store_to_gnssvod_nc`).
    store_or_site : MyIcechunkStore, site/manager object, or path
        Destination VOD store. A site/manager object is used via its
        ``.vod_store`` attribute (matches ``GnssResearchSite``).
    analysis_name : str
        VOD analysis group to write.
    band_map : list of (band_suffix, snr_col, vod_col), optional
        Defaults to ``BAND_MAP``.
    branch : str, default "main"
        Icechunk branch to write to.
    commit_message : str, optional
        Defaults to a message citing the source file name.

    Returns
    -------
    bool
        ``True`` if written (``write_or_append_group``'s ``dedup=False``
        default for VOD/derived-data stores means this only returns
        ``False`` in edge cases the store itself defines).

    Notes
    -----
    The reconstructed VOD dataset carries
    ``attrs["vod_reconstructed_code_ambiguous"] = True`` — gnssvod merges
    tracking codes per band before export, so the per-code identity in the
    resulting SIDs is a placeholder, not observed. See
    ``canvod.adapters.gnssvod.convert.from_gnssvod_dataset``.
    """
    gnssvod_ds = xr.open_dataset(nc_path)
    vod_ds = from_gnssvod_dataset(gnssvod_ds, band_map=band_map)
    vod_ds.attrs.update(build_provenance_attrs("gnssvod_to_canvodpy", analysis_name))

    store = _resolve_store(store_or_site)
    return store.write_or_append_group(
        vod_ds,
        analysis_name,
        branch=branch,
        commit_message=commit_message or f"Imported from gnssvod NetCDF: {Path(nc_path).name}",
    )
