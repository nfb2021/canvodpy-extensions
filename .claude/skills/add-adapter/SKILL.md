---
name: add-adapter
description: Add support for another GNSS-T program (besides gnssvod) to canvod-adapters, so its observation or VOD files can be imported into and exported from canvodpy. Use when asked to exchange data with a new tool or file format of another program.
---

# Add an adapter for a GNSS-T program

Model: `packages/canvod-adapters/src/canvod/adapters/gnssvod/`. Read
`packages/canvod-adapters/AGENTS.md` first, then the canvodpy side (root
`AGENTS.md`): the reader contract in
`canvodpy:docs/packages/readers/extending.md` applies to the reader you
write.

## 1. Find out what the program exchanges

Look at the program's files and code, not only its docs:

- Observations, VOD, or both? Implement only those interfaces.
- Dims, variable names, units (degrees vs radians, dB-Hz), time scale of
  the epochs, how satellites and signals are named.
- How it combines signals (e.g. gnssvod merges several codes into one band).
  This decides how sids map in both directions.

## 2. Layout

```text
src/canvod/adapters/<tool>/
    __init__.py   # public names, __all__
    convert.py    # pure functions: dataset <-> dataset, no I/O
    reader.py     # only for observations: a canvodpy reader of its files
    adapter.py    # Tool constant and the adapter classes
```

## 3. Implement

- `Tool(name=..., distribution=..., url=...)`: `name` is also the store
  group of imported VOD, `distribution` the installed package whose version
  goes into the provenance (recorded as "not installed" when absent; the
  program is never a dependency).
- Observations: subclass `canvod.readers.GNSSDataReader` for its files
  (abstract: `source_format`, `file_hash`, `to_ds`, `iter_epochs`,
  `start_time`, `end_time`, `systems`, `num_satellites`; see
  `packages/canvod-adapters/src/canvod/adapters/gnssvod/reader.py`), so
  imports carry the file hash and reader attributes. Then `ObservationsAdapter` with `reader`,
  `convert_from_canvodpy`, `save`.
- VOD: `VodAdapter` with `open`, `save`, `convert_to_canvodpy`,
  `convert_from_canvodpy`.
- Settings the conversion needs (time scale, band definitions) are pydantic
  fields; check them in validators so a wrong setting fails on creation.
- Do not override `import_file` / `export_file` / `import_dataset`: the base
  class checks the canvodpy contract and adds provenance there.
- sids: build them with `canvod.readers.gnss_specs.obs_codes` and
  `canvod.readers.sid_coords`. Codes the program cannot tell apart use
  canvodpy's unknown-code marker (`G01|L1|u`). Don't invent new sid forms.
- Angles: canvodpy `phi`/`theta` in radians; convert at the edge.

## 4. Test

In `packages/canvod-adapters/tests/`, using the fixtures `obs_ds` and
`vod_ds` from `packages/canvod-adapters/tests/conftest.py`:

- round trip: canvodpy -> tool -> canvodpy gives the same data and sids;
- import passes `validate_dataset` / `validate_vod_dataset` (the base class
  raises otherwise);
- every settings validator rejects what it should;
- if possible, one comparison with output of the real program on a small
  file. Say in the docs what it was verified against.

## 5. Wire up and document

- Re-export from `<tool>/__init__.py`; list the subpackage in the
  docstring of `packages/canvod-adapters/src/canvod/adapters/__init__.py`.
- `docs/api/canvod-adapters.md`: a section `::: canvod.adapters.<tool>.adapter`.
- `docs/packages/adapters/overview.md` and `packages/canvod-adapters/README.md`:
  usage and the mapping rules.
- `packages/canvod-adapters/AGENTS.md`: a short "<tool> specifics" section.
- Commit as `feat(adapters): <tool> adapter`.
