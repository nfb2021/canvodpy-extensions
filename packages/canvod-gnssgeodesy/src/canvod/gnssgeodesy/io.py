"""`geodesy_store` I/O -- `store`-extra-gated, requires `canvod-store>=0.4.0`.

Every product in this package writes into a dedicated `geodesy_store`
(mirroring `vod_store`), never as extra groups bolted onto `gnss_store`.
This requires four small `canvodpy`-core touch points that are **not yet
implemented in `canvodpy` as of this package's initial scaffold**:

- `StorageConfig.geodesy_store_name` (default `"geodesy"`) +
  `get_geodesy_store_path(site_name)`.
- `StorageConfig.geodesy_store_strategy`
  (`skip`/`overwrite`/`unsafe_append`).
- `IcechunkConfig.chunk_strategies["geodesy_store"]`
  (`ChunkStrategy(epoch=17280, sid=-1)`, same default as `gnss_store`/
  `vod_store`).
- `GnssResearchSite.geodesy_store` property + `create_geodesy_store()`
  factory in `canvod-store`, and `Site.geodesy_store` in canvodpy's
  public `api.py`.

Icechunk group naming inside `geodesy_store`: module/algorithm name as
the family, exactly matching VOD's own `{calculator_name}/
{analysis_name}` precedent —

- `snr_multipath/rh/<strategy>`
- `code_multipath/nmri/<strategy>`
- `receiver_multipath/diagnostic/<strategy>`

with a sibling `.../rollup` group per family for the per-day,
sample-count-weighted rollup each product also produces. No `station`
dim anywhere -- `station` is purely the group-path routing argument
below (one station = one group), never a real Dataset dimension.

Update mechanism: this package reuses `canvod-store`'s VOD append/dedup
ledger mechanism rather than inventing a new one -- a per-write metadata
row keyed on `source_file_hashes` (the `gnss_store` files actually
consumed), gating every write on exact-hash-match (skip, already
computed from this source) or temporal overlap with a different hash
(don't silently diverge). `canvod-store` needs its own
`write_or_append_geodesy_group()`, structurally identical to its
existing `write_or_append_vod_group()` -- also not yet implemented as of
this scaffold. This mechanism only fits a genuinely per-day-independent
product: RH and the firmware diagnostic qualify unmodified; MP1/NMRI
only qualifies once the two-tier baseline policy (see
`code_multipath.py`) has resolved what "the record" means for a given
station.
"""

from __future__ import annotations

from typing import Any

import xarray as xr

_MISSING_CANVODPY_CORE_TOUCH_POINT = (
    "canvod-gnssgeodesy's io.py requires canvodpy-core touch points that "
    "do not exist yet in the installed canvod-store: a dedicated "
    "geodesy_store (StorageConfig.geodesy_store_name/geodesy_store_strategy, "
    "IcechunkConfig.chunk_strategies['geodesy_store'], "
    "GnssResearchSite.geodesy_store/create_geodesy_store()) and a "
    "write_or_append_geodesy_group() mirroring canvod-store's existing "
    "write_or_append_vod_group(). See this module's docstring and "
    "docs/design/canvod-gnssgeodesy/PLAN.md §10 / RATIONALE.md §32 before "
    "implementing either side of this."
)


def write_or_append_geodesy_group(
    store_or_site: Any,
    group_name: str,
    dataset: xr.Dataset,
    source_file_hashes: dict[str, str],
    source_gnss_stores: dict[str, str],
    product_name: str,
    *,
    append_dim: str = "epoch",
    branch: str = "main",
    commit_message: str | None = None,
    dedup: bool = True,
) -> bool:
    """Write or append one product's output into `geodesy_store`.

    Parameters
    ----------
    store_or_site
        A `canvod.store.GnssResearchSite`/`canvodpy.Site`-like object
        exposing a `.geodesy_store`, or a `MyIcechunkStore` instance
        directly.
    group_name
        `{module}/{analysis_name}` group path, e.g.
        `"code_multipath/nmri/gnssrefl_default"`.
    dataset
        Computed product output, dims `(epoch, sid)` or `(epoch, sv)`.
    source_file_hashes
        `{receiver_name: File Hash}` for every `gnss_store` file actually
        consumed -- the dedup key.
    source_gnss_stores
        `{receiver_name: gnss_store_path}`, for provenance.
    product_name
        One of `"rh"`, `"nmri"`, `"receiver_multipath"`.
    dedup
        When `True` (default), skip a write that exactly matches an
        already-recorded `source_file_hashes` and warn on temporal
        overlap with a *different* one.

    Returns
    -------
    bool
        `True` if written, `False` if skipped as a duplicate.

    Raises
    ------
    NotImplementedError
        If the required `canvodpy`-core touch points aren't present on
        the installed `canvod-store` -- see this module's docstring.
    """
    raise NotImplementedError(_MISSING_CANVODPY_CORE_TOUCH_POINT)


def read_geodesy_group(
    store_or_site: Any,
    station: str,
    family: str,
    strategy_name: str,
    *,
    branch: str = "main",
) -> xr.Dataset:
    """Read one product's output back from `geodesy_store`.

    Raises
    ------
    NotImplementedError
        If the required `canvodpy`-core touch points aren't present on
        the installed `canvod-store` -- see this module's docstring.
    """
    raise NotImplementedError(_MISSING_CANVODPY_CORE_TOUCH_POINT)
