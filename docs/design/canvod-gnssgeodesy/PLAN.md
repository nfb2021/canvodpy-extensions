# `canvod-gnssgeodesy` — Implementation Plan

**Status: pre-implementation design, v4.** This is the actionable spec —
what to build, in what order, with what defaults. It assumes no prior
context: read this file top to bottom and you have what you need to start
Phase 0.

For *why* these decisions were made (license analysis, the four-way
literature review, discarded earlier approaches, and an audit log of what
in this document has actually been verified against primary sources versus
asserted), see **[`RATIONALE.md`](./RATIONALE.md)** in this same directory.
Section numbers in this file (currently `§1`–`§17`) are independent of
`RATIONALE.md`'s own numbering (currently `§0`, `§14`–`§30`) — despite the
overlapping-looking numbers, `§14` in one file is not `§14` in the other.
Every cross-reference in either file names which file it points to
explicitly (e.g. "RATIONALE.md §27"); a bare "§N" always means the
current file.

**Package name and scope, current as of 2026-09-18 (see RATIONALE.md §20
for the rename decision):** `canvod-gnssgeodesy` is the central home for
GNSS geodetic products in canvodpy, not a multipath-only package — that
was this package's original, narrower scope (still its largest piece:
reflectometry RH and code-multipath MP1/NMRI, §5-§6 below) before it
broadened to cover tropospheric/mapping-function products and PPP.
(Receiver position estimation/DOP was also briefly in this broadened
scope — cut 2026-09-18, RATIONALE.md §29, once neither RH nor MP1/NMRI
turned out to need a computed position at all and the SP3-path
architectural conflict in RATIONALE.md §28 raised the cost of building it
anyway.) (An earlier draft of this paragraph
explained the name choice `canvod-multipath` over `canvod-gnssir` —
that comparison is moot now; see `RATIONALE.md` §14/§20 for the full
naming history if it matters.)

