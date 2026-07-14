# canvod.adapters API Reference

## gnssvod

::: canvod.adapters.gnssvod.convert

::: canvod.adapters.gnssvod.provenance

!!! note "Why `io.py` isn't auto-generated below"
    `canvod.adapters.gnssvod.io` imports `canvod-store` lazily inside each
    function body specifically so the rest of the package stays importable
    without the optional `store` extra — mkdocstrings would need that extra
    installed to introspect it safely. Its public interface is documented
    by hand instead.

### `vod_store_to_gnssvod_nc(store_or_site, analysis_name, out_path, *, band_map=None, branch="main")`

Reads a canvodpy VOD analysis and exports it as a gnssvod-shaped NetCDF
file, with provenance attrs attached. Requires the `store` extra.

### `gnssvod_nc_to_vod_store(nc_path, store_or_site, analysis_name, *, band_map=None, branch="main", commit_message=None)`

Imports a gnssvod NetCDF export into a canvodpy VOD Icechunk store, with
provenance attrs attached. Requires the `store` extra.

See the [Overview](../packages/adapters/overview.md) for full usage examples.
