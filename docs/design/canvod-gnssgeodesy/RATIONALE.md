# `canvod-gnssgeodesy` — Design Rationale, Discard Log, and Audit Trail

Companion to **[`PLAN.md`](./PLAN.md)** in this same directory, which is the
actionable spec. This file is the *why*: the license/reuse analysis behind
the plan's governing principle, a literature review of four candidate
"cannibalize gnssrefl" targets, a log of earlier claims this document
discarded, and an audit trail of what has actually been verified against a
primary source versus asserted with confidence. Nothing in this file should
be read as current guidance if `PLAN.md` says something different —
`PLAN.md` wins.

Section numbers here (`§0`, `§14`–`§33`) continue the numbering of an
earlier single-file draft and are kept for continuity with the audit log's
own citations; they don't imply sections 1-13 are missing — those are
`PLAN.md`'s.

## 0. Decision recap and the community-standard counterweight

> **Superseded by §17 (2026-09-16), not by rewrite.** Everything below in
> this section describes the *original* clean-room verdict — "never
> importing or copying gnssrefl's code" — which §17 explicitly reversed:
> canvod-gnssgeodesy now wraps gnssrefl/gnssmultipath directly, which is why
> the package is packaged GPL-3.0-only (§19). Left as-is for the audit
> trail; do not treat the "Verdict" paragraph below as current policy.

- `gnssrefl` is **GPLv3**; `canvodpy-extensions` is Apache-2.0 and
  REUSE-compliant (`REUSE.toml` stamps a blanket
  `SPDX-License-Identifier: Apache-2.0` over `path = "**"` — this makes
  vendoring *any* GPLv3-repo file, even test data, an affirmative
  mis-licensing unless given an explicit `[[annotations]]` override; see
  `PLAN.md` §8). Importing gnssrefl at runtime, or porting/translating its
  code, is ruled out.
- `gnssmultipath` is **MIT** — no license conflict — but duplicates a RINEX
  parser canvodpy already has. Not worth depending on.
- `canvod-readers` parses `Pseudorange`/`Phase`/`Doppler`/`LLI`/`SSI` on
  `(epoch, sid)` — **true for RINEX only**. The SBF reader does not produce
  `LLI` at all (no loss-of-lock indicator in the SBF format), and its
  `Pseudorange`/`Phase` are **already firmware multipath-corrected and
  Hatch-smoothed** — see `PLAN.md` §3/§6. "Getting what code-multipath
  needs is a config value change" is true for RINEX and false for SBF as
  originally scoped.
- Verdict: build `canvod-gnssgeodesy` clean-room from the papers, validated
  against local `gnssrefl`/`gnssmultipath` clones as black-box numeric
  oracles, never importing or copying their code or data files. The one
  exception worth tracking is `gnssIR_matlab_v3` (Larson's own MATLAB
  predecessor) for the LSP/RH core specifically — **confirmed MIT
  2026-09-16** by fetching the repository's actual `LICENSE` file directly
  (`raw.githubusercontent.com/kristinemlarson/gnssIR_matlab_v3/master/LICENSE`:
  "Copyright (c) 2018 Kristine M. Larson / Permission is hereby granted,
  free of charge..." — standard MIT boilerplate, not inferred from a
  README badge or GitHub's license-detector heuristic). See §15.1 and §16.
- **Community-standard counterweight (user-raised).** "More rigorous than
  gnssrefl" is not an unqualified win: gnssrefl is the de facto standard
  tool in the GNSS-IR geodesy community, and RH/NMRI values that don't
  reproduce its numbers for the same input aren't comparable to the rest of
  the published literature that uses it — which undercuts a real reason to
  build this at all. Resolution: **gnssrefl-compatible behavior is the
  default `StrategyConfig`** for every module — same thresholds/conventions
  as gnssrefl, reimplemented from its papers and published documentation
  (not its code; the license boundary above is unaffected), and held to the
  oracle-comparison tests in `PLAN.md` §8 as an actual acceptance bar, not a
  nice-to-have. The methodologically-improved alternatives surfaced in §15
  (FAP-based QC, GPT3/VMF3 refraction, Zavorotny/Chew vegetation model) ship
  as a second, opt-in named strategy for users who want the scientific
  improvement over community comparability — a config choice, not a fork in
  the architecture (the `StrategyConfig` pattern in `PLAN.md` §11 already
  supports multiple named strategies per module).

## 14. Discarded/superseded claims (from earlier drafts, for the record)

- "`frequency_hz` sid-coord" does not exist — it's `freq_center`, float32,
  MHz. See `PLAN.md` §6.
- "keep_gnss_observables + LLI is a pure config change" — true for RINEX,
  false for SBF (no LLI; corrected Pseudorange/Phase). See `PLAN.md` §3, §6.
- "VOD uses one flat Icechunk group per analysis_name" — false; nested
  `{calculator}/{analysis_name}`. See `PLAN.md` §10.
- "`_StrictModel`... used elsewhere for canvod-filemap config models" — false
  attribution; `canvod-filemap` uses plain `BaseModel` without
  `extra="forbid"`. `_StrictModel` is canvodpy-core-private. See `PLAN.md` §11.
- "mirrors gnssrefl's `daily_avg`... median absolute deviation filtering" —
  overstated; the reference implementation uses a fixed-metres median
  -deviation reject + mean-of-survivors, not MAD statistics. See `PLAN.md` §5.
- "oracle tests compare against reference numbers already shipped in
  `gnssrefl/test/data/`" — gnssrefl ships inputs and regenerates golden
  outputs at test time; there is no shipped expected-output file. See
  `PLAN.md` §8.
- Receiver multipath as an "independent QC cross-check" — not independent
  once `code_multipath` is fixed to require raw observables; it's the same
  correction, correlated by construction. See `PLAN.md` §1, §7.
- Package/store naming under a blanket "gnssir" label — conflated
  reflectometry (genuinely GNSS-IR) with code-multipath (a generic,
  older geodetic QC concept independent of GNSS-IR). Renamed package to
  `canvod-gnssgeodesy`; store groups keyed by module/algorithm name with no
  umbrella prefix. See `PLAN.md` title, §10.
- The "cannibalize from gnssrefl, wrapped in a mapping/adapter layer that
  guarantees its exact behavior is carried over" strategy — superseded
  after the literature review below: there turned out to be no gnssrefl
  artifact, per component, that was actually the right thing to carry over
  faithfully. Replaced by: clean-room implementation from cited papers,
  defaulted to reproduce gnssrefl's documented behavior for community
  comparability, oracle-tested against its output (§0, §15).
- "`canvod-adapters/gnssvod/provenance.py`'s `_package_version` pattern
  mirrored exactly" — overstated on first write; only the `_package_version`
  helper is a literal match, the rest of `PLAN.md` §9's function shape is
  this package's own design. See §16.
- "`teqc` doesn't run on Apple Silicon" — my own unverified guess,
  undersold the real situation. User-corrected: `teqc` is deprecated
  outright, not merely platform-limited. See §16 and `PLAN.md` §8.

## 15. Cannibalization-candidate literature review

Four parallel research passes, one per component originally flagged as a
cannibalization candidate, tasked to check peer-reviewed literature first
and any alternative geodetic-community tools second. All four instructed
to answer the same underlying question: is gnssrefl's own code/data
artifact the right thing to reuse for this component, or does a better
source exist. Findings below; see §0 for how the "community-standard
counterweight" changes what "using" a finding means in practice (default
strategy vs. opt-in alternative, not outright rejection of gnssrefl's
conventions).

**Purpose clarification (user, 2026-09-16) — this is design-space
reconnaissance, not a citation-accuracy exercise.** The point of this
research was not primarily to build an airtight case that gnssrefl's code
shouldn't be touched (that came out as a byproduct verdict). It was to
know the landscape of established geodetic-community methods well enough
to design the `config.py` pydantic base classes and ABCs (`PLAN.md` §11's
`StrategyConfig` family) so that gnssrefl's default logic can genuinely be
*extended* — a new named strategy per module, swapped in via config, not a
fork — with other methods the wider community already treats as
legitimate (FAP-based QC, GPT3/VMF3 refraction, a from-scratch vegetation
model), rather than being permanently locked to whatever gnssrefl ships.
That reframes what §16 flags below: the citations' job is to be *plausible
enough to design an extension point around*, not to be exact-equation-
level ground truth baked into the code — the actual equations still get
verified against the real paper text when each strategy is implemented in
Phase 6+, not assumed correct from a research agent's summary today.

### 15.1 LSP / reflector-height core

The Lomb-Scargle transform itself is standard, well-published numerical
method (Lomb 1976; Scargle 1982) with no license entanglement — `astropy`
and `scipy` both ship general-purpose implementations already listed as
dependencies (`PLAN.md` §2/§5). Separately, Larson's own predecessor tool,
`gnssIR_matlab_v3` (MATLAB, pre-dates gnssrefl), is **confirmed MIT** (§16
— its actual `LICENSE` file was fetched and read directly, not inferred
from a badge). Its detrending-window and oversampling conventions are
therefore a legitimate, license-clean reference for matching gnssrefl's
documented defaults exactly (gnssrefl is a direct descendant of this
MATLAB code) — this is now usable, not merely aspirational. Action:
implement the LSP core against `astropy.timeseries.LombScargle` (`PLAN.md`
§5, already planned), tune its detrend/oversample defaults to match
gnssrefl's documented behavior (§0 counterweight), cross-checking against
`gnssIR_matlab_v3`'s MATLAB source where gnssrefl's own docs are silent on
a specific constant.

### 15.2 Arc QC thresholds

gnssrefl's peak-to-noise-region and amplitude thresholds are ad hoc,
empirically tuned constants with no direct theoretical grounding published
alongside them. Lomb-Scargle periodogram peaks have a rigorous, general
significance theory instead: Scargle (1982) derived the false-alarm-
probability distribution for LSP peak heights under a null hypothesis of
Gaussian noise; Baluev (2008) extended this to a more accurate bound
accounting for the "look-elsewhere" effect across the frequency grid;
VanderPlas (2018, "Understanding the Lomb-Scargle Periodogram," *ApJS*)
is the standard modern synthesis and tutorial reference, and its
recommended false-alarm-probability (FAP) computation is directly
implemented in `astropy.timeseries.LombScargle.false_alarm_probability()`
— already a dependency path via the `fast` extra (`PLAN.md` §2). No
comparable open, general-purpose QC alternative exists in the wider
geodetic-tools community beyond gnssrefl's own thresholds and this FAP
theory. Per the §0 counterweight: FAP-based QC ships as the improved
opt-in strategy; the default strategy still reproduces gnssrefl's specific
threshold values for comparability, documented as empirical/ungrounded
where that's the honest characterization.

### 15.3 Refraction / mapping-function model