**One-line summary of the governing design principle, corrected 2026-09-16
— READ THIS BEFORE ANYTHING ELSE IN THIS DOCUMENT (full rationale in
RATIONALE.md §17):** earlier drafts of this plan said to build every
module clean-room from the published literature, never importing or
porting gnssrefl's (GPLv3) code. **That principle was reversed partway
through this design process and no longer applies to anything below.**
The current, governing principle instead: gnssrefl (and, for code-
multipath, gnssmultipath) are community-trusted reference
implementations, and their correctness-sensitive computational cores are
called *directly* — not reimplemented — wherever a clean, in-memory
function exists to wrap (confirmed case by case, not assumed; see §5
step 5, §5 steps 1-4, and RATIONALE.md §17-§18 for exactly which pieces
qualify and which don't). Textbook, non-proprietary surrounding logic
(unit conversion, detrending, arc segmentation, aggregation) stays
canvod-native. The `StrategyConfig` pattern in §11 still exists and still
matters, but its job changed too: it's the kwarg-based, named-not-numbered
extension point around each wrapped default (§17), and the slot the §15
literature review was actually for (design-space reconnaissance for
future alternative methods, not license-avoidance — see §15's purpose
clarification, corrected twice by the user). Because gnssrefl is GPLv3
and its logic is called directly rather than avoided, `canvod-gnssgeodesy`
itself ships as `GPL-3.0-only`, a deliberate exception to this monorepo's
Apache-2.0 default (§2, RATIONALE.md §19) — a direct consequence of this
principle, not an independent choice.

## 1. Scope and the three-way split

| Module | Family | Observable(s) | Product | v1? |
|---|---|---|---|---|
| `snr_multipath` | reflectometry (GNSS-IR proper) | `SNR` | Reflector height (RH) | Yes |
| `code_multipath` | code/pseudorange multipath (generic geodetic QC concept, repurposed) | raw `Pseudorange`, raw `Phase` (L1+L2), GPS only | MP1rms, **NMRI** | Yes — primary driver |
| `receiver_multipath` | code/pseudorange multipath, firmware-reported | SBF firmware `mp_correction_m`/`car_mp_corr_cycles` | Firmware-reported multipath, diagnostic only | Yes, small |
| VWC / vegetation correction | reflectometry | `SNR` phase | VWC | Deferred to Phase 6 — reimplement from Zavorotny et al. 2010 + Chew et al. 2015 TGRS forward model, NOT gnssrefl's Chew/Clara lookup table (`RATIONALE.md` §15.4) |
| `tropospheric` | tropospheric/mapping-function modeling | epoch, station lat/lon/height | ZHD/ZWD, mapping functions, refraction-corrected elevation — as a standalone product, not just §5 step 5's internal RH input | Phase 7, §14 |
| ~~`position`~~ | ~~positioning~~ | — | — | **Cut from scope 2026-09-18, §15/RATIONALE.md §29** — no module in this package needs a computed position; RH and MP1/NMRI both use the station's already-known surveyed coordinate |
| `ppp` | precise point positioning | raw `Pseudorange`/`Phase`, precise ephemeris | PPP position/trajectory solution | Not scoped — tool choice pending, §16 |

**Scope broadened 2026-09-18** (`RATIONALE.md` §20): this package is the
central home for GNSS geodetic products in canvodpy, not a multipath-only
package — reflectometry/code-multipath remain the largest, most-developed
piece (they're what forced the "wrap, don't reimplement" pattern that now
governs every module here), and tropospheric modeling and PPP are
explicitly in scope too, each following the same pattern: identify
a community-trusted tool with a clean wrappable core, wrap it, keep
canvodpy-integration glue (arc segmentation, xarray shaping, config)
native. (Position estimation/DOP was briefly a third addition alongside
these — cut 2026-09-18, RATIONALE.md §29, once it turned out nothing in
this package's pipeline consumes a computed position.) Anything not on
this table is out of scope until it goes through
that same case-by-case analysis — this table is the boundary that keeps
"geodetic products" from becoming an unbounded catch-all (user's own
framing when scoping the rename).

`receiver_multipath` is **not** an independent QC cross-check against
`code_multipath` — on SBF the firmware multipath correction is *already
subtracted* from the corrected `Pseudorange`/`Phase` that a naive
`code_multipath` run would otherwise use. Once `code_multipath` is fixed to
require raw observables (§6), the two signals are correlated by
construction, not independent — useful as a diagnostic ("does our
from-scratch MP1 estimate track the firmware's own estimate in trend, on
days both are available"), not as validation.

## 2. Package skeleton

```
packages/canvod-gnssgeodesy/
  pyproject.toml
  LICENSE                   # GPL-3.0-only, full canonical text — see §2's licensing note, NOT the repo's Apache-2.0
  README.md                 # must state the GPL-3.0-only license plainly and credit gnssrefl — see §2
  CLAUDE.md
  Justfile
  pytest.ini
  src/canvod/gnssgeodesy/
    __init__.py
    arcs.py                 # shared: arc segmentation, rise/set, azimuth-sector filter
    qc.py                   # shared: threshold-based arc QC
    snr_multipath.py         # RH retrieval (Lomb-Scargle) — the reflectometry family
    code_multipath.py        # MP1 -> MP1rms -> NMRI — the code-multipath family
    receiver_multipath.py    # SBF firmware multipath, diagnostic
    refraction.py            # wraps gnssrefl's refraction.py directly, ABC extension point — see §5 step 5
    tropospheric.py           # Phase 7, stub only — standalone ZHD/ZWD/mapping-function product, see §14
    # position.py             # CUT from scope 2026-09-18, see §15/RATIONALE.md §29 — no module needs a computed position
    ppp.py                    # Phase 9, NOT SCOPED — tool choice pending user input, see §16
    config.py                # pydantic models (local _StrictModel, see §11)
    provenance.py            # attrs stamping
    io.py                    # `store`-extra-gated Icechunk read/write
  tests/
    conftest.py
    test_arcs.py
    test_qc.py
    test_snr_multipath.py
    test_code_multipath.py
    test_receiver_multipath.py
    test_refraction.py       # contract tests against the GnssreflRefractionCorrector translation layer, see §5 step 5
    test_tropospheric.py      # Phase 7
    test_config.py
    test_provenance.py
    test_io.py               # skipped unless `store` extra installed
    oracle/                  # validation-only, see §8 — never in the wheel (src/ layout already excludes tests/)
      test_against_gnssrefl.py       # RH only
      test_against_gnssmultipath.py  # MP1 only — NOT NMRI (no NMRI oracle exists anywhere), NOT position/DOP (cut from scope, §15/RATIONALE.md §29)
      fixtures/                       # regenerated from public IGS/UNAVCO RINEX, NOT vendored from gnssrefl/test/data
```

Mirrors `canvod-adapters`'s package layout (verified against its actual
source tree).

`pyproject.toml`:

```toml
[project]
name = "canvod-gnssgeodesy"
version = "0.1.0"
description = "Native GNSS multipath and reflectometry products for canvodpy"
readme = "README.md"
license = "GPL-3.0-only"
requires-python = ">=3.14"
dependencies = [
    "xarray>=2024.1.0",
    "numpy>=1.26.0",
    "scipy>=1.13.0",
    "pandas>=2.0.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
store = ["canvod-store>=0.4.0"]      # >=0.4.0: need the nested-group-path fix, see §10
parallel = ["joblib>=1.4.0"]          # arc-level fan-out, see §5
# NOTE: there is deliberately no `astropy`/`scipy` extra here anymore. Earlier
# drafts planned canvod-gnssgeodesy's own dual LSP-backend dispatch — withdrawn
# along with the from-scratch RH reimplementation (§5 steps 1-4, RATIONALE.md
# §17). RH now calls gnssrefl's gps.py:strip_compute() directly, which already
# does its own astropy/scipy dispatch internally via its own `lsp_method`
# argument (translated from RhStrategyConfig.lsp_backend, §11 — named
# explicitly after the library each option actually uses, not gnssrefl's
# internal 'fast'/'scipy' shorthand); astropy/scipy both arrive transitively
# through the `gnssrefl` extra below, not as direct dependencies. Confirmed
# via reading astropy's actual false_alarm_probability() source (RATIONALE.md
# §18) that FAP-based QC does NOT need astropy as a direct dependency either
# — the closed-form Baluev formula is used instead, computed from arrays this
# package already owns.
# Prerequisite for implementing against this plan: every exact file:line
# citation throughout this document and RATIONALE.md was read against a
# local clone of each wrapped library, at:
#   gnssrefl:      .dev_deps/gnssrefl (github.com/kristinemlarson/gnssrefl @ 526060f, 2026-08-30)
#   gnssmultipath: .dev_deps/GNSS_Multipath_Analysis_Software
#                  (github.com/paarnes/GNSS_Multipath_Analysis_Software @ e037a9b, 2026-08-21)
# `.dev_deps/` is gitignored — it does NOT ship with this repo. Clone both
# repos there yourself at the commits above before trusting any file:line
# citation in this document or RATIONALE.md; if either upstream has moved
# on, re-verify citations against the pinned commit first, current HEAD
# second (line numbers drift, the pinned commit is the source of truth for
# what was actually read).
gnssrefl = ["gnssrefl"]                # GPLv3 — see RATIONALE.md §17/§19. The whole package is GPL-3.0-only
                                        # (`license` above), so there is no Apache-2.0 core left to protect —
                                        # kept as an extra purely for install-footprint minimalism now, not a
                                        # license-boundary requirement. Could become a hard dependency with no
                                        # licensing consequence; kept as an extra as the lower-churn choice.
                                        # Version floor not yet verified against a pinned gnssrefl release — do
                                        # not ship this unpinned, resolve before Phase 3. `refraction.py`'s
                                        # GnssreflRefractionCorrector imports gnssrefl lazily (inside the method,
                                        # not at module import time) so the rest of the package works with this
                                        # extra absent.
gnssmultipath = ["gnssmultipath"]      # MIT — see RATIONALE.md §18. Same footprint-only reasoning as gnssrefl
                                        # above (MIT never carried a license-boundary requirement in the first
                                        # place). §6's Mp1Computer imports it lazily, same pattern as
                                        # GnssreflRefractionCorrector/GnssreflRhComputer. Version floor not yet
                                        # verified — resolve before Phase 3, same as gnssrefl.

[project.urls]
Homepage = "https://github.com/nfb2021/canvodpy-extensions"
Documentation = "https://nfb2021.github.io/canvodpy-extensions/packages/multipath/overview/"
Repository = "https://github.com/nfb2021/canvodpy-extensions"
Issues = "https://github.com/nfb2021/canvodpy-extensions/issues"

[build-system]
requires = ["uv_build>=0.9.17,<0.10.0"]
build-backend = "uv_build"

[tool.uv.build-backend]
module-name = "canvod.gnssgeodesy"
```

`version = "0.1.0"` is not cosmetic — the root `[tool.commitizen]
version_files` bumps every package's `pyproject.toml:version` in lockstep;
omitting it breaks that mechanism.

**Licensing: `canvod-gnssgeodesy` is GPL-3.0-only, not Apache-2.0 — a
deliberate per-package exception, decided 2026-09-18 (see RATIONALE.md
§19).** This monorepo's repo-level license is Apache-2.0, but a monorepo
can host differently-licensed packages; nothing forces every member to
match. Because this package depends on and directly calls gnssrefl
(GPLv3) rather than reimplementing its logic, the combined/distributed
work is treated as GPLv3 under the standard reading of that license.
**`GPL-3.0-only`, not the more common `GPL-3.0-or-later`** — verified by
reading gnssrefl's own `pyproject.toml` classifier directly:
`"License :: OSI Approved :: GNU General Public License v3 (GPLv3)"`, the
fixed variant, not `"GPLv3+"`. (The generic "or later" wording that
appears at the end of every vanilla GPLv3 `LICENSE` text file is a
suggested boilerplate template for projects to copy, not evidence of what
a given project actually elected — don't infer the license variant from
that text; check the project's own declared classifier/SPDX tag instead,
as done here.) A work depending on GPL-3.0-only code must itself stay
GPL-3.0-only, not upgrade to "or later."

Four mechanical steps this requires, all present in the skeleton above:
1. `pyproject.toml`: `license = "GPL-3.0-only"` (done above).
2. `LICENSE`: the canonical GPLv3 text, copied verbatim (e.g. from
   `.dev_deps/gnssrefl/LICENSE` or the canonical text at gnu.org) — this
   text is identical across every GPLv3 project, nothing to author.
3. Root `REUSE.toml` needs a new scoped `[[annotations]]` block for
   `path = "packages/canvod-gnssgeodesy/**"` with
   `SPDX-License-Identifier = "GPL-3.0-only"`, overriding the repo's
   existing blanket `path = "**"` → Apache-2.0 rule for just this
   package's path. The existing blanket rule uses
   `precedence = "aggregate"` — run `reuse lint` once this package and
   its `REUSE.toml` entry both exist, to confirm the scoped rule actually
   wins rather than merging unexpectedly; don't assume without checking.
4. `README.md` must state the GPL-3.0-only license plainly and credit
   gnssrefl (Kristine Larson et al.) as the reason this package differs
   from the rest of the monorepo — GPLv3 doesn't strictly mandate a
   NOTICE-style attribution the way Apache-2.0 does, but crediting the
   project this package is built on is the substance of "respecting
   gnssrefl's wishes," not just the license text's letter.

## 3. Observable availability — per format, not a single config flag

**RINEX**: `ProcessingParams.keep_gnss_observables` (default `["SNR"]`,
`canvod-config/src/canvod/config/models/processing_params.py:45-48`) gates
exactly what the reader keeps. For `code_multipath` on RINEX-sourced stores:

```yaml
processing:
  params:
    keep_gnss_observables: ["SNR", "Pseudorange", "Phase", "LLI"]
```

still applies as-is — RINEX readers support all four.

**SBF**: the same config key controls the SBF reader's `keep_data_vars`
filter too, but two problems block the RINEX recipe from working unmodified:

1. `"LLI"` is not a producible variable on SBF — including it in the list
   raises (`validate_dataset` requires every listed var to exist). Cycle-slip
   detection on SBF must use a different signal (`cum_loss_cont`, already
   parsed — see §6).
2. **This is the important one.** SBF's `Pseudorange`/`Phase` variables are
   *derived*, not raw. Per Septentrio's own documented firmware design
   (`canvod-readers/src/canvod/readers/sbf/reader.py:457-522`, the
   `_PSEUDORANGE_RAW_ATTRS`/`_PHASE_RAW_ATTRS`/`_PSEUDORANGE_UNSMOOTHED_ATTRS`
   constants, which cite the *Septentrio AsteRx SB3 ProBase Firmware v4.14.0
   Reference Guide* by block/field/page number):

   ```
   Pseudorange_raw = Pseudorange + smoothing_corr_m + mp_correction_m
   Phase_raw       = Phase + car_mp_corr_cycles
   ```

   i.e. the default `Pseudorange`/`Phase` are Hatch-filter-smoothed and
   firmware multipath-corrected. Confirmed on real ROSA fixtures
   (`canvod-readers/tests/test_data/valid/sbf/01_Rosalia/`): `Pseudorange −
   Pseudorange_raw` has mean |diff| = 0.163 m, max |diff| = 2.24 m — the
   same order of magnitude as the seasonal NMRI signal itself. `MP1`'s
   classical algebraic definition (Larson & Small 2014) requires
   uncorrected input, so `code_multipath.py` **must refuse to run** (raise,
   not warn) if it receives corrected `Pseudorange`/`Phase` on SBF-sourced
   data rather than the `_raw` variants — checked at input-validation time.

   Reader exposes `Pseudorange_raw`/`Phase_raw` via the same
   `keep_gnss_observables` mechanism, but **not requested by default**, and
   getting them requires a workaround for a real upstream bug (below).

**Upstream `canvod-readers` bug — SBF raw-observable request always fails.**
`SbfReader.to_ds_and_auxiliary()` calls `validate_dataset(obs_ds,
required_vars=keep_data_vars)` at `sbf/reader.py:2490` — **before** the
`store_raw_observables` block (`:2876-2930`) that actually creates
`Pseudorange_raw`/`Phase_raw`/`SNR_raw`/`Pseudorange_unsmoothed`. Passing any
of those four names in `keep_data_vars` therefore always raises "Missing
required data variables," unconditionally, regardless of
`store_raw_observables`. This is not a library-internals-only issue — it
sits on the real production ingest path:
`canvodpy/src/canvodpy/orchestrator/processor.py:186-192` calls
`rnx.to_ds_and_auxiliary(keep_data_vars=keep_vars, ...,
store_raw_observables=store_sbf_raw_observables, ...)` where `keep_vars`
traces back to `load_config().processing.params.keep_gnss_observables`
(four separate call sites in `processor.py`: `3713`, `3881`, `4197`,
`4915`). Requesting `["SNR", "Pseudorange_raw", "Phase_raw"]` via the
documented config mechanism **will crash real ingest**, not just a
hand-rolled reader call.

**Working recipe** (verified against the real fixture): request
`keep_data_vars=None` — this validates against the default `["SNR"]` only
and skips the post-hoc drop-filter entirely (both gated on `is not None`),
returning every variable including the raw ones — then subset in Python
afterward. `canvod-gnssgeodesy`'s SBF ingest path cannot go through the
standard `keep_gnss_observables` mechanism as-is. Two options:

- (a) always request `keep_data_vars=None` for SBF and filter downstream,
  bypassing config-driven selection for this one format — the workaround if
  the upstream fix hasn't landed; or
- (b) **file this as a bug against `canvod-readers`** (move the
  `validate_dataset` call after the `store_raw_observables` block) and get
  it fixed before Phase 1. This is the honest fix, do this first if timing
  allows.

Phase 0 (§12) must exercise **both** RINEX and SBF re-ingest — the
SBF-specific failure modes above are invisible from the RINEX path alone.

Storage-cost note: the global default stays `["SNR"]`; this is an opt-in
per analysis run, documented in this package's README, not a global default
change. Confirm before v1: whether an existing SNR-only store needs a full
re-ingest from raw RINEX/SBF to add these fields (almost certainly yes —
Icechunk/Zarr variable sets aren't retrofittable onto an existing store
without reprocessing the source files).

## 4. `arcs.py` — shared arc segmentation

```python
class Arc(NamedTuple):
    sid: str
    satellite: str            # e.g. "G01"
    band: str                  # e.g. "L1"
    tracking_code: str          # e.g. "C" vs "W" — see tracking-code policy below
    rise_set: int                # +1 rise, -1 set
    epoch_index: np.ndarray       # integer indices into the parent Dataset's epoch axis — NOT a slice
    azimuth_at_min_elev: float
    elevation_deg: np.ndarray
    azimuth_deg: np.ndarray

def detect_arcs(
    ds: xr.Dataset,
    *,
    min_elev_deg: float,
    max_elev_deg: float,
    azimuth_sectors: list[tuple[float, float]] | None,
    max_gap_epochs: int,              # sampling-interval / gap tolerance
    theta_var: str = "theta",         # NOT "elevation" — no such variable exists on reader/VOD output
    constellations: list[str] = ["G"], # v1 default GPS-only, see §6 constellation-scope note
    tracking_codes: dict[str, str] = DEFAULT_TRACKING_CODES,  # per-band code selection policy, see below — literature default, always overridable, never auto-detected
) -> list[Arc]: ...

DEFAULT_TRACKING_CODES: dict[str, str] = {"L1": "C", "L2": "W"}
```

- **`epoch_index: np.ndarray`, not a slice.** Arcs on a real, SID-padded
  grid can have interior NaN gaps (padding to the global SID universe
  reindexes with `fill_value=NaN`); a plain slice can't represent that. Use
  an index array or boolean mask, and derive `elevation_deg`/`azimuth_deg`
  from it rather than carrying both an index and separately materialized
  arrays that could disagree.
- **`theta_var` default is `theta`, not `elevation`.** No bare `elevation`
  variable exists on raw reader/ephemeris-augmented output (an optional
  `ElevationAugmentation` transform in `canvod-auxiliary` can add one, but
  don't assume it ran). Derive inside `detect_arcs`:
  `elevation_deg = 90 - np.degrees(theta)`, `azimuth_deg = np.degrees(phi) % 360`.
  `theta`/`phi` are radians; the declared domain is `theta ∈ [0, π]`
  (`canvod-auxiliary/src/canvod/auxiliary/position/spherical_coords.py`),
  with an explicit runtime rule "`theta > π/2` → below horizon (set to
  NaN)" — so populated values are always in `[0, π/2]`. Three independent
  sources agree on the `Elevation = 90 - degrees(theta)` mapping: that
  docstring, `canvod-grids`' own `cos(theta)` usage in solid-angle
  calculations, and `canvod-adapters/CLAUDE.md:37-38`. Assert the range
  defensively anyway — `canvod-readers/src/canvod/readers/gnss_specs/metadata.py:296-317`
  carries a stale, confirmed-unused `DATAVARS_TO_BE_FILLED` dict claiming
  `theta`/`phi` are in *degrees* with a `-9999.0` fill value; it's dead code
  (grepped, referenced nowhere else) but would mislead anyone who trusts
  attrs over the actual values.
- `theta` is float32; boundary detection by raw sign-of-diff will chatter
  near the arc apex (elevation-rate approaches zero there). Use a smoothed
  gradient or hysteresis band, not a raw `diff` sign flip.
- **`azimuth_at_min_elev` vs. `azimuth_deg`, and which one `azimuth_sectors`
  filters against — checked directly, gnssrefl has no equivalent field to
  copy this from.** `strip_compute()` (`gnssrefl/gps.py:1371-1408`) returns
  `eminObs`/`emaxObs`/`riseSet` but no azimuth at all — RH's own core LSP
  function doesn't track a per-arc azimuth, so this field is canvod-native,
  not something to defer to gnssrefl's behavior for. Two things this plan
  must pin down that gnssrefl's absence of the field left open:
  1. **`azimuth_at_min_elev` is a single summary value per arc**: the
     `azimuth_deg` sample at the arc's lowest-elevation endpoint — index
     `0` for a rising arc (`rise_set == 1`, elevation increasing from the
     horizon), index `-1` for a setting arc (`rise_set == -1`, elevation
     decreasing to the horizon), given `epoch_index` (and therefore
     `elevation_deg`/`azimuth_deg`) are time-ordered ascending. It exists
     for output/QC/plotting (a compact "where on the horizon" tag per arc,
     e.g. for RH-vs-azimuth diagnostic plots), not for filtering.
  2. **`azimuth_sectors` filters against the full per-epoch `azimuth_deg`
     array, not `azimuth_at_min_elev`** — matching gnssrefl's own actual
     behavior, confirmed directly: `window_data()`/`removeDC()`
     (`gnssrefl/gps.py:1614-1618,1954-1958`) mask every sample by
     `(azi > az1) & (azi < az2)` against the full per-epoch `azi` array,
     not a single representative azimuth. A satellite pass whose azimuth
     drifts across a sector boundary during the arc is therefore
     partially masked (some epochs in-sector, some not), the same as
     gnssrefl — `detect_arcs` must apply `azimuth_sectors` per-epoch
     before or during segmentation, not as a whole-arc accept/reject test
     against `azimuth_at_min_elev`.
- **Tracking-code selection policy — prescribed literature default,
  explicitly overridable, never auto-detected (decided 2026-09-18, see
  RATIONALE.md §27).** SIDs are `SV|band|code` (e.g. `G01|L1|C` vs
  `G01|L1|W` — same satellite, same band, different code, identical
  geometry). Without an explicit selection policy, `detect_arcs` either
  double-counts arcs (RH) or has an ill-defined input for MP1 (the
  classic formula is defined against C1/P1 specifically, not "whichever
  code happened to be present"). `DEFAULT_TRACKING_CODES = {"L1": "C",
  "L2": "W"}` is the module-level default — verified against Larson &
  Small's own text (RATIONALE.md §26), not an arbitrary or gnssmultipath-
  docstring-derived choice. **Deliberately not auto-discovered per
  station/file**, even though many current receivers report L2C-based
  codes (`L`/`X`/`Q`) instead of legacy semi-codeless `W` — a real,
  common mismatch, not a rare one (RATIONALE.md §27). The chosen
  mitigation is a fixed, explicit, user-overridable default plus loud
  failure when the configured code is genuinely absent from a file (§6
  step 2's validation), not silent per-file code discovery — a
  discovery/fallback policy would quietly mix tracking methods with
  different, uncalibrated noise floors across stations/days without the
  caller ever choosing that.

## 5. `snr_multipath.py` — reflector height (RH)

**Superseded design decision (2026-09-16, see RATIONALE.md §17):** earlier
drafts of steps 1-4 below planned an independent from-scratch
reimplementation of gnssrefl's detrend/LSP/peak-pick pipeline, validated
against gnssrefl's output as an oracle (§8). That plan is withdrawn for the
same reason as refraction correction (step 5): gnssrefl is the
community-trusted baseline, and canvod-gnssgeodesy now calls its actual RH
core functions directly instead of re-deriving them. This was verified
concretely, not assumed — traced gnssrefl's own RH pipeline from
`extract_arcs.py` (arc segmentation; file/env-entangled orchestration
layer, not reused) down into `gnssrefl/gps.py`, and found two genuinely
clean, in-memory, dependency-free functions doing the actual computation:
`get_ofac_hifac(elevAngles, cf, maxH, desiredPrec)` (oversampling-factor
math) and `strip_compute(x, y, cf, maxH, desiredP, minH, lsp_method='fast')`
(the LSP itself, peak-pick included) — same shape as `correct_elevations()`,
no `REFL_CODE`, no station name, no file I/O.

One consequence worth naming explicitly: **the entire angular-vs-ordinary-
frequency risk flagged in earlier drafts of this section is now gnssrefl's
problem, not canvod-gnssgeodesy's.** `strip_compute` internally dispatches
`scipy.signal.lombscargle(x, y, 2*np.pi*px)` (angular) vs
`astropy.timeseries.LombScargle(x, y).power(px, ...)` (ordinary) itself,
confirmed by reading `gps.py:1439-1441` directly — canvod-gnssgeodesy never
touches either LSP call, so it can't get the frequency-grid convention
wrong. This is strictly less implementation risk than the original plan,
not just a licensing-motivated substitution.

Per arc:
1. `SNR` dB-Hz → linear: `A = 10**(SNR/20)`. Unchanged from earlier drafts —
   this is a fixed physical conversion, not gnssrefl-specific logic.
2. **Detrend stays a plain polynomial fit in this package — it is not
   wrapped.** gnssrefl's own equivalent step lives inside
   `gnssir_v2.py:window_new()` (`np.polyfit(ele, data, pfitV)` over the full
   arc, subtract, *then* mask to `[e1, e2]`), and is exactly as simple as
   what earlier drafts already specified: polynomial fit vs
   elevation-in-degrees, order and window sourced from gnssrefl's own
   `gnssir_input.py:78-80,444-445` defaults — window `[5°, 30°]`, order `4`
   (`RhStrategyConfig.detrend_window_deg`/`detrend_poly_order`, §11).
   Deliberately **not** called via gnssrefl's `window_new()` itself: doing
   so would force this package into gnssrefl's on-disk multi-column SNR-
   file column convention (`extract_arcs.py`'s `COL_CONST_TO_FREQ` table)
   for zero correctness benefit — `np.polyfit`/`np.polyval` is textbook, not
   gnssrefl-proprietary geodesy, so reimplementing *this specific step* over
   canvodpy's own xarray-shaped arc data carries none of the
   silent-divergence risk that motivated wrapping the LSP core.
3. **Lomb-Scargle periodogram and peak-pick — call gnssrefl's
   `strip_compute()` directly**, passing the detrended residual from step 2
   plus the per-satellite/frequency wavelength scale factor. That scale
   factor is *also* sourced from gnssrefl directly
   (`gnssrefl.gnss_frequencies.get_scale_factor(f, satNu)`) rather than
   reimplemented — GLONASS's FDMA channel-dependent wavelengths are exactly
   the kind of easy-to-get-subtly-wrong lookup this pivot exists to avoid.
   `strip_compute` returns the RH peak, its amplitude, observed
   elevation-range bounds, a rise/set flag, and the full periodogram
   (`px`/`pz`) — kept as-is, not renamed or reshaped, so nothing about
   gnssrefl's own amplitude/PSD scaling convention needs to be re-derived or
   separately documented here.
4. **Noise floor / peak-to-noise stays canvod-native**, computed on top of
   `strip_compute`'s returned periodogram arrays: define
   `noise_region_m: tuple[float, float]` in the config (an RH range known to
   be past any real reflector), compute noise as mean periodogram power
   inside that window, `peak2noise = amplitude / noise`. This is a
   deliberate, simple post-processing step on gnssrefl's own periodogram
   output, not a re-derivation of anything gnssrefl computes internally —
   gnssrefl's own peak2noise/QC thresholding happens in its file-oriented
   orchestration layer (`gnssir_guts_v2`), not in `strip_compute` itself, so
   there is nothing to call through to here. **No gnssrefl default exists
   for the noise region** (its own `nr1`/`nr2` are `None` unless
   station-supplied) — require it explicitly per station, do not invent one.

   `canvod/gnssgeodesy/refraction.py`'s sibling module gains the RH
   equivalent of §5 step 5's `RefractionCorrector` ABC:

   ```python
   from abc import ABC, abstractmethod
   from dataclasses import dataclass

   import numpy as np
   import numpy.typing as npt

   from canvod.gnssgeodesy.config import RhStrategyConfig


   @dataclass(frozen=True)
   class RhResult:
       """Runtime return value, not a config — same rationale as
       RefractionResult (§5 step 5): numpy arrays don't belong in a
       YAML-round-trippable model."""

       rh_m: float
       amplitude: float
       elevation_min_observed_deg: float
       elevation_max_observed_deg: float
       rise_or_set: int  # gnssrefl's own convention kept as-is: 1 rise, -1 set
       periodogram_rh_m: npt.NDArray[np.floating]
       periodogram_power: npt.NDArray[np.floating]


   class RhComputer(ABC):
       """Extension point mirroring RefractionCorrector. v1's only
       implementation wraps gnssrefl's gps.py:strip_compute() directly for
       the LSP peak-pick — the actual correctness-sensitive geodesy. A
       future alternative RH-retrieval method the §15 literature review
       surfaces plugs in here as a second subclass, without touching call
       sites."""

       def __init__(self, config: RhStrategyConfig) -> None:
           self._config = config

       @abstractmethod
       def compute(
           self,
           elevation_deg: npt.NDArray[np.floating],
           detrended_snr_linear: npt.NDArray[np.floating],
           *,
           frequency_code: int,
           satellite_number: int,
       ) -> RhResult: ...


   # gnssrefl's own strip_compute() takes lsp_method='fast'/'scipy' — 'fast'
   # is just its chosen sentinel for "use astropy" (the branch condition is
   # literally `if lsp_method == 'scipy': ... else: <astropy>`, gps.py:1438).
   # RhStrategyConfig.lsp_backend names the actual library instead of
   # reusing that internal shorthand; this dict is the one place the
   # translation happens.
   _GNSSREFL_LSP_METHOD: dict[str, str] = {"astropy": "fast", "scipy": "scipy"}


   class GnssreflRhComputer(RhComputer):
       """v1's only implementation. Looks up gnssrefl's own wavelength scale
       factor, calls strip_compute() unmodified, wraps its 7-tuple return
       into RhResult. No LSP math is reimplemented, altered, or ported."""

       def compute(
           self,
           elevation_deg: npt.NDArray[np.floating],
           detrended_snr_linear: npt.NDArray[np.floating],
           *,
           frequency_code: int,
           satellite_number: int,
       ) -> RhResult:
           # optional dep (`gnssrefl` extra, see §2) — imported lazily so the
           # rest of canvod-gnssgeodesy works with the extra uninstalled
           from gnssrefl.gnss_frequencies import get_scale_factor
           from gnssrefl.gps import strip_compute

           cf = get_scale_factor(frequency_code, satellite_number)
           maxF, maxAmp, eminObs, emaxObs, riseSet, px, pz = strip_compute(
               elevation_deg,
               detrended_snr_linear,
               cf,
               self._config.max_height_m,
               self._config.desired_precision_m,
               self._config.min_height_m,
               lsp_method=_GNSSREFL_LSP_METHOD[self._config.lsp_backend],
           )
           return RhResult(
               rh_m=maxF,
               amplitude=maxAmp,
               elevation_min_observed_deg=eminObs,
               elevation_max_observed_deg=emaxObs,
               rise_or_set=riseSet,
               periodogram_rh_m=px,
               periodogram_power=pz,
           )


   def build_rh_computer(config: RhStrategyConfig) -> RhComputer:
       """Factory — today always returns GnssreflRhComputer. Same seam as
       build_refraction_corrector (§5 step 5): callers depend on the
       RhComputer ABC, never the concrete class."""
       return GnssreflRhComputer(config)
   ```

5. **Refraction correction — call gnssrefl directly, do not reimplement.**
   Atmospheric bending shifts RH by cm-to-dm, elevation- and
   season-dependent; not optional for an RH *product*. **Superseded design
   decision (2026-09-16, see RATIONALE.md §17):** earlier drafts of this
   step planned a from-scratch reimplementation of Landskron & Böhm (2018)
   to avoid touching gnssrefl's GPLv3 `refraction.py`. That plan is
   withdrawn. gnssrefl is the community-established baseline and its
   refraction logic must not be re-derived or subtly changed by an
   independent reimplementation — instead, `canvod-gnssgeodesy` takes
   gnssrefl as a runtime dependency (optional `gnssrefl` extra, see §2) and
   calls its actual `correct_elevations()`/`gpt2_1w()` functions unmodified.
   `canvod-gnssgeodesy`'s own code is a translation layer only, in a new
   `refraction.py` module: canvodpy-shaped inputs in, gnssrefl's
   `station_config` dict built and passed through, its output translated
   back out. No refraction geodesy is written in this package.

   This also resolves the TU Wien source-code license question from
   `RATIONALE.md` §15.3/§16 by making it moot: gnssrefl's `refraction.py`
   is itself a Python port of TU Wien's older GMF-generation code, done by
   gnssrefl's own authors under GPLv3 (its docstring says so directly —
   "written in python from original TU Vienna codes for GMF"). Calling
   gnssrefl's port means `canvod-gnssgeodesy` never touches TU Wien's `.f90`/
   `.m` files at all; the only license boundary that matters here is
   gnssrefl's own GPLv3, which is a solved, standard copyleft grant (unlike
   TU Wien's bare, ungranted copyright). Practical consequence, verified
   by reading `refraction.py` in full: gnssrefl's own refraction model is
   *not* real-time/NWM-driven VMF3 at all — it's a one-time-downloaded
   static 1°×1° grid (`gpt_1wA.pickle`, an older GPT2w-generation model)
   evaluated with a built-in annual+semiannual harmonic for "time variation."
   There is no live TU Wien network dependency, no CC BY 4.0 grid-download
   step, and none of the forecast/password-tier concerns raised earlier
   apply to v1 at all.

   **Kwarg-based config, not gnssrefl's numbered `refr_model` (1-6).**
   gnssrefl's own CLI already lets users type `NITE`/`MPF` as strings for
   models 5/6 but not names for 1-4 (`gnssrefl/gnssir_input.py:546-566`);
   `RefractionStrategyConfig` (§11) extends that same idea uniformly across
   all four methods it implements, via a `RefractionMethod` enum
   (`bennett`/`ulich`/`nite`/`mpf`) crossed with a `time_varying: bool`
   flag, validated against the exact 6 combinations gnssrefl actually
   supports (NITE/MPF are always time-varying in gnssrefl; requesting
   `time_varying=False` for either raises, rather than being silently
   coerced).

   `canvod/gnssgeodesy/refraction.py`:

   ```python
   from abc import ABC, abstractmethod
   from dataclasses import dataclass
   from datetime import date

   import numpy as np
   import numpy.typing as npt

   from canvod.gnssgeodesy.config import RefractionStrategyConfig


   @dataclass(frozen=True)
   class RefractionResult:
       """Runtime return value, not a config — deliberately a plain
       dataclass, not pydantic, for the same reason `exclude_days` is kept
       out of `NmriStrategyConfig` (§11): numpy arrays don't belong in a
       YAML-round-trippable model."""

       corrected_elevation_deg: npt.NDArray[np.floating]
       valid_mask: npt.NDArray[np.bool_]


   class RefractionCorrector(ABC):
       """Extension point. v1 ships exactly one implementation, backed
       directly by gnssrefl's own refraction.py. A later,
       literature-motivated alternative (e.g. a live/periodically-refreshed
       VMF3-operational-grid corrector instead of gnssrefl's static-grid-
       plus-harmonic model — see RATIONALE.md §15.3) plugs in here as a
       second subclass, with zero changes to call sites. This is exactly
       the kind of "other community-established method" slot the §15
       literature review was for (per the user's framing: that review's
       job was to identify what to design an extension point around, not
       to justify avoiding gnssrefl's code)."""

       def __init__(self, config: RefractionStrategyConfig) -> None:
           self._config = config

       @abstractmethod
       def correct(
           self,
           elevation_deg: npt.NDArray[np.floating],
           *,
           epoch: date,
           station_id: str,
           station_lat_deg: float,
           station_lon_deg: float,
           station_height_m: float,
       ) -> RefractionResult: ...


   class GnssreflRefractionCorrector(RefractionCorrector):
       """v1's only implementation. A thin translation layer: builds the
       `station_config` dict gnssrefl.refraction.correct_elevations()
       expects, calls it unmodified, wraps its `(corrected_ele, valid_mask)`
       tuple back into RefractionResult. No gnssrefl logic is reimplemented,
       altered, or ported — this class contains zero geodesy, only
       translation."""

       def correct(
           self,
           elevation_deg: npt.NDArray[np.floating],
           *,
           epoch: date,
           station_id: str,
           station_lat_deg: float,
           station_lon_deg: float,
           station_height_m: float,
       ) -> RefractionResult:
           # optional dep (`gnssrefl` extra, see §2) — imported lazily so the
           # rest of canvod-gnssgeodesy works with the extra uninstalled
           from gnssrefl.refraction import correct_elevations

           station_config = {
               "station": station_id,
               "lat": station_lat_deg,
               "lon": station_lon_deg,
               "ht": station_height_m,
               "refraction": self._config.enabled,
               "refr_model": self._config.to_gnssrefl_model_id(),
               "apriori_rh": self._config.apriori_rh_m,
           }
           corrected, valid_mask = correct_elevations(
               elevation_deg,
               station_config,
               epoch.year,
               epoch.timetuple().tm_yday,
               verbose=False,
           )
           return RefractionResult(corrected_elevation_deg=corrected, valid_mask=valid_mask)


   def build_refraction_corrector(config: RefractionStrategyConfig) -> RefractionCorrector:
       """Factory — today always returns GnssreflRefractionCorrector. This is
       the seam a future dynamic-source corrector registers into; callers
       only ever depend on the RefractionCorrector ABC, never the concrete
       class."""
       return GnssreflRefractionCorrector(config)
   ```

   **RH/LSP re-scoping is now done (2026-09-16); MP1/NMRI (§6) is
   confirmed *not* eligible for the same treatment, not just unaudited.**
   Checked `gnssrefl/computemp1mp2.py` looking for the same kind of clean,
   in-memory core function `strip_compute()`/`correct_elevations()` turned
   out to be: there isn't one. gnssrefl's own MP1 computation is not
   Python at all — `computemp1mp2.py` shells out to the `teqc` binary
   (`subprocess.call([teqc, '-nav', navfile, '+qc', rinexfile])`) and
   parses its text log output, gated throughout on `os.environ['REFL_CODE']`
   /`os.environ['ORBITS']`. There is no gnssrefl logic to wrap for MP1/NMRI
   — the actual computation lives inside a deprecated, legacy-only external
   binary this plan already ruled out depending on (§8). §6 therefore
   correctly remains an independent reimplementation from the published
   literature (Larson & Small 2014; Small, Larson & Smith 2014, §15.1) —
   this was already how §6/§8 were written, and that framing is now
   *confirmed* correct rather than merely unrevisited. The asymmetry is the
   finding: RH and refraction wrap gnssrefl directly; MP1/NMRI cannot, and
   must stay a from-scratch, literature-sourced implementation.
6. **Nyquist / maximum-resolvable-RH guard.** At a given sampling interval
   there's a hard ceiling on unambiguous RH. `max_height_m` must be checked
   against the station's actual sampling interval at run time — this is a
   canvod-native sanity check on the *config values* handed to
   `GnssreflRhComputer` (step 3), not a call-through to anything gnssrefl
   computes itself; `strip_compute()` will happily return an aliased peak
   if handed a `max_height_m` inconsistent with the arc's sampling rate,
   the same way it would for gnssrefl's own CLI.

QC (`qc.py`): elevation-range compliance, arc duration bounds, amplitude
threshold, peak-to-noise ratio, reject-if-too-close-to-search-bounds — pinned
to the amplitude/noise conventions above. **Do not port gnssrefl's ad hoc
peak/noise-region thresholds** — implement Lomb-Scargle False Alarm
Probability (FAP) theory instead (Scargle 1982; VanderPlas 2018; Baluev
2008 — see `RATIONALE.md` §15.2). **Resolved (2026-09-16, see RATIONALE.md
§18): the closed-form Baluev formula is the only FAP path — astropy's
built-in method is not usable here and is not needed as a dependency.**
Read astropy's actual `LombScargle.false_alarm_probability()` source
(`astropy/timeseries/periodograms/lombscargle/core.py:594-678`) directly:
it is an *instance* method requiring `self._trel`/`self.y`/`self.dy`/
`self.normalization` — i.e. a fully-constructed `LombScargle(x, y)` object
holding the exact internal state `strip_compute()` used, not a function of
the `power` array alone. Since canvod-gnssgeodesy never constructs that
object (step 3 only ever sees `strip_compute()`'s returned `(px, pz)`
arrays), reconstructing one solely to call this method would mean
re-deriving gnssrefl's internal transform (`x = sin(ele)/cf`) ourselves —
exactly the kind of silent-divergence risk this whole pivot exists to
avoid — for a dependency (astropy, direct) this package doesn't otherwise
need. The closed-form Baluev/Scargle formula sidesteps this entirely: it's
computable from data canvod-gnssgeodesy already owns outright (its own
input arc's `N` points, plus `strip_compute()`'s own `(px, pz)` for the
peak height and frequency-grid span) with no astropy object and no
gnssrefl-internal-state reconstruction. It is therefore the **sole** FAP
path, not a fallback for a "base" method that no longer exists now that
LSP itself is wrapped — `RhStrategyConfig` carries no astropy-vs-closed-form
choice, there is only one implementation. A `peak2noise`-style threshold may still be
exposed as a cheap pre-filter (gnssrefl default: `2.8`), but arc acceptance
in the *improved* opt-in strategy should be driven by FAP, not by it alone.
The *default* (gnssrefl-compatible) strategy keeps `peak2noise_min = 2.8`,
`req_amp_min = 5.0`, `delT_max_min = 75.0` min, `ediff_deg = 2.0` — all
sourced from `gnssrefl/gnssir_input.py`'s own defaults, see §11.

Daily aggregation: **per-satellite (per-`sid`), not pooled across
satellites — see RATIONALE.md §23.** Within each satellite's own arcs for
the day, reject arcs whose RH deviates from that satellite's day-median RH
by more than a configurable metres threshold, then report the **mean** (not
median) of survivors for that `sid`, plus a minimum-accepted-track count. A
deliberate, simple design choice — not a MAD filter, and not a
reimplementation of any specific reference tool's exact algorithm. A
same-satellite, multiple-arc-per-day case (different azimuth sectors) is
expected and pools correctly under this scheme; different satellites are
never pooled together at this stage.

Output: `xr.Dataset`, dims `(epoch, sid)` where `epoch` holds one timestamp
per day (see §10 — the store write path hard-requires this dim name) and
`sid` follows canvodpy's own `f"{sv}|{band}|{code}"` convention (§17) — RH
is derived from SNR phase, so `band`/`code` here identify which signal the
arc's LSP was run on, genuinely per-`sid` (not just per-satellite, see
RATIONALE.md §23). **No `station` dim** — `station` is never a real Dataset
dimension in canvodpy (confirmed: zero matches for `"station"` as a dim
anywhere in `canvod-store/manager.py`), it's the group-path argument
`write_multipath_group()` already takes (§10); one station = one group,
same as `gnss_store`/`vod_store`. Vars `RH`, `amplitude`, `peak2noise`,
`n_arcs_used`, all per-`sid`-per-day. A separate, explicitly-derived
per-day rollup (sample-count-weighted mean of `RH` across available `sid`s
that day, dims `(epoch,)`) is produced for the GNSS-VOD-feeding use case —
see §10 — documented as a rollup, not the primary product.

Performance: the LSP step is inherently per-arc (astropy/scipy don't batch
irregular per-arc frequency grids in one call). The real performance lever
versus a reference tool is not "vectorize the LSP math" but "run thousands
of independent per-arc LSPs in parallel" — arcs across stations/days/
satellites are embarrassingly parallel. **`joblib` fan-out at the arc
level is the throughput strategy** (see `parallel` extra in §2), not a
numerical rewrite of Lomb-Scargle itself. **Not `dask.delayed`** — this
project's convention (user correction, 2026-09-18) is `joblib` for
parallel *compute*; `dask` is used only for lazy-array *storage*
(Icechunk/zarr-backed lazy loading via `canvod-store`, §10), never as a
task-scheduling/parallelization mechanism. Don't reach for
`dask.delayed`/`dask.bag` anywhere in this package even where it would be
a natural fit — that's a house convention, not a per-module judgment call.

## 6. `code_multipath.py` — MP1 / NMRI

**Superseded design decision (2026-09-18, see RATIONALE.md §18/§21):**
steps 2-4 below originally planned a from-scratch MP1 formula and
independent cycle-slip detection. That plan is withdrawn for the same
reason as RH/refraction: `gnssmultipath` (MIT, `.dev_deps/
GNSS_Multipath_Analysis_Software`) already has a real, community-used
Python implementation of both — `estimateSignalDelays()` (the MP1/
ionospheric-delay linear combination and its own ambiguity-slip
correction) and `detectCycleSlips()`/`getLLISlipPeriods()` (the two slip
detectors it uses internally). canvod-gnssgeodesy wraps these directly
instead of re-deriving the formula and the slip logic by hand. Unlike
gnssrefl, no packaging/license-boundary decision is needed here (MIT).

1. Align raw `L1`/`L2` phase for the same satellite/epoch (reindex on
   `(epoch, satellite)`), using the tracking codes selected per §4's
   policy — unchanged, this is canvodpy-side data shaping, not gnssrefl/
   gnssmultipath logic.
   **Validate code availability before calling gnssmultipath, loud not
   silent (decided 2026-09-18, RATIONALE.md §27).** `DEFAULT_TRACKING_CODES`
   (§4) is a fixed, literature-sourced default, not auto-discovered — so
   a station whose receiver doesn't emit the configured L2 code (e.g. an
   L2C-only receiver with no legacy `W`-attribute observables at all)
   will have neither `range2_Code` nor, critically, `phase2_Code`
   resolvable at all: canvod-readers' `sid = f"{sv}|{band}|{code}"`
   shares one `code` character across Pseudorange/Phase/Doppler/SNR
   (`v3_04.py:1512`), so a missing `W` isn't a partial degradation, it's
   a missing `sid` entirely, for phase *and* range alike — the phase is
   what actually feeds the live MP1 formula (see step 2 below). Check
   whether `f"{sv}|{band}|{code}"` exists in the input Dataset's `sid`
   coordinate for the constellation's configured `tracking_codes`
   *before* calling `estimateSignalDelays()`, not after via
   gnssmultipath's own internal missing-observation gate (that gate
   still applies per-satellite for genuine per-day data gaps — this
   check is a separate, earlier, per-file/per-system gate for "is the
   configured code even offered by this receiver at all"). If absent for
   every satellite of that constellation in that file (the expected
   shape — RINEX 3 headers declare one obs-code list per system, shared
   across all its satellites, not per-satellite), emit `MP1rms`/`NMRI`/
   etc. as NaN for that whole (station, day) and set the day-level
   `tracking_codes_resolved=False` output flag (see Output below) —
   don't raise and halt a batch run, don't silently proceed with
   gnssmultipath's internal gate dropping satellites one at a time with
   no visible explanation of why.
2. **Call `gnssmultipath.estimateSignalDelays()` once per (station, day)
   across all satellites — not per arc.** Building the `GNSS_obs`/
   `GNSS_SVs` arrays this call needs from canvodpy's `(epoch, sid)` shape
   is the §17 adapter's job, not inlined here. Traced through `SignalAnalyzer.
   run()` and `estimateSignalDelays.py` directly: the MP1/ionospheric-delay
   linear combination, its own ambiguity-period detection (via
   `detectCycleSlips()`, called twice internally — once on the
   ionospheric-delay residual, once on the code-phase pseudo-ambiguity
   residual — and unioned), and the per-segment mean removal all happen
   inside this one call. **Must be called on a continuous, evenly-sampled
   full-day epoch grid, not fragmented per arc**: `detectCycleSlips()`
   computes `np.diff(estimates, axis=0) / tInterval` internally — running
   it on disjoint per-arc epoch ranges would corrupt the rate-of-change
   at every arc boundary. Arc segmentation (step 3) slices/clips this
   day-level output per arc *afterward*, it doesn't drive the call.
   Carrier frequencies are still supplied by *us*, not derived internally
   by gnssmultipath — **the float64-precision concern from earlier drafts
   of this step is retargeted, not eliminated**: `carrier_freq1`/
   `carrier_freq2` passed into `estimateSignalDelays()` come from the
   registered `AlphaCalibration` for the active constellation (below), not
   a bare inline constant — for GPS this resolves to the same exact
   1575.42 MHz / 1227.60 MHz values as before (matching canvodpy's own
   `validation_constants.py`/`constellations.py`), never derived from
   `freq_center` (canvodpy's actual sid-coord: float32, MHz). Same unit
   test requirement as before: assert float64, exact to 1e-15 relative
   tolerance — the risk moved from "our formula" to "our inputs to
   gnssmultipath's formula," it didn't go away.

   **`AlphaCalibration` — the extension point, and not `RhComputer`/
   `RefractionCorrector`'s ABC-with-`compute()` shape.** There is no
   algorithmic variation to dispatch on here: read directly,
   `estimateSignalDelays()`'s MP1 formula depends on exactly one physical
   quantity, `alpha = carrier_freq1**2/carrier_freq2**2`
   (`estimateSignalDelays.py:143` — its own comment calls this the
   "amplfication factor"), which then sets the ionospheric-delay and
   multipath coefficients directly: `ion_delay_phase1 = 1/(alpha-1)*
   (phase1-phase2)` and `multipath_range1 = range1 - (1 + 2/(alpha-1))*
   phase1 + (2/(alpha-1))*phase2` (`estimateSignalDelays.py:195,197`). No
   GPS-specific constant appears anywhere in the function — see
   RATIONALE.md §23 update. What varies per constellation/band-pair is
   only the *literature-sourced numbers* derived for a given `alpha`
   (elevation mask, baseline fraction), not the code path, so this is a
   plain registered `frozen` dataclass, not an ABC:

   ```python
   from dataclasses import dataclass


   @dataclass(frozen=True)
   class AlphaCalibration:
       """One literature-validated (constellation, band-pair) combination
       for code_multipath. Named after alpha = carrier_freq1**2/
       carrier_freq2**2 — the one physical quantity estimateSignalDelays()
       actually depends on (estimateSignalDelays.py:143,195,197) — because
       everything else here (elevation_mask_deg, baseline_top_fraction) is
       a number the literature derived *for that specific alpha*, not a
       constellation-level constant. A closely-spaced pair (e.g. Galileo
       E5a/E5b) has a small (f1-f2) and therefore amplifies phase noise via
       the 2/(alpha-1) coefficient far more than a widely-spaced pair (GPS
       L1/L2, Galileo E1/E5a) — so calibration is keyed per band-pair, not
       merely per constellation."""

       constellation: str            # sv's leading letter, e.g. "G", "E", "C", "R"
       band_pair: tuple[str, str]    # e.g. ("L1", "L2"), ("E1", "E5a")
       carrier_freq1_hz: float       # float64, exact — see the precision note above
       carrier_freq2_hz: float
       range_codes: tuple[str, str]  # (range1_Code, range2_Code) passed to
                                       # estimateSignalDelays(). NOT symmetric
                                       # in what they feed the MP1 *formula*:
                                       # range_codes[0]'s value is read by the
                                       # live math; range_codes[1]'s value
                                       # isn't. But both share their attribute
                                       # character with the corresponding
                                       # phase code via canvod-readers' sid
                                       # scheme (RATIONALE.md §26/§27) — a
                                       # receiver with no "W"-attribute L2
                                       # observables at all is missing
                                       # phase2_Code too, which DOES feed the
                                       # formula. Not silently degraded:
                                       # validated up front, see §6 step 1.
       elevation_mask_deg: tuple[float, float]
       baseline_top_fraction: float
       citation: str                  # literature source for elevation_mask_deg/baseline_top_fraction specifically

       @property
       def alpha(self) -> float:
           return (self.carrier_freq1_hz / self.carrier_freq2_hz) ** 2


   _ALPHA_CALIBRATION_REGISTRY: dict[str, AlphaCalibration] = {
       "G": AlphaCalibration(
           constellation="G",
           band_pair=("L1", "L2"),
           carrier_freq1_hz=1575.42e6,
           carrier_freq2_hz=1227.60e6,
           range_codes=("C1C", "C2W"),  # verified against Larson & Small 2014 / Small Larson & Smith 2014 / Small Larson & Braun 2010 full text (RATIONALE.md §26): PBO's Trimble NetRS receivers have no P-code access, so "P1" in the classic MP1 formula is populated by C/A-code C1 in practice; "C2W" is required by estimateSignalDelays()'s signature but only gates missing-obs completeness, see range_codes' field comment above
           elevation_mask_deg=(10.0, 15.0),  # citation list above names the convention (classic teqc MP1
                                              # mask / Larson & Small 2014-family literature), not one traced
                                              # page/equation the way range_codes was; consumed via
                                              # NmriStrategyConfig.min_elev_deg/max_elev_deg's None-fallback,
                                              # same pattern as baseline_top_fraction below (§6 step 3/§11)
           baseline_top_fraction=0.05,
           citation="Larson & Small 2014 (IEEE JSTARS); Small, Larson & Smith 2014; Small, Larson & Braun 2010 (GRL); classic teqc MP1 convention (Estey & Meertens 1999)",
       ),
       # Architecturally pluggable, not registered in v1 (see step 6):
       # Galileo E1/E5a and BeiDou B1I/B3I are the most plausible next
       # entries (both widely-spaced pairs); GLONASS is additionally
       # blocked independent of calibration by aggregate_glonass_fdma
       # (step 6).
   }


   def get_alpha_calibration(constellation: str) -> AlphaCalibration:
       """Raises, does not silently fall back to GPS — the single
       enforcement point step 6's GPS-only-in-v1 rule now goes through."""
       try:
           return _ALPHA_CALIBRATION_REGISTRY[constellation]
       except KeyError:
           raise NotImplementedError(
               f"No AlphaCalibration registered for constellation {constellation!r}. "
               "estimateSignalDelays()'s formula itself is constellation-generic "
               "(alpha-only dependency, see AlphaCalibration's docstring) — what's "
               "missing is a literature-sourced (or internally noise-floor-"
               "characterized) elevation_mask_deg/baseline_top_fraction for this "
               "constellation/band-pair, not a code change."
           ) from None
   ```

   The input must be `Pseudorange_raw`/`Phase_raw` on SBF-sourced data —
   see §3. `code_multipath.py` takes an explicit
   `observable_source: Literal["rinex", "sbf_raw"]` argument (or infers it
   from `ds.attrs["source_format"]`) and **raises** if SBF-sourced data
   lacks the `_raw` variables, rather than silently falling back to the
   corrected ones.
3. **Arc segmentation, slip diagnostics, and a real design fork — resolved
   here, not left implicit.** Before calling `detect_arcs` (§4): resolve
   `NmriStrategyConfig.min_elev_deg`/`max_elev_deg` if either is `None` —
   fall back to the active constellation's `AlphaCalibration.
   elevation_mask_deg[0]`/`[1]` (step 2; `(10.0, 15.0)` for GPS), same
   resolution point and rule as `baseline_top_fraction` (step 8) — then
   re-check `min_elev_deg < max_elev_deg` on the resolved, non-Optional
   pair (§11's `NmriStrategyConfig._check_elev_order` only checks this
   when the caller supplied both explicitly; a mixed None/explicit pair
   still needs this check after resolution). `estimateSignalDelays()`'s own
   ambiguity
   correction is driven *only* by its two internal `detectCycleSlips()`
   calls (ionospheric-delay rate + code-phase rate) — checked
   `SignalAnalyzer.run()` directly: LLI-based detection
   (`getLLISlipPeriods()`) is called *separately*, stored in
   `SlipPeriods.lli`, and never folded back into the correction.
   `estimateSignalDelays()`'s signature has no slot for externally-supplied
   slip evidence either. **Decision: accept gnssmultipath's own correction
   exactly as computed (ionospheric/code-phase-rate only) — do not attempt
   to fold LLI or SBF's `cum_loss_cont` into it.** Report both as
   *separate, additional diagnostic* slip counts instead (this package's
   own `getLLISlipPeriods()` call for RINEX; a small canvod-native
   `cum_loss_cont`-change detector for SBF, same shape as originally
   planned) — evidence a downstream user can look at without it silently
   changing what `MP1rms` means. **Store these explicitly, don't discard
   them after use** (see Output below) — a day with high `MP1rms` from
   real vegetation-driven multipath is indistinguishable from a day with
   high `MP1rms` from a flaky receiver dropping lock constantly unless
   slip counts are exposed.
   **Indexing gotcha, source-verified:** `detectCycleSlips()`'s returned
   dict uses 1-based string keys (`"1"`..`"nPRN"`); `getLLISlipPeriods()`
   uses 0-based int keys (`0`..`n_sat-1`). `computeDelayStats.py` reconciles
   this internally with a `+1` offset (`computeDelayStats.py:270,302`) —
   anything in this module that cross-references both dicts must replicate
   that offset explicitly, it is not implicit or automatic.
   **Minimum segment length — still a real bias, now a post-filter on
   gnssmultipath's output rather than our own segmentation.**
   `estimateSignalDelays()` mean-removes every ambiguity segment it finds
   regardless of length; it does not discard short ones. Short segments
   (from frequent slips) get artificially suppressed RMS — which biases
   `MP1rms` low, which biases NMRI *up* — and slip-rich periods are
   exactly the high-multipath, vegetated periods. **This bias is
   correlated with the thing being measured.** Use the returned
   `ambiguity_slip_periods` to identify segment boundaries/lengths, and
   set epochs in segments shorter than `min_segment_epochs` to NaN before
   computing `MP1rms` — discard, don't merge.
   Elevation mask for arc boundaries stays canvod-native, ~10-15° per the
   code/pseudorange-multipath literature convention — **not yet traced to
   a specific sourced default the way RH's numbers in §11 are; still an
   open item, see §11's `NmriStrategyConfig` comment**.
4. (Folded into step 2 — gnssmultipath's own per-segment mean removal
   replaces what was previously a separate step here.)
5. Daily aggregation: per-satellite RMS → **stop here, do not collapse
   across satellites.** `MP1rms` is emitted per `sv` (satellite — **not**
   `sid`: `estimateSignalDelays()` takes a fixed range/phase code set
   (`range1_Code`/`range2_Code`/`phase1_Code`/`phase2_Code`, e.g.
   `"C1C"`/`"C2W"`/`"L1C"`/`"L2W"`, RATIONALE.md §26) and produces
   `multipath_range1[epoch, PRN]` — **asymmetrically**: only `range1`
   (+ both phases) feeds the actual MP1 combination
   (`estimateSignalDelays.py:197`); `range2` is read but its own
   multipath computation is dead code (`:161,198`, commented out
   upstream) — `range2` is still a required argument because it feeds a
   *missing-observation completeness gate* (`:202`,
   `find_missing_observation(range1, range2, phase1, phase2)`), not
   because MP1 is symmetric in the two ranges. One per-satellite value
   either way, so there is no natural per-band/per-code MP1 value
   to key a `sid` dim on — see RATIONALE.md §23 correction) per day. The
   previous design's "sample-count-weighted mean across satellites" step is
   now the separate, explicitly-derived per-day rollup described in §10,
   not part of computing `MP1rms` itself.
6. **`code_multipath` is GPS-only in v1 by calibration, not by formula —
   enforced via the `AlphaCalibration` registry (step 2), not a bare
   `constellation != "G"` check.** `estimateSignalDelays()`'s MP1 formula
   depends on exactly one physical quantity (`alpha`, step 2) and takes
   its two frequencies/codes as plain parameters — confirmed by direct
   read, nothing GPS-specific is hardcoded inside gnssmultipath itself
   (α-generic formula; GPS L1/L2 is the only *calibrated* pair). The
   restriction is that NMRI's empirical calibration (elevation mask,
   `baseline_top_fraction`, expected dynamic range) is sourced from
   Larson & Small 2014, GPS-L1/L2-specific literature — using it on
   another band-pair without re-deriving those numbers would silently
   produce values of unknown validity, and a closely-spaced pair (e.g.
   Galileo E5a/E5b) additionally has a different noise-amplification
   scale via `alpha` itself (step 2's `AlphaCalibration` docstring), so
   calibration doesn't transfer even across two band-pairs on the *same*
   constellation. `get_alpha_calibration()` raising `NotImplementedError`
   for anything not registered *is* the GPS-only enforcement — extending
   to Galileo E1/E5a or BeiDou B1I/B3I later (both widely-spaced pairs,
   the closest analogues to L1/L2) is a plausible later-phase extension:
   registering one more `AlphaCalibration` instance with literature-sourced
   (or internally noise-floor-validated) numbers, not an algorithm change.
   GLONASS specifically has a second, independent blocker regardless of
   calibration status: `aggregate_glonass_fdma` defaults **True** in
   canvodpy core (`canvod-config/src/canvod/config/models/processing_params.py:49`,
   `canvod-readers/src/canvod/readers/gnss_specs/bands.py:55`), which
   collapses GLONASS FDMA sub-band frequencies to a channel-plan midpoint
   rather than each satellite's actual frequency — a ~0.25% frequency
   error, an order of magnitude worse than the `freq_center` float32 issue
   above, and canvodpy cannot currently resolve true per-satellite GLONASS
   frequency without flipping a store-breaking config flag. Registering a
   GLONASS `AlphaCalibration` would not be sufficient on its own.
7. QC:
   - Snow/rain masking stays out-of-package for v1 as a caller-supplied
     `exclude_days: xr.DataArray[bool] | None` — a **required runtime
     argument**, not a config field with a silent default (config models
     should stay serializable; a caller-supplied mask is data, not config —
     see §11). When `None`, stamp `attrs["nmri_masking"] = "none"` and emit
     a `UserWarning` naming snow and heavy rain as unmasked confounders, so
     the omission is loud, not silent. (Later phase, not v1: this package's
     own RH output is a plausible in-house snow proxy — a sustained RH drop
     is snow accumulation — worth revisiting once both modules exist.)
   - Outlier rejection: MAD-based filter, not a plain 3σ filter — multipath
     residuals are right-skewed, and a symmetric 3σ cutoff systematically
     over-rejects the high tail, which is exactly the vegetation signal.
     Applies to per-day `MP1rms` (specified explicitly, not left ambiguous
     across per-epoch/per-arc/per-day levels).
8. Normalization: **per-`sv` (satellite), not pooled across satellites —
   a real methodological fork, not just a shape change, see RATIONALE.md
   §23.** `MP1max` = mean of the top `baseline_top_fraction` (config field
   default `None` → falls back to the active constellation's
   `AlphaCalibration.baseline_top_fraction`, 0.05 for GPS — see step 2/§11;
   an explicit config value always overrides it) of *that satellite's own*
   daily `MP1rms` history at that station. `NMRI = (MP1max − MP1rms) / MP1max`, computed per `sv` per day.
   Pooling all satellites into one shared baseline (the original design)
   would have mixed different elevation/geometry multipath regimes into a
   single threshold; a per-satellite baseline is more physically correct,
   not merely finer-grained.
   Explicit range/sign guard needed: by this definition, `NMRI` goes
   negative on the very days that define that satellite's own `MP1max` (the
   top-5% days themselves have `MP1rms` values at or above `MP1max` in
   general). Add a test that characterizes this as an expected property of
   the normalization, documented, not discovered by a confused downstream
   user.
   Minimum record length — see resolved question 3 in §13; now evaluated
   per `sv` (a satellite that's only intermittently tracked has its own,
   possibly thinner, baseline history than the station's other satellites).
   Station-metadata discontinuities: antenna, radome, or receiver/firmware
   changes step `MP1rms` discontinuously and corrupt a multi-year baseline
   silently. At minimum, expose station-metadata-change dates (if available
   from `canvod-store-metadata`) as an optional input that marks
   baseline-eligible date ranges; full handling deferred, but the absence
   must be documented as a known limitation, not silently ignored.

Output: `xr.Dataset`, dims `(epoch, sv)` (epoch = one daily timestamp, see
§10; `sv` — **not** `sid`, see step 5 — GPS-only in v1 so always a `G`
prefix per step 6). **No `station` dim** — station is never a real Dataset
dimension in canvodpy (confirmed: zero matches for `"station"` as a dim
anywhere in `canvod-store/manager.py`, same finding as §5's Output). Vars
`MP1rms`, `NMRI`, `MP1max` (the normalizer itself must be an output
variable — a user needs to see what produced their index),
`nmri_baseline_n_days`, `nmri_baseline_confidence` (both per-`sv`, see step
8), QC flags, plus the slip diagnostics from step 3 —
`n_slips_threshold` (gnssmultipath's own ionospheric/code-phase-rate
detector, the one that actually drove the correction),
`n_slips_lli`/`n_slips_cum_loss_cont` (format-appropriate, reported
alongside but not folded into the correction, per step 3's resolved
design fork) — per `sv` per day, same treatment RH gives
`amplitude`/`peak2noise`/`n_arcs_used`, not discarded after use.
`n_satellites_used` is dropped here (redundant with the `sv` dim itself —
count non-NaN entries along `sv` if needed) and reappears only in the
per-day rollup (§10) where it's actually informative.
`tracking_codes_resolved` — new, dims `(epoch,)` (day-level, not per-`sv`:
whether the configured `tracking_codes` were offered by the RINEX file at
all is a per-file/per-system property, not a per-satellite one, see step
1's validation) — `bool`, `False` means the whole day is NaN across every
`sv` because the configured L1/L2 codes weren't present in that file, not
because of a genuine per-satellite data gap. Required precisely because
`tracking_codes` is a fixed, non-auto-detected default (§4) — a batch run
across many stations needs to distinguish "no vegetation signal today"
from "this station's receiver doesn't emit the configured tracking code"
without inspecting logs.

## 7. `receiver_multipath.py` (SBF-only, diagnostic)

Reads firmware `mp_correction_m`/`car_mp_corr_cycles` from the SBF reader's
**metadata** dataset (`metadata/sbf_obs`, not the main observation group —
different read path than the other modules). Both source variables are
dims `["epoch", "sid"]` at raw (per-observation-epoch) resolution —
confirmed directly (`sbf/reader.py:2012-2034` and, at the second call site
that emits the same fields, `:2799-2821` — identical dims both places).

Aggregates to a daily per-`sid` mean/std: `sid`, **not** `sv` — unlike
MP1/NMRI (§6), these are true per-observable firmware corrections (one
value per band/code, not a value that mixes two observation codes into a
single per-satellite number), so RH's per-`sid` resolution is the right
model here, not MP1's per-`sv` collapse (RATIONALE.md §23 point 1).
Output dims `(epoch, sid)` (epoch = one daily timestamp, see §10). **No
`station` dim** — station is never a real Dataset dimension in canvodpy
(confirmed: zero matches for `"station"` as a dim anywhere in
`canvod-store/manager.py`, same finding as §5/§6's Output, RATIONALE.md
§23 point 2). A station-level rollup, if ever wanted, is a downstream
consumer's job (across this module's per-file output), not something
`receiver_multipath.py` computes itself.

Documented explicitly as a diagnostic correlated-by-construction signal,
not an independent validation of `code_multipath`'s own MP1 estimate.

## 8. Validation strategy and the license boundary

- **Refraction and RH/LSP are contract tests, not oracle tests.** Since §5's
  2026-09-16 pivot, both `refraction.py` and the RH core (steps 1-4) call
  gnssrefl's own code directly (`correct_elevations()`, `strip_compute()`)
  rather than reimplementing it — there is no independent algorithm to
  check against an oracle for either. `test_refraction.py`/
  `test_snr_multipath.py`'s gnssrefl-facing tests verify the translation
  layer only: does `GnssreflRefractionCorrector`/`GnssreflRhComputer` build
  the arguments gnssrefl expects, call its function unmodified, and return
  what that call returned. This is narrower and cheaper than the
  oracle-comparison bullets below, and needs the `gnssrefl` extra installed
  to run at all (skip otherwise, same convention as `test_io.py`/`store`).
  The remaining canvod-native pieces of RH (detrend in step 2, noise/
  peak2noise in step 4) are still worth a synthetic-signal unit test, but
  not an oracle comparison — they're generic numpy/statistics, not
  gnssrefl-derived geodesy. **MP1/NMRI (§6) is the one family that still
  needs the oracle-comparison strategy below**, confirmed (not just
  assumed) in §5 step 5's closing note: gnssrefl's own MP1 has no Python
  implementation to wrap, only a `teqc` subprocess call, so an independent
  reimplementation is the only option there.
- **Unit tests**: synthetic inputs, known injected signals, no `.dev_deps`
  involved.
- **Oracle validation, RH only, against gnssrefl**: gnssrefl ships no
  precomputed reference *numbers* — its own regression tests generate
  "golden" output by re-running gnssrefl at a pinned commit at test time.
  Budget for actually running gnssrefl (env vars, orbit downloads) in Phase
  3, not just reading a fixtures directory.
- **Oracle validation, MP1 only, against gnssmultipath**: valid — it ships
  actual `TestData/` + `Results_example/`. **There is no NMRI oracle
  anywhere.** gnssrefl's own MP1 path shells out to a `teqc` binary, and
  never computes NMRI in code (confirmed: zero matches for "nmri" across
  every `.py` file in its source). `teqc` is itself deprecated outright —
  UNAVCO/EarthScope stopped developing it years ago, only legacy binaries
  exist — so a `teqc`-based oracle path is a dead end, not a
  platform-support workaround. The MP1rms → MP1max → NMRI normalization
  must be validated by construction (synthetic monotonicity/sign/range
  tests) and, ideally, by reproducing a published figure from Small et al.
  2014 at a station with available data — not by comparing against any
  existing package's output, because none computes it.
- **License boundary**: comparing our independently-computed *numbers*
  against gnssrefl's/gnssmultipath's own output is legally clean (output of
  a program is not a derivative work of the program). The separate,
  narrower question is **test-fixture files**. Resolution: **don't vendor
  gnssrefl's `test/data/` fixtures at all — regenerate them from the
  original public IGS/UNAVCO RINEX** (traceable, side-steps the question
  entirely). gnssmultipath's `TestData/` (MIT) can be vendored freely, with
  attribution. **If anything from a GPLv3 source is ever vendored despite
  this, `REUSE.toml`'s blanket `path = "**"` rule will mis-stamp it as
  Apache-2.0 — an explicit `[[annotations]]` override for that path is then
  mandatory, not optional.**
- **Wheel-exclusion is moot**: `uv_build` with `module-name = "canvod.gnssgeodesy"`
  only packages `src/`; `tests/` (including `tests/oracle/`) never enters
  the wheel regardless of markers.
- Markers: `slow`, `integration`, `oracle` (new), matching the existing
  `pytest.ini` convention (`-v --strict-markers --strict-config
  --showlocals`).

## 9. `provenance.py`

Follows the same idiom as `canvod-adapters/src/canvod/adapters/gnssvod/provenance.py`
(small pure function, dict of attrs, `_package_version` helper with
`try`/`except PackageNotFoundError: return "unknown"`, optional `timestamp`
override defaulting to `datetime.now(UTC)`) — not a copy of its specific
field names, which serve a different purpose (bidirectional format
conversion, not retrieval-algorithm attribution):

```python
def build_provenance_attrs(
    product: Literal["rh", "nmri", "receiver_multipath"],
    station: str,
    *,
    timestamp: datetime | None = None,
) -> dict[str, Any]:
    return {
        "retrieval_algorithm": {
            "rh": "lomb_scargle_snr_multipath",
            "nmri": "mp1_code_multipath_nmri",
            "receiver_multipath": "sbf_firmware_multipath",
        }[product],
        "retrieval_paper_reference": {
            "rh": "Larson et al., various — GNSS-IR reflector height",
            "nmri": "Larson & Small 2014 (IEEE JSTARS); Small, Larson & Smith 2014",
            "receiver_multipath": "n/a (receiver firmware estimate)",
        }[product],
        "canvod_multipath_version": _package_version("canvod-gnssgeodesy"),
        "retrieval_timestamp": (timestamp or datetime.now(UTC)).isoformat(),
        "station": station,
        "strategy_config_hash": ...,  # hash/serialization of the run's strategy config — algorithm+version alone isn't reproducible when every threshold is configurable
    }
```

## 10. `io.py`

Icechunk group naming: **no blanket family prefix** — a `gnssir/` prefix
over both families would mislabel the code-multipath side. Use the
module/algorithm name as the group family, exactly matching VOD's own
precedent (`{calculator_name}/{analysis_name}`, verified directly in
`canvod-store/src/canvod/store/manager.py:484,540,588` — e.g.
`"tau_omega_zeroth_order/canopy_01_vs_reference_01"`):

- `snr_multipath/rh/<strategy>`
- `code_multipath/nmri/<strategy>`
- `receiver_multipath/diagnostic/<strategy>`

Nested paths are supported throughout `MyIcechunkStore` (`group_exists`,
`read_group`, `write_or_append_group` all handle `/`-separated paths) — note
the store carries a documented historical bug where code that assumed flat
naming once silently destroyed prior writes, so this isn't a stylistic
choice, it's load-bearing. Caveat: `list_groups`-style top-level enumeration
won't surface nested groups — use tree/exists-style lookups instead, as the
store's own docstring warns for VOD. (Separately: `canvod-adapters`'
`io.py`/`CLAUDE.md` inherited the flat assumption and should get a bug
report — its reads are consequently against the wrong group shape.)

The store's write paths hard-require an `epoch` coordinate — both
`write_or_append_group` and the VOD-specific writer read `dataset.epoch`
directly, and the default chunk strategy keys off `"epoch"`. This is why
§5/§6/§7's output uses `(epoch, sid)` or `(epoch, sv)` rather than
`(day, station)` — the time dimension must be literally named `epoch` (one
timestamp per day) to go through either write path; `station` is never a
Dataset dim at all (confirmed: zero matches in `canvod-store/manager.py` —
see §5/§6 Output), it's purely an Icechunk group-path/routing parameter to
`write_multipath_group` below. `sid`/`sv`-dimensioned chunking is **not**
an open problem — `canvod-config`'s `ChunkStrategy`
(`canvod-config/src/canvod/config/models/compression.py:27-44`) already
has exactly two fields, `epoch` and `sid` (no `station` field exists at
all), and `gnss_store`/`vod_store` already default to
`ChunkStrategy(epoch=17280, sid=-1)` (`compression.py:87-94`) — a `sid`-
chunked dimension is existing, reusable precedent, not something this
package introduces. The one real touch point is registering a
`"multipath_store"`-style entry mirroring that same default in
`canvod-config`'s `chunk_strategies` dict (currently only
`gnss_store`/`vod_store` exist) — a small canvodpy-core touch point
(chunking config only, not the observable-parsing path, which stays
config-only per §3).

**Per-day rollup, a second, explicitly-derived product.** Since the
GNSS-VOD-feeding use case (this package's original motivating goal) wants
one scalar per station per day, not one per satellite, each of §5/§6/§7
also produces a rollup — sample-count-weighted mean across available
`sid`s/`sv`s that day, dims `(epoch,)` (no `station` dim — see above; a
`station` value is implicit in which group `write_multipath_group` wrote
to), carrying `n_satellites_used` (moved here from §6's per-`sv` output) —
written to a sibling group (`code_multipath/nmri/<strategy>/rollup`, same
pattern for the other two) rather than overwriting the per-`sid`/per-`sv`
product. This keeps the per-`sid`/per-`sv` data as the source of truth and
the rollup as a documented, reproducible derivation from it, not a second
independent computation. §5's rollup collapses `sid`→scalar (RH is
genuinely per-band); §6's collapses `sv`→scalar (MP1/NMRI is genuinely
per-satellite, see §6 step 5) — same rollup pattern, different source dim,
not a discrepancy.

Baseline-recomputation semantics: `MP1max` is a function of the *entire*
record, so appending one new day of data can silently change every
previously-emitted `NMRI` value if recomputed naively on every append. This
is incompatible with a pure append-only write mode. Two options, pick one
explicitly: (a) freeze the baseline window in the strategy config
(`baseline_from: [start_date, end_date]`, computed once, reused thereafter),
or (b) always recompute-and-overwrite (`mode="w"`) the whole `NMRI` series
on each run rather than appending, documenting that NMRI values are not
stable across reprocessing. Recommend (a) for scientific reproducibility.

```python
def write_multipath_group(store_or_site, station, family, strategy_name, ds, *, branch="main", commit_message=None): ...
def read_multipath_group(store_or_site, station, family, strategy_name, *, branch="main") -> xr.Dataset: ...
```

## 11. `config.py` — pydantic models

`_StrictModel` is a **private class defined in canvodpy-core**
(`canvod-config`), not something this package should import — that would add
a hard `canvod-*` runtime dependency this package otherwise doesn't need
(both `canvod-filemap` and `canvod-adapters` deliberately avoid this).
Define a local one-liner in `canvod/gnssgeodesy/config.py`:

```python
class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
```

Style matches `canvod-config`'s actual convention (every field carries
`Field(default, description=...)`; cross-field constraints go in
`@model_validator(mode="after")`, not per-field `@field_validator`):

```python
class ArcStrategyConfig(_StrictModel):
    min_elev_deg: float = Field(..., description="Minimum elevation angle, degrees")
    max_elev_deg: float = Field(..., description="Maximum elevation angle, degrees")
    azimuth_sectors: list[tuple[float, float]] | None = Field(
        None, description="Azimuth sectors to include, degrees; None = all"
    )
    max_gap_epochs: int = Field(..., description="Max epoch gap before an arc is split")
    tracking_codes: dict[str, str] = Field(
        default_factory=lambda: dict(DEFAULT_TRACKING_CODES),
        description="Per-band tracking code. Defaults to the literature-verified "
        "{'L1': 'C', 'L2': 'W'} (RATIONALE.md §26) — override explicitly per station "
        "if the receiver reports a different L2 code (e.g. {'L2': 'L'} for L2C-only "
        "receivers, common on current hardware, RATIONALE.md §27). Never "
        "auto-detected: an unmatched code fails loud via tracking_codes_resolved=False "
        "(§6 step 1/Output), not a silent per-file fallback."
    )
    constellations: list[str] = Field(
        ["G"], description="Constellations to include; v1 GPS-only for code_multipath — enforced by "
        "get_alpha_calibration() raising NotImplementedError for unregistered constellations (§6 step 2/6), "
        "not a hardcoded restriction on this field"
    )

    @model_validator(mode="after")
    def _check_elev_order(self) -> "ArcStrategyConfig":
        if self.min_elev_deg >= self.max_elev_deg:
            raise ValueError("min_elev_deg must be < max_elev_deg")
        return self

class RhStrategyConfig(ArcStrategyConfig):
    # Field defaults below are gnssrefl's own hardcoded values, read directly
    # from `gnssrefl/gnssir_input.py:78-80` (its `make_gnssir_input` function
    # signature) — this is what makes the "gnssrefl" named strategy (see
    # top of this file) an actual default rather than a principle. Still
    # overridable per-station via YAML exactly as gnssrefl itself allows
    # (these are its fallback constants, not station-specific truth).
    min_elev_deg: float = Field(5.0, description="Minimum elevation angle, degrees (gnssrefl e1 default)")
    max_elev_deg: float = Field(25.0, description="Maximum elevation angle, degrees (gnssrefl e2 default)")
    min_height_m: float = Field(0.5, description="RH search lower bound, metres (gnssrefl h1 default)")
    max_height_m: float = Field(8.0, description="RH search upper bound, metres (gnssrefl h2 default)")
    desired_precision_m: float = Field(0.005, description="Target RH precision, metres (gnssrefl desiredP default)")
    noise_region_m: tuple[float, float] = Field(
        ..., description="RH range used to estimate periodogram noise floor — gnssrefl's nr1/nr2 have NO default "
        "(None unless station-supplied); do not invent one, require it explicitly"
    )
    peak2noise_min: float = Field(2.8, description="Minimum peak-to-noise ratio to accept an arc (gnssrefl peak2noise default)")
    req_amp_min: float = Field(5.0, description="Minimum periodogram amplitude to accept an arc (gnssrefl ampl/reqAmp default)")
    delT_max_min: float = Field(75.0, description="Maximum arc duration, minutes (gnssrefl delTmax default)")
    ediff_deg: float = Field(2.0, description="Elevation-range compliance tolerance, degrees (gnssrefl ediff default)")
    detrend_window_deg: tuple[float, float] = Field(
        (5.0, 30.0), description="DC-removal/detrend elevation window, degrees (gnssrefl pele default [5,30] — "
        "see §5 step 2; NOT the same range as min_elev_deg/max_elev_deg, gnssrefl keeps these two windows distinct)"
    )
    detrend_poly_order: int = Field(4, description="Detrend polynomial order (gnssrefl polyV default)")
    lsp_backend: Literal["astropy", "scipy"] = Field(
        "astropy", description="Named after the actual library, not gnssrefl's internal 'fast'/'scipy' "
        "shorthand for the same choice. Translated to gnssrefl's own lsp_method='fast'/'scipy' argument "
        "at the GnssreflRhComputer call site (§5 step 3) — canvod-gnssgeodesy never calls astropy or scipy "
        "directly itself, this only selects which one gnssrefl uses internally. 'astropy' matches "
        "gnssrefl's own default ('fast')."
    )

    @model_validator(mode="after")
    def _check_height_order(self) -> "RhStrategyConfig":
        if self.min_height_m >= self.max_height_m:
            raise ValueError("min_height_m must be < max_height_m")
        return self

class RefractionMethod(str, Enum):
    """Named replacement for gnssrefl's numeric refr_model (1-6, see
    gnssrefl/gnssir_input.py:546-566). gnssrefl itself already accepts the
    strings "NITE"/"MPF" for models 5/6 but not names for models 1-4 — this
    extends that same idea uniformly across all four methods it implements.
    See §5 step 5 for the ABC that consumes this."""

    BENNETT = "bennett"   # gnssrefl models 1 (static) / 2 (time-varying)
    ULICH = "ulich"        # gnssrefl models 3 (static) / 4 (time-varying)
    NITE = "nite"          # gnssrefl model 5 (Peng 2023) — always time-varying
    MPF = "mpf"            # gnssrefl model 6 (Williams & Nievinski 2017 / Strandberg 2020) — always time-varying


_GNSSREFL_MODEL_ID: dict[tuple[RefractionMethod, bool], int] = {
    (RefractionMethod.BENNETT, False): 1,
    (RefractionMethod.BENNETT, True): 2,
    (RefractionMethod.ULICH, False): 3,
    (RefractionMethod.ULICH, True): 4,
    (RefractionMethod.NITE, True): 5,
    (RefractionMethod.MPF, True): 6,
}


class RefractionStrategyConfig(_StrictModel):
    enabled: bool = Field(True, description="Apply refraction correction at all (False == gnssrefl refr_model=0)")
    method: RefractionMethod = Field(RefractionMethod.BENNETT, description="Correction model (gnssrefl refr_model, named)")
    time_varying: bool = Field(
        False, description="Annual+semiannual harmonic term evaluated from the static grid (gnssrefl's 'it' flag); "
        "NITE/MPF force this True in gnssrefl, there is no static variant of either"
    )
    apriori_rh_m: float = Field(
        5.0, description="A-priori reflector height guess for NITE/MPF's equivalent-angle geometry term "
        "(gnssrefl apriori_rh default — gnssrefl silently falls back to 5.0 if unset, so this mirrors "
        "that as an explicit default rather than inventing a different one)"
    )

    @model_validator(mode="after")
    def _check_gnssrefl_model_id(self) -> "RefractionStrategyConfig":
        if self.enabled and (self.method, self.time_varying) not in _GNSSREFL_MODEL_ID:
            raise ValueError(
                f"{self.method.value} with time_varying={self.time_varying} has no gnssrefl equivalent — "
                "NITE and MPF are always time-varying in gnssrefl (models 5/6 only); "
                "set time_varying=True for those methods"
            )
        return self

    def to_gnssrefl_model_id(self) -> int:
        return 0 if not self.enabled else _GNSSREFL_MODEL_ID[(self.method, self.time_varying)]


class NmriStrategyConfig(ArcStrategyConfig):
    # No gnssrefl precedent exists for any field below — gnssrefl never
    # implements NMRI in code (see §8), so there is no "gnssrefl default"
    # to source for this class the way RhStrategyConfig has one.
    # min_elev_deg/max_elev_deg here are NOT gnssrefl's RH e1/e2 (5,25) —
    # the code/pseudorange-multipath literature (Larson & Small 2014 and
    # the classic teqc MP1 convention) commonly uses a ~10-15° mask instead,
    # per §6 step 3 — do not silently borrow RhStrategyConfig's 5.0/25.0,
    # they are a different module's numbers. That ~10-15° figure IS the
    # AlphaCalibration.elevation_mask_deg=(10.0, 15.0) registered just above
    # (not yet traced past step 3's citation list to one specific paper
    # section, but not a separate open number either) — resolved below with
    # the exact same None-means-defer-to-AlphaCalibration pattern
    # baseline_top_fraction already uses, for consistency: both fields live
    # on the same AlphaCalibration entry, share its `citation`, and should
    # resolve the same way, not one falling back automatically while the
    # other stays a silently-orphaned, never-read struct field.
    min_elev_deg: float | None = Field(
        None, description="Minimum elevation angle, degrees. None = fall back to the active "
        "constellation's AlphaCalibration.elevation_mask_deg[0] (§6 step 2; 10.0 for GPS) — "
        "an explicit value here always overrides the literature-sourced default, same "
        "resolution point and same rule as baseline_top_fraction below."
    )
    max_elev_deg: float | None = Field(
        None, description="Maximum elevation angle, degrees. None = fall back to the active "
        "constellation's AlphaCalibration.elevation_mask_deg[1] (§6 step 2; 15.0 for GPS) — "
        "same resolution point and rule as min_elev_deg above."
    )
    min_segment_epochs: int = Field(..., description="Minimum slip-free segment length kept for MP1 mean removal")
    baseline_top_fraction: float | None = Field(
        None, description="Fraction of driest days used for MP1max, evaluated per-sv (RATIONALE.md §23). "
        "None = fall back to the active constellation's AlphaCalibration.baseline_top_fraction (§6 step 2; "
        "0.05 for GPS) — an explicit value here always overrides the literature-sourced default."
    )
    baseline_from: tuple[str, str] | None = Field(
        None, description="Frozen [start, end] baseline window (ISO dates); None = recompute each run, see io.py notes"
    )
    outlier_mad_threshold: float = Field(3.0, description="MAD-based outlier threshold on daily MP1rms")

    @model_validator(mode="after")
    def _check_elev_order(self) -> "NmriStrategyConfig":
        # Overrides ArcStrategyConfig's own version of this check: min_elev_deg/
        # max_elev_deg are Optional here (resolved against AlphaCalibration at
        # the code_multipath entry point, §6 step 2, not inside this model) —
        # the base class's unconditional `self.min_elev_deg >= self.max_elev_deg`
        # comparison would raise a TypeError comparing None to a float before
        # that resolution ever runs. Only enforce ordering when the caller
        # supplied both explicitly; a None/non-None mix is allowed (each
        # resolves independently) and checked again, non-Optional, right
        # after resolution in §6 step 2.
        if self.min_elev_deg is not None and self.max_elev_deg is not None:
            if self.min_elev_deg >= self.max_elev_deg:
                raise ValueError("min_elev_deg must be < max_elev_deg")
        return self
```

`exclude_days: xr.DataArray | None` is **not** a config field — an
`xr.DataArray` in a pydantic model needs `arbitrary_types_allowed` and
breaks YAML round-tripping. It's a **runtime function argument** to
`code_multipath`'s entry point, not part of the serializable strategy
config (see §6.7).

## 12. Phasing

| Phase | Content | Depends on |
|---|---|---|
| 0 | Confirm the observable opt-in path for **both RINEX and SBF** (not RINEX alone — the SBF-specific failures in §3/§6 are invisible from RINEX) | — |
| 0.5 | Prove raw, unsmoothed, uncorrected GPS P1/L1/L2 is obtainable from both readers at float64 wavelength precision, end to end into a synthetic `code_multipath` dry run | Phase 0 |
| 1 | `arcs.py` + `qc.py` + the §17 SID→PRN/`GNSS_obs` adapter + tests | Phase 0.5 |
| 2 | `code_multipath.py` (NMRI) — oracle tests vs `gnssmultipath` for MP1 only (no NMRI oracle exists, see §8) | Phase 1 |
| 3 | `snr_multipath.py` (RH) — oracle tests vs `gnssrefl` (requires actually running it, see §8); refraction-correction literature synthesis (§5 step 5) happens here, not before | Phase 1 |
| 4 | `receiver_multipath.py` (diagnostic-only, re-scoped per §1/§7) | Phase 1 |
| 5 | `provenance.py`, `io.py` (incl. the `canvod-config` chunk-strategy touch point, §10), `config.py`, README/CLAUDE.md | Phases 2-4 |
| 5.1 | Monorepo integration checklist: root `pyproject.toml` `testpaths`/`coverage source`/`commitizen version_files`/`oracle` marker registration; `zensical.toml` nav entries ("Geodesy", not "Multipath" or "GNSS-IR" — see §20 rename); `docs/packages/geodesy/overview.md` + `docs/api/canvod-gnssgeodesy.md`; root `README.md`/`CLAUDE.md` package tables | Phase 5 |
| 6 (deferred) | VWC + vegetation correction, reimplemented from Zavorotny et al. 2010 + Chew et al. 2015 TGRS forward radiative-transfer model (NOT gnssrefl's Chew/Clara lookup table — `RATIONALE.md` §15.4) | — |
| 7 | `tropospheric.py` — expose the §5 step 5 refraction/mapping-function correction as its own standalone product (ZHD/ZWD/mapping functions per epoch), not just an internal RH input. See §14. | Phase 3 |
| ~~8~~ | ~~`position.py`~~ — **cut from scope 2026-09-18**, see §15/RATIONALE.md §29 | — |
| 9 | `ppp.py` — PPP, wrapping an external CLI/library (tool not yet chosen — user input needed, see §16). Not scoped in detail until that choice is made. | — |

Sequencing rationale for NMRI-before-RH: see resolved question 6 below.

## 13. Resolved questions

1. **Is LLI alone reliable for cycle-slip detection? — No.** Absent
   entirely on SBF. On RINEX, use LLI as primary trigger plus a near-free
   residual-rate cross-check on the already-computed MP1 series (§6.3). On
   SBF, use `cum_loss_cont`.
2. **Is externally-supplied snow/rain masking acceptable for v1? — Yes, but
   the absence must be loud, not silent** — required runtime argument,
   `UserWarning` + an `nmri_masking` attr when `None` (§6.7).
3. **Minimum record length for NMRI? — Don't refuse, don't compute silently:
   emit `NMRI` as NaN below a threshold, with the threshold and status as
   explicit output variables** (`nmri_baseline_n_days`,
   `nmri_baseline_confidence`). `MP1rms` itself is always emitted regardless
   — it doesn't need a multi-year baseline to be meaningful on its own (§6.8).
4. **Test-fixture license boundary? — Regenerate RH fixtures from public
   RINEX rather than vendoring gnssrefl's; vendor gnssmultipath's MIT
   fixtures freely; add explicit `REUSE.toml` annotations for anything
   vendored from a non-Apache-2.0 source** (§8).
5. **Icechunk group naming? — Module/algorithm name as the family, no
   umbrella prefix** — `snr_multipath/rh/<strategy>`,
   `code_multipath/nmri/<strategy>`, matching the VOD precedent exactly.
6. **NMRI before RH, or RH first? — Keep NMRI first**, but insert Phase 0.5:
   the three blockers are all input-data problems specific to the NMRI path
   (raw-vs-corrected observables, per-format LLI availability, frequency
   precision/GLONASS), not algorithmic ones. RH needs none of them — only
   `SNR` and `theta`, both already verified correct. If Phase 0.5 turns out
   to need a canvodpy-core change (plausible, for the SBF `keep_data_vars`
   default), RH becomes the sensible thing to ship first while that lands
   upstream — don't reorder pre-emptively, reorder only if Phase 0.5 stalls.
7. **`astropy` as optional `fast` extra, or base? — Superseded, not just
   answered differently.** This question assumed canvod-gnssgeodesy would
   call astropy/scipy itself, choosing between two LSP implementations it
   owned. Since the RH re-scoping (§5 steps 1-4, RATIONALE.md §17), it
   calls neither directly — `strip_compute()` does its own dispatch inside
   gnssrefl. There is no `astropy`/`scipy` extra to choose between; both
   arrive transitively through the `gnssrefl` extra. See `RhStrategyConfig.
   lsp_backend` (§11) for the (renamed, explicit) equivalent choice that
   remains — which library gnssrefl itself uses internally, not which one
   this package calls.
8. **Is MP1/NMRI's GPS-L1/L2 restriction a formula limitation, or a
   calibration one? — Calibration only; the formula is α-generic.**
   Read directly: `estimateSignalDelays()` depends on exactly one physical
   quantity, `alpha = carrier_freq1**2/carrier_freq2**2`
   (`estimateSignalDelays.py:143`) — every coefficient in the MP1/
   ionospheric-delay combination is `alpha`-only (`:195,197`), and
   `carrier_freq1`/`carrier_freq2`/the observation codes are plain
   parameters, not hardcoded GPS constants. GPS L1/L2 is the only
   *calibrated* pair (Larson & Small 2014's elevation mask/
   `baseline_top_fraction`/dynamic range are GPS-L1-specific literature
   numbers, not formula requirements) — see §6 step 2's `AlphaCalibration`
   and step 6. Other widely-spaced pairs (Galileo E1/E5a, BeiDou B1I/B3I)
   are architecturally reachable as a later-phase extension (register one
   more `AlphaCalibration`); closely-spaced pairs (Galileo E5a/E5b) have a
   materially different noise-amplification scale via `alpha` itself and
   would need their own calibration, not GPS's reused. GLONASS is blocked
   by a second, independent issue (`aggregate_glonass_fdma`, §6 step 6)
   regardless of calibration.
9. **`GNSS_SVs`/`obsCodes` exact construction — verified, adapter gap
   closed (§17).** `GNSS_SVs[sys][epoch, j]`: `j=0` is the observed-count,
   `j=1..count` is filled by a per-epoch running write cursor (order of
   appearance), not indexed by PRN — a real distinction from "column index
   = PRN," which the docstring alone didn't rule out. `obsCodes` entries
   are the literal 3-character RINEX 3 codes straight off the header
   (`[obs_type][band_digit][attribute]`); canvod-readers' `code` coord is
   a direct pass-through of `attribute`, but `band_digit` must go through
   `SYSTEM_BANDS[system]` reverse lookup, not string-slicing the `band`
   coord (Galileo's digits "5"/"7" both produce `band` names starting
   "E5"). Fixed `AlphaCalibration.range_codes` for GPS from the
   unverified placeholder `("C1X", "C2X")` to `("C1C", "C2W")`, matching
   §4's already-decided `tracking_codes` example.
10. **Is GPS `range_codes=("C1C", "C2W")` actually what Larson & Small
    used, and does W-code semi-codeless tracking hurt MP1's SNR? —
    Verified against the papers' own text (RATIONALE.md §26), and no:
    MP1 never reads an L2 pseudorange at all.** `C1` confirmed directly:
    PBO's civilian Trimble NetRS receivers have no P-code access, so
    Larson & Small's own "P1" is populated by C/A-code `C1` in practice.
    `range_codes[1]` (`"C2W"`) is required by `estimateSignalDelays()`'s
    signature but feeds only a missing-observation completeness gate, not
    the MP1 arithmetic — the formula is `P1 − 4.0915·L1 + 3.0915·L2 + C1`
    (one pseudorange, both phases), confirmed independently both from the
    paper's own notation and from `estimateSignalDelays.py`'s live code
    (`multipath_range2`'s computation is dead, commented out). Real
    residual gotcha, not blocking: a receiver emitting only modern L2C
    codes (`C2L`/`C2X`) instead of legacy `C2W` would fail that
    completeness gate and have satellites spuriously dropped, even though
    the math doesn't need the value — a QC note for implementation, see
    §6 step 2's field comment.

## 14. `tropospheric.py` — standalone tropospheric product (Phase 7, stub)

**Added 2026-09-18 as part of the scope broadening (RATIONALE.md §20).**
Not a new integration — §5 step 5 already wraps gnssrefl's `refraction.py`
for RH's elevation-angle correction, and that same module's
`gpt2_1w()`/`saastam2()`/`asknewet()` already compute pressure,
temperature, humidity, mapping-function coefficients (`ah`/`aw`), zenith
hydrostatic delay (ZHD), and zenith wet delay (ZWD) as intermediate values
— currently discarded after producing a corrected elevation angle. This
module exposes those same values directly as a per-epoch/per-station
product (`ZHD`, `ZWD`, `ah`, `aw`, `pressure`, `temperature`, `humidity`),
reusing the `GnssreflRefractionCorrector`'s underlying grid/config
machinery rather than duplicating it. Same static-grid-plus-harmonic
model, same "no live TU Wien dependency" property established in §5
step 5 — nothing new to verify about the data source.

**Not designed further than this in the current pass** — scoping stopped
at "this is cheap because the values already exist inside the wrapped
call," which is enough to justify Phase 7 existing, not enough to write
the actual `TroposphericStrategyConfig`/output-Dataset shape. Before
implementation: decide whether GPT3/VMF3 (the modern model, §15.3) should
be offered as a second, opt-in `StrategyConfig` strategy here — the same
literature-synthesis caveat from the original refraction-correction plan
applies if so, this is not a place to casually add "just also support the
better model" without budgeting that work.

## 15. `position.py` — CUT from scope (2026-09-18)

**Cut, not deferred-as-a-stub.** Added earlier the same day as part of
the §20 scope broadening ("wrap whatever gnssmultipath/gnssrefl offer"),
then reconsidered once its actual justification was checked: neither
`snr_multipath.py` (RH) nor `code_multipath.py` (MP1/NMRI) computes or
needs a receiver position — both derive elevation/azimuth from the
station's already-known, surveyed ECEF coordinate (canvodpy stations are
fixed geodetic/IGS reference sites, not rovers). The original scoping
rationale was "gnssmultipath happens to also offer this," not a
demonstrated pipeline dependency — and a full read of the three estimator
classes (RATIONALE.md §28) found that building it properly, consistent
with the ephemeris/clock decision already made in RATIONALE.md §18 (use
canvod-auxiliary's `Sp3InterpolationStrategy`/`ClockInterpolationStrategy`,
not gnssmultipath's own interpolator, for clock especially — gnssmultipath's
approach has no jump handling and produces wrong values across clock
resets), means real reimplementation work (`SP3PositionEstimator`
hardcodes gnssmultipath's own rejected SP3 interpolator with no injection
point), not a thin wrap.
User's call, verbatim: "why do we even need DOP etc?" → **cut it
entirely** rather than re-scope narrower (RATIONALE.md §29).

**What's preserved, for if this comes back.** RATIONALE.md §28 keeps the
full verified findings from reading `GNSSPositionEstimator.py`,
`SP3PositionEstimator.py`, `BroadNavPositionEstimator.py`, and
`StatisticalAnalysis.py` — the single-epoch (not vectorized) call
pattern, the `SP3PositionEstimator`/ephemeris-decision conflict,
`BroadNavPositionEstimator`'s BeiDou refusal and apparent GLONASS
clock-bias gap, both classes' implicit-first-match pseudorange-code
selection, DOP's ECEF-frame/no-HDOP-VDOP limitation, and the silent
elevation-refilter fallback. A concrete future trigger would be mobile/
rover GNSS receiver support (a receiver that doesn't already know its
position) or station-coordinate-drift QC against survey metadata —
neither exists in this package's scope today.

## 16. `ppp.py` — PPP (not scoped — tool choice pending)

**Added 2026-09-18, deliberately left unscoped.** The user's own framing:
"PPP and other things I know how to implement, there is proper libraries
for this (CLIs etc.)" — naming the *category* (wrap an existing,
established PPP tool) without naming a specific tool. This matters more
here than it did for gnssrefl/gnssmultipath, because PPP tooling spans a
much wider license range than the two tools wrapped so far: e.g. RTKLIB
(BSD-2-Clause, permissive), PRIDE PPP-AR (GPL, same family as gnssrefl),
gLAB (restricted academic license, not OSI-approved), GipsyX
(JPL/Caltech, distribution-restricted, not open source), CSRS-PPP (a web
service, not a CLI/library at all). **None of these have been checked
this session — this is a placeholder category, not a researched
recommendation.** Whichever tool is chosen determines the integration
shape (in-process function call vs. subprocess-to-a-binary, matching
either the gnssrefl/gnssmultipath pattern or the teqc-shells-out pattern
already ruled out for MP1 in RATIONALE.md §17) and whether it fits inside
`canvod-gnssgeodesy`'s existing `GPL-3.0-only` umbrella cleanly or needs its
own license-boundary decision the way gnssrefl did. **Next step is the
user naming a specific tool**, not further design work here.

**Memo, 2026-09-18 (user, for future work — not yet a decision, no
research done):** narrow the candidate list above to two, now with exact
repos named by the user: **[rtklibexplorer/RTKLIB](https://github.com/rtklibexplorer/RTKLIB)**
(the actively-maintained fork, not the abandoned original
`tomojitakasu/RTKLIB`) and **[PrideLab/PRIDE-PPPAR](https://github.com/PrideLab/PRIDE-PPPAR)**.
Both were already listed above with a first-pass license
characterization (RTKLIB BSD-2-Clause permissive; PRIDE PPP-AR GPL, same
family as gnssrefl) but neither has been verified this session the way
gnssrefl's/gnssmultipath's licenses were (SPDX/classifier check, not
boilerplate-text inference — per this project's verification
convention), and that characterization was made against the candidate
*names*, not these specific repos. When this section is picked back up:
(1) verify both licenses directly against these two exact repos rather
than trusting this placeholder characterization, (2) check whether
either ships a clean in-process Python-callable core (the
gnssrefl/gnssmultipath pattern) or is CLI/binary-only (the
teqc-shells-out pattern, RATIONALE.md §17) — that answer, not license
alone, determines the integration shape.

## 17. SID → gnssrefl/gnssmultipath array adapter (translation layer)

**Added 2026-09-18, gap-closing pass same day.** Answers "how do we apply
the wrapped tools to our `(epoch, sid)`-shaped data" concretely — the
design in §4/§6 assumed this adapter exists but didn't specify it.
Findings below are from a direct read of `canvod-readers` (`sbf/reader.py`,
`rinex/v2_11.py`, `rinex/v3_04.py`, `gnss_specs/metadata.py`,
`gnss_specs/satellite_catalog.py`, `gnss_specs/constellations.py`,
`builder.py`) and `canvod-auxiliary/position/spherical_coords.py`, plus a
direct read of `gnssmultipath/readers/readRinexObs.py`'s RINEX 3.04 header
parser and epoch-fill loop end-to-end (not just
`estimateSignalDelays.py`'s docstring, which is where the earlier pass
stopped) — tiered by source, not uniform confidence.

- **`sid` format, verified:** pipe-delimited `f"{sv}|{band}|{code}"`
  (`sbf/reader.py:1003,1864,2654`; `_build_sid()` in `rinex/v2_11.py:1055`),
  e.g. `"G01|L1|C"` — matches what §4 already assumed. `sv`, `system`,
  `band`, `code`, `freq_center`/`freq_min`/`freq_max` are separate coords
  (`gnss_specs/metadata.py:187-219`), so a `sid` string never needs
  string-splitting at runtime — pull `sv`/`band`/`code` from their own
  coords instead.
- **`sv` format, verified:** `f"{constellation_letter}{prn:02d}"`, 1-indexed,
  zero-padded to 2 digits (e.g. `"G01"`, `"E36"`). Per-constellation PRN
  ranges from `_CONSTELLATION_SVS` (`rinex/v3_04.py:100-107`): G(GPS) 1-32,
  E(Galileo) 1-36, R(GLONASS) 1-24, C(BeiDou) 1-63, J(QZSS) 1-10, S(SBAS)
  1-36, I(NavIC) 1-14.
- **PRN extraction is trivial, and it lines up with gnssmultipath's own
  convention — the harder mapping I'd expected turned out not to be
  needed.** Re-read `estimateSignalDelays.py`'s docstring directly
  (lines ~60-79): `GNSS_obs(PRN, obsType, epoch)` is a **dense array
  indexed directly by the raw PRN integer** (1..`max_sat`, `max_sat` =
  "max PRN number of current GNSS system" — not a compacted index
  skipping absent satellites). So `int(sv[1:])` (strip the constellation
  letter, parse the zero-padded number) *is* the PRN index gnssmultipath
  expects — no lookup table needed for the mapping itself. What genuinely
  doesn't exist anywhere in canvod-readers (checked directly, not just
  "not found by grep") is a named `sid_to_prn()`/`sv_to_prn()` helper — the
  parse-and-strip is one line, but it needs to live in `canvod-gnssgeodesy`
  as an explicit, tested adapter function, not be re-inlined ad hoc at
  every call site into `estimateSignalDelays`/`detectCycleSlips`.
- **False friend for the *PRN-number* mapping, but not to be dismissed
  wholesale — correction from the "no existing LUT" framing above.**
  `satellite_catalog.py:428-455`'s `prn_to_svn`/`svn_to_prn` is PRN-to-
  *space-vehicle-number* (the physical spacecraft ID, which changes when a
  satellite is replaced in an orbital slot) — still not what `int(sv[1:])`
  needs. But the user pointed out (2026-09-18) that canvod-readers already
  fetches an IGS SINEX file (`igs_satellite_metadata.snx`, via
  `SatelliteCatalog.fetch()`, `satellite_catalog.py:22,361-`) natively, and
  it's a real candidate LUT for a different, more important part of this
  adapter than the PRN-integer parse: **which PRNs are actually active on
  a given day**, not just the integer-string parse. Read the file this
  pass, not inferred:
  - `SatelliteCatalog.active_prns(constellation, on_date)`
    (`satellite_catalog.py:508-532`) returns the sorted, real, SINEX-backed
    list of active PRN codes for a constellation on a date — the
    authoritative source for constructing gnssmultipath's `GNSS_SVs`
    per-epoch active-satellite list, superseding the "hardcode
    `max_sat=32`, assume PRNs 1..32 are all populated" plan below. This is
    already wired up one layer up: `ConstellationBase.update_svs_from_catalog()`
    (`constellations.py:63-94`) calls exactly this and caches the result
    on `self.svs` — the adapter should call through that existing method,
    not re-implement a SINEX query.
  - **`SatelliteCatalog.enrich_dataset()` (`satellite_catalog.py:714-792`)
    looks like the ready-made LUT-application helper but is currently
    broken against canvodpy's actual `sid` convention — a real bug, not a
    design choice, found by reading the body, not assumed.** Its docstring
    says "Dataset with a `sid` dimension containing PRN codes" and it does
    `for prn in ds.sid.values: self.get_prn_metadata(str(prn), on_date)`
    (line 757-758) — an **exact string match** against
    `prn_assignments` (bare `"G01"`-style codes, confirmed at
    `satellite_catalog.py:24-25,100-105`). Real `sid` values are the
    pipe-delimited `"G01|L1|C"` compound (confirmed above) — `"G01|L1|C" ==
    "G01"` never matches, `get_prn_metadata` silently returns `None` for
    every entry, and `enrich_dataset` appends empty-string placeholders
    with no error raised (`satellite_catalog.py:766-772`). **This is a
    silent no-op on real reader output, not a loud failure — worth an
    upstream canvod-readers fix (pass `ds.sv`, not `ds.sid`, or split
    internally) independent of this package**, flagged here rather than
    filed — logged in `BUGS.md` alongside the SBF `validate_dataset`
    timing issue. The adapter in this package should call
    `get_prn_metadata(sv, on_date)` per-`sv` directly (not
    `enrich_dataset()` on the whole Dataset) until that's fixed.
  - **Tangential pointer, not actionable in v1 (GPS-only, §6 step 6):**
    `SatelliteCatalog.glonass_channel(svn, on_date)`
    (`satellite_catalog.py:581-587`) is a second, SINEX-sourced source of
    true per-satellite GLONASS FDMA channel — independent of
    `constellations.py`'s own file-based `glonass_channel_pth` mechanism
    (`constellations.py:422-437`) and of the `aggregate_glonass_fdma`
    config flag flagged as broken in §6 step 6. Worth comparing against
    when/if GLONASS scope is added to `code_multipath`; not relevant while
    v1 stays GPS-only.
- **`theta`/`phi` already carry `dims=["epoch", "sid"]`**
  (`spherical_coords.py:187,193,242,257,270`), i.e. broadcast onto the
  *full* `sid` axis, not just `sv` — geometry is duplicated redundantly
  across every band/code sharing one physical satellite. This is
  harmless for the adapter: §4's `tracking_codes` policy already selects
  one `sid` per `(satellite, band)` before arc detection runs, so the
  redundancy is never actually read twice for the same value.
- **No reshape needed going in.** `(epoch, sid)` is already a dense 2D
  array — confirmed via `builder.py:197-199`
  (`arr[ei, sid_to_idx[sid_str]] = val`), not a sparse/ragged structure
  requiring a materialization step before the adapter can slice it.
- **What the adapter actually does, concretely — revised to use the
  catalog, not a hardcoded range.** For a given `(station, day,
  constellation)`: get the real active-PRN list for that day via
  `ConstellationBase.update_svs_from_catalog(on_date)` (GPS-only in v1, so
  `constellation="G"`), take `max_sat = 32` as the *array-sizing* bound
  (GPS's fixed PRN ceiling per the ICD, still a constant — `active_prns`
  doesn't change what `max_sat` means, it changes which slots within
  `1..max_sat` are actually expected to be populated for that day, useful
  for QC/validation rather than array sizing), allocate the dense
  `GNSS_obs`/`GNSS_SVs` arrays, and fill them by iterating the `sid`
  coord, resolving each entry's PRN via `sid_to_prn()` (the trivial
  `int(sv[1:])` parse — still needed, the catalog doesn't replace it),
  and writing into `GNSS_obs[prn, obsType, epoch]` from the corresponding
  `Pseudorange`/`Phase` `(epoch, sid)` slice. Cross-check the PRNs actually
  present in the Dataset against `active_prns()` as a QC step — a PRN in
  the data that the catalog says wasn't active that day is a real data
  quality signal, not just noise.
- **Gap closed 2026-09-18 — `GNSS_SVs` construction, verified against
  `readRinexObs.py:754-934` directly, not the docstring alone.** Shape is
  `(nepochs, max_sat + 1)`, `int16`, one array per constellation
  (`readRinexObs.py:766`, GPS: `max_sat=32`). Per epoch: column 0 gets the
  observed-satellite count (`:934`); columns `1..count` are filled by a
  **running per-epoch counter, not indexed by PRN** —
  `GNSS_SVs[sys][epoch-1, nGNSS_sat_current_epoch[gi-1]] = prn` (`:929`),
  i.e. column index = order of appearance in that epoch's satellite
  block, cell value = the PRN. (The docstring's "j>1: PRN of observed
  satellites" is accurate but easy to misread as "column index equals
  PRN" — it doesn't; this was the actual open question and it's now
  resolved by reading the fill loop, not just the header comment.) The
  adapter therefore needs a per-epoch write cursor per constellation, not
  a direct `array[epoch, prn] = ...` write.
- **Gap closed 2026-09-18 — `obsCodes` format, verified against
  `readRinexObs.py:1436-1483` (RINEX 3.04 header parser) and cross-checked
  against `canvod-readers/rinex/v3_04.py:1473-1531,1579-1595` directly.**
  `obsCodes[gnss_system_index][sys_char]` is a list of the literal
  3-character RINEX 3 observation codes copied verbatim off the `SYS / # /
  OBS TYPES` header line (`readRinexObs.py:1454,1464`) — e.g.
  `obsCodes[1]["G"] = ["C1C", "L1C", "D1C", "S1C", "C2W", "L2W", ...]`.
  Each code's 3 characters are `[obs_type][band_digit][attribute]`:
  `obs_type` ∈ `{"C": Pseudorange, "L": Phase, "D": Doppler, "S": SNR}` —
  confirmed as the literal dispatch characters canvod-readers' own RINEX
  3 parser matches on (`v3_04.py:1657-1669`, `match obs_type: case "S"/
  "C"/"L"/"D"`), so this isn't gnssmultipath-specific, it's the shared
  RINEX 3 convention both tools read off the same header line.
  `band_digit` is **not** directly recoverable from canvod-readers'
  `band` coord by string-slicing in general — canvod-readers stores the
  human-readable `band_name` (e.g. `"L1"`, `"E5a"`), resolved via
  `SYSTEM_BANDS[system][band_digit]` (`gnss_specs/constellations.py`,
  e.g. GPS `{"1": "L1", "2": "L2", "5": "L5"}`, but Galileo
  `{"1": "E1", "5": "E5a", "7": "E5b", "6": "E6", "8": "E5"}` — note "5"
  and "7" both produce band names starting with "E5", so slicing the
  digit back out of the name is unsafe in general even though it happens
  to work for GPS's `"L" + digit` pattern). `attribute` **is** exactly
  canvod-readers' `code` coord (`v3_04.py:1480,1589`, `code_char =
  obs_code[2]`) — no lookup needed, direct pass-through.
  **Adapter recipe:** for a `sid`'s `(band, code)` coord pair plus the
  target obs_type character, reverse-look-up `band_digit` from
  `SYSTEM_BANDS[system]` (already an existing, reusable dict — no new LUT
  to build) and concatenate `obs_type + band_digit + code`. This is also
  why `AlphaCalibration.range_codes` (step 2 above) is corrected to
  `("C1C", "C2W")`, matching §4's `tracking_codes` example
  (`{"L1": "C", "L2": "W"}`) exactly — the earlier `("C1X", "C2X")` value
  was an unverified placeholder, not derived from the tracking-code
  policy already decided in §4.
