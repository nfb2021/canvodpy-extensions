"""Adapters between canvodpy and gnssvod (Humphrey et al.) data structures."""

from canvod.adapters.gnssvod.convert import (
    BAND_MAP,
    GnssvodAdapter,
    detect_band_map,
    from_gnssvod_dataset,
    gnssvod_df_to_xarray,
    gnssvod_merge_codes,
    to_gnssvod_dataset,
)
from canvod.adapters.gnssvod.io import gnssvod_nc_to_vod_store, vod_store_to_gnssvod_nc
from canvod.adapters.gnssvod.provenance import build_provenance_attrs

__all__ = [
    "BAND_MAP",
    "GnssvodAdapter",
    "build_provenance_attrs",
    "detect_band_map",
    "from_gnssvod_dataset",
    "gnssvod_df_to_xarray",
    "gnssvod_merge_codes",
    "gnssvod_nc_to_vod_store",
    "to_gnssvod_dataset",
    "vod_store_to_gnssvod_nc",
]
