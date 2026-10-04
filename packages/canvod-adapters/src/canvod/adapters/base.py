"""Interfaces of the adapters, one per kind of data canvodpy exchanges.

A tool implements the interfaces of the data it exchanges with canvodpy,
and only those. Everything entering canvodpy is checked against
canvodpy's own contract for that kind of data:

- observations: :func:`canvod.readers.validate_dataset`, the contract of
  every canvodpy reader. Observations are imported with a reader of the
  tool's files, a :class:`canvod.readers.GNSSDataReader`.
- VOD: :func:`canvod.readers.validate_vod_dataset`, the contract of VOD
  calculator output and of the VOD store.

A subclass converts; checking the result and recording provenance is done
here, the same for every tool.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar

import xarray as xr
from canvod.adapters.provenance import Provenance, Tool
from canvod.readers import GNSSDataReader, validate_dataset, validate_vod_dataset
from pydantic import BaseModel, ConfigDict


class _Adapter(BaseModel):
    """Settings of an adapter; a subclass adds the tool's own fields."""

    model_config = ConfigDict(frozen=True)

    #: The tool this adapter converts from and to.
    tool: ClassVar[Tool]


class ObservationsAdapter(_Adapter, ABC):
    """Observations: the tool's observation files <-> canvodpy observations."""

    @abstractmethod
    def reader(self, path: Path) -> GNSSDataReader:
        """A canvodpy reader of one of the tool's observation files."""

    @abstractmethod
    def convert_from_canvodpy(self, obs_ds: xr.Dataset) -> xr.Dataset:
        """canvodpy observations in the tool's data structure."""

    @abstractmethod
    def save(self, tool_ds: xr.Dataset, path: Path) -> None:
        """Write a dataset in the tool's data structure to its file format."""

    def import_file(self, path: Path | str, keep_data_vars: list[str] | None = None) -> xr.Dataset:
        """Read one of the tool's observation files as canvodpy observations.

        Parameters
        ----------
        path : Path or str
            The tool's observation file.
        keep_data_vars : list of str, optional
            Data variables to keep and require; ``None`` keeps all and
            requires ``SNR`` (:func:`canvod.readers.validate_dataset`).

        Returns
        -------
        xarray.Dataset
            canvodpy observations with provenance attributes.

        Raises
        ------
        ValueError
            If the result does not meet the observations contract.
        """
        path = Path(path)
        ds = self.reader(path).to_ds(keep_data_vars=keep_data_vars)
        ds.attrs.update(Provenance.now(self.tool, "import", path.name).to_attrs())
        validate_dataset(ds, required_vars=keep_data_vars)
        return ds

    def export_file(self, obs_ds: xr.Dataset, path: Path | str, source: str) -> Path:
        """Write canvodpy observations as one of the tool's files.

        Parameters
        ----------
        obs_ds : xarray.Dataset
            canvodpy observations.
        path : Path or str
            File to write.
        source : str
            What ``obs_ds`` is, recorded as provenance (e.g. a store group).

        Returns
        -------
        Path
            ``path``.
        """
        path = Path(path)
        tool_ds = self.convert_from_canvodpy(obs_ds)
        tool_ds.attrs.update(Provenance.now(self.tool, "export", source).to_attrs())
        self.save(tool_ds, path)
        return path


class VodAdapter(_Adapter, ABC):
    """VOD: the tool's VOD files <-> canvodpy VOD."""

    @abstractmethod
    def open(self, path: Path) -> xr.Dataset:
        """Read one of the tool's VOD files in its own data structure."""

    @abstractmethod
    def save(self, tool_ds: xr.Dataset, path: Path) -> None:
        """Write a dataset in the tool's data structure to its file format."""

    @abstractmethod
    def convert_to_canvodpy(self, tool_ds: xr.Dataset) -> xr.Dataset:
        """VOD in the tool's data structure as canvodpy VOD."""

    @abstractmethod
    def convert_from_canvodpy(self, vod_ds: xr.Dataset) -> xr.Dataset:
        """canvodpy VOD in the tool's data structure."""

    def import_dataset(self, tool_ds: xr.Dataset, source: str) -> xr.Dataset:
        """The tool's VOD as canvodpy VOD.

        Parameters
        ----------
        tool_ds : xarray.Dataset
            VOD in the tool's data structure.
        source : str
            What ``tool_ds`` is, recorded as provenance (e.g. a file name).

        Returns
        -------
        xarray.Dataset
            canvodpy VOD with provenance attributes.

        Raises
        ------
        ValueError
            If the result does not meet the VOD dataset contract.
        """
        ds = self.convert_to_canvodpy(tool_ds)
        ds.attrs.update(Provenance.now(self.tool, "import", source).to_attrs())
        validate_vod_dataset(ds)
        return ds

    def import_file(self, path: Path | str) -> xr.Dataset:
        """Read one of the tool's VOD files as canvodpy VOD.

        See :meth:`import_dataset`.
        """
        path = Path(path)
        return self.import_dataset(self.open(path), source=path.name)

    def export_dataset(self, vod_ds: xr.Dataset, source: str) -> xr.Dataset:
        """canvodpy VOD in the tool's data structure, with provenance.

        Parameters
        ----------
        vod_ds : xarray.Dataset
            canvodpy VOD.
        source : str
            What ``vod_ds`` is, recorded as provenance (e.g. a store group).
        """
        tool_ds = self.convert_from_canvodpy(vod_ds)
        tool_ds.attrs.update(Provenance.now(self.tool, "export", source).to_attrs())
        return tool_ds

    def export_file(self, vod_ds: xr.Dataset, path: Path | str, source: str) -> Path:
        """Write canvodpy VOD as one of the tool's VOD files.

        See :meth:`export_dataset`. Returns ``path``.
        """
        path = Path(path)
        self.save(self.export_dataset(vod_ds, source), path)
        return path
