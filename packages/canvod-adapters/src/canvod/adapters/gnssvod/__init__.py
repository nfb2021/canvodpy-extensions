"""Adapters between canvodpy and gnssvod (Humphrey et al.).

:class:`GnssvodObservations` and :class:`GnssvodVod` convert files;
the functions of :mod:`~canvod.adapters.gnssvod.convert` convert datasets
in memory, without the contract checks and provenance of the adapters.
"""

from canvod.adapters.gnssvod.adapter import GNSSVOD, GnssvodObservations, GnssvodVod
from canvod.adapters.gnssvod.convert import (
    OBS_TYPES,
    from_gnssvod_observations,
    from_gnssvod_vod,
    to_gnssvod_observations,
    to_gnssvod_vod,
)
from canvod.adapters.gnssvod.reader import GnssvodObsReader

__all__ = [
    "GNSSVOD",
    "OBS_TYPES",
    "GnssvodObsReader",
    "GnssvodObservations",
    "GnssvodVod",
    "from_gnssvod_observations",
    "from_gnssvod_vod",
    "to_gnssvod_observations",
    "to_gnssvod_vod",
]
