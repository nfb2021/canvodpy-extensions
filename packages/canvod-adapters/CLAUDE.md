# canvod-adapters

Bidirectional data adapters between canvodpy and third-party GNSS-VOD tools.

## Key modules

| Module | Purpose |
|---|---|
| `gnssvod/convert.py` | `to_gnssvod_dataset()` / `from_gnssvod_dataset()` — pure-format transform, no `canvod-store`/`gnssvod` import |
| `gnssvod/provenance.py` | `build_provenance_attrs()` — records source/tool/version/direction/timestamp in output attrs |
| `gnssvod/io.py` | `vod_store_to_gnssvod_nc()` / `gnssvod_nc_to_vod_store()` — Icechunk store I/O, requires the `store` extra |

## Design

`convert.py` has zero dependency on `canvod-store` or the real `gnssvod`
package — it only matches gnssvod's documented data shape (verified against
gnssvod's own `io/io.py::Observation.to_xarray()` /
`io/exporters.py::export_as_nc()`). This keeps the core conversion logic
importable and testable without either optional dependency installed.

Originally built for `canvod-audit`'s Tier-3 comparison
(`audit_vs_gnssvod`), extracted here so it's reusable outside the audit
suite. `canvod-audit` now depends on this package instead of vendoring its
own copy.

### canvodpy VOD store shape

One Icechunk group per `analysis_name`: `(epoch, sid)` dims, variables
`VOD`, `delta_snr`, `phi` (rad, azimuth from North CW), `theta` (rad, polar
angle from zenith). SID format `"G01|L1|C"` (PRN|band|code).

### gnssvod shape

`(Epoch, SV)` dims (SV = PRN string like `"G01"`), columns `S1C`/`S2W`/...
(SNR per band+code), `Azimuth` (deg, North CW), `Elevation` (deg, from
horizon), `VOD1`/`VOD2`/... (VOD per band, codes already merged via
gnssvod's own fillna). Mapping: `Elevation = 90 - degrees(theta)`,
`Azimuth = degrees(phi) mod 360`.

### Known lossy direction

gnssvod → canvodpy is lossy for per-code identity on `VOD` columns (gnssvod
merges codes before export); reconstructed SIDs use the band map's
designated primary code and set `vod_reconstructed_code_ambiguous=True`.

## Testing

```bash
uv run pytest packages/canvod-adapters/tests/
```
