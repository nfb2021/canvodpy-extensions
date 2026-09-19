# canvod-gnssgeodesy

Native GNSS geodetic products for canvodpy. **Read
`docs/design/canvod-gnssgeodesy/PLAN.md` (repo root) before touching
anything in this package** — it is the actionable spec, written to be
buildable by a fresh agent with no other context. `RATIONALE.md` in the
same directory is the *why*; consult it when a decision in `PLAN.md`
seems arbitrary, but `PLAN.md` wins on any conflict between the two.

## License: GPL-3.0-only

This package is GPL-3.0-only, a deliberate exception to this monorepo's
Apache-2.0 default — see `README.md` and `RATIONALE.md` §19. Do not
import anything from this package into an Apache-2.0-licensed package in
this monorepo without checking the license implications first.

## Key modules

| Module | Purpose | Plan section |
|---|---|---|
| `arcs.py` | Shared arc segmentation, rise/set detection, azimuth-sector filtering | PLAN.md §4 |
| `qc.py` | Threshold-based arc QC (elevation compliance, duration, amplitude, FAP) | PLAN.md §5/§6 |
| `snr_multipath.py` | Reflector height (RH) via gnssrefl's `strip_compute()`, wrapped not reimplemented | PLAN.md §5 |
| `code_multipath.py` | MP1 → MP1rms → NMRI, from-scratch (no gnssrefl core exists to wrap) | PLAN.md §6 |
| `receiver_multipath.py` | SBF firmware-reported multipath, diagnostic only | PLAN.md §7 |
| `refraction.py` | Wraps gnssrefl's `refraction.py` directly; `RefractionCorrector` ABC extension point | PLAN.md §5 step 5 |
| `tropospheric.py` | ZHD/ZWD/mapping-function product (Phase 7, stub) | PLAN.md §14 |
| `ppp.py` | PPP (Phase 9, **not scoped** — tool choice pending) | PLAN.md §16 |
| `config.py` | Pydantic strategy configs (local `_StrictModel`, no `canvod-config` import) | PLAN.md §11 |
| `provenance.py` | `build_provenance_attrs()` | PLAN.md §9 |
| `io.py` | `geodesy_store` I/O — `store`-extra-gated, requires `canvod-store>=0.4.0` | PLAN.md §10 |

## The one governing principle

gnssrefl (and, for reflectometry only, gnssmultipath — checked and found
*not* to have a wrappable MP1/NMRI core, PLAN.md §5 step 5 finding) are
community-trusted reference implementations. Their correctness-sensitive
computational cores are called **directly**, never reimplemented, wherever
a clean in-memory function exists to wrap (`RhComputer`/
`RefractionCorrector` in `snr_multipath.py`/`refraction.py`). Textbook,
non-proprietary surrounding logic (detrending, arc segmentation,
aggregation) stays canvod-native. MP1/NMRI (`code_multipath.py`) is the
one exception forced by absence, not choice: gnssrefl's own MP1 path
shells out to the deprecated `teqc` binary, so there is no Python core to
wrap, and it stays a from-scratch, literature-sourced implementation
(Larson & Small 2014; Small, Larson & Smith 2014).

## Store: `geodesy_store`, not `gnss_store`

Every product in this package writes to a dedicated `geodesy_store`
(canvodpy-core, mirrors `vod_store`), never as extra groups inside
`gnss_store`. See `PLAN.md` §10 and `RATIONALE.md` §32. The canvodpy-core
touch points this requires (a new `StorageConfig.geodesy_store_name`/
`get_geodesy_store_path`/`geodesy_store_strategy`, a
`chunk_strategies["geodesy_store"]` entry, and `GnssResearchSite`/`Site`
properties) are **not yet implemented in `canvodpy`** as of this
package's initial scaffold — check `canvodpy`'s actual source before
assuming they exist.

## NMRI baseline: two-tier, not a single frozen window

`code_multipath.py`'s `NMRI` normalization uses a two-tier baseline
policy (entire-available-record while young, frozen climatology once
mature) — see `PLAN.md` §10 and `RATIONALE.md` §33 before touching
`NmriStrategyConfig.baseline_from`/`climatology_min_years` or the
baseline-computation logic. The climatology-revision problem (how a
mature station's frozen window should ever be revisited as decades of
data accumulate) is an explicit, deliberate stub — `NotImplementedError`,
not a bug — do not "fix" it without a design discussion first.

## Testing

```bash
uv run pytest packages/canvod-gnssgeodesy/tests/
```

`tests/oracle/` validates numerically against gnssrefl (RH) and
gnssmultipath (MP1 only — no NMRI oracle exists anywhere, PLAN.md §8).
Oracle tests are never part of the wheel and require the `gnssrefl`/
`gnssmultipath` extras installed.
