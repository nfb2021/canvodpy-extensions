# Upstream `canvod-readers`/`canvod-auxiliary` bugs found during `canvod-gnssgeodesy` design

Bugs discovered incidentally while designing `canvod-gnssgeodesy` (see
`PLAN.md`/`RATIONALE.md`), against `canvodpy` core, not against this
package. **Noted here, not filed as upstream issues yet** — this file is
the tracking point until that happens. Each entry cites exact
file:line locations and how it was confirmed, per this project's
source-verification convention (`RATIONALE.md` throughout).

None of these are blocking `canvod-gnssgeodesy`'s design work — each has a
documented workaround, cross-referenced below to where it's used in
`PLAN.md`/`RATIONALE.md`. They matter for implementation, not for the
design itself.

---

## 1. `SbfReader.to_ds_and_auxiliary()` — raw-observable request always fails

**Status:** confirmed, real, hits production ingest — not a library-internals-only issue.

**Where:** `canvod-readers/src/canvod/readers/sbf/reader.py`

**What happens:** `to_ds_and_auxiliary()` calls
`validate_dataset(obs_ds, required_vars=keep_data_vars)` at
`sbf/reader.py:2490` — **before** the `store_raw_observables` block
(`sbf/reader.py:2876-2930`) that actually creates `Pseudorange_raw`/
`Phase_raw`/`SNR_raw`/`Pseudorange_unsmoothed`. Passing any of those four
names in `keep_data_vars` therefore always raises "Missing required data
variables," unconditionally, regardless of whether
`store_raw_observables=True` was also passed — the validation runs against
a Dataset that doesn't have the raw variables yet no matter what.

**Why it matters:** SBF's default `Pseudorange`/`Phase` are *derived*, not
raw — Hatch-filter-smoothed and firmware multipath-corrected per
Septentrio's own documented firmware design (`sbf/reader.py:457-522`,
`_PSEUDORANGE_RAW_ATTRS`/`_PHASE_RAW_ATTRS`/`_PSEUDORANGE_UNSMOOTHED_ATTRS`,
citing the *Septentrio AsteRx SB3 ProBase Firmware v4.14.0 Reference
Guide* by block/field/page number). Confirmed on real ROSA fixtures
(`canvod-readers/tests/test_data/valid/sbf/01_Rosalia/`):
`Pseudorange − Pseudorange_raw` has mean |diff| = 0.163 m, max
|diff| = 2.24 m — the same order of magnitude as the seasonal NMRI signal
`canvod-gnssgeodesy`'s `code_multipath.py` needs to measure. Any consumer
that needs the true raw observables (this package's MP1/NMRI module is
one) hits this immediately.

**Not library-internals-only:** the real production ingest path,
`canvodpy/src/canvodpy/orchestrator/processor.py:186-192`, calls
`rnx.to_ds_and_auxiliary(keep_data_vars=keep_vars, ...,
store_raw_observables=store_sbf_raw_observables, ...)` where `keep_vars`
traces back to `load_config().processing.params.keep_gnss_observables`
(four separate call sites in `processor.py`: `3713`, `3881`, `4197`,
`4915`). Requesting `["SNR", "Pseudorange_raw", "Phase_raw"]` via the
documented, intended config mechanism **will crash real ingest**.

**Workaround (verified against the real fixture):** request
`keep_data_vars=None` instead of naming the raw variables explicitly —
this validates against the default `["SNR"]` only and skips the post-hoc
drop-filter entirely (both gated on `is not None`), returning every
variable including the raw ones; subset in Python afterward.
`canvod-gnssgeodesy`'s SBF ingest path cannot go through the standard
`keep_gnss_observables` mechanism as documented.

**Proper fix:** move the `validate_dataset` call to after the
`store_raw_observables` block.

**Referenced from:** `PLAN.md` §3.

---

## 2. `SatelliteCatalog.enrich_dataset()` — silent no-op against real `sid` values

**Status:** confirmed by direct read of the method body, not inferred.

**Where:** `canvod-readers/src/canvod/readers/gnss_specs/satellite_catalog.py:714-792`

