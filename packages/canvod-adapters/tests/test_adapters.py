"""Tests for the adapter interfaces, provenance and the gnssvod adapters."""

from pathlib import Path

import numpy as np
import pytest
import xarray as xr
from canvod.adapters import Provenance, Tool, VodAdapter
from canvod.adapters.gnssvod import (
    GNSSVOD,
    GnssvodObservations,
    GnssvodObsReader,
    GnssvodVod,
    to_gnssvod_observations,
    to_gnssvod_vod,
)
from canvod.adapters.provenance import NOT_INSTALLED
from canvod.readers import validate_dataset, validate_vod_dataset
from canvod.utils.tools import file_hash
from pydantic import ValidationError

BANDS = {"VOD_L1": ["S1C", "S1W"], "VOD_L2": ["S2W"]}


@pytest.fixture
def gnssvod_vod_file(vod_ds, tmp_path) -> Path:
    path = tmp_path / "vod.nc"
    to_gnssvod_vod(vod_ds, BANDS).to_netcdf(path)
    return path


@pytest.fixture
def gnssvod_obs_file(obs_ds, tmp_path) -> Path:
    path = tmp_path / "obs.nc"
    to_gnssvod_observations(obs_ds).to_netcdf(path)
    return path


class TestProvenance:
    def test_now_records_tool_and_versions(self):
        prov = Provenance.now(GNSSVOD, "import", "vod.nc")

        assert prov.tool == "gnssvod"
        assert prov.tool_url == GNSSVOD.url
        # gnssvod is not a dependency: its absence is recorded, not an error
        assert prov.tool_version == NOT_INSTALLED
        assert prov.adapter_version != NOT_INSTALLED

    def test_attrs_round_trip(self):
        prov = Provenance.now(GNSSVOD, "export", "tau_omega/a")
        attrs = prov.to_attrs()

        assert all(key.startswith("conversion_") for key in attrs)
        assert Provenance.from_attrs({**attrs, "other": 1}) == prov

    def test_incomplete_attrs_raise(self):
        attrs = Provenance.now(GNSSVOD, "import", "x").to_attrs()
        del attrs["conversion_direction"]
        with pytest.raises(ValidationError):
            Provenance.from_attrs(attrs)

    def test_unknown_direction_raises(self):
        with pytest.raises(ValidationError):
            Provenance.now(GNSSVOD, "sideways", "x")  # ty: ignore[invalid-argument-type]


class TestInterfaces:
    def test_incomplete_adapter_cannot_be_created(self):
        class HalfAdapter(VodAdapter):
            tool = Tool(name="half", distribution="half", url="https://example.org")

            def open(self, path):
                return xr.Dataset()

        with pytest.raises(TypeError, match="abstract"):
            HalfAdapter()  # ty: ignore[call-non-callable]

    def test_import_is_checked_whatever_the_adapter_returns(self, gnssvod_vod_file):
        """The interface checks the contract, not the tool's conversion."""

        class SloppyAdapter(GnssvodVod):
            def convert_to_canvodpy(self, tool_ds):
                return tool_ds  # still gnssvod-shaped

        with pytest.raises(ValueError, match="VOD dataset validation failed"):
            SloppyAdapter(bands=BANDS).import_file(gnssvod_vod_file)

    def test_settings_are_frozen(self):
        adapter = GnssvodVod(bands=BANDS)
        with pytest.raises(ValidationError):
            adapter.bands = {}  # ty: ignore[invalid-assignment]


class TestGnssvodVodSettings:
    @pytest.mark.parametrize(
        ("bands", "match"),
        [
            ({}, "bands is empty"),
            ({"VOD_L1": []}, "has no observation codes"),
            ({"VOD_L1": ["C1C"]}, "not a signal-strength observation code"),
            ({"VOD_L1": ["S3C"]}, "not a signal-strength observation code"),
            ({"VOD_X": ["S1C", "S2W"]}, "different frequencies"),
            ({"A": ["S1C", "S1W"], "B": ["S1", "S1X"]}, "same signals"),
        ],
    )
    def test_bad_bands_raise(self, bands, match):
        with pytest.raises(ValidationError, match=match):
            GnssvodVod(bands=bands)

    def test_rinex2_codes_are_accepted(self):
        GnssvodVod(bands={"VOD_L1": ["S1"], "VOD_L2": ["S2"]})


