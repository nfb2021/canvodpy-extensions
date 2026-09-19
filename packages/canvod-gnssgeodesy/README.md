# canvod-gnssgeodesy

Native GNSS geodetic products for canvodpy: reflectometry (reflector
height, GNSS-IR), code/pseudorange multipath (MP1rms, NMRI), and
firmware-reported multipath diagnostics — with tropospheric products and
PPP planned. See
[`docs/design/canvod-gnssgeodesy/PLAN.md`](../../docs/design/canvod-gnssgeodesy/PLAN.md)
in this repo for the full implementation plan, and
[`RATIONALE.md`](../../docs/design/canvod-gnssgeodesy/RATIONALE.md) in
the same directory for the *why* behind every non-obvious decision.

## License: GPL-3.0-only

**This package is licensed under GPL-3.0-only, not this monorepo's
Apache-2.0 default.** This is a deliberate, package-scoped exception (see
`RATIONALE.md` §19) — `canvod-gnssgeodesy` calls
[gnssrefl](https://github.com/kristinemlarson/gnssrefl)'s (GPLv3)
reflector-height and refraction-correction functions directly rather than
reimplementing them, on the principle that gnssrefl is the
community-trusted reference implementation for GNSS-IR and should be
called, not silently re-derived (`RATIONALE.md` §17). Because this
package depends on and directly calls GPL-3.0-only code, the combined
work is GPL-3.0-only under the standard reading of that license — not
`GPL-3.0-or-later`, matching gnssrefl's own declared classifier exactly
(verified directly against gnssrefl's `pyproject.toml`, not inferred from
generic license boilerplate; see `PLAN.md` §2).

**Credit:** the reflector-height retrieval and atmospheric refraction
correction in this package are thin translation layers around
[gnssrefl](https://github.com/kristinemlarson/gnssrefl) by Kristine M.
Larson and collaborators. No GNSS-IR geodesy is re-derived here; gnssrefl
is called directly wherever a clean, in-memory function exists to wrap.
Code/pseudorange multipath (MP1rms, NMRI) has no equivalent Python core
to wrap anywhere upstream (gnssrefl's own MP1 path shells out to the
deprecated `teqc` binary) and is implemented here from the published
literature (Larson & Small 2014; Small, Larson & Smith 2014) instead.

## Status

Pre-implementation scaffold. See `PLAN.md` §12 for the phase plan.

## Installation

Not yet published. Once `canvod-gnssgeodesy` has real functionality,
install via this repo's git-subdirectory source, same as
`canvod-filemap`/`canvod-adapters`:

```toml
[tool.uv.sources]
canvod-gnssgeodesy = { git = "https://github.com/nfb2021/canvodpy-extensions.git", subdirectory = "packages/canvod-gnssgeodesy", tag = "vX.Y.Z" }
```

## Development

```bash
uv sync
just check   # lint + format + type-check
just test    # run tests
```
