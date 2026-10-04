"""Adapters between canvodpy and gnssvod (Humphrey et al.)."""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

import xarray as xr
from canvod.adapters.base import ObservationsAdapter, VodAdapter
from canvod.adapters.gnssvod.convert import (
    from_gnssvod_vod,
    to_gnssvod_observations,
    to_gnssvod_vod,
)
from canvod.adapters.gnssvod.reader import GnssvodObsReader
from canvod.adapters.provenance import Tool
from pydantic import field_validator

GNSSVOD = Tool(
    name="gnssvod",
    distribution="gnssvod",
    url="https://github.com/vincenthumphrey/gnssvod",
)

#: Carrier frequency digits of RINEX observation codes.
_FREQUENCY_DIGITS = frozenset("12456789")


def _netcdf(path: Path) -> xr.Dataset:
    with xr.open_dataset(path) as ds:
        return ds.load()


class GnssvodObservations(ObservationsAdapter):
    """gnssvod observation files <-> canvodpy observations.

    Parameters
    ----------
    time_system : str
        Time scale of the epochs of the gnssvod files to import, as in the
        RINEX files they came from (e.g. ``"GPS"``); see
        :class:`~canvod.adapters.gnssvod.reader.GnssvodObsReader`.

    Examples
    --------
    >>> adapter = GnssvodObservations(time_system="GPS")
    >>> obs = adapter.import_file("ROSA_obs.nc")
    >>> adapter.export_file(obs, "back_obs.nc", source="ROSA_obs.nc")
    """

    tool: ClassVar[Tool] = GNSSVOD

    time_system: str

    def reader(self, path: Path) -> GnssvodObsReader:
        return GnssvodObsReader(fpath=path, time_system=self.time_system)

    def convert_from_canvodpy(self, obs_ds: xr.Dataset) -> xr.Dataset:
        return to_gnssvod_observations(obs_ds)

    def save(self, tool_ds: xr.Dataset, path: Path) -> None:
        tool_ds.to_netcdf(path)


class GnssvodVod(VodAdapter):
    """gnssvod VOD files <-> canvodpy VOD.

    A gnssvod VOD file is the result of ``gnssvod.calc_vod`` for one
    station pair (``DataFrame.to_xarray()``) written as NetCDF: dims
    ``Epoch``, ``SV``, one variable per band, ``Azimuth``/``Elevation``.

    Parameters
    ----------
    bands : dict[str, list[str]]
        gnssvod's ``bands`` argument: band variable to the signal-strength
        observation codes ``calc_vod`` merges into it, e.g.
        ``{"VOD_L1": ["S1C", "S1W"], "VOD_L2": ["S2W"]}``. Importing gives
        each band's VOD the sids of its code if the band has one code
        (``"S2W"`` -> ``"G01|L2|W"``), and of its RINEX 2 form if it merges
        several (``"S1"`` -> ``"G01|L1|u"``, canvodpy's marker for a band
        whose tracking code is not known). Exporting merges canvodpy's VOD
        the same way as ``calc_vod``, a merged band also taking the sids
        an import gives it, so imported VOD exports unchanged.

    Notes
    -----
    ``calc_vod`` reports the reference receiver's ``Azimuth``/
    ``Elevation``; canvodpy reports the canopy receiver's. Imported VOD
    keeps gnssvod's angles.

    Examples
    --------
    >>> adapter = GnssvodVod(bands={"VOD_L1": ["S1C", "S1W"]})
    >>> vod = adapter.import_file("vod_canopy_vs_reference.nc")
    """

    tool: ClassVar[Tool] = GNSSVOD

    bands: dict[str, list[str]]

    @field_validator("bands")
    @classmethod
    def _check_bands(cls, bands: dict[str, list[str]]) -> dict[str, list[str]]:
        if not bands:
            raise ValueError("bands is empty")
        for band, codes in bands.items():
            if not codes:
                raise ValueError(f"band {band!r} has no observation codes")
            for code in codes:
                if len(code) not in (2, 3) or code[0] != "S" or code[1] not in _FREQUENCY_DIGITS:
                    raise ValueError(
                        f"band {band!r}: {code!r} is not a signal-strength "
                        "observation code (e.g. 'S1C', or 'S1' in RINEX 2)"
                    )
            if len({code[1] for code in codes}) > 1:
                raise ValueError(f"band {band!r} merges codes of different frequencies: {codes}")
        imported = [cls._import_code(codes) for codes in bands.values()]
        if len(set(imported)) < len(imported):
            raise ValueError(
                f"two bands would import to the same signals: {dict(zip(bands, imported, strict=True))}"
            )
        return bands

    @staticmethod
    def _import_code(codes: list[str]) -> str:
        """Observation code the sids of an imported band get."""
        return codes[0] if len(codes) == 1 else codes[0][:2]

    def open(self, path: Path) -> xr.Dataset:
        return _netcdf(path)

    def save(self, tool_ds: xr.Dataset, path: Path) -> None:
        tool_ds.to_netcdf(path)

    def convert_to_canvodpy(self, tool_ds: xr.Dataset) -> xr.Dataset:
        return from_gnssvod_vod(
            tool_ds,
            {band: self._import_code(codes) for band, codes in self.bands.items()},
        )

    def convert_from_canvodpy(self, vod_ds: xr.Dataset) -> xr.Dataset:
        # A merged band also takes the sids an import gives it ("S1" ->
        # "G01|L1|u"), so imported VOD exports as it came in
        bands = {
            band: sorted({*codes, self._import_code(codes)}) for band, codes in self.bands.items()
        }
        return to_gnssvod_vod(vod_ds, bands)