class TestGnssvodVod:
    def test_import_meets_the_contract_with_provenance(self, gnssvod_vod_file):
        vod = GnssvodVod(bands=BANDS).import_file(gnssvod_vod_file)

        validate_vod_dataset(vod)
        assert set(vod["sid"].values) == {
            "E05|E1|u",
            "G01|L1|u",
            "G02|L1|u",
            "G01|L2|W",
            "G02|L2|W",
        }
        prov = Provenance.from_attrs(vod.attrs)
        assert (prov.tool, prov.direction, prov.source) == ("gnssvod", "import", "vod.nc")

    def test_export_round_trip(self, vod_ds, tmp_path):
        adapter = GnssvodVod(bands={"VOD_L2": ["S2W"]})
        path = adapter.export_file(vod_ds, tmp_path / "out.nc", source="tau_omega/a")
        back = adapter.import_file(path)

        np.testing.assert_allclose(
            back["VOD"].values, vod_ds["VOD"].sel(sid=back["sid"].values).values
        )
        with xr.open_dataset(path) as exported:
            assert Provenance.from_attrs(exported.attrs).direction == "export"

    def test_import_export_returns_the_file(self, gnssvod_vod_file, tmp_path):
        """Merged bands come in with the marker sids and go out unchanged."""
        adapter = GnssvodVod(bands=BANDS)
        path = adapter.export_file(
            adapter.import_file(gnssvod_vod_file), tmp_path / "again.nc", source="x"
        )

        with xr.open_dataset(gnssvod_vod_file) as original, xr.open_dataset(path) as again:
            for band in BANDS:
                a, b = xr.align(original[band], again[band], join="outer")
                np.testing.assert_allclose(a.values, b.values)

    def test_file_without_angles_is_rejected(self, vod_ds, tmp_path):
        path = tmp_path / "no_angles.nc"
        to_gnssvod_vod(vod_ds, BANDS).drop_vars(["Azimuth", "Elevation"]).to_netcdf(path)
        with pytest.raises(ValueError, match="theta"):
            GnssvodVod(bands=BANDS).import_file(path)


class TestGnssvodObservations:
    def test_import_meets_the_reader_contract(self, obs_ds, gnssvod_obs_file):
        obs = GnssvodObservations(time_system="GPS").import_file(gnssvod_obs_file)

        validate_dataset(obs)
        assert obs.attrs["File Hash"] == file_hash(gnssvod_obs_file)
        assert obs["epoch"].attrs["time_system"] == "GPS"
        assert Provenance.from_attrs(obs.attrs).source == "obs.nc"
        np.testing.assert_allclose(
            obs["SNR"].values, obs_ds["SNR"].sel(sid=obs["sid"].values).values
        )

    def test_keep_data_vars(self, gnssvod_obs_file):
        obs = GnssvodObservations(time_system="GPS").import_file(
            gnssvod_obs_file, keep_data_vars=["SNR"]
        )
        assert set(obs.data_vars) == {"SNR"}

    def test_file_without_snr_is_rejected(self, obs_ds, tmp_path):
        path = tmp_path / "no_snr.nc"
        to_gnssvod_observations(obs_ds.drop_vars("SNR")).to_netcdf(path)
        with pytest.raises(ValueError, match="SNR"):
            GnssvodObservations(time_system="GPS").import_file(path)

    def test_time_system_is_required(self):
        with pytest.raises(ValidationError, match="time_system"):
            GnssvodObservations()  # ty: ignore[missing-argument]

    def test_unknown_time_system_raises(self, gnssvod_obs_file):
        with pytest.raises(ValueError, match="unknown epoch time system"):
            GnssvodObservations(time_system="MARS").import_file(gnssvod_obs_file)

    def test_export_round_trip(self, obs_ds, tmp_path):
        adapter = GnssvodObservations(time_system="GPS")
        path = adapter.export_file(obs_ds, tmp_path / "out.nc", source="canopy_01")
        back = adapter.import_file(path)

        np.testing.assert_allclose(
            back["Pseudorange"].values,
            obs_ds["Pseudorange"].sel(sid=back["sid"].values).values,
        )


class TestGnssvodObsReader:
    def test_reader_properties(self, obs_ds, gnssvod_obs_file):
        reader = GnssvodObsReader(fpath=gnssvod_obs_file, time_system="GPS")

        assert reader.source_format == "gnssvod"
        assert reader.systems == ["E", "G"]
        assert reader.num_satellites == 3
        assert reader.num_epochs == obs_ds.sizes["epoch"]
        assert np.datetime64(reader.start_time) == obs_ds["epoch"].values[0]
        assert np.datetime64(reader.end_time) == obs_ds["epoch"].values[-1]
        assert sum(1 for _ in reader.iter_epochs()) == obs_ds.sizes["epoch"]

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            GnssvodObsReader(fpath=tmp_path / "missing.nc", time_system="GPS")
