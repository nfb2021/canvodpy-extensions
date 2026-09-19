"""Provenance metadata attached to every canvod-gnssgeodesy retrieval output.

Follows the same idiom as `canvod-adapters/src/canvod/adapters/gnssvod/
provenance.py` (small pure function, dict of attrs, a `_package_version`
helper that never raises, an optional `timestamp` override) — not a copy
of its specific field names, which serve a different purpose
(bidirectional format-conversion attribution, not retrieval-algorithm
attribution).
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from importlib import metadata as importlib_metadata
from typing import Any, Literal

from pydantic import BaseModel

Product = Literal["rh", "nmri", "receiver_multipath"]

_RETRIEVAL_ALGORITHM: dict[Product, str] = {
    "rh": "lomb_scargle_snr_multipath",
    "nmri": "mp1_code_multipath_nmri",
    "receiver_multipath": "sbf_firmware_multipath",
}

_RETRIEVAL_PAPER_REFERENCE: dict[Product, str] = {
    "rh": "Larson et al., various -- GNSS-IR reflector height",
    "nmri": "Larson & Small 2014 (IEEE JSTARS); Small, Larson & Smith 2014",
    "receiver_multipath": "n/a (receiver firmware estimate)",
}


def _package_version(name: str) -> str:
    """Resolve an installed package's version, or "unknown" if unavailable.

    Must never raise — a caller may run in an environment where an
    optional dependency (e.g. `gnssrefl`) isn't installed.
    """
    try:
        return importlib_metadata.version(name)
    except importlib_metadata.PackageNotFoundError:
        return "unknown"


def _strategy_config_hash(strategy_config: BaseModel) -> str:
    """Deterministic hash of a strategy config's serialized field values.

    Algorithm name + package version alone are not reproducible when
    every threshold (elevation mask, baseline fraction, ...) is
    independently configurable — this hash lets two outputs be compared
    for "were these produced with the exact same settings" without
    diffing every field by hand.
    """
    canonical = strategy_config.model_dump_json(exclude_none=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_provenance_attrs(
    product: Product,
    station: str,
    strategy_config: BaseModel,
    *,
    timestamp: datetime | None = None,
) -> dict[str, Any]:
    """Build the global-attrs dict recording a retrieval's provenance.

    Parameters
    ----------
    product : {"rh", "nmri", "receiver_multipath"}
        Which product this output is.
    station : str
        Station identifier.
    strategy_config : BaseModel
        The `*StrategyConfig` instance the run actually used — hashed
        into `strategy_config_hash` below.
    timestamp : datetime, optional
        UTC timestamp to record. Defaults to now.

    Returns
    -------
    dict
        Attrs to merge into the output dataset via `ds.attrs.update(...)`.
    """
    return {
        "retrieval_algorithm": _RETRIEVAL_ALGORITHM[product],
        "retrieval_paper_reference": _RETRIEVAL_PAPER_REFERENCE[product],
        "canvod_gnssgeodesy_version": _package_version("canvod-gnssgeodesy"),
        "retrieval_timestamp": (timestamp or datetime.now(UTC)).isoformat(),
        "station": station,
        "strategy_config_hash": _strategy_config_hash(strategy_config),
    }