**What happens:** the method's own docstring says "Dataset with a `sid`
dimension containing PRN codes," and its body does, for every value in
`ds.sid`:

```python
for prn in sids:                                  # sids = list(ds.sid.values)
    meta = self.get_prn_metadata(str(prn), on_date)  # exact string match
```

`get_prn_metadata()` → `prn_to_svn()` matches `prn` against
`PrnAssignment.prn` by exact equality (`satellite_catalog.py:443-446`),
and those are bare PRN codes like `"G01"` (confirmed at
`satellite_catalog.py:24-25` and the `PrnAssignment` dataclass,
`:99-105`). But canvodpy's actual `sid` coordinate is the pipe-delimited
compound `f"{sv}|{band}|{code}"` (e.g. `"G01|L1|C"`) — confirmed at
`sbf/reader.py:1003,1864,2654` and `_build_sid()` in
`rinex/v2_11.py:1055`. `"G01|L1|C" == "G01"` is never true, so
`get_prn_metadata()` returns `None` for every real entry.

**Why it's dangerous, not just wrong:** the `None` case is handled by
silently appending empty-string/`None` placeholders
(`satellite_catalog.py:766-772`) — no exception, no warning, no log at
error/warning level (only an `_log.info("dataset_enriched_with_catalog",
...)` line that reports `enriched=0` without raising it in severity). The
method returns successfully, attaches all the expected coordinate names
(`svn`, `block`, `tx_power_watts`, `mass_kg`, `plane`, `slot`) to the
Dataset, and every one of them is empty. A caller has no signal that
enrichment silently did nothing unless they specifically check the
`enriched=0` info-level log line or inspect the output values.

**Workaround:** call `get_prn_metadata(sv, on_date)` directly per-`sv`
(from the `sv` coordinate, not `sid`) instead of `enrich_dataset()` on the
whole Dataset.

**Proper fix:** either pass `ds.sv.values` instead of `ds.sid.values`
internally, or split `sid` before the lookup, and consider raising/warning
loudly when the enriched fraction is 0% rather than logging at `info`.

**Referenced from:** `PLAN.md` §17, `RATIONALE.md` §22.

---

## 3. `ClockConfig.window_size` — declared, documented, passed explicitly, never used

**Status:** confirmed by direct read of `_interpolate_sat_clock`'s full body.

**Where:** `canvod-auxiliary/src/canvod/auxiliary/interpolation/interpolator.py:45-58,259-404`

**What happens:** `ClockConfig.window_size` is a documented pydantic
field ("Window size for discontinuity detection", default `9`) and both
call sites that construct a `ClockInterpolationStrategy` pass it
explicitly rather than relying on the default:
`ephemeris/provider.py:213` (`ClockConfig(window_size=9,
jump_threshold=1e-6)`) and `clock/reader.py:74-77`
(`ClkFile.get_interpolation_strategy()`, same values). But
`ClockInterpolationStrategy.interpolate()` and
`_interpolate_sat_clock()` — read in full — never reference
`self.config.window_size` anywhere; only `jump_threshold` drives the
actual segment-splitting logic (`np.where(np.abs(np.diff(valid_data)) >
threshold)`). The name suggests a rolling-window discontinuity detector
that isn't there — the real implementation is a single global
`np.diff`/threshold pass over the whole series, no window.

**Why it matters:** low-severity on its own (the actual jump detection
still works via `jump_threshold`), but it's a documented parameter that
silently does nothing regardless of what value is passed — someone tuning
`window_size` to fix a clock-interpolation problem would see no effect
and reasonably conclude the wrong thing about how the detector works.

**Workaround:** none needed for `canvod-gnssgeodesy` right now — the one
module that would have consumed `ClockInterpolationStrategy`,
`position.py`, was **cut from scope entirely** (`PLAN.md` §15,
RATIONALE.md §29), so nothing in this package currently calls this code
path at all. This bug's relevance is preserved research, not a live
workaround: if position/DOP work is ever revived, RATIONALE.md §18's
recommendation still holds — use canvod-auxiliary's
`ClockInterpolationStrategy` over gnssmultipath's own interpolator for
clock (no jump handling there, produces wrong values across clock
resets) — and this bug doesn't change that recommendation, it's a
documentation/dead-parameter issue, not a correctness issue in the code
path that recommendation actually takes.