gnssrefl's `refraction.py` is itself a port ("written in python from
original TU Vienna codes for GMF," per its own docstring) of an older,
superseded generation of the same mapping-function family this user's own
department (TU Wien, Geodesy and Geoinformation) originated and continues
to maintain. The current state-of-the-art in that lineage is Landskron &
Böhm (2018, "VMF3/GPT3: refined discrete and empirical troposphere mapping
functions," *Journal of Geodesy*), with reference implementations and
CC BY 4.0 grid data published independently of gnssrefl by TU Wien's own
VMF Data Server. The GNSS-IR-specific refraction correction (adapting a
tropospheric mapping function to the reflected-signal elevation-angle
geometry, not just the direct-signal case mapping functions were designed
for) has its own dedicated literature: Williams & Nievinski (2017) and
Strandberg (2020).

**License check on the TU Wien reference code, 2026-09-16 (this was
initially left ambiguous and needed its own verification pass — the plan
originally said "reimplement... from... TU Wien's own independent
reference code," which reads as license to port that code, and it isn't).**
Fetched `vmf.geo.tuwien.ac.at/codes/` directly: it offers `.f90` (Fortran),
`.m` (MATLAB), and `.cpp` source for `vmf3`/`vmf3_grid`/`vmf3_ht`/`gpt3_1`/
`gpt3_5` and related routines. Read the actual header of `vmf3.f90`: it
carries a bare copyright line — "(c) Department of Geodesy and
Geoinformation, Vienna University of Technology, 2016" — and **no license
grant**. Checked both the codes directory page and the site's separate
`terms.html` for anything covering the code specifically: the only
licensing language found ("free of charge," CC BY 4.0) applies to the
*data* products, not the source files. A bare copyright notice with no
license is, by default, all-rights-reserved — publicly downloadable does
not mean freely reusable/redistributable. This makes TU Wien's own source
code *more* restrictive than gnssrefl's GPLv3 for reuse purposes (GPLv3 at
least grants copy/modify/redistribute rights under copyleft conditions;
an unlicensed copyrighted work grants none), even though it's the more
scientifically current implementation.

Recommendation, corrected: reimplement GPT3/VMF3 from the *published paper*
(Landskron & Böhm 2018) and the CC BY 4.0 *grid data* (which is genuinely
reusable, with attribution) — not from TU Wien's source code, which may be
read for understanding and used to cross-check a from-scratch
implementation's correctness, but not copied or translated, for the same
category of reason gnssrefl's code can't be ported (`PLAN.md` §5 step 5
carries the corrected version of this instruction). Apply the GNSS-IR-
specific correction from Williams & Nievinski/Strandberg on top. This is
still a case where the more rigorous and the community-current choice are
the same choice — gnssrefl's own refraction.py lags this same lineage — the
correction here is about *how* to get there (from the paper, not by
porting anyone's code, gnssrefl's or TU Wien's), not about which model to
target. Default strategy and opt-in strategy likely converge here; confirm
once implemented whether gnssrefl's older GMF-generation output diverges
enough from GPT3/VMF3 to need a separate "legacy-compatible" strategy
after all.

### 15.4 Vegetation correction (Chew/Clara model)

Confirmed: "Clara" is Clara Chew (PhD, CU Boulder 2015, thesis "Soil
Moisture Remote Sensing Using GPS-Interferometric Reflectometry"; now at
UCAR/COSMIC). The core papers are Zavorotny et al. (2010, *IEEE JSTARS*,
bare-soil forward model, no vegetation term), Chew et al. (2014, *IEEE
TGRS*, bare-soil retrieval algorithm), and — the actual vegetation
model — Chew et al. (2015, *IEEE TGRS*, "Vegetation Sensing Using GPS-IR:
Theoretical Effects of Canopy Parameters on SNR Data"), a 1-D
plane-stratified radiative-transfer forward model. gnssrefl's
`advanced_vegetation_correction.py` cites Chew, Small & Larson (2016,
*GPS Solutions*) for both its "simple" and "advanced" correction paths,
but the advanced path's actual mechanism — a k-NN lookup (`scipy.spatial.
cKDTree`, k=1) against a 16,593-row precomputed table,
`vegetation_models/clara_high_model.txt` — is not documented in that
published paper. The module's own header states it was **"ported to
gnssrefl from original MATLAB in October 2025,"** i.e. this specific
table is Clara Chew's own unpublished personal MATLAB artifact, merged
into gnssrefl's GPLv3 tree only recently. No independent copy, archive,
or open-source reimplementation of this table exists anywhere (checked:
no standalone repo, no Zenodo archive, no paper supplementary data).
Other 2018-2025 vegetation-correction approaches exist in the literature
(Kumar et al. 2024, *Advances in Space Research*, phase-only empirical
correction; MDPI *Atmosphere* 2023; various 2021-2024 ML/fusion papers)
but none ship reusable code or data — each would need independent
reimplementation from its paper's equations. **Recommendation: do not
vendor `clara_high_model.txt` or port the k-NN lookup** — its provenance
(unpublished personal data, recently GPL-merged) makes it both a license
risk (data-as-compiled-database is a legal gray area under GPLv3 vendoring)
and a black-box the software design shouldn't depend on regardless of
license. Build Phase 6 (`PLAN.md` §12) from scratch against the published
Zavorotny (2010) and Chew (2015 TGRS) forward radiative-transfer equations
instead — a transparent, cited physical model in place of an opaque table,
and the only version of this component with no license question attached
at all. This is the one component of the four where "clean, cited, and
transparent" and "gnssrefl-compatible" cannot both be the default — there
is no way to reproduce gnssrefl's specific table-driven output without
the table itself. Document this divergence explicitly when Phase 6 is
scoped, rather than silently shipping a different-but-similar vegetation
correction under the same name.

## 16. Deep-review audit log (2026-09-16)

User-requested audit: re-check what in this document was actually verified
against a primary source versus asserted with confidence. Every claim below
was independently re-checked this pass (source file read, or repository
LICENSE file fetched directly) — this section exists so the confidence
level of every non-trivial claim in the document is traceable, not just
asserted a second time.

**Re-confirmed exactly as stated, evidence re-checked directly:**

- `gnssrefl` LICENSE is verbatim GPLv3 text (read `.dev_deps/gnssrefl/LICENSE`
  directly, not inferred from `pyproject.toml`'s classifier — though that
  also says so, at `.dev_deps/gnssrefl/pyproject.toml:17`).
- `canvod-store/manager.py:484,540,588` — `group_name = f"{calculator_name}/
  {analysis_name}"`, and `store.py:2221`'s docstring literally contains the
  `"tau_omega_zeroth_order/canopy_01_vs_reference_01"` example quoted in
  `PLAN.md` §10. Not paraphrased — read verbatim.
- `canvod-readers/gnss_specs/metadata.py:296-317` — `DATAVARS_TO_BE_FILLED`
  really does carry `units: "degrees"` and `fill_value: -9999.0` for
  `theta`/`phi`, **and** a repo-wide grep confirms this dict is referenced
  nowhere else in `canvod-readers` — the "stale/dead code" characterization
  in `PLAN.md` §4 holds, it isn't just unused-looking, it's actually unused.
- `canvod-auxiliary/position/spherical_coords.py`'s docstring: declared
  domain is `theta ∈ [0, π]` with an explicit runtime rule "`theta > π/2` →
  below horizon (set to NaN)". `PLAN.md` §4's compressed claim ("theta ∈
  [0, π/2], below-horizon → NaN") describes the *populated* range
  post-masking, which is what `detect_arcs` actually receives — this is
  the same fact stated two ways, not a discrepancy, but the wording was
  worth stress-testing since "declared domain" and "populated range" are
  genuinely different things and it read ambiguously on a fresh pass.
- `canvod-adapters/CLAUDE.md:37-38` independently states
  `Elevation = 90 - degrees(theta)`, `Azimuth = degrees(phi) mod 360` —
  the third of the "three separate confirmations" claimed in `PLAN.md` §4,
  now actually read rather than remembered.
- `gnssrefl/advanced_vegetation_correction.py`'s docstring is verbatim
  "Ported to gnssrefl from original MATLAB in October 2025." and
  `vegetation_models/clara_high_model.txt` is exactly 16,593 lines —
  both numbers in §15.4 quoted exactly, not rounded or approximated.
- `gnssrefl/computemp1mp2.py` genuinely shells out to a `teqc` binary
  (`run_teqc`, `g.teqc_version()`, `line = [teqc, '-nav', ...]`) — confirms
  the `PLAN.md` §8 "shells out to teqc" claim. A repo-wide grep for `nmri`
  across every `.py` file in `.dev_deps/gnssrefl` returns zero matches —
  confirms "never computes NMRI in code" is not an overstatement of an
  incomplete search.
- `canvod-adapters/gnssvod/provenance.py` exists and was read in full —
  see the `PLAN.md` §9 correction; the `_package_version` idiom is a
  genuine match, the rest of the earlier "mirrors exactly" claim was not.
- The SBF-bug production-impact chain (`PLAN.md` §3) was re-walked end to
  end this pass, not just cited from memory: `processor.py:186-192` really
  does call `rnx.to_ds_and_auxiliary(keep_data_vars=keep_vars, ...,
  store_raw_observables=store_sbf_raw_observables, ...)`, and `keep_vars`
  really does trace back to `load_config().processing.params.
  keep_gnss_observables` (confirmed at `processor.py:3713`, `3881`, `4197`,
  `4915` — four separate call sites, not one). This is the single
  highest-impact claim in the document (a real upstream bug on the
  production ingest path, not a hypothetical), so it earned the most
  re-checking.
- `gnssIR_matlab_v3` license — **resolved**, see §0/§15.1 above. Fetched
  the raw `LICENSE` file directly rather than trusting GitHub's license
  badge/detector; it is the standard MIT boilerplate with Larson's own
  2018 copyright line.
- RH-side gnssrefl defaults (`PLAN.md` §5/§11: `e1=5.0`, `e2=25.0`,
  `h1=0.5`, `h2=8.0`, `peak2noise=2.8`, `ampl/reqAmp=5.0`, `ediff=2.0`,
  `delTmax=75.0`, `desiredP=0.005`, `pele=[5,30]`, `polyV=4`) are read
  verbatim from `gnssrefl/gnssir_input.py:78-80,444-445,468-469,504,533` —
  the tool's own hardcoded function-signature defaults, not inferred or
  approximated.

**Corrected this pass (was overstated or imprecise):**

- **New finding, not just a re-check:** "reimplement GPT3/VMF3... from...
  TU Wien's own independent reference code" (§15.3, `PLAN.md` §5 step 5)
  was ambiguous enough to read as license to port that code. Checked
  directly: `vmf.geo.tuwien.ac.at/codes/vmf3.f90`'s header carries a bare
  copyright notice with no license grant, and neither the codes page nor
  the site's `terms.html` states different terms for the code specifically
  (only the CC BY 4.0 grid data is licensed). Corrected in both files —
  the grid data and the published paper are reusable, the source code is
  not, for the same reason as gnssrefl's code (arguably a stronger one,
  since there's no license at all rather than a copyleft one).
- The earlier "mirrors `canvod-adapters/gnssvod/provenance.py` exactly
  (verified correct)" claim — softened; only the `_package_version` helper
  is literal, the rest was invented for this package. See `PLAN.md` §9.
- The earlier "`teqc` doesn't run on Apple Silicon" claim — replaced with
  the user's correction that `teqc` is deprecated outright. See `PLAN.md` §8.

**Still resting on secondhand sourcing, not independently re-verified —
flagged so this isn't quietly presented at the same confidence level as
the items above:**

- §15.1–15.4's literature citations (Landskron & Böhm 2018, Williams &
  Nievinski 2017, Strandberg 2020, Scargle 1982, Baluev 2008,
  VanderPlas 2018, Zavorotny et al. 2010, Chew et al. 2014/2015, Chew/
  Small/Larson 2016) came from four delegated web-research passes in an
  earlier session. Nobody has personally fetched and read the full text of
  any of these papers — the citations, DOIs, and claimed findings are the
  research agents' summaries. They are plausible (the paper titles/venues/
  years are internally consistent and match what's publicly known about
  this field) and, per the purpose clarification above, their job here is
  design-space reconnaissance for the `StrategyConfig` extension points —
  but they should be treated as one tier below the source-code-verified
  claims above until someone actually opens the PDFs, and the real
  equations must come from the papers directly when each strategy is
  implemented (Phase 3 for refraction, Phase 6 for vegetation).
- The MP1-formula-requires-uncorrected-input inference (`PLAN.md` §3/§6)
  remains, as already flagged there, an inference applied to a verified
  firmware fact — not something externally confirmed for Septentrio/SBF
  specifically. Unchanged by this audit; repeated here so this is a
  complete index of what's still open, not just what got fixed.
- `code_multipath`'s elevation-mask default (`PLAN.md` §6 step 3,
  `NmriStrategyConfig` in §11) — "~10-15°" is impressionistic language
  from the general code-multipath literature convention, not traced to a
  specific sourced default the way the RH-side numbers now are. Open item
  for Phase 2.

## 17. Pivot: wrap gnssrefl directly instead of reimplementing (2026-09-16)

**The decision, stated precisely (user directive).** gnssrefl is the
community-established baseline/"truth" for GNSS-IR geodetic products, but
it is not well-engineered (numbered flags instead of named config, file/
env-var-driven I/O instead of an in-memory API, etc.). `canvod-gnssgeodesy`'s
job is to make gnssrefl's logic available inside canvodpy through a better
interface — **without changing that logic**. Concretely: it is fine for
`canvod-gnssgeodesy` to take gnssrefl (and its own dependencies) as a real
runtime dependency and call its actual functions, provided that's
performant enough, rather than independently reimplementing gnssrefl's
algorithms from descriptions/papers and hoping the result matches. This
reverses the posture every earlier section of this document was written
under ("read gnssrefl's code to understand it, then write an independent
implementation to avoid GPLv3 contamination").

**Why this is a real pivot, not a wording tweak.** Every "do not port
gnssrefl's X" instruction in earlier drafts (see §14 and `PLAN.md`
throughout) was solving a problem — GPLv3 contamination of an Apache-2.0
package — by avoiding gnssrefl's code entirely and re-deriving the same
behavior from papers. That approach has a failure mode the user is
explicitly not willing to accept: a from-scratch reimplementation can
subtly diverge from gnssrefl's actual behavior (different rounding, a
missed edge case, a paper equation gnssrefl doesn't actually use verbatim),
and gnssrefl is the reference "truth" precisely because the wider community
already trusts *its* numbers. Calling gnssrefl's own code directly cannot
diverge from gnssrefl, by construction.

**What this looks like architecturally: wrap, don't reimplement, behind an
ABC.** `PLAN.md` §5 step 5 (refraction correction) is the first section
fully redone under this pattern:
- A pydantic `RefractionStrategyConfig` (`PLAN.md` §11) replaces gnssrefl's
  numbered `refr_model` (1-6) with a named `RefractionMethod` enum
  (`bennett`/`ulich`/`nite`/`mpf`) crossed with a `time_varying: bool`,
  validated against the exact combinations gnssrefl supports.
- An abstract `RefractionCorrector` (`PLAN.md` §5 step 5, new
  `refraction.py` module) defines the contract; `GnssreflRefractionCorrector`
  is v1's only concrete implementation, and is deliberately "dumb" — it
  contains no geodesy, only a translation from canvodpy-shaped arguments to
  the `station_config` dict gnssrefl's `correct_elevations()` expects, and
  back.
- The ABC is the extension point the §15 literature review was for (see
  the sharpened purpose-clarification below): a future
  `Vmf3OperationalRefractionCorrector` (real periodically-refreshed NWM
  grids, per the static-vs-dynamic-data discussion earlier in this session)
  can be added later as a second subclass without touching any call site.

**A second, sharper purpose-clarification from the user (2026-09-16,
restating and tightening the one already in §15):** the literature review's
job was specifically "to identify other metrics, methods and accordingly
design the software, so that in the future we can accommodate these" — not
to build a case against gnssrefl's code, and not to produce
equation-ready specs for immediate implementation either. The concrete
deliverable that purpose demands is exactly the ABC/ `StrategyConfig`
pattern above: an extension point sized and shaped around what the
literature review found *exists* (FAP-based QC, GPT3/VMF3, a from-scratch
vegetation model, potential future NMRI/VWC methods), populated today only
with the gnssrefl-wrapping default. This is now the second time the user
has corrected the framing of why that research was done (see §15's
existing clarification) — treat "the literature review informs extension
points, it does not justify avoiding gnssrefl" as settled, not open to
re-litigation.

