"""Pydantic strategy configs for canvod-gnssgeodesy.

`_StrictModel` is defined locally, not imported from `canvod-config`'s
own private equivalent — that would add a hard `canvod-*` runtime
dependency this package otherwise doesn't need (both `canvod-filemap`
and `canvod-adapters` deliberately avoid this too).
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from canvod.gnssgeodesy.arcs import DEFAULT_TRACKING_CODES
from pydantic import BaseModel, ConfigDict, Field, model_validator


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


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
        "{'L1': 'C', 'L2': 'W'} — override explicitly per station if the receiver "
        "reports a different L2 code (e.g. {'L2': 'L'} for L2C-only receivers, "
        "common on current hardware). Never auto-detected: an unmatched code fails "
        "loud (tracking_codes_resolved=False on output), not a silent per-file "
        "fallback.",
    )
    constellations: list[str] = Field(
        ["G"],
        description="Constellations to include; v1 GPS-only for code_multipath — "
        "enforced by get_alpha_calibration() raising NotImplementedError for "
        "unregistered constellations, not a hardcoded restriction on this field",
    )

    @model_validator(mode="after")
    def _check_elev_order(self) -> ArcStrategyConfig:
        if self.min_elev_deg >= self.max_elev_deg:
            raise ValueError("min_elev_deg must be < max_elev_deg")
        return self


class RhStrategyConfig(ArcStrategyConfig):
    # Field defaults below are gnssrefl's own hardcoded values, read directly
    # from gnssrefl/gnssir_input.py's make_gnssir_input() signature — this is
    # what makes the "gnssrefl" named strategy an actual default rather than a
    # principle. Still overridable per-station via YAML exactly as gnssrefl
    # itself allows (these are its fallback constants, not station-specific
    # truth).
    min_elev_deg: float = Field(
        5.0, description="Minimum elevation angle, degrees (gnssrefl e1 default)"
    )
    max_elev_deg: float = Field(
        25.0, description="Maximum elevation angle, degrees (gnssrefl e2 default)"
    )
    min_height_m: float = Field(
        0.5, description="RH search lower bound, metres (gnssrefl h1 default)"
    )
    max_height_m: float = Field(
        8.0, description="RH search upper bound, metres (gnssrefl h2 default)"
    )
    desired_precision_m: float = Field(
        0.005, description="Target RH precision, metres (gnssrefl desiredP default)"
    )
    noise_region_m: tuple[float, float] = Field(
        ...,
        description="RH range used to estimate periodogram noise floor — gnssrefl's "
        "nr1/nr2 have NO default (None unless station-supplied); do not invent one, "
        "require it explicitly",
    )
    peak2noise_min: float = Field(
        2.8,
        description="Minimum peak-to-noise ratio to accept an arc (gnssrefl peak2noise default)",
    )
    req_amp_min: float = Field(
        5.0,
        description="Minimum periodogram amplitude to accept an arc (gnssrefl ampl/reqAmp default)",
    )
    delT_max_min: float = Field(
        75.0, description="Maximum arc duration, minutes (gnssrefl delTmax default)"
    )
    ediff_deg: float = Field(
        2.0, description="Elevation-range compliance tolerance, degrees (gnssrefl ediff default)"
    )
    detrend_window_deg: tuple[float, float] = Field(
        (5.0, 30.0),
        description="DC-removal/detrend elevation window, degrees (gnssrefl pele default "
        "[5,30] — NOT the same range as min_elev_deg/max_elev_deg, gnssrefl keeps these "
        "two windows distinct)",
    )
    detrend_poly_order: int = Field(
        4, description="Detrend polynomial order (gnssrefl polyV default)"
    )
    lsp_backend: Literal["astropy", "scipy"] = Field(
        "astropy",
        description="Named after the actual library, not gnssrefl's internal "
        "'fast'/'scipy' shorthand for the same choice. Translated to gnssrefl's own "
        "lsp_method='fast'/'scipy' argument at the GnssreflRhComputer call site — "
        "canvod-gnssgeodesy never calls astropy or scipy directly itself, this only "
        "selects which one gnssrefl uses internally. 'astropy' matches gnssrefl's own "
        "default ('fast').",
    )

    @model_validator(mode="after")
    def _check_height_order(self) -> RhStrategyConfig:
        if self.min_height_m >= self.max_height_m:
            raise ValueError("min_height_m must be < max_height_m")
        return self


class RefractionMethod(StrEnum):
    """Named replacement for gnssrefl's numeric refr_model (1-6, see
    gnssrefl/gnssir_input.py:546-566). gnssrefl itself already accepts the
    strings "NITE"/"MPF" for models 5/6 but not names for models 1-4 —
    this extends that same idea uniformly across all four methods it
    implements."""

    BENNETT = "bennett"  # gnssrefl models 1 (static) / 2 (time-varying)
    ULICH = "ulich"  # gnssrefl models 3 (static) / 4 (time-varying)
    NITE = "nite"  # gnssrefl model 5 (Peng 2023) — always time-varying
    MPF = "mpf"  # gnssrefl model 6 (Williams & Nievinski 2017 / Strandberg 2020) — always time-varying


_GNSSREFL_MODEL_ID: dict[tuple[RefractionMethod, bool], int] = {
    (RefractionMethod.BENNETT, False): 1,
    (RefractionMethod.BENNETT, True): 2,
    (RefractionMethod.ULICH, False): 3,
    (RefractionMethod.ULICH, True): 4,
    (RefractionMethod.NITE, True): 5,
    (RefractionMethod.MPF, True): 6,
}


class RefractionStrategyConfig(_StrictModel):
    enabled: bool = Field(
        True, description="Apply refraction correction at all (False == gnssrefl refr_model=0)"
    )
    method: RefractionMethod = Field(
        RefractionMethod.BENNETT, description="Correction model (gnssrefl refr_model, named)"
    )
    time_varying: bool = Field(
        False,
        description="Annual+semiannual harmonic term evaluated from the static grid "
        "(gnssrefl's 'it' flag); NITE/MPF force this True in gnssrefl, there is no "
        "static variant of either",
    )
    apriori_rh_m: float = Field(
        5.0,
        description="A-priori reflector height guess for NITE/MPF's equivalent-angle "
        "geometry term (gnssrefl apriori_rh default — gnssrefl silently falls back to "
        "5.0 if unset, so this mirrors that as an explicit default rather than "
        "inventing a different one)",
    )

    @model_validator(mode="after")
    def _check_gnssrefl_model_id(self) -> RefractionStrategyConfig:
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
    # implements NMRI in code, so there is no "gnssrefl default" to source
    # for this class the way RhStrategyConfig has one.
    #
    # min_elev_deg/max_elev_deg here are NOT gnssrefl's RH e1/e2 (5,25) —
    # the code/pseudorange-multipath literature (Larson & Small 2014 and
    # the classic teqc MP1 convention) commonly uses a ~10-15° mask
    # instead. Do not silently borrow RhStrategyConfig's 5.0/25.0, they
    # are a different module's numbers. Both fields resolve, when None,
    # against the active constellation's AlphaCalibration entry
    # (code_multipath.py) — same pattern and same AlphaCalibration entry
    # as baseline_top_fraction below, for consistency.
    min_elev_deg: float | None = Field(
        None,
        description="Minimum elevation angle, degrees. None = fall back to the active "
        "constellation's AlphaCalibration.elevation_mask_deg[0] (10.0 for GPS) — an "
        "explicit value here always overrides the literature-sourced default, same "
        "resolution point and same rule as baseline_top_fraction below.",
    )
    max_elev_deg: float | None = Field(
        None,
        description="Maximum elevation angle, degrees. None = fall back to the active "
        "constellation's AlphaCalibration.elevation_mask_deg[1] (15.0 for GPS) — same "
        "resolution point and rule as min_elev_deg above.",
    )
    min_segment_epochs: int = Field(
        ..., description="Minimum slip-free segment length kept for MP1 mean removal"
    )
    baseline_top_fraction: float | None = Field(
        None,
        description="Fraction of driest days used for MP1max, evaluated per-sv. "
        "None = fall back to the active constellation's AlphaCalibration."
        "baseline_top_fraction (0.05 for GPS) — an explicit value here always "
        "overrides the literature-sourced default.",
    )
    climatology_min_years: int = Field(
        2,
        description="Minimum record span, in years, before a station may move from "
        "Tier 1 (entire-available-record baseline) to Tier 2 (frozen climatology "
        "window) — see io.py's baseline policy. 2 is canvod-gnssgeodesy's own "
        "engineering default, NOT a literature-sourced number (the literature is "
        "silent on this exact operational question) — it's the floor at which "
        "'climatology' stops being numerically identical to the raw record (a single "
        "year has nothing to average over). Exposed here, not hardcoded, so a station "
        "with an unusually weak/ambiguous seasonal contrast can be tuned without a "
        "code change.",
    )
    baseline_from: tuple[str, str] | None = Field(
        None,
        description="Explicit [start, end] climatology window (ISO dates). None "
        "(default) = Tier 1, use the entire available record so far (provisional, "
        "matches Larson & Small's literal one-time-retrospective definition — see "
        "io.py). Setting this is the only supported way to enter Tier 2; the "
        "transition is never automatic, even once climatology_min_years is exceeded "
        "(loud-not-silent). See io.py for the full two-tier policy and the explicit "
        "stub for revisiting a Tier 2 window later.",
    )
    outlier_mad_threshold: float = Field(
        3.0, description="MAD-based outlier threshold on daily MP1rms"
    )

    @model_validator(mode="after")
    def _check_elev_order(self) -> NmriStrategyConfig:
        # Overrides ArcStrategyConfig's own version of this check: min_elev_deg/
        # max_elev_deg are Optional here (resolved against AlphaCalibration at
        # code_multipath.py's entry point, not inside this model) — the base
        # class's unconditional `self.min_elev_deg >= self.max_elev_deg`
        # comparison would raise a TypeError comparing None to a float before
        # that resolution ever runs. Only enforce ordering when the caller
        # supplied both explicitly; a None/non-None mix is allowed (each
        # resolves independently) and checked again, non-Optional, right after
        # resolution in code_multipath.py.
        if self.min_elev_deg is not None and self.max_elev_deg is not None:
            if self.min_elev_deg >= self.max_elev_deg:
                raise ValueError("min_elev_deg must be < max_elev_deg")
        return self
