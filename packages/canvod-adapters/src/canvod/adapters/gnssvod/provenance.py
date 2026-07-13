"""Provenance metadata attached to every canvodpy <-> gnssvod conversion."""

from __future__ import annotations

from datetime import UTC, datetime
from importlib import metadata as importlib_metadata
from typing import Any, Literal

#: canvodpy's own repository URL.
CANVODPY_URL = "https://github.com/nfb2021/canvodpy"

#: gnssvod (Humphrey et al.) repository URL — verified against its own
#: pyproject.toml [project.urls] "Source" entry and git remote.
GNSSVOD_URL = "https://github.com/vincenthumphrey/gnssvod"

Direction = Literal["canvodpy_to_gnssvod", "gnssvod_to_canvodpy"]


def _package_version(name: str) -> str:
    """Resolve an installed package's version, or "unknown" if unavailable.

    Conversions may run in an environment that only has one side of the
    conversion installed (e.g. a pure gnssvod environment converting *to*
    canvodpy format) — this must never raise.
    """
    try:
        return importlib_metadata.version(name)
    except importlib_metadata.PackageNotFoundError:
        return "unknown"


def build_provenance_attrs(
    direction: Direction,
    analysis_name: str,
    *,
    timestamp: datetime | None = None,
) -> dict[str, Any]:
    """Build the global-attrs dict recording a conversion's provenance.

    Parameters
    ----------
    direction : {"canvodpy_to_gnssvod", "gnssvod_to_canvodpy"}
        Which way the conversion ran.
    analysis_name : str
        The canvodpy VOD analysis name (e.g. ``"canopy_01_vs_reference_01"``)
        this dataset corresponds to.
    timestamp : datetime, optional
        UTC timestamp to record. Defaults to now — pass an explicit value
        for reproducible/deterministic callers (e.g. tests, replay tooling).

    Returns
    -------
    dict
        Attrs to merge into the converted dataset via ``ds.attrs.update(...)``.
    """
    if direction == "canvodpy_to_gnssvod":
        source_name, source_url = "canvodpy", CANVODPY_URL
    elif direction == "gnssvod_to_canvodpy":
        source_name, source_url = "gnssvod", GNSSVOD_URL
    else:
        raise ValueError(
            f"direction must be 'canvodpy_to_gnssvod' or 'gnssvod_to_canvodpy', got {direction!r}"
        )

    ts = timestamp or datetime.now(UTC)

    return {
        "conversion_source": source_name,
        "conversion_source_url": source_url,
        "conversion_source_version": _package_version(source_name),
        "conversion_tool": "canvod-adapters.gnssvod",
        "conversion_tool_version": _package_version("canvod-adapters"),
        "conversion_direction": direction,
        "conversion_timestamp": ts.isoformat(),
        "analysis_name": analysis_name,
    }