**Byproduct resolution of the TU Wien license question (§15.3/§16).**
Reading gnssrefl's `refraction.py` in full (prompted by the user's "how
does gnssrefl solve these two [static/dynamic VMF data] natively?")
surfaced that gnssrefl's own refraction model is a Python port of TU
Wien's *older* GMF-generation code (its docstring says so:  "written in
python from original TU Vienna codes for GMF"), released by gnssrefl's
authors under GPLv3, and that it uses a one-time-downloaded static grid
plus a built-in harmonic term — never a live call to TU Wien's VMF Data
Server, and never GPT3/VMF3 specifically (that's a newer generation TU
Wien ships independently, unrelated to what gnssrefl actually uses). Under
this pivot, `canvod-gnssgeodesy` only ever touches gnssrefl's GPLv3 port —
never TU Wien's unlicensed original files — so the earlier finding that TU
Wien's source has no license grant at all (§15.3, still true and still
worth keeping on record) is no longer a constraint this package needs to
navigate. The operative license boundary is now gnssrefl's GPLv3 alone.

**Resolved 2026-09-18 (see §19): `canvod-gnssgeodesy` ships as GPL-3.0-only.**
This paragraph originally left the packaging question open, asked the user
directly, and got no immediate answer — it sat open for several turns
before being decided. Left here for the audit trail; §19 has the decision
and its mechanics.

**Update, same day: RH/LSP re-scoped, MP1/NMRI confirmed exempt.** The
paragraph above originally left RH (`PLAN.md` §5 steps 1-4) and MP1/NMRI
(§6) as unaudited follow-up work. Both were checked directly, not assumed:
- **RH**: traced gnssrefl's actual RH pipeline (`extract_arcs.py` down into
  `gnssrefl/gps.py`) and found the real computational core —
  `get_ofac_hifac()` and `strip_compute()` — is exactly as clean and
  in-memory as `correct_elevations()` was. `PLAN.md` §5 steps 1-4 are now
  rewritten the same way step 5 was: detrend stays a plain canvod-native
  `np.polyfit` (textbook, not gnssrefl-proprietary — gnssrefl's own
  `window_new()` does the identical thing, just entangled in an on-disk
  SNR-file column convention not worth adopting), the LSP peak-pick calls
  `strip_compute()` directly, and the per-satellite wavelength scale factor
  is sourced from gnssrefl's `gnss_frequencies.get_scale_factor()` rather
  than reimplemented (GLONASS FDMA channel wavelengths are an easy silent-
  divergence trap). A genuine bonus, not just a licensing win: the
  angular-vs-ordinary-frequency LSP risk flagged throughout earlier drafts
  is now entirely inside gnssrefl's own `strip_compute()` — confirmed by
  reading `gps.py:1439-1441` directly — so canvod-gnssgeodesy cannot get that
  wrong anymore, because it never makes either LSP call itself. One design
  question this surfaced and left open: the FAP-based QC plan (§15.2)
  assumed access to an `astropy.timeseries.LombScargle` object, and
  `strip_compute()` returns only periodogram arrays, not that object —
  whether astropy's FAP method works from arrays alone, or the closed-form
  Baluev/Scargle formula becomes the only path, needs checking against
  astropy's actual API before Phase 3 (`PLAN.md` §5's QC paragraph).
- **MP1/NMRI**: checked `gnssrefl/computemp1mp2.py` for the same kind of
  wrappable core function and found none exists — gnssrefl's own MP1
  computation is not Python; it shells out to the `teqc` binary via
  `subprocess.call` and parses its text log, gated on `REFL_CODE`/`ORBITS`
  throughout. There is nothing to wrap. §6 was already written as an
  independent from-scratch reimplementation from the published literature
  (Larson & Small 2014; Small, Larson & Smith 2014) — that design is now
  *confirmed correct*, not merely not-yet-revisited. RH and refraction wrap
  gnssrefl directly; MP1/NMRI structurally cannot, and stays a from-scratch
  implementation validated against `gnssmultipath`'s oracle instead (§8),
  same as before this pivot.

## 18. Three follow-ups from the RH re-scoping (2026-09-16)

