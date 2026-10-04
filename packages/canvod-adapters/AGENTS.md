# canvod-adapters

Data exchange between canvodpy and other GNSS-T programs. Today: gnssvod
(Humphrey et al.).

## Where things are

- `src/canvod/adapters/base.py`: the interfaces, one ABC per kind of data
  (`ObservationsAdapter`, `VodAdapter`). Their concrete methods
  (`import_file`, `export_file`, ...) check the result against canvodpy's
  contract and add provenance; subclasses only convert.
- `src/canvod/adapters/provenance.py`: `Tool`, `Provenance`, written as
  `conversion_*` attributes.
- `src/canvod/adapters/store.py`: `import_vod` / `export_vod`, VOD store
  I/O through any `VodAdapter` (needs the `store` extra).
- `src/canvod/adapters/gnssvod/`: the gnssvod adapter.
  `src/canvod/adapters/gnssvod/convert.py` holds pure dataset conversions,
  `src/canvod/adapters/gnssvod/reader.py` a canvodpy reader of gnssvod
  observation files, `src/canvod/adapters/gnssvod/adapter.py` the two
  adapters.

## Design

- One subpackage per program. It implements only the interfaces of the
  data it exchanges, and only converts. Checks, provenance and store I/O are
  shared at the package root.
- Observations are imported through a canvodpy reader
  (`canvod.readers.GNSSDataReader`) of the program's files, so they carry
  the file hash, reader attributes and the epoch time scale like any other
  canvodpy input.
- Contracts are canvodpy's: `canvod.readers.validate_dataset` and
  `validate_vod_dataset`. sid <-> observation code:
  `canvod.readers.gnss_specs.obs_codes`; sid coordinates:
  `canvod.readers.sid_coords`.
- Imported VOD goes to the store group `{tool}/{analysis_name}`, apart from
  VOD canvodpy computed.

## gnssvod specifics

Dims `(Epoch, SV)`, one variable per observation code or VOD band,
`Azimuth`/`Elevation` in degrees (canvodpy: `phi`/`theta` in radians).
`calc_vod` merges a band's codes in sorted order, each filling the gaps of
the previous; a merged band imports with the unknown-code marker
(`G01|L1|u`) and exports back unchanged. `calc_vod` reports the reference
receiver's angles, canvodpy the canopy receiver's. Verified against gnssvod
on the Rosalia test files.

## Tests

`just test-package canvod-adapters`. `tests/conftest.py` builds synthetic
datasets that meet the contracts (`obs_ds`, `vod_ds`); gnssvod itself is
not needed. `tests/test_store.py` is skipped unless canvod-store is
installed (`store` extra).