**Proper fix:** either implement the windowed behavior the docstring
promises, or remove the unused field and update the docstring.

**Referenced from:** `RATIONALE.md` §18 (SP3/CLK comparison, the
recommendation this bug doesn't undermine), §28 (position.py estimator
classes read in full), §29 (position.py cut from scope — this bug
currently has no live call site in this package).

---

## 4. `canvod-auxiliary/interpolation.py` — shadowed, unreachable dead file

**Status:** confirmed empirically (import resolution tested directly, not inferred from reading alone).

**Where:** `canvod-auxiliary/src/canvod/auxiliary/interpolation.py`
(378 lines) coexists in the same directory as the package
`canvod-auxiliary/src/canvod/auxiliary/interpolation/` (with its own
`__init__.py` re-exporting from `interpolation/interpolator.py`).

**What happens:** Python's import system resolves `canvod.auxiliary.
interpolation` to the **package** (the directory), never the **module**
(the `.py` file) — confirmed by importing it directly in this
environment (`uv run python -c "import canvod.auxiliary.interpolation as
m; print(m.__file__)"` → resolves to
`interpolation/__init__.py`, not `interpolation.py`). The top-level
`interpolation.py` file is therefore **unreachable code**: nothing in the
codebase imports it (all six call sites checked import `from
canvod.auxiliary.interpolation import ...`, which always hits the
package), and it cannot be imported even deliberately without an explicit
file-path import. Its content is a near-duplicate of `interpolation/
interpolator.py` (`Sp3Config`/`ClockConfig`/`Sp3InterpolationStrategy`/
`ClockInterpolationStrategy`, same class names, same docstring header
style, both citing "gnssvodpy.processor.interpolator" as their origin) —
almost certainly an artifact of the file being split into a package
without the flat file being deleted afterward, not two deliberately
different implementations.

**Why it matters:** not a runtime-correctness bug (nothing executes this
code) but a real maintenance hazard — a future editor grepping for
`ClockInterpolationStrategy`, `Sp3Config`, etc. and landing in
`interpolation.py` would edit a file that can never run, silently no-op,
and waste time debugging why their change "isn't taking effect." This
session confirmed the two files' class signatures are similar but did
**not** diff them line-by-line for behavioral differences — if they've
drifted, that's an additional risk (someone might believe the dead file
represents older, intentionally-reverted behavior).

**Workaround:** none needed — always import through the package
(`canvod.auxiliary.interpolation`, i.e. `interpolation/interpolator.py`),
which is what every existing call site already does.

**Proper fix:** delete `canvod-auxiliary/src/canvod/auxiliary/
interpolation.py`.

**Referenced from:** `RATIONALE.md` §18 update (SP3/CLK comparison).

---

## Investigated and retracted — not a bug

**`v3_04.py:1020`, `:624`, `:1061` — `except ValueError, IndexError:`.**
A fork investigating `canvod-readers`' LLI handling flagged this as
Python-2 exception syntax (the pre-3.0 `except Type, name:` form, a
`SyntaxError` under Python 3 historically). **Re-checked directly while
assembling this file and the flag was wrong.** `canvod-readers` requires
`python >=3.14` (`canvod-readers/pyproject.toml:6`), and Python 3.14
introduced **PEP 758** (unparenthesized multi-exception `except`
clauses): `except ValueError, IndexError:` is valid Python 3.14+ syntax,
equivalent to `except (ValueError, IndexError):`. Confirmed empirically —
`python3 --version` in this environment is 3.14.7, `ast.parse()` on the
file raises nothing, and a standalone repro
(`except ValueError, IndexError:` catching a raised `IndexError`) behaves
exactly like a tuple-except. Not a bug, not a portability risk given the
package's own `requires-python` floor. Logged here only so the earlier
claim (repeated in `PLAN.md`/`RATIONALE.md` before this correction) has a
visible retraction instead of silently disappearing.