**1. `lsp_method` renamed to `lsp_backend`, values renamed to library names
(user directive: "no weird kwargs like 'fast', be explicit").** gnssrefl's
own `strip_compute(..., lsp_method='fast')` uses `'fast'` as an internal
sentinel — the actual branch condition is `if lsp_method == 'scipy':
<scipy path> else: <astropy path>` (`gps.py:1438`), so `'fast'` really means
"anything that isn't the string 'scipy'," which is exactly the kind of
unexplained, gnssrefl-internal shorthand not worth exposing verbatim in
canvod-gnssgeodesy's own config. `RhStrategyConfig.lsp_backend:
Literal["astropy", "scipy"]` (`PLAN.md` §11) names the library each option
actually is; a small translation dict at the `GnssreflRhComputer` call site
(`PLAN.md` §5 step 3) maps `"astropy"` back to gnssrefl's `'fast'` string.
This is a naming-only change — gnssrefl's own dispatch logic is untouched.

**2. FAP resolved: closed-form Baluev only, astropy not needed as a
dependency.** The open question from the RH re-scoping pass was whether
astropy's `LombScargle.false_alarm_probability()` could be driven from the
`(px, pz)` arrays `strip_compute()` returns, or whether canvod-gnssgeodesy
would need astropy as a *direct* dependency (not just transitively via the
`gnssrefl` extra) to reconstruct enough state to call it. Read the actual
method (`astropy/timeseries/periodograms/lombscargle/core.py:594-678`,
checked against the copy installed in this repo's own `.venv`): it is an
*instance* method reading `self._trel`, `self.y`, `self.dy`,
`self.normalization`, `self.nterms` — i.e. it needs the exact
`LombScargle(x, y)` object `strip_compute()` constructed internally, not
just the peak-power value. Reconstructing that object ourselves would mean
re-deriving gnssrefl's internal transform (`x = sin(ele·π/180)/cf`,
`gps.py:1429-1433`) — precisely the silent-divergence risk this whole
pivot exists to avoid — purely to gain a dependency canvod-gnssgeodesy
otherwise doesn't need. The closed-form Baluev/Scargle FAP formula avoids
this entirely: it only needs `N` (canvod-gnssgeodesy's own arc point count,
already known) and the periodogram's peak height and frequency-grid span
(`strip_compute()`'s own `px`/`pz`, already returned). **Conclusion: no
astropy dependency is needed for FAP.** This also confirms the earlier
`pyproject.toml` simplification (removing the `fast`/astropy extra, §5
step 3's rewrite) doesn't need to be walked back — astropy stays a
transitive dependency via the `gnssrefl` extra only, never a direct one.

**3. A second MP1 candidate found: `gnssmultipath`
(github.com/paarnes/GNSS_Multipath_Analysis_Software, MIT, cloned to
`.dev_deps/GNSS_Multipath_Analysis_Software`).** This is the same package
already named in `PLAN.md` §8 as the MP1 *oracle* — checked here for
whether it's also wrappable the way gnssrefl's RH/refraction turned out to
be, now that gnssrefl itself was confirmed to have no MP1 logic to wrap
(only a `teqc` subprocess call, §17's closing update). It is: MIT-licensed
(`LICENSE.md`, Per Helge Aarnes, 2023 — no copyleft, no packaging-boundary
decision needed at all, unlike gnssrefl), and its actual MP1 computation
is real, from-scratch Python, not a binary wrapper —
`estimateSignalDelays()` (`src/gnssmultipath/estimateSignalDelays.py:15`)
implements the standard dual-frequency ionosphere-free code-minus-carrier
combination (`multipath_range1 = range1 - (1 + 2/(alpha-1))*phase1 +
(2/(alpha-1))*phase2`, `alpha = f1²/f2²`) plus its own cycle-slip/ambiguity
handling, and `computeDelayStats()` computes per-satellite `MP1rms`. Both
take plain arrays/dicts, no file I/O. Better still: the package exposes a
documented, explicitly-named "preferred entry point" for exactly this —
`SignalAnalyzer`/`SignalStats` (`signalAnalysis.py`) — a clean
object-oriented wrapper around both functions, all-array/dict
constructor arguments, `.run() -> (SignalStats | None, success: bool)`.
This is a better-documented public API than anything found in gnssrefl.

**Real tension this surfaces, not yet resolved — flagged rather than
silently designed around:** `gnssmultipath`'s `estimateSignalDelays()` (and
`SignalAnalyzer`) operates at the whole-observation-*session* level
(`nepochs` for an entire RINEX file) and does its own internal
ambiguity/cycle-slip segmentation using its own thresholds
(`phaseCodeLimit`, `ionLimit`) — its returned `multipath_range1` is
*already* per-segment-mean-removed by the time it comes back. `PLAN.md`
§6 steps 3-4, by contrast, were carefully designed around canvod-
multipath's own per-*arc* (rise/set) segmentation and an SBF-aware
cycle-slip cross-check (`cum_loss_cont`, which `gnssmultipath` — a
RINEX-only tool — has no concept of), plus an explicit concern about
short-segment RMS bias correlated with vegetation signal. Wrapping
`estimateSignalDelays()`/`SignalAnalyzer` wholesale would mean *replacing*
that carefully-designed segmentation and slip logic with gnssmultipath's
session-level, RINEX-only equivalent — a real design trade, not a
mechanical substitution.

**Update, 2026-09-18 (§21): resolved, and revised from the narrower
recommendation originally sketched here.** The original plan (immediately
above) proposed wrapping only the raw linear-combination arithmetic and
keeping canvod-gnssgeodesy's own slip logic entirely separate. Having
since read `detectCycleSlips()`/`getLLISlipPeriods()`/`orgSlipEpochs()` in
full (§21), the actual resolution is a middle ground: wrap
`estimateSignalDelays()` wholesale, including its own internal
ambiguity/slip correction (ionospheric-delay-rate + code-phase-rate
detectors only) — because that correction is inseparable from the
formula in gnssmultipath's implementation, not a bolt-on step — while
*not* folding LLI/`cum_loss_cont` into it (confirmed via `SignalAnalyzer.
run()` that gnssmultipath itself keeps LLI as a parallel, non-unioned
diagnostic, never merged into the correction; there's no signature slot
to feed it in even if we wanted to). canvod-gnssgeodesy's own arc
segmentation, SBF-aware slip *diagnostics* (not correction), minimum-
segment-length bias filtering (now a post-filter on gnssmultipath's
returned segment boundaries, not our own segmentation driving the mean
removal), aggregation, and NMRI normalization all still stay canvod-
native, per steps 1, 3, 5-8 — narrower than "wrap `SignalAnalyzer`
wholesale," broader than "wrap only the bare formula." Written into
`PLAN.md` §6.

**Other `gnssmultipath` features noted, not adopted for v1, one flagged for
re-examination:** RINEX v2/v3/v4 observation and navigation readers
(including new RINEX 4 message types), receiver-position least-squares
estimation (now actually in scope, §15), cycle-slip/LLI distribution
reporting, CDDIS download helper. RINEX/nav readers stay out of scope —
canvodpy already has its own (`canvod-readers`), duplicating that here
would be scope creep.

**SP3-c/d interpolation comparison — resolved (2026-09-18): use
canvod-auxiliary's own machinery, not gnssmultipath's, for §15.** Both
`SP3Interpolator.py` (gnssmultipath) and canvod-auxiliary's
`Sp3InterpolationStrategy`/`ClockInterpolationStrategy`
(`canvod-auxiliary/src/canvod/auxiliary/interpolation/interpolator.py` —
**not** the top-level `interpolation.py` file of the same near-name one
directory up, see `BUGS.md` #3) read in full this pass. Position and
clock are different enough in behavior that they get separate verdicts:

- **Position: both are reasonable, canvod-auxiliary's is arguably the
  better-conditioned choice, not a clear-cut win either way.**
  gnssmultipath uses windowed Neville's algorithm (Lagrange interpolation
  through the `n_interpol_points` — default 7 — nearest SP3 epochs,
  refit per query point) on position alone. canvod-auxiliary uses a
  global cubic Hermite spline per satellite, fit using velocities
  (`Vx`/`Vy`/`Vz`) — and, verified by reading `ephemeris/reader.py:
  189-247`, those velocities are **always self-computed by central
  differencing** (`compute_velocity()`, forward/backward differences at
  the two file-boundary epochs), never read from native SP3 velocity
  records — so canvod-auxiliary's Hermite path doesn't depend on whether
  a given SP3 product happens to ship V-records, unlike a naive
  "use SP3 velocities if present" design would. `add_velocities` defaults
  `True` (`ephemeris/reader.py:58`) and is wired through
  `Sp3File.get_interpolation_strategy()` unconditionally, so the linear
  `_interpolate_positions_only` fallback is effectively dead in the
  default configuration. One genuine shared caveat for both approaches,
  not just canvod-auxiliary's: accuracy degrades near the first/last
  epoch of a single day's SP3 file (Neville's window runs out of
  same-side points; central-difference velocity degrades to one-sided) —
  relevant to `position.py` if `canvod-gnssgeodesy` processes single-day
  windows without stitching adjacent days' SP3 files, a real edge case to
  carry into §15, not resolved here.
- **Clock: canvod-auxiliary's approach is methodologically the correct
  one, not just "the one we already have" — worth stating plainly rather
  than hedging.** gnssmultipath's `SP3Interpolator` treats the SP3 file's
  own embedded `Clock Bias` column as a fourth Neville-interpolated
  channel alongside X/Y/Z, using the **same smooth polynomial fit** as
  position — with **no discontinuity/jump handling at all**. Satellite
  clocks step discontinuously at clock resets; fitting a degree-6
  polynomial across a jump produces spurious oscillation on either side
  of it (Runge's-phenomenon-adjacent, not merely lower accuracy). It also
  only ever sees clock values at the SP3 file's own orbit-epoch spacing
  (per `Sp3File.generate_filename_based_on_type()`'s example, `05M` — 5
  minutes for `COD0MGXFIN` products), since gnssmultipath never reads a
  dedicated clock product. canvod-auxiliary instead reads a **dedicated
  CLK file** at native 30-second sampling (`ClkFile.
  generate_filename_based_on_type()`: `_01D_30S_CLK.CLK`,
  `clock/reader.py:80-102`) and applies **piecewise linear interpolation
  with explicit jump detection** (`ClockInterpolationStrategy.
  _interpolate_sat_clock`: splits the series into continuous segments
  wherever `|diff| > jump_threshold`, interpolates only within a segment,
  leaves cross-jump gaps as `NaN` rather than bridging them) — the
  standard, textbook-correct handling for this specific kind of signal.
  **Recommendation for §15: use canvod-auxiliary's `ClockInterpolationStrategy`
  for clock, not gnssmultipath's — this isn't a stylistic preference, the
  gnssmultipath approach would produce wrong values across clock jumps.**
- **A real, separate bug found while reading this code, not a design
  question — logged as `BUGS.md` #3.** `ClockConfig.window_size`
  (documented: "Window size for discontinuity detection", default `9`,
  passed explicitly as `9` at both call sites —
  `ephemeris/provider.py:213` and `clock/reader.py:74-77`) is **never
  referenced anywhere in `_interpolate_sat_clock`'s body** — only
  `jump_threshold` actually drives the segmentation logic. A declared,
  documented, non-default-looking config field that does nothing.

**CLK usage in canvod-auxiliary, checked directly (user question,
2026-09-18): disabled by default, and unused downstream even when
enabled.** `AuxDataConfig.fetch_clock` (`canvod-config/src/canvod/config/
models/aux_data.py:28-29`) defaults to `True` in the pydantic model, but
the repository's actual shipped default config overrides it:
`canvodpy/config/canvod-settings.yaml:61` sets `fetch_clock: false`
explicitly. The machinery itself is real, not stubbed — `provider.py:
212-217` builds a `ClockInterpolationStrategy`, interpolates, and merges
a `clock` variable into the dataset when enabled — but the field's own
docstring (`aux_data.py:32-34`) states plainly that "canvod-vod's VOD
formula only needs transmittance and polar angle — clock is not consumed
downstream" even when the flag is flipped on. Relevant to §15: position
estimation genuinely needs clock corrections (unlike the VOD pipeline),
so this is exactly the kind of currently-dormant capability §15 would
need to actually turn on and start consuming, not just leave switched
off by default.

## 19. GPLv3 packaging decision (2026-09-18)

**Decision: `canvod-gnssgeodesy` ships as `GPL-3.0-only`, a deliberate
per-package exception to the monorepo's Apache-2.0 default.** User's own
framing: "can we have just canvod-gnssgeodesy as GNU? minimum effort, but
respecting gnssrefl wishes?" — i.e. license the whole package GPLv3 rather
than keep gnssrefl gated behind an optional extra with an Apache-2.0 core,
because it's the lower-complexity option (no need to police a license
boundary *within* one package) even though it has a broader downstream
consequence (GPLv3's copyleft obligation attaches to the whole package,
not just the gnssrefl-backed parts).

**Why `GPL-3.0-only` and not `GPL-3.0-or-later`, verified not assumed.**
Checked gnssrefl's own `pyproject.toml` classifier:
`"License :: OSI Approved :: GNU General Public License v3 (GPLv3)"` — the
fixed-version classifier, not `"GPLv3+"`. gnssrefl elected the plain
version-3-only variant. The "or (at your option) any later version"
sentence that appears near the end of gnssrefl's `LICENSE` file
(`.dev_deps/gnssrefl/LICENSE:639`) is *not* evidence to the contrary — that
sentence is part of the FSF's standard "How to Apply These Terms to Your
New Programs" template, included verbatim in every vanilla GPLv3 license
text as a suggestion for other projects to adapt, not a statement of what
gnssrefl itself chose. A work built on GPL-3.0-only code must stay
GPL-3.0-only; picking the more common `GPL-3.0-or-later` here would have
been a plausible-looking but wrong default.

**Mechanics, written into `PLAN.md` §2 (skeleton + pyproject + a new
licensing-note paragraph):**
1. `pyproject.toml`: `license = "GPL-3.0-only"`.
2. A `LICENSE` file holding the canonical GPLv3 text (identical across
   every GPLv3 project — nothing to author, just copy).
3. A new `REUSE.toml` `[[annotations]]` block scoped to
   `path = "packages/canvod-gnssgeodesy/**"`, overriding the repo's existing
   blanket `path = "**"` → Apache-2.0 rule. Flagged explicitly as needing a
   `reuse lint` check once both exist, because the existing blanket rule
   sets `precedence = "aggregate"` and it hasn't been verified that a more
   specific path wins over an aggregate blanket rule in this tool's actual
   precedence resolution — don't assume, check when the package exists.
4. `README.md` stating the license plainly and crediting gnssrefl
   (Kristine Larson et al.) by name — the "respecting gnssrefl's wishes"
   half of the ask isn't fully satisfied by the correct SPDX tag alone.

**Consequence noted, not acted on:** with the whole package GPL-3.0-only,
the license-boundary reason to keep `gnssrefl` (and `gnssmultipath`)
behind optional extras is gone — there's no Apache-2.0 core left to
protect. Both stay extras in `PLAN.md` §2 anyway, now purely for
install-footprint minimalism (matching the `store` extra's own
rationale), not because the license requires it. Making either a hard
dependency instead would have no licensing consequence — a pure
preference call, left as extras as the lower-churn choice for now.

## 20. Rename and scope broadening: `canvod-multipath` → `canvod-gnssgeodesy` (2026-09-18)

**Decision, in the user's own words:** "PPP and other things I know how
to implement, there is proper libraries for this (CLIs etc). to me it
sounds increasingly as if we are not just dealing with multipath, but a
broad collection of geodetic metrics. it may be worth renaming this
package and making it the central point that brings all 'geodetic'
capabilities to canvodpy." Prompted directly by the pattern that had just
emerged: gnssrefl gave RH + refraction (§17), gnssmultipath is giving MP1
+ cycle-slip detection + (candidate, unverified) position estimation
(§18), and PPP is recognizably the same shape again — wrap an established,
trusted external tool rather than reimplement, one candidate at a time.

**Two follow-up questions asked before acting, both answered:**
1. *Rename now, or keep the current scope and revisit later?* → **Now** —
   cheap while this is still pure design, nothing built yet.
2. *What's explicitly in-bounds, so "geodetic capabilities" doesn't become
   an unbounded catch-all?* → **PPP (wrap existing CLIs/libraries),
   position estimation/DOP, and tropospheric/ionospheric modeling beyond
   RH** — all selected; "leave undefined, let it emerge organically" was
   offered as an option and *not* chosen. The scope is these three
   additions plus the pre-existing reflectometry/code-multipath work, not
   an open-ended mandate.

**Mechanics performed:** directory `docs/design/canvod-multipath/` →
`docs/design/canvod-gnssgeodesy/`; every `canvod-multipath`/`canvod.multipath`/
`canvod/multipath` token in `PLAN.md`/`RATIONALE.md`/`verify_phase0_5.py`
mechanically replaced (`sed`, verified zero old-name occurrences remain
afterward, not just assumed). `PLAN.md`'s opening framing paragraph — which
still described the *original*, since-reversed "clean-room reimplementation,
never touch gnssrefl's code" principle (predating §17's pivot and never
updated when that pivot happened) — was rewritten in the same pass, since
leaving it stale would have meant a fresh reader hitting flatly
contradictory guidance in the first page of the document. Same for
`PLAN.md` §13 resolved-question 7 (the `astropy`/`fast`-extra question,
also stale for the same reason, §17's pivot). New `PLAN.md` §14
(`tropospheric.py`), §15 (`position.py`), §16 (`ppp.py`) scope the three
additions at whatever depth is honestly supported: §14 is genuinely cheap
(the values already exist inside the already-wrapped `refraction.py` call,
just currently discarded), §15 is flagged explicitly as unverified —
gnssmultipath's position-estimator classes were confirmed to exist and be
MIT-licensed (`__init__.py` exports) but their actual call signatures were
never read this session, unlike `SignalAnalyzer`/`estimateSignalDelays`
which were — and §16 is deliberately left unscoped pending the user naming
a specific PPP tool, since the license range across common PPP tools
(BSD/permissive to GPL to fully proprietary/distribution-restricted) is
wide enough that guessing one would risk exactly the kind of unverified
claim this whole document has been trying to avoid.

**What did *not* change:** the `GPL-3.0-only` decision (§19) — still
scoped to "canvod-gnssgeodesy depends on gnssrefl," not revisited for the
broadened scope in this pass. If PPP ends up wrapping a permissively-
licensed tool (e.g. RTKLIB, BSD-2-Clause), that doesn't change anything —
a GPL-3.0-only package can freely depend on permissive-licensed code, the
constraint only ever runs the other direction. It would only become a live
question again if a *non*-GPL-compatible restrictive license (some
academic-only PPP tools) were the eventual choice — noted for whenever
§16 actually gets scoped, not resolved now.

## 21. MP1/NMRI wrap finalized; joblib-not-dask correction (2026-09-18)

**`detectCycleSlips.py`/`getLLISlipPeriods.py` read in full**, resolving
§18's open design fork. Exact signatures:
- `detectCycleSlips(estimates, missing_obs_overview, epoch_first_obs, epoch_last_obs, tInterval, crit_slip_rate) -> dict[str, list[int]]`
  — `estimates` shape `(nepochs, nPRN+1)`, column 0 unused; returns
  **1-based string keys** (`"1"`..`"nPRN"`) mapping to flagged epoch
  indices. Must be paired with `orgSlipEpochs(epochs_for_one_prn) ->
  (periods, n_periods)` to get grouped `[start, end]` periods — it does
  not group internally.
- `getLLISlipPeriods(LLI_current_phase) -> dict[int, ndarray]` —
  `LLI_current_phase` shape `(n_epochs, n_sat+1)`, column 0 unused;
  returns **0-based int keys** (`0`..`n_sat-1`), already grouped into
  `[start, end]` periods internally (duplicates `orgSlipEpochs`'s grouping
  logic inline rather than calling it).
- **Indexing mismatch between the two is real and easy to get wrong**:
  `computeDelayStats.py` reconciles it with an explicit `+1` offset
  (`computeDelayStats.py:270`: `range1_slip_periods[i+1]` against
  `LLI_slip_periods[i]`, same pattern at line 302). Anything in
  `canvod-gnssgeodesy` that cross-references both dicts must replicate
  that offset explicitly.

**Confirmed via re-reading `SignalAnalyzer.run()` (`signalAnalysis.py:
366-406`): LLI is diagnostic-only in gnssmultipath's own pipeline.**
`estimateSignalDelays()`'s internal ambiguity correction unions exactly
two `detectCycleSlips()` calls (ionospheric-delay rate, code-phase rate)
— `getLLISlipPeriods()` is called separately by `SignalAnalyzer.run()`
afterward and stored in `SlipPeriods.lli`, never merged back into
`multipath_range1`. This ruled out the option of feeding SBF's
`cum_loss_cont` (or RINEX LLI) into gnssmultipath's own correction — there
is no signature slot for external slip evidence. Resolution written into
`PLAN.md` §6 step 3: accept gnssmultipath's correction as computed,
report LLI/`cum_loss_cont` as separate diagnostic output variables
instead of trying to fold them in.

**Also resolved: whole-session vs. per-arc invocation, revised from the
"call it per arc" recommendation two turns earlier.** `detectCycleSlips()`
computes `np.diff(estimates, axis=0) / tInterval` — this needs a
continuous, evenly-sampled epoch grid to be meaningful; running it on
disjoint per-arc fragments would corrupt the rate-of-change at every arc
boundary. Corrected design: call `estimateSignalDelays()` once per
(station, day) across all satellites (its natural, vectorized shape,
matching how gnssmultipath itself uses it), and have arc segmentation
slice/clip the day-level result per arc afterward, rather than calling
the whole-session function once per arc as previously proposed. Written
into `PLAN.md` §6 step 2.

**Slip diagnostics: store explicitly, don't discard.** Following up on
the observation two turns earlier that cycle-slip detection was being
treated as a discardable intermediate — `PLAN.md` §6's Output paragraph
now includes `n_slips_threshold`/`n_slips_lli`/`n_slips_cum_loss_cont` per
station per day, the same treatment RH already gives `amplitude`/
`peak2noise`/`n_arcs_used`. Rationale unchanged from when it was first
raised: a day with high `MP1rms` from real vegetation multipath is
indistinguishable from a day with high `MP1rms` from a flaky receiver
unless slip counts are exposed downstream.

**Unrelated correction, same message: `joblib`, not `dask.delayed`, for
parallel compute — a house convention, not a per-module choice.** `PLAN.
md` §5's "Performance" paragraph previously named `joblib`/`dask.delayed`
as interchangeable fan-out options. User correction: this project uses
`joblib` for parallel compute throughout; `dask` is reserved for lazy
*array storage* (Icechunk/zarr-backed lazy loading via `canvod-store`,
§10) and is not used as a task scheduler anywhere in canvodpy. Fixed in
`PLAN.md` §5 — worth carrying forward to any other canvodpy-extensions
package design, not specific to this one.

## 22. SID→PRN adapter: `SatelliteCatalog` (SINEX) as the LUT, not a hardcoded PRN range (2026-09-18)

**Correction to §17/`PLAN.md` §17, one turn after it was written.** That
section's first draft claimed "nothing converts canvodpy's `sv` string to
gnssmultipath's PRN index... no existing utility, that would be new code."
Narrowly true for the *integer parse itself* (`int(sv[1:])` is one line and
genuinely doesn't exist as a named helper anywhere) — but the user pointed
out canvod-readers already has a more load-bearing piece of this problem
solved: it natively fetches and parses the IGS `igs_satellite_metadata.snx`
SINEX file via `SatelliteCatalog` (`canvod-readers/src/canvod/readers/
gnss_specs/satellite_catalog.py`), which is exactly the kind of
authoritative LUT the earlier draft said didn't exist. Read the file
directly this pass rather than accepting the earlier claim at face value —
same discipline as the rest of this session.

**What the catalog actually gives the adapter:** not the PRN-integer parse
(unrelated, still needed as-is), but `active_prns(constellation, date)`
(`satellite_catalog.py:508-532`) — the real, SINEX-backed set of PRNs
active on a given day, already wired one layer up via
`ConstellationBase.update_svs_from_catalog()`
(`canvod-readers/gnss_specs/constellations.py:63-94`). This replaces the
"just hardcode `max_sat=32` and assume all 32 GPS PRN slots are populated"
framing in the first draft of §17 with something closer to the real
picture: `max_sat=32` is still the correct *array-sizing* bound (GPS's PRN
ceiling is fixed by the ICD), but which slots within it are genuinely
expected to have data on a given day is a catalog query, not an assumption
— and mismatches between "what the catalog says should be active" and
"what's actually in the Dataset" are a QC signal worth surfacing, not
noise to ignore.

**A real bug found while checking this, not a design choice — flagged, not
fixed here.** `SatelliteCatalog.enrich_dataset()`
(`satellite_catalog.py:714-792`) looks like the ready-made "apply the LUT
to a Dataset" helper, but its docstring's assumption ("Dataset with a
`sid` dimension containing PRN codes") doesn't match canvod-readers' own
actual `sid` convention, confirmed in §17: `sid` is the pipe-delimited
`"G01|L1|C"` compound, not a bare PRN code. `enrich_dataset()` does
`get_prn_metadata(str(prn), on_date)` for `prn` pulled straight from
`ds.sid.values` (line 757-758) — an exact string match against
bare-code `prn_assignments` that can never succeed for real `sid` values,
and `get_prn_metadata` returning `None` is handled by silently appending
empty-string placeholders (lines 766-772), not raising. **Net effect: a
silent, fully-successful-looking no-op if called on real reader output as
documented.** Same category as the SBF `to_ds_and_auxiliary()` premature
`validate_dataset` call (§3) — both now logged in `BUGS.md`, worth an
upstream issue, not filed yet. **One earlier "bug" from this same
noted-not-filed bucket is retracted, not carried into `BUGS.md`** — see
the note at the top of that file: a fork this session flagged
`v3_04.py:1020`'s `except ValueError, IndexError:` as Python-2 syntax;
re-checked directly while assembling `BUGS.md` and it's valid Python 3.14
syntax (PEP 758, unparenthesized multi-exception `except`), behaves
identically to `except (ValueError, IndexError):`, and matches
`canvod-readers`' own `requires-python = ">=3.14"` floor exactly. The
claim was wrong; flagged as a correction rather than silently dropped, per
the standing source-verification pattern for this session.
`canvod-gnssgeodesy`'s own adapter works around the real `enrich_dataset()`
bug by calling `get_prn_metadata(sv, on_date)` per-`sv` directly rather
than `enrich_dataset()` on the whole Dataset.

**Tangential, noted for later, not actionable while v1 stays GPS-only
(§6 step 6):** `SatelliteCatalog.glonass_channel(svn, date)`
(`satellite_catalog.py:581-587`) is a second, independent, SINEX-sourced
source of true per-satellite GLONASS FDMA channel — alongside
`constellations.py`'s own file-based `glonass_channel_pth` mechanism and
separate from the `aggregate_glonass_fdma` config-flag problem already
flagged in `PLAN.md` §6 step 6. Two independent candidate fixes for that
GLONASS frequency issue now exist; worth comparing if/when GLONASS scope
is added, not resolved here.

## 23. Per-`sid` output resolution across §5/§6/§7 (2026-09-18)

**Decision: `RH` is computed and emitted at `(epoch, sid)` resolution (per
satellite, per band/code, per day); `MP1rms`/`NMRI` at `(epoch, sv)`
resolution (per satellite, per day — see correction below); the SBF
firmware multipath diagnostic's exact resolution is deferred, not yet
corrected this session (user directive: focus on RINEX, not SBF) — none of
the three carry a `station` dim (see correction below). This replaces the
original design, which collapsed all three to a station-level scalar before
any output ever reached a caller.** User directive: "we need per-SID
everything, mirroring and naturally expanding our canvodpy philosophy" —
canvodpy's own core Dataset convention is `(epoch, sid)` (§17), and
collapsing across satellites at the daily-aggregation step was an
unexamined default carried over from thinking of the output as "one number
per station per day" rather than following the dimension canvodpy already
uses everywhere else.

**Correction (same session, 2026-09-18): the first draft of this decision
used `sid` as a blanket dimension name for RH, MP1/NMRI, and the SBF
diagnostic alike, and separately claimed the existing chunk-strategy
defaults were sized for `(epoch, station)`. Both were wrong, caught
directly by the user, not self-discovered — logged per this project's
source-verification convention rather than silently amended.**

1. *`sid` vs `sv`.* User: "'MP1max (the baseline) is now computed per
   satellite' per satellite or per SID? thats different." Checked directly:
   `gnssmultipath.estimateSignalDelays()` takes two fixed observation codes
   (`range1_Code`/`range2_Code`, e.g. `"C1X"`/`"C5X"`) and produces
   `multipath_range1[epoch, PRN]` — both codes are consumed into one
   per-satellite value, so there is no natural per-band/per-code MP1 value
   to key a `sid` dim on. RH stays genuinely per-`sid` (gnssrefl treats each
   frequency's SNR arcs independently); MP1/NMRI is genuinely per-`sv`.
   `PLAN.md` §5/§6 corrected accordingly.
2. *`station` was never a real Dataset dimension at all.* User: "'the
   existing chunk-strategy defaults were sized for (epoch, station)' wrong,
   check again." Checked directly: `canvod-config`'s `ChunkStrategy`
   (`compression.py:27-44`) has exactly two fields, `epoch` and `sid` — no
   `station` field exists, and `gnss_store`/`vod_store` already default to
   `ChunkStrategy(epoch=17280, sid=-1)` (`:87-94`), meaning `sid`-
   dimensioned chunking is existing, reusable precedent, not an open
   problem this package introduces. Following that thread further:
   grepping `canvod-store/manager.py` for `"station"` as a dim returns zero
   matches — `station` is purely a group-path/routing argument to
   `write_multipath_group`/`write_or_append_group`, never a Dataset
   dimension anywhere in canvodpy's real architecture. This was wrong not
   just in the "open item" framing corrected here, but in the **original**,
   pre-this-session design too — §5/§6/§7's outputs never should have
   carried a `station` dim. `PLAN.md` §5/§6/§10 corrected to drop it
   entirely; the per-day rollup's dims changed from `(epoch, station)` to
   `(epoch,)`.

**This is not free — it's a real, if small, statistical fork for NMRI, not
just a reshape.** The original design computed one shared `MP1max` baseline
per station, pooled across every GPS satellite visible that day. Under
per-`sv` resolution, each satellite gets its **own** `MP1max`, computed
from that satellite's own top-5% `MP1rms` history. Verdict: **the per-`sv`
baseline is methodologically better, not merely finer-grained** — different
satellites occupy different, systematically different elevation/azimuth
tracks relative to a fixed antenna, so their multipath regimes are not
interchangeable; pooling them into one threshold was already quietly
averaging over a real physical difference the literature's per-satellite
framing (Larson & Small 2014's own MP1 treatment is inherently
per-satellite) doesn't actually license. One consequence, flagged in
`PLAN.md` §6 step 8: minimum-record-length adequacy (`nmri_baseline_n_days`/
`nmri_baseline_confidence`) is now evaluated per satellite, so an
intermittently-tracked PRN can have a thin, low-confidence baseline even
when the station as a whole has years of data — this is more honest than
the old pooled number, not a regression.

**RH (§5) pools less riskily than NMRI did — no baseline-fork issue there.**
RH's daily aggregation was already just "reject outlier arcs, mean the
survivors"; making that per-`sid` instead of pooled-across-satellites has
no equivalent statistical-validity question, it's a straightforward
resolution increase. Multiple arcs from the same satellite on the same day
(different azimuth sectors) already pooled correctly and continue to.

**The GNSS-VOD-feeding goal (this package's original motivation) still
needs a single per-day scalar, so it doesn't disappear — it moves.** Each
module now also produces an explicitly-derived per-day rollup — RH's
collapses `sid`→scalar, MP1/NMRI's collapses `sv`→scalar (sample-count-
weighted mean, `PLAN.md` §10), dims `(epoch,)`, **not** `(epoch, station)`
— written to a sibling Icechunk group rather than replacing the per-`sid`/
per-`sv` product. This keeps the per-`sid`/per-`sv` data as the actual
source of truth (inspectable, re-aggregable differently later without
recomputing anything upstream) and demotes the old single-number-per-day
output to a documented derivation of it — the reverse of the original
design, where the per-satellite intermediate existed only transiently
inside the aggregation step and was never surfaced.

**Chunking status: not an open item — see correction 2 above.** The only
remaining work is registering a `"multipath_store"`-style entry in
`canvod-config`'s `chunk_strategies` dict mirroring the existing
`ChunkStrategy(epoch=17280, sid=-1)` default, tracked in `PLAN.md` §10 —
not evaluating `sid`-aware chunking from scratch.

## 24. `AlphaCalibration`: MP1/NMRI's GPS-only restriction is calibration, not formula (2026-09-18)

**Question raised by user, in two passes.** First: "'MP1 formula confirms
per-satellite (sv)': yes, because two frequencies are needed. but is it
always GPS L1 and L2? can't we use other systems too? galileo, glonass and
bds all have 2-3 bands. what about codes?" Reframed more precisely on
follow-up: "what is the reason GPS L1 and L2 were used? is the underlying
specific frequencies? or just generally that two freqs are available? can
we use galileo e5a and e5b eg?"

**Answer, verified by direct read of `estimateSignalDelays.py`:** the MP1/
ionospheric-delay combination depends on exactly one physical quantity,
`alpha = carrier_freq1**2/carrier_freq2**2` (`estimateSignalDelays.py:143`
— the function's own comment names it the "amplfication factor"). Every
downstream coefficient is `alpha`-only: `ion_delay_phase1 =
1/(alpha-1)*(phase1-phase2)` and `multipath_range1 = range1 - (1 +
2/(alpha-1))*phase1 + (2/(alpha-1))*phase2` (`:195,197`). `carrier_freq1`/
`carrier_freq2`/all four observation codes are plain function parameters;
`currentGNSSsystem` is used only to branch FDMA (`'R' in currentGNSSsystem`)
vs CDMA frequency handling. **No GPS-specific constant exists anywhere in
the function.** GPS L1/L2 is a historical-availability artifact
(dual-frequency code+phase GPS tracking was standard for decades before
other constellations had usable civilian dual-frequency signals), not a
formula requirement.

**What doesn't transfer: the literature calibration.** NMRI's elevation
mask, `baseline_top_fraction`, and expected dynamic range are Larson &
Small 2014 numbers, derived under GPS L1/L2's specific `alpha`. Because
`alpha` itself sets the `2/(alpha-1)` noise-amplification coefficient, a
different band-pair — even on the same constellation — has a materially
different noise floor for the same physical multipath severity: a
closely-spaced pair (Galileo E5a/E5b) amplifies phase noise far more than a
widely-spaced one (GPS L1/L2, Galileo E1/E5a). Calibration is therefore
keyed per band-pair, not per constellation.

**Decision: build the constellation-generic architecture now; restrict
what's *enabled* to GPS.** `code_multipath.py` gains `AlphaCalibration`
(`PLAN.md` §6 step 2) — a frozen dataclass, not an ABC-with-`compute()`
like `RhComputer`/`RefractionCorrector`, because there is no algorithmic
variation to dispatch on, only literature-sourced constants that vary per
registered (constellation, band-pair) entry; `alpha` itself is a computed
property on the class so the finding above has a permanent, citable home
in the code, not just this document. A module-level registry
(`_ALPHA_CALIBRATION_REGISTRY`) holds one entry (`"G"`: GPS L1/L2) in v1;
`get_alpha_calibration()` raises `NotImplementedError` for anything
unregistered, replacing what would otherwise have been a bare
`constellation != "G"` check. Extending to Galileo E1/E5a or BeiDou
B1I/B3I later — both widely-spaced pairs, the closest analogues to L1/L2
— is registering one more `AlphaCalibration` instance with its own
literature-sourced (or internally noise-floor-characterized) numbers, not
a code change. GLONASS additionally carries the pre-existing, independent
`aggregate_glonass_fdma` frequency-error blocker (`PLAN.md` §6 step 6) —
registering a GLONASS calibration would not be sufficient on its own.

`PLAN.md` updated: §6 steps 2/6/8 and its Output block; §11
`NmriStrategyConfig.baseline_top_fraction`/`ArcStrategyConfig.
constellations`; §13 resolved question 8.

## 25. `GNSS_SVs`/`obsCodes` adapter gap closed (2026-09-18)

**Decision starting point:** §17's own text flagged this explicitly —
`GNSS_SVs`'s exact construction and `obsCodes`' exact cell/string format
were "not yet verified, flagged as a real gap before implementation
starts." Closed this session by reading `gnssmultipath/readers/
readRinexObs.py`'s RINEX 3.04 header parser and epoch-fill loop
end-to-end (`:754-934` for `GNSS_SVs`, `:1436-1483` for the `obsCodes`
header parse) and cross-checking against `canvod-readers/rinex/
v3_04.py:1473-1531,1579-1595` and `gnss_specs/constellations.py`'s
per-constellation `BANDS` dicts — source, not inference, per this
project's verification convention.

**`GNSS_SVs` finding, and why it mattered to actually read the fill
loop, not stop at the docstring.** The docstring (`readRinexObs.py:456-
463`) says "`GNSS_SVs{GNSSsystemIndex}(epoch, j)`: `j=1` number of
observed satellites, `j>1` PRN of observed satellites" — true, but
ambiguous between two different array layouts: (a) column index *is* the
PRN (a PRN-indexed sparse row, direct `array[epoch, prn] = prn`), or (b)
column index is an arbitrary per-epoch write order, PRN is only the
*value* stored there. Reading the fill loop (`:928-929`,
`GNSS_SVs[sys_char][current_epoch-1, nGNSS_sat_current_epoch[gi-1]] =
prn`) resolved it: it's (b), a running per-epoch counter
(`nGNSS_sat_current_epoch`), not the PRN itself, used as the column
index. Had the adapter been written against reading (a) into the
docstring, it would have written correct-looking code
(`GNSS_SVs[epoch, prn] = prn`) that silently produced a wrong, much
sparser array — the kind of bug that wouldn't necessarily fail loudly
since gnssmultipath's own consumers (`estimateSignalDelays`,
`signalAnalysis.py`) iterate `GNSS_SVs[epoch, 1:count+1]` and would just
see the wrong satellites at the wrong indices without raising.

**`obsCodes` finding.** Confirmed the 3-character RINEX 3 code
(`[obs_type][band_digit][attribute]`) is copied verbatim off the RINEX
header (`readRinexObs.py:1454,1464`), and that the `obs_type` dispatch
characters (`C`/`L`/`D`/`S`) are the *same* literal characters
`canvod-readers`' own RINEX 3 parser matches on
(`v3_04.py:1657-1669`, a `match obs_type` block) — both tools read the
same RINEX 3 spec convention off the same header line, not two
independently-invented schemes that happen to coincide. The one real
mapping gap: canvod-readers' `band` coord stores a human-readable name
(`"L1"`, `"E5a"`) resolved via `SYSTEM_BANDS[system][band_digit]`
(`gnss_specs/constellations.py`), and that mapping is **not safely
reversible by string-slicing** in general — GPS's `{"1": "L1", "2":
"L2", "5": "L5"}` happens to be `"L" + digit`, but Galileo's `{"1":
"E1", "5": "E5a", "7": "E5b", "6": "E6", "8": "E5"}` maps two different
digits ("5" and "7") to names both starting `"E5"`. The adapter must do
a real reverse-dict lookup against `SYSTEM_BANDS[system]`, not assume
GPS's coincidental prefix pattern generalizes — a concrete instance of
the same formula-vs-constellation-specific-detail trap §24 already
flagged for `AlphaCalibration`, this time in the I/O layer rather than
the calibration numbers.

**Fallout: `AlphaCalibration.range_codes` for GPS was wrong.** The GPS
registry entry (§6 step 2) had `range_codes=("C1X", "C2X")`, marked
explicitly as an unverified placeholder. Cross-checked against §4's
already-decided `tracking_codes` policy (`{"L1": "C", "L2": "W"}`,
chosen because "the classic [MP1] formula is defined against C1/P1
specifically") — the correct RINEX 3 codes for that policy are `"C1C"`
(pseudorange, L1, C/A-code attribute `C`) and `"C2W"` (pseudorange, L2,
attribute `W`, RINEX 3's code for legacy P2/Z-tracking), not `"C1X"`/
`"C2X"` (`X` is a different attribute — "tracking mode/channel unknown
or unspecified"). Fixed in `PLAN.md` §6 step 2 (both the field comment
and the registry entry).

`PLAN.md` updated: §17 (both bullets rewritten from "not yet verified"
to verified findings, source list in the section preamble extended);
§6 step 2 (`range_codes` fix); §13 (new resolved question 9).

## 26. `AlphaCalibration.range_codes` for GPS verified against Larson & Small's own text, not just gnssmultipath's docstring (2026-09-18)

**Question raised by user:** "so we use GPS L1 C and L2 W? who decided
that? the W code results in semi-codeless tracking, significantly
[im]pacting the SNR..." — a direct, correct challenge. `{"L1": "C",
"L2": "W"}` had gone into `PLAN.md` §4 in an earlier turn this session
as an unverified example, justified only by "the classic formula is
defined against C1/P1 specifically" — never checked against the actual
SNR tradeoff, and never checked against Larson & Small's own text, only
against gnssmultipath's docstring (§25/§6, itself only weak corroborating
evidence — it shows what the *wrapped tool* illustrates, not what the
*calibration's source literature* actually used).

**Verification method, tiered explicitly.** Queried the user's NotebookLM
notebook (`https://notebook.google.com/notebook/8e3f1e08-7210-40a2-8d4b-
0596c79f75c4`) with the `notebooklm` skill, asking for full-text-grounded
quotes from Larson & Small 2014, Small/Larson/Smith 2014, and Small/
Larson/Braun 2010 (GRL) on the exact observables MP1 uses. This is
full-text-grounded evidence, not a web-search abstract paraphrase — the
same evidentiary bar the user's `foresttrack_proposal` vault enforces
("unbreakable rule": every claim needs peer-reviewed full-text
verification, not abstract-level). Tooling note: the skill's local copy
(`~/.claude/skills/notebooklm`) had already been patched for the
`notebooklm.google.com` → `notebook.google.com` rebrand and two other
scraping bugs (per that vault's `NotebookLM Registry.md`), but its
hardcoded 10s page-load timeouts were too short for a slow connection
this session — bumped to 45s/20s locally (uncommitted, matches the
existing pattern of local uncommitted patches already in that repo).

**Verified findings, with direct quotes:**
- **MP1 formula:** `MP1 = P1 − 4.0915·L1 + 3.0915·L2 + C1` (Larson &
  Small 2014's own notation) — one pseudorange (`P1`), both carrier
  phases (`L1`, `L2`), and a constant ambiguity bias. This independently
  corroborates the exact same structure found by direct code read
  (`estimateSignalDelays.py:161,198`: `multipath_range2`'s computation is
  commented out — only `multipath_range1` is live) — two independent
  sources (the paper's own formula and the wrapped tool's actual
  arithmetic) agreeing, not one inferred from the other.
- **`C1` confirmed, not `P1`, and *why*:** "because EarthScope Plate
  Boundary Observatory (PBO) stations use standard civilian geodetic
  receivers (e.g., Trimble NetRS) that do not have access to encrypted
  P-code, the L1 pseudorange measurement is obtained from the
  unencrypted L1 C/A code (RINEX code C1)." Direct quote from Larson
  et al. 2010: "It tracks the un-encrypted C/A code on the L1 carrier
  frequency. On the L2 carrier, it uses a proprietary tracking method
  which produces a P-code-like observable (known as P2) for older Block
  II satellites... For the newer Block IIR-M satellites, the receiver is
  able to track the un-encrypted L2C code." **So `range_codes[0]="C1C"`
  is not an assumption transplanted from gnssmultipath's docstring — it's
  the literal receiver behavior the calibration's own source data came
  from.**
- **No L2 pseudorange in the formula at all** — "does not use L2
  pseudorange (P2 or L2C pseudorange)." This means the user's SNR concern
  about `W`-code semi-codeless tracking, while technically accurate about
  what `W` means, **doesn't actually degrade MP1's own noise floor** —
  MP1 never reads an L2 pseudorange value, codeless-tracked or otherwise.
  What `W` (`range_codes[1]`, `"C2W"`) actually is: a *required function
  argument* to `estimateSignalDelays()` that feeds only a
  missing-observation completeness gate (`:202`,
  `find_missing_observation(range1, range2, phase1, phase2)` — drops an
  epoch/satellite if *any* of the four listed observables is absent),
  never the multipath arithmetic itself. This is a real, separate gotcha
  from the one the user's question raised: a receiver that emits only
  modern L2C-based codes (`C2L`/`C2X`) instead of legacy semi-codeless
  `C2W` would have satellites spuriously dropped by this check alone —
  worth a QC note when implementation starts, not blocking the design.
- **L2 phase (`L2W` vs `L2C`/`L2X`) is what actually varies by receiver
  vintage**, per Larson et al. 2010's quote above — legacy Block II/IIA/
  IIR satellites via semi-codeless tracking, Block IIR-M+ via civil L2C.
  This is the derived-phase-code path (`§4`'s `tracking_codes`,
  `phase2_Code = "L" + band_digit + code`), separate from `range_codes`,
  and not yet given its own `AlphaCalibration` field — `tracking_codes`
  already covers it generically, so no new field needed, just noting
  it's a second axis (receiver vintage) alongside the SNR-of-tracking-
  method axis the user's question named.

**Verdict: `range_codes=("C1C", "C2W")` for the GPS `AlphaCalibration`
entry is correct, and now sourced against the calibration's own
literature rather than a secondhand illustrative example.** No further
change to `PLAN.md` §6 step 2's values — only its citation and field
comment, tightened to state the asymmetric role precisely (already
applied, this pass).

`PLAN.md` updated: §6 step 2 (`range_codes` field comment now states the
range1-vs-range2 asymmetry and the L2C-codes gotcha explicitly; registry
entry's inline comment and `citation` field updated with the verified
sources); §6 step 5 (stale `"C1X"`/`"C5X"` example replaced, asymmetry
noted inline).

## 27. Tracking-code mismatch is severe and common, not rare — fixed default over auto-discovery (2026-09-18)

**Correction to §26's own framing, same day.** §26 characterized
`range_codes[1]`/`"C2W"` as feeding "only" a missing-observation
completeness gate, with the practical consequence framed as "a few
satellites spuriously dropped." User pushback, verbatim: "thats
essentially all modern receivers. how to handle this? and there is also
phase info of GPS L2 W, jus[t] like doppler, range and snr. so i dont
understand your reasi[o]ning" — correct on both counts, and worth logging
precisely rather than just fixing quietly:

1. **Severity was understated, not just framing.** canvod-readers builds
   `sid = f"{sv}|{band}|{code}"` where `code` is the RINEX obs-code's
   third character, **shared across all four observation types**
   (Pseudorange/Phase/Doppler/SNR) for that band
   (`v3_04.py:1512`, `sid_suffix = "|" + band_name + "|" + code_char`,
   verified in §25's read of this file). `"C2W"` and `"L2W"` are not two
   independent config choices — they resolve to the *same* `sid`
   (`"G01|L2|W"`). A receiver whose RINEX header lists no `W`-attribute
   L2 observation code at all (common: many current receivers emit only
   L2C-based codes — `L`/`X`/`Q` — instead of, or without, legacy
   semi-codeless `W`) doesn't just fail a completeness gate on the
   *unused* `range2` value. `phase2_Code="L2W"` — the one that **does**
   feed the live MP1 formula — fails to resolve too, for the identical
   reason. The correct failure shape is "the whole GPS L1/L2 MP1
   computation produces nothing for that station" (data doesn't exist),
   not "a few satellites get an over-strict false-negative" (data exists
   but gets discarded). §26's "worth a QC note later, not a design
   blocker" was wrong to defer.
2. **Frequency was understated.** Framed as a hypothetical ("a receiver
   reporting...") when it's the common case on present-day hardware, not
   an edge case to handle eventually.

**Decision: prescribe one fixed, literature-sourced default; make it
explicitly overridable; do not auto-discover per file.** User's own
words: "i agree with all [of the four proposed fixes] except [per-file
auto-discovery]: lets prescribe one, which per literature default is W,
but can be changed." Rejected alternative (per-file/per-station dynamic
code discovery with a fallback priority order) explicitly, for a reason
worth recording: silently substituting whichever L2 code a given file
happens to offer would mix tracking methods with materially different,
*uncalibrated* noise floors across stations or even across days on the
same station (a firmware update mid-deployment), with no visible signal
to the caller that the calibration's assumptions no longer hold for that
row — the same "formula transfers, calibration doesn't automatically"
failure mode `AlphaCalibration` itself exists to prevent, reintroduced
at the code-selection layer if discovery were automatic.

**What was kept from the original four-part proposal:** (2) provenance
recording — new `tracking_codes_resolved: bool` output var, `(epoch,)`
dims, day-level not per-`sv` since code availability is a per-file/
per-system RINEX header property, not a per-satellite one; (3) loud
failure — a day where the configured codes aren't offered by the file
gets `tracking_codes_resolved=False` and NaN across every `sv`, checked
*before* calling `estimateSignalDelays()`, not discovered indirectly via
gnssmultipath's internal per-satellite gate; (4) unchanged, restated
precisely — no usable code means an explicit NaN day, not a crash or a
silent zero. What was dropped: (1) per-file auto-discovery/fallback,
per the user's explicit rejection above.

`PLAN.md` updated: §4 (`tracking_codes` default promoted from `None`/
required to a named `DEFAULT_TRACKING_CODES = {"L1": "C", "L2": "W"}`
constant, tracking-code policy bullet rewritten to state the
fixed-default/no-auto-discovery decision and why); §6 step 1 (new
validation-before-call behavior, loud not silent); §6 `AlphaCalibration.
range_codes` field comment (corrected — no longer implies range_codes[1]
is a low-stakes/only-a-gate detail); §6 Output block (new
`tracking_codes_resolved` var); §11 (`ArcStrategyConfig.tracking_codes`
given the literature default instead of `Field(...)` required-with-no-
default).

## 28. `position.py`'s three estimator classes read in full — a real architectural conflict, not just missing detail (2026-09-18)

**Starting point:** §15 had explicitly flagged its own gap — "Their
actual call signatures have NOT been read this session." Closed by
reading `GNSSPositionEstimator.py`, `SP3PositionEstimator.py`,
`BroadNavPositionEstimator.py`, and `utils/StatisticalAnalysis.py` in
full, the same discipline §6 applied to `estimateSignalDelays.py`/
`SignalAnalyzer`.

**The load-bearing finding: `SP3PositionEstimator` conflicts with a
decision this same section already made.** §15's ephemeris/clock
resolution (added earlier the same day) chose canvod-auxiliary's
`Sp3InterpolationStrategy`/`ClockInterpolationStrategy` over
gnssmultipath's own `SP3Interpolator`, calling the clock case "not a
close call" — gnssmultipath fits one smooth polynomial across the whole
file with no jump detection, at orbit-epoch (typically 5 min) resolution,
where canvod-auxiliary reads the dedicated 30-second CLK product with
jump-aware piecewise-linear interpolation. Reading `SP3PositionEstimator.
__init__` now shows that decision can't simply be "applied" to this
class: `sp3_interpolator = SP3Interpolator(self.sp3_df,
self.sp3_epoch_interval)` is constructed internally
(`SP3PositionEstimator.py:349`), with no parameter or subclass hook to
substitute a different interpolator. Wrapping `SP3PositionEstimator`
unmodified would silently reintroduce the exact clock-interpolation
behavior the ephemeris/clock decision rejected — an easy mistake to make
if Phase 8 treated "already resolved: use canvod-auxiliary's
interpolators" as covering the whole module rather than checking whether
the specific class being wrapped actually allows it.

**Why this is a fork, not a default to assume silently:** the two ways
forward are asymmetric in effort. Reimplementing
`SP3PositionEstimator`'s Newton-Raphson/Sagnac-correction loop
(`SP3PositionEstimator.py:324-421`, roughly 80 lines) against
canvod-auxiliary's interpolated positions/clock is real, non-trivial new
code for canvod-gnssgeodesy to own and test — a materially bigger lift
than §6's MP1 wrap, which needed zero reimplementation. Accepting
gnssmultipath's own SP3 interpolation for this one path keeps it a thin
wrap but directly contradicts the reasoning already written down for why
that interpolator was rejected. Logged here rather than decided
unilaterally — this needs the same kind of explicit go-ahead
`AlphaCalibration`'s shape got, not an assumed default.

**Secondary findings, real but not blocking:**
- `BroadNavPositionEstimator` doesn't share this conflict (broadcast
  Keplerian propagation via `SatelliteEphemerisToECEF`/`Kepler2ECEF` is
  an independent code path from SP3-product interpolation), but has two
  defects of its own: it raises `ValueError` outright for BeiDou
  (`:84-86`), and its GLONASS branch never assigns a clock-error
  correction from ephemeris (`dTj` stays zero-initialized, `:362`,
  `:393-407`) — pseudoranges go into the solve clock-bias-uncorrected for
  that system. Neither is a canvodpy-core bug (this is a vendored MIT
  dev-dep, not core), but worth flagging with the same discipline as
  `BUGS.md` rather than silently trusting GLONASS output from this class.
- Both estimator classes select the pseudorange code via "first
  RINEX-header obs-code starting with C" (`SP3PositionEstimator.py:102`,
  `BroadNavPositionEstimator.py:129-130`) — the identical "implicit
  first-match" problem §4/§27 already named and rejected for arc
  detection, recurring here in a class with no override parameter for
  it. Not solved this pass; flagged as a concrete Phase 8 integration
  decision (preprocess `obsCodes` so the heuristic resolves to
  `tracking_codes`'s configured choice, or fork the class).
- DOP (`PDOP`/`TDOP`/`GDOP`, `StatisticalAnalysis.py:145-172`) is
  computed from ECEF-frame cofactors directly, not rotated to local ENU
  first — no `HDOP`/`VDOP` without `position.py` doing that rotation
  itself. `run_statistical_analysis()` also rounds every value to 3
  decimals internally (`:192,219-226`), a wrap-vs-bypass decision if
  full precision matters downstream.
- The elevation-filtered re-solve pass is wrapped in a bare
  `try/except Exception: pass` in both classes
  (`SP3PositionEstimator.py:411-418`, `BroadNavPositionEstimator.py:
  445-453`) — a failure there silently falls back to the unfiltered
  all-satellites solution with only a log warning, no distinguishing
  output flag. `position.py` should expose which case occurred, matching
  §6's precedent of surfacing correction provenance rather than
  discarding it.

`PLAN.md` updated: §15 rewritten from "not read this session" to
verified findings — call-pattern difference (single-epoch, not
vectorized), the `SP3PositionEstimator`/ephemeris-decision conflict (flagged
as an open fork, not resolved), `BroadNavPositionEstimator`'s BeiDou/
GLONASS defects, the recurring implicit-first-match code-selection
problem, DOP's ECEF-frame/no-HDOP-VDOP limitation and baked-in rounding,
and the silent elevation-refilter fallback.

## 29. `position.py` cut from scope entirely (2026-09-18)

**Question that triggered this, verbatim:** "why do we even need DOP
etc?" — asked immediately after §28 surfaced that building `position.py`
properly (consistent with the ephemeris/clock decision already made)
means real reimplementation work, not a thin wrap. Worth tracing the
question to its root rather than defending the existing scope reflexively.

**Where `position.py` actually came from.** §20's scope-broadening
decision named "position estimation/DOP" as one of three deliberately
chosen additions (alongside PPP and tropospheric modeling), explicitly
rejecting "leave scope undefined, let it emerge organically" as an
option. But the reasoning recorded at the time was pattern-matching, not
a demonstrated need: "gnssrefl gave RH + refraction, gnssmultipath is
giving MP1 + cycle-slip detection + (candidate, unverified) position
estimation... wrap an established, trusted external tool rather than
reimplement, one candidate at a time." In other words: gnssmultipath
happens to also expose position estimators, so the same "wrap it"
playbook that worked for MP1 was assumed to apply here too, without ever
checking whether anything in this package's actual pipeline consumes a
computed position.

**Checked, and nothing does.** `snr_multipath.py` (RH) and
`code_multipath.py` (MP1/NMRI) both derive elevation/azimuth from the
station's already-known ECEF coordinate — canvodpy's target stations are
fixed, surveyed IGS/geodetic reference sites, not rovers whose position
is unknown and needs solving for. A code-based least-squares position/DOP
fix is a capability receivers use when they *don't* already know their
location precisely (mobile platforms), or as a station-coordinate-drift
QC check against survey metadata — neither of which this package does or
has been asked to do.

**Decision: cut entirely, not re-scope narrower.** Offered three options:
cut it, keep it narrowed to a station-coordinate-QC use case (which could
have avoided the `SP3PositionEstimator` conflict entirely by using only
`BroadNavPositionEstimator`), or keep the original general-purpose scope
and resolve §28's fork. User chose the first, flat: "Cut it from v1
scope entirely." No narrower-QC compromise taken up.

**What this doesn't undo:** §28's findings about the three estimator
classes remain here as verified research, not deleted — if mobile/rover
GNSS support or station-drift QC becomes a real, asked-for feature later,
the SP3-interpolator conflict, the BeiDou/GLONASS defects in
`BroadNavPositionEstimator`, and the implicit-first-match code-selection
problem are already known going in, not rediscovered.

`PLAN.md` updated: §1's scope table (`position` row struck through, cut
noted); §15 replaced with a short cut rationale, no longer scoped as a
Phase 8 stub; §12's phasing table (Phase 8 struck through); file-tree
listing and oracle-test comment (`position.py`, `test_position.py`,
`test_against_gnssmultipath.py`'s DOP mention removed); opening scope
paragraph (§1's prose) updated to list only tropospheric modeling and PPP
as the surviving scope-broadening additions.

## 30. `receiver_multipath.py` (§7) resolution gap closed (2026-09-18)

§23 explicitly left §7's exact output resolution deferred: "the SBF
firmware multipath diagnostic's exact resolution is deferred, not yet
corrected this session (user directive: focus on RINEX, not SBF)." §7's
text in the meantime still read "aggregates to a daily per-`sid`-per-
station mean/std" — a `station` dim §23 point 2 had already established
doesn't exist anywhere in canvodpy, and §7 was the one section that
never got the explicit "No `station` dim" callout §5/§6 both received.

**Verified directly** (not re-derived from the RH/MP1 pattern by
analogy): `sbf/reader.py`'s two call sites that build the metadata
dataset (`:2012-2034` and `:2799-2821`, identical both places) confirm
`mp_correction_m` and `car_mp_corr_cycles` are dims `["epoch", "sid"]` —
no `station` axis, matching §23 point 2's finding for the main
observation Datasets exactly.

**Resolution decided: per-`sid`, not per-`sv`.** Unlike MP1/NMRI (§23
point 1, which collapses to `sv` because `estimateSignalDelays()` mixes
two observation codes into one per-satellite number), these SBF firmware
fields are one value per band/code already — closer to RH's per-`sid`
model (§23) than to MP1's per-`sv` collapse. `PLAN.md` §7 rewritten to
state this explicitly: source dims, aggregation target (`(epoch, sid)`,
day-resolution), the no-`station`-dim citation, and the `sid`-vs-`sv`
reasoning — bringing §7 to the same verification standard §5/§6 already
had, closing the gap §23 left open.

## 31. Pre-commit buildability audit: five gaps closed (2026-09-18)

Before the first real commit of this design work, ran a fresh agent with
**no access to this project's conversation history** against `PLAN.md`
alone, asked one question: could you actually implement this package from
this document, or would you have to guess? The point was to test the
document itself, not the design decisions behind it — everything logged
in this file lives in a conversation a future implementer won't have.
Five concrete gaps came back, all fixed in `PLAN.md`/`BUGS.md` this pass:

1. **`BUGS.md` bug #3's "see `PLAN.md` §15" pointed at nothing.** §15 was
   rewritten into the `position.py` cut notice (§29) and no longer
   mentions `ClockInterpolationStrategy` at all — the actual SP3/CLK
   interpolation recommendation this bug doesn't undermine lives in §18,
   not §15. `BUGS.md` #3 rewritten to cite §18/§28/§29 correctly and to
   state plainly that this bug currently has no live call site in the
   package (position.py is cut) — it's preserved research, not an active
   workaround.
2. **`PLAN.md`'s own numbering self-description was stale.** It claimed
   "`§1`-`§13`" for itself and "`§0`, `§14`-`§16`" for this file, written
   back when both were true; both files have grown well past those ranges
   since (`PLAN.md` to §17, this file to §30 as of that point). Corrected
   to state the ranges as "currently" and lean on the actual rule
   (cross-references always name their target file) rather than a number
   range that goes stale on every future section addition.
3. **No pinned commit recorded for the two source clones every citation
   in both files depends on.** `.dev_deps/gnssrefl` and `.dev_deps/
   GNSS_Multipath_Analysis_Software` are gitignored — they don't ship with
   the repo, and nothing said what commit their file:line citations were
   actually read against. Recorded in `PLAN.md` §2:
   `kristinemlarson/gnssrefl @ 526060f` (2026-08-30) and
   `paarnes/GNSS_Multipath_Analysis_Software @ e037a9b` (2026-08-21) — a
   fresh implementer now knows what to clone and what to re-verify against
   if upstream has moved past these commits.
4. **`Arc.azimuth_at_min_elev` was an undefined field.** Checked directly
   whether gnssrefl has an equivalent to copy: it doesn't —
   `strip_compute()` (`gnssrefl/gps.py:1371-1408`) returns no azimuth at
   all, so this is a canvod-native field with nothing to defer to. Defined
   explicitly in `PLAN.md` §4: the `azimuth_deg` sample at the arc's
   lowest-elevation endpoint (index `0` rising, `-1` setting), an
   output/QC field, not a filter input. Separately confirmed what
   `azimuth_sectors` actually filters against by reading gnssrefl's own
   sector logic (`window_data()`/`removeDC()`, `gnssrefl/gps.py:
   1614-1618,1954-1958`): it masks the full per-epoch `azi` array
   sample-by-sample (`az1 < azi < az2`), not a single representative
   azimuth per arc — `detect_arcs` must do the same, not filter whole
   arcs against `azimuth_at_min_elev`.
5. **`AlphaCalibration.elevation_mask_deg` was declared but never
   consumed anywhere.** It sits on the same struct as
   `baseline_top_fraction`, shares its `citation` field, but unlike
   `baseline_top_fraction` (`NmriStrategyConfig.baseline_top_fraction:
   float | None = None`, falls back to the registry) `NmriStrategyConfig`
   inherited `ArcStrategyConfig`'s *required*, non-Optional
   `min_elev_deg`/`max_elev_deg` — so the registered `(10.0, 15.0)` had no
   code path that ever read it. Almost certainly an oversight from when
   `NmriStrategyConfig`'s comment said "don't silently borrow
   `RhStrategyConfig`'s 5.0/25.0" — true, but never revisited once
   `AlphaCalibration.elevation_mask_deg` was added as the actual
   constellation-specific number to borrow instead. Fixed for consistency
   with `baseline_top_fraction`'s already-established pattern: `PLAN.md`
   §11's `NmriStrategyConfig.min_elev_deg`/`max_elev_deg` are now
   `float | None = None` with the same None-defers-to-`AlphaCalibration`
   rule, a `NmriStrategyConfig`-local override of `_check_elev_order` that
   skips the ordering check until both are non-`None` (the base class's
   version would `TypeError` comparing `None >= float`), and §6 step 3
   states exactly where resolution happens (before `detect_arcs` is
   called) and that the order check re-runs on the resolved pair.

**Verdict from the audit, before these fixes: "not buildable as-is
without a short fixup pass."** Nothing else it checked needed changing —
BUGS.md #1/#2's cross-references, the sourced `RhStrategyConfig` defaults,
and the phasing/scope tables were all confirmed accurate as they stood.

This plan went through several rounds before landing in this two-file
form: an initial clean-room design (v1), a pivot toward cannibalizing
gnssrefl's code wrapped in a compatibility-adapter layer (v3), a reversal
back to clean-room after the four-way literature review surfaced no good
cannibalization target (v4), the community-standard-counterweight
amendment above, and finally this handover pass — which re-verified the
accumulated claims against primary sources (this §16), closed two content
gaps with sourced gnssrefl defaults, and split the single ~1100-line
working document into `PLAN.md` (the spec) and this file (the why), moving
both out of an ephemeral session scratchpad into the repository so a
fresh agent can actually find them. The Phase 0.5 verification script that
produced the empirical SBF-fixture evidence cited throughout `PLAN.md` §3
is preserved alongside these two files as `verify_phase0_5.py`.

## 32. `geodesy_store`: a dedicated Icechunk store, not groups inside `gnss_store` (2026-09-19)

**Starting point.** Working through how `canvod-gnssgeodesy` actually gets
used surfaced a question `PLAN.md` §10 had left implicit: which Icechunk
store do RH/NMRI/the firmware diagnostic actually get written into? The
original §10 draft assumed "the store" generically, without saying whether
that meant `gnss_store` (with these products as extra groups) or something
else. Two sub-questions got resolved in sequence, both by reading
`canvodpy`'s actual code rather than assuming:

**Branch vs. store — a real distinction that got conflated at first.** The
first framing considered was "should this package's products get their own
Icechunk *branch*?" Rejected: an Icechunk branch is for versioning the
*whole tree over time* (diverge/merge/rebase, git-like), not for keeping
two products apart within one store — that's what group paths already do,
and it's the same pattern VOD already uses on `main` alongside raw GNSS
data. A dedicated branch would mean periodically rebasing against `main`
as new raw days land, and would break the ability to atomically commit
"new raw day + its derived metrics" together. `write_or_append_geodesy_group`'s
`branch="main"` kwarg (§10) stays for the general Icechunk capability (a
throwaway experimental run against an alternate strategy config), not as a
second permanent branch.

**But that only answered "not a branch" — it didn't answer "which store."**
Re-reading `canvodpy`'s actual `StorageConfig`
(`canvod-config/src/canvod/config/models/storage.py:112-150`) rather than
assuming settled it: there are already **four** independent, per-site named
store slots, not two — `gnss_store` (dir `"rinex"`), `vod_store` (dir
`"vod"`), `statistics_store` (Zarr), `rollup_store` (dir `"rollup"`) — each
a genuinely separate on-disk Icechunk/Zarr repo under
`stores_root_dir/<site>/<name>`, each with its own write-strategy field
(`gnss_store_strategy`/`vod_store_strategy`), each exposed as its own
property on `GnssResearchSite`/`Site`
(`canvodpy/canvodpy/src/canvodpy/api.py:120-128`: `site.gnss_store`,
`site.vod_store`). VOD — the closest existing analogue to this package
(a derived product computed from `gnss_store` data) — already gets its own
store rather than living inside `gnss_store`'s groups. A fifth slot,
`geodesy_store`, is that same established pattern extended by one, not a
new architectural concept, and is the more consistent answer than the
groups-inside-`gnss_store` framing §10 originally implied.

**Naming: `geodesy_store`, not `nmri_store`/`gnssir_store`.** Both narrower
names were considered and rejected for the same reason `canvod-gnssgeodesy`
itself was already renamed away from a multipath/GNSS-IR-specific name
(§20): NMRI (code-multipath) is not GNSS-IR (that's the SNR/reflectometry
family, per `PLAN.md` §1's own table) — a name built around either family
misdescribes what's inside once RH, NMRI, the firmware diagnostic,
tropospheric ZHD/ZWD, and eventually PPP all land in the same store.
`vod_store` also sets a naming precedent worth matching: it drops the
`gnss_` prefix (it's not `gnss_vod_store`) — `geodesy_store` matches that
brevity and echoes the package name directly.

**Update mechanism: reuse VOD's, don't invent a new one.** Read
`write_or_append_vod_group()`/`should_skip_vod_write()`/
`_vod_metadata_row_exists()` in full
(`canvod-store/src/canvod/store/store.py:2095-2224`) rather than assuming
a mechanism existed to reuse. It does: a per-write metadata ledger keyed on
`source_file_hashes` (the `gnss_store` files actually consumed), gating
every write on exact-hash-match (skip, already computed from this source)
or temporal overlap with a different hash (warn, don't silently diverge) —
one Icechunk commit per write covering data and metadata together. Nothing
about this mechanism is VOD-specific except the method name and ledger
column names, so `canvod-gnssgeodesy` gets `write_or_append_geodesy_group()`
in `canvod-store`, structurally identical (`PLAN.md` §10). This mechanism
only fits a genuinely per-day-independent product, which is what made the
NMRI baseline question (§33) load-bearing rather than a nice-to-have:
without resolving what "the record" means for `MP1max`, NMRI couldn't use
this same append path at all.

`PLAN.md` updated: §10 (dedicated-store definition, four canvodpy-core
touch points, `write_or_append_geodesy_group()`).

## 33. NMRI baseline: entire-record vs. climatology, and why `climatology_min_years=2` (2026-09-19)

**Starting point.** §10's original baseline-recomputation paragraph posed
two options — freeze `baseline_from` once, or recompute-and-overwrite on
every run — and recommended freezing "for scientific reproducibility."
That reasoning was engineering-only; it never asked what Larson & Small
themselves actually did, or what a *stable* baseline should mean at a
station whose record spans multiple, genuinely different climate years.
Investigated in three passes, source-tiered explicitly below because two
different earlier framings of this investigation's own findings needed
correcting mid-stream — flagged here rather than silently smoothed over,
per this project's verification convention.

**Pass 1 — does teqc itself define any baseline concept? No, confirmed
three independent ways, not just asserted once.** `PLAN.md` §5 step 5
had already established that gnssrefl never implements MP1/NMRI in code
(it shells out to the deprecated `teqc` binary). This pass asked the
follow-up: does *teqc* itself define a multi-day baseline, separately from
whatever gnssrefl does or doesn't wrap? Three independent sources, all
answering no:
1. The NMRI literature itself (queried via the project's NotebookLM
   notebook, §26's source): *"teqc itself does not compute or define any
   baseline value (MP1max)... The baseline estimation... was defined by
   Larson & Small entirely on top of teqc's raw output."*
2. Official, currently-reachable UNAVCO documentation
   (`unavco.org/software/data-processing/teqc/teqc.html`): confirms teqc
   is end-of-life since 2019-02-25, and cites Estey & Meertens (1999,
   *GPS Solutions*, paywalled — full formula not retrievable) as the only
   source for teqc's QC linear combinations; no baseline/normalization
   concept mentioned anywhere on the page. (The specific mailing-list URL
   the user supplied, `postal.unavco.org/pipermail/teqc/2019/002642.html`,
   is unreachable — the whole mailing-list host is down, confirmed via
   both `WebFetch` `ECONNREFUSED` and a direct `curl` timeout, not just a
   sandbox restriction. A neighboring message from the same list,
   `002644.html`, titled "So long, partner... (Goodbye)," suggests this is
   Lou Estey's 2019 retirement post, consistent with the EOL date above,
   but wasn't itself retrievable to confirm.)
3. A teqc tutorial PDF the user added to the NotebookLM notebook directly
   (primary source, not a paper's paraphrase of teqc): confirms teqc
   computes a moving-average RMS over one observation window and checks it
   against **static, global, hardcoded** thresholds (*"Expected rms of
   MP1 multipath: 50.00 cm; Expected rms of MP2 multipath: 65.00 cm"*),
   used only for single-run hardware-health flags (*"Significantly higher
   [slip] ratios... are an indication of a sick receiver"*) — categorically
   different from a per-station, per-satellite, multi-day statistical
   baseline. teqc's own defaults must not be borrowed for anything
   baseline-related; they answer a different question ("is this receiver
   behaving normally") than NMRI's ("how dry can it get here").

**Pass 2 — what did Larson & Small actually do, and does it transfer
directly to a live, growing operational store? Quoted precisely, then a
mistake in how the first answer was framed got caught on follow-up.**
Queried the same NotebookLM notebook for the papers' own methods-section
text. Confirmed with exact quotes: `MP1max` = mean of the top 5% of daily
`MP1rms` values. Small, Larson & Smith (2014): *"NMRI is calculated by
normalizing the daily MP1rms values using the average of the highest 5%
individual MP1rms values... The highest 5% of observations provides a
representative value for times when there is a minimum amount of
vegetation."* The original retrospective database: Larson & Small (2014),
*"begins on January 1, 2007 and extends through the end of 2012"* —
6 years, network-wide, 300+ sites. Small, Larson & Smith (2014) validated
against 12 Montana sites (P046/P048/P049/P719 primary, 8 supplemental);
Small et al. (2018) extended to 146 California sites, 2007–2016.

The first answer also stated that the papers' later operational system,
PBO H2O (Larson 2016; Small et al. 2018 — a genuinely continuous,
near-real-time pipeline, *"processed into daily MP1rms metrics,
normalized into NMRI, and published to a public portal within 12
hours"*), used a freeze-after-initial-calibration approach "standard for
operational real-time products," with "at least 2-3 years" of warm-up
before locking a station's baseline. **That characterization was wrong,
or at least unsupported — caught on a deliberate, more precise follow-up
query that explicitly demanded "not specified" instead of an inferred
number.** Re-asked directly: none of the four sources (Larson & Small
2014; Small, Larson & Smith 2014; Larson 2016; Small et al. 2018) state
any minimum warm-up period, minimum count of dry-season days, or
re-calibration cadence for an operational deployment — confirmed
explicitly as "not specified" on a second pass, not merely absent from
what was quoted the first time. The only real minimum-length number
anywhere in these sources is Small et al. (2018)'s *"we required that a
NMRI station have at least a six-year record"* — but that is a
**retrospective study-inclusion filter** ("which stations were trustworthy
enough to include in this comparison paper"), not an operational
first-lock rule, and the first-pass answer had blurred that distinction.
**Correction recorded here explicitly rather than silently fixed**, per
this project's own verification convention: the "2-3 years, standard
practice" framing from the first pass should be discounted; only the
six-year figure is actually quotable, and even it answers a different
question than the one this package needs answered.

**Pass 3 — why six years is the wrong number for canvod-gnssgeodesy
specifically (user's own catch, not a NotebookLM finding).** Six years
reflects Larson having pre-existing access to a multi-decade PBO archive
to mine retrospectively — it says nothing about what a *new* station
needs before its own baseline is usable. Adopting it here would mean every
new deployment produces no stable `NMRI` for its first six years, which
defeats an incrementally-updating, near-real-time product. This is not a
literature disagreement to resolve by more querying — the literature is
correctly silent on this question because Larson & Small never had to
answer it; canvod-gnssgeodesy does, because it targets stations starting
from zero, not a pre-existing archive.

**Decision — a two-tier policy, full mechanism in `PLAN.md` §10:**
- **Tier 1** (record shorter than `climatology_min_years`): use the
  literal literature definition, top 5% of the entire available record —
  honestly provisional, flagged low-confidence via the existing
  `nmri_baseline_confidence`/`nmri_baseline_n_days` output vars (§6 step
  8), never silently withheld.
- **Tier 2** (record at or past `climatology_min_years`): freeze an
  explicit climatology window, `baseline_from`, set manually, never
  auto-transitioned — this is what makes the frozen-baseline mechanism a
  genuine *climatology* rather than an arbitrary convenience window, and
  what makes NMRI eligible for the same append/dedup mechanism as
  everything else in `geodesy_store` (§32) instead of needing a bespoke
  overwrite path.
- **`climatology_min_years=2` is canvod-gnssgeodesy's own engineering
  judgment, stated as such, not a literature citation** — confirmed by
  Pass 2 that the literature is silent on this exact number. The
  motivating logic, made explicit per the user's own framing: a
  climatology fundamentally requires observing more than one annual
  cycle to mean anything — with only one year of data, "the climatology"
  is numerically identical to that year's own raw record, so there is
  nothing independent to average over and no way to separate a genuinely
  typical dry state from that particular year's weather. Two years is the
  floor at which the concept stops being vacuous, not a number chosen for
  additional statistical comfort beyond that.
- **Explicit stub, not implemented in v1:** how a mature (Tier 2)
  station's climatology should ever be revisited as decades of data
  accumulate is an open, deliberately deferred question — most likely a
  periodically-revised moving/rolling window (in the spirit of
  meteorological climate-normal revisions), but the cadence, overlap
  handling, and how to avoid retroactively rewriting already-published
  `NMRI` are all unresolved. `code_multipath.py` raises
  `NotImplementedError` rather than guessing; only a manual `baseline_from`
  change is supported, same as the initial Tier 1→2 transition. This is
  distinct from the already-documented hardware-discontinuity handling
  (§6 step 8) — that's a required era-split on a known event, not a
  moving-window problem.

`PLAN.md` updated: §6 step 8 (pointer to this policy, hardware-
discontinuity note distinguished from the deferred stub), §10
(`write_or_append_geodesy_group()`'s per-day-independence requirement,
full two-tier policy, the stub), §11 (`NmriStrategyConfig.
climatology_min_years`, `baseline_from`'s docstring rewritten to match).
