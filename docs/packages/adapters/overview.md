# canvod-adapters

`canvod-adapters` exchanges data between canvodpy and other GNSS-T
programs. It currently provides an adapter to
[gnssvod](https://github.com/vincenthumphrey/gnssvod) (Humphrey et al.),
widely used in the GNSS-T community.

## Design

The package separates what all programs share from what is specific to
one program.

```
canvod/adapters/
  base.py          one interface per kind of data: ObservationsAdapter, VodAdapter
  provenance.py    Tool, Provenance
  store.py         import_vod / export_vod: VOD store I/O through any VodAdapter
  gnssvod/
    convert.py     conversion of datasets, gnssvod <-> canvodpy
    reader.py      GnssvodObsReader: canvodpy reader of gnssvod observation files
    adapter.py     GnssvodObservations, GnssvodVod
```

**One interface per kind of data.** Programs exchange different data with
canvodpy: one writes observations, another only VOD. A program's adapter
implements the interfaces of the data it exchanges, and only those.

**canvodpy's contracts guard everything that comes in.** canvodpy defines
what its data looks like, and the interfaces check every import against
it, whichever program it comes from:

| Data | Contract | Also checked by |
|---|---|---|
| Observations | `canvod.readers.validate_dataset`, the contract of every canvodpy reader | every canvodpy reader |
| VOD | `canvod.readers.validate_vod_dataset` | the VOD store, before every write |

Observations are imported with a canvodpy reader of the program's files
(a `canvod.readers.GNSSDataReader`), so imported observations carry the
same file hash, attributes and epoch time scale as observations read from
RINEX or SBF files.

**Settings are pydantic models.** An adapter is a frozen pydantic model
whose fields are the program's settings, checked when the adapter is
created, e.g. the bands of `GnssvodVod`.

**Provenance.** Every conversion records the program, its URL and
installed version, the canvod-adapters version, the direction, the source
and the time in the dataset attributes (`conversion_*`), readable back
with `Provenance.from_attrs`.

## gnssvod

gnssvod works on datasets with dimensions `(Epoch, SV)`, one variable per
RINEX observation code (`S1C`, `C1C`, ...) or per VOD band, and angles in
degrees. canvodpy works on `(epoch, sid)`, sid `"G01|L1|C"`, angles in
radians. Signal IDs and observation codes are mapped with the rules of
canvodpy's RINEX readers.

### VOD

```python
from canvod.adapters.gnssvod import GnssvodVod
from canvod.adapters.store import export_vod, import_vod

# The bands argument of gnssvod.calc_vod
adapter = GnssvodVod(bands={"VOD_L1": ["S1C", "S1W", "S1X"], "VOD_L2": ["S2W"]})

# gnssvod -> canvodpy: into the VOD store group "gnssvod/canopy_01_vs_reference_01"
import_vod(adapter, "vod_rosalia.nc", site.vod_store, "canopy_01_vs_reference_01")

# canvodpy -> gnssvod, merged per band as calc_vod merges
export_vod(
    adapter,
    site.vod_store,
    "tau_omega_zeroth_order/canopy_01_vs_reference_01",
    "vod_canvodpy.nc",
)

# Without a store
vod = adapter.import_file("vod_rosalia.nc")
adapter.export_file(vod, "again.nc", source="vod_rosalia.nc")
```

A gnssvod VOD file is the result of `calc_vod` for one station pair,
written with `DataFrame.to_xarray().to_netcdf()`.

`calc_vod` merges the observation codes of a band. Imported VOD of a band
with one code gets that code's sids (`S2W` → `G01|L2|W`). A band with
several codes gets canvodpy's marker for an unknown tracking code
(`G01|L1|u`). Exporting such data gives the same file back.

`calc_vod` reports the reference receiver's `Azimuth`/`Elevation`;
canvodpy reports the canopy receiver's. Imported VOD keeps gnssvod's
angles.

The VOD store keeps imported VOD under the program's name in place of
the VOD model, apart from VOD canvodpy computed. Importing the same file
again is skipped.

### Observations

```python
from canvod.adapters.gnssvod import GnssvodObservations

adapter = GnssvodObservations(time_system="GPS")
obs = adapter.import_file("ROSA_obs.nc")  # a file gnssvod.preprocess wrote
adapter.export_file(obs, "for_gnssvod.nc", source="canopy_01")
```

gnssvod keeps the epochs of the RINEX file, so the time scale of the
file (its `TIME OF FIRST OBS` record) is a required setting.

### Verification

On the Rosalia test RINEX files, gnssvod's own observation files read
with `GnssvodObservations` give the same signals, sid coordinates and
values as canvodpy's RINEX reader. canvodpy's VOD exported with
`GnssvodVod` matches gnssvod's `calc_vod` on the same input to 1e-6.
Importing gnssvod's VOD and exporting it again gives the same file.

## Adding an adapter for another program

1. Create a subpackage `canvod/adapters/<program>/`.
2. Describe the program with a `Tool` (name, Python distribution, URL).
3. Implement the interfaces of the data it exchanges:
    - `VodAdapter`: `open`, `save`, `convert_to_canvodpy`,
      `convert_from_canvodpy`;
    - `ObservationsAdapter`: `reader` (a `canvod.readers.GNSSDataReader`
      of the program's files), `convert_from_canvodpy`, `save`.
4. Put the program's settings in fields of the adapter.

Contract checks, provenance and store I/O come with the interfaces.

## Installation

```bash
uv add "canvod-adapters @ git+https://github.com/nfb2021/canvodpy-extensions.git@v0.1.0#subdirectory=packages/canvod-adapters"
uv add "canvod-adapters[store] @ git+https://github.com/nfb2021/canvodpy-extensions.git@v0.1.0#subdirectory=packages/canvod-adapters"
```

See the [API Reference](../../api/canvod-adapters.md) for the full public API.
