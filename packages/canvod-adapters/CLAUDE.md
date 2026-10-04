# canvod-adapters

Data exchange between canvodpy and other GNSS-T programs.

## Key modules

| Module | Purpose |
|---|---|
| `base.py` | `ObservationsAdapter`, `VodAdapter`: one ABC per kind of data; imports are checked against canvodpy's contracts (`canvod.readers.validate_dataset` / `validate_vod_dataset`) and get provenance |
| `provenance.py` | `Tool`, `Provenance` (pydantic) <-> `conversion_*` attrs |
| `store.py` | `import_vod` / `export_vod`: VOD store I/O through any `VodAdapter` (`store` extra) |
| `gnssvod/convert.py` | dataset conversion gnssvod <-> canvodpy, pure functions |
| `gnssvod/reader.py` | `GnssvodObsReader(GNSSDataReader)`: gnssvod observation files |
| `gnssvod/adapter.py` | `GnssvodObservations`, `GnssvodVod` |

## Design

- Shared logic (interfaces, contract checks, provenance, store I/O) lives
  at the package root; a program's subpackage only converts.
- A program implements only the interfaces of the data it exchanges.
- The contracts are canvodpy's (canvod-readers), not this package's; the
  VOD store checks the VOD contract too.
- Observations come in through a canvodpy reader of the program's files,
  so they carry the file hash, reader attrs and epoch time scale.
- Adapter settings are frozen pydantic fields, validated on creation.
- sid <-> observation code: `canvod.readers.gnss_specs.obs_codes`; sid
  coordinates: `canvod.readers.sid_coords`.

### gnssvod

`(Epoch, SV)` dims, one variable per observation code or VOD band,
`Azimuth`/`Elevation` in degrees. `calc_vod` merges a band's codes in
sorted order (`numpy.intersect1d`), each filling the gaps of the previous;
merged bands import with the unknown-code marker (`G01|L1|u`) and export
back unchanged. Verified against gnssvod on the Rosalia test files.

## Testing

```bash
uv run pytest packages/canvod-adapters/tests/
```
