"""canvod-gnssgeodesy: native GNSS geodetic products for canvodpy.

Reflectometry (reflector height), code/pseudorange multipath (MP1rms,
NMRI), and firmware-reported multipath diagnostics -- with tropospheric
products and PPP planned. GPL-3.0-only, see this package's README.md.
"""

from __future__ import annotations

try:
    from importlib.metadata import version as _version

    __version__ = _version("canvod-gnssgeodesy")
except Exception:  # pragma: no cover
    __version__ = "unknown"

__all__ = ["__version__"]
