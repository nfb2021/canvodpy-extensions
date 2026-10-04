"""canvodpy reader of gnssvod observation files."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime
from functools import cached_property

import numpy as np
import xarray as xr
from canvod.adapters.gnssvod.convert import from_gnssvod_observations
from canvod.readers import GNSSDataReader, validate_dataset
from canvod.readers.gnss_specs.metadata import epoch_coord_attrs
from canvod.utils.tools import file_hash


class GnssvodObsReader(GNSSDataReader):
    """Reads the observation NetCDF files ``gnssvod.preprocess`` writes.

    A canvodpy reader like the RINEX and SBF readers: its datasets meet
    the reader contract (:func:`canvod.readers.validate_dataset`), carry
    the file hash for deduplication and the global attributes of every
    canvodpy reader.

    Parameters
    ----------
    fpath : Path
        gnssvod observation file (dims ``Epoch``, ``SV``).
    time_system : str
        Time scale of the file's epochs, which gnssvod keeps as in the
        RINEX file (its ``TIME OF FIRST OBS`` record), e.g. ``"GPS"``.
        Recorded on the epoch coordinate, like the other readers do.
    """

    time_system: str

    @property
    def source_format(self) -> str:
        return "gnssvod"

    @cached_property
    def _gnssvod_ds(self) -> xr.Dataset:
        with xr.open_dataset(self.fpath) as ds:
            return ds.load()

    @cached_property
    def _file_hash(self) -> str:
        return file_hash(self.fpath)

    @property
    def file_hash(self) -> str:
        return self._file_hash

    def to_ds(
        self,
        keep_data_vars: list[str] | None = None,
        **kwargs: object,
    ) -> xr.Dataset:
        """The file's observations as a canvodpy dataset.

        Parameters
        ----------
        keep_data_vars : list of str, optional
            Data variables to keep (e.g. ``["SNR"]``); ``None`` keeps all.
        **kwargs
            Not used; accepted for the reader interface.

        Raises
        ------
        ValueError
            If the result does not meet the reader contract.
        """
        ds = from_gnssvod_observations(self._gnssvod_ds)
        if keep_data_vars is not None:
            ds = ds[[v for v in keep_data_vars if v in ds.data_vars]]
        ds["epoch"].attrs.update(epoch_coord_attrs(self.time_system))
        ds.attrs.update(self._build_attrs())
        validate_dataset(ds, required_vars=keep_data_vars)
        return ds

    def iter_epochs(self) -> Iterator[xr.Dataset]:
        """The file's observations, one epoch at a time."""
        ds = self.to_ds()
        for i in range(ds.sizes["epoch"]):
            yield ds.isel(epoch=i)

    def _epochs(self) -> np.ndarray:
        return np.sort(self._gnssvod_ds["Epoch"].values)

    @property
    def start_time(self) -> datetime:
        return self._epochs()[0].astype("datetime64[us]").item()

    @property
    def end_time(self) -> datetime:
        return self._epochs()[-1].astype("datetime64[us]").item()

    @property
    def num_epochs(self) -> int:
        return int(self._gnssvod_ds.sizes["Epoch"])

    @property
    def systems(self) -> list[str]:
        return sorted({str(sv)[0] for sv in self._gnssvod_ds["SV"].values})

    @property
    def num_satellites(self) -> int:
        return int(self._gnssvod_ds.sizes["SV"])
