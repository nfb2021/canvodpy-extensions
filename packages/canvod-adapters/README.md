# canvod-adapters

Bidirectional data adapters between canvodpy and third-party GNSS-VOD tools.

Part of the [canVODpy](https://github.com/nfb2021/canvodpy) ecosystem.

## Overview

`canvod-adapters` converts canvodpy's native data structures into the
shapes expected by other tools in the GNSS-Transmissometry/VOD field, and
back — so each tool's ecosystem can be used on the other's output.

Every conversion records its provenance in the output dataset's global
attributes (source tool, URL, version, direction, timestamp), so converted
files remain traceable back to their origin.

## Adapters

| Adapter | Converts | Direction |
|---|---|---|
| `canvod.adapters.gnssvod` | canvodpy VOD Icechunk store ⟷ [gnssvod](https://github.com/GEUS-SATRO/gnssvod) (Humphrey et al.) NetCDF | Both |

### gnssvod adapter

canvodpy stores computed VOD per analysis pair as one Icechunk group with
`(epoch, sid)`-dimensioned variables `VOD`, `delta_snr`, `phi`, `theta`
(SID format `"G01|L1|C"`). gnssvod's own tooling (`Hemi.add_CellID()`,
plotting, hemispheric statistics) expects `(Epoch, SV)`-dimensioned
datasets with per-band columns like `S1C`/`Azimuth`/`Elevation`/`VOD1`.

```python
from canvod.adapters.gnssvod.convert import to_gnssvod_dataset, from_gnssvod_dataset

# canvodpy VOD dataset -> gnssvod-shaped dataset
gnssvod_ds = to_gnssvod_dataset(vod_ds)
gnssvod_ds.to_netcdf("canopy_01_vs_reference_01.nc")

# gnssvod-shaped dataset -> canvodpy VOD dataset
vod_ds = from_gnssvod_dataset(gnssvod_ds)
```

With the optional `store` extra installed, convenience functions read/write
an Icechunk VOD store directly:

```python
from canvod.adapters.gnssvod.io import vod_store_to_gnssvod_nc, gnssvod_nc_to_vod_store

vod_store_to_gnssvod_nc(site, "canopy_01_vs_reference_01", "out.nc")
gnssvod_nc_to_vod_store("gnssvod_output.nc", site, "imported_analysis")
```

**Note:** the reverse direction (gnssvod → canvodpy) is lossy for the
per-code tracking identity of `VOD` — gnssvod merges multiple tracking
codes per band via `fillna` before export, so the original per-code SID
can't be recovered. Reconstructed datasets carry
`vod_reconstructed_code_ambiguous=True` in their attrs to flag this.

## Installation

GitHub-only by design; install via the git-subdirectory pattern:

```bash
uv add "canvod-adapters @ git+https://github.com/nfb2021/canvodpy-extensions.git@v0.1.0#subdirectory=packages/canvod-adapters"
uv add "canvod-adapters[store] @ git+https://github.com/nfb2021/canvodpy-extensions.git@v0.1.0#subdirectory=packages/canvod-adapters"  # for direct Icechunk store I/O
```

## Documentation

[Full documentation](https://nfb2021.github.io/canvodpy-extensions/packages/adapters/overview/)

## License

Apache License 2.0
