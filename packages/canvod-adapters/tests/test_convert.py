"""Tests for canvod.adapters.gnssvod.convert."""

import numpy as np
import pytest
import xarray as xr
from canvod.adapters.gnssvod.convert import (
    BAND_MAP,
    from_gnssvod_dataset,
    to_gnssvod_dataset,
)
from canvod.adapters.gnssvod.provenance import build_provenance_attrs


class TestToGnssvodDataset:
    def test_basic_conversion(self, vod_ds):
        out = to_gnssvod_dataset(vod_ds)

        assert set(out.dims) == {"epoch", "sid"}
        assert sorted(out.sid.values) == ["G01", "G02"]
        assert "Azimuth" in out.data_vars
        assert "Elevation" in out.data_vars
        assert "VOD1" in out.data_vars
        assert "VOD2" in out.data_vars
        assert "dSNR1" in out.data_vars
        assert "dSNR2" in out.data_vars
        # gnssvod columns, never renamed from delta_snr
        assert "S1C" not in out.data_vars
        assert "S2W" not in out.data_vars

    def test_azimuth_elevation_conversion(self, vod_ds):
        out = to_gnssvod_dataset(vod_ds)

        band1_sids = [s for s in vod_ds.sid.values if s.endswith("|L1|C")]
        sub = vod_ds.sel(sid=band1_sids)
        expected_az = np.degrees(sub["phi"].values) % 360.0
        expected_el = 90.0 - np.degrees(sub["theta"].values)

        np.testing.assert_allclose(out["Azimuth"].values, expected_az)
        np.testing.assert_allclose(out["Elevation"].values, expected_el)

    def test_duplicate_prn_per_band_raises(self, vod_ds):
        # Duplicate the exact same SID -- same PRN appears twice for band L1|C
        dup = vod_ds.copy()
        extra = dup.sel(sid=["G01|L1|C"])
        dup = xr.concat([dup, extra], dim="sid")

        with pytest.raises(ValueError, match="Duplicate PRNs"):
            to_gnssvod_dataset(dup, band_map=[("L1|C", "S1C", "VOD1")])

    def test_no_matching_band_raises(self, vod_ds):
        with pytest.raises(ValueError, match="No bands in band_map matched"):
            to_gnssvod_dataset(vod_ds, band_map=[("L5|Q", "S5Q", None)])


class TestFromGnssvodDataset:
    def test_round_trip_recovers_values(self, vod_ds):
        gnssvod_ds = to_gnssvod_dataset(vod_ds)
        recovered = from_gnssvod_dataset(gnssvod_ds)

        assert recovered.attrs["vod_reconstructed_code_ambiguous"] is True

        # Band L1|C round-trips through band_map's declared "C" code again,
        # so values (not necessarily the original SID) should match exactly.
        for band_suffix, _snr_col, vod_col in BAND_MAP:
            if vod_col is None:
                continue
            band_sids = [s for s in vod_ds.sid.values if s.endswith(f"|{band_suffix}")]
            if not band_sids:
                continue
            original = vod_ds.sel(sid=band_sids)
            recovered_band = recovered.sel(
                sid=[f"{s.split('|')[0]}|{band_suffix}" for s in band_sids]
            )
            np.testing.assert_allclose(recovered_band["VOD"].values, original["VOD"].values)
            np.testing.assert_allclose(
                recovered_band["phi"].values, original["phi"].values, atol=1e-9
            )
            np.testing.assert_allclose(
                recovered_band["theta"].values, original["theta"].values, atol=1e-9
            )

    def test_reconstructed_code_may_differ_from_original(self, vod_ds):
        # Original G01 L1 band uses code "C"; reconstruct declaring a
        # different primary code in band_map -- the placeholder SID should
        # reflect band_map's code, not the original observed code.
        gnssvod_ds = to_gnssvod_dataset(vod_ds, band_map=[("L1|C", "S1C", "VOD1")])
        recovered = from_gnssvod_dataset(gnssvod_ds, band_map=[("L1|X", "S1C", "VOD1")])
        assert all(str(s).endswith("|L1|X") for s in recovered.sid.values)

    def test_normalizes_epoch_sv_dims(self, vod_ds):
        gnssvod_ds = to_gnssvod_dataset(vod_ds).rename({"epoch": "Epoch", "sid": "SV"})
        recovered = from_gnssvod_dataset(gnssvod_ds)
        assert "epoch" in recovered.dims
        assert "sid" in recovered.dims

    def test_no_matching_vod_column_raises(self, vod_ds):
        gnssvod_ds = to_gnssvod_dataset(vod_ds)
        gnssvod_ds = gnssvod_ds.drop_vars(["VOD1", "VOD2"])
        with pytest.raises(ValueError, match="No VOD column"):
            from_gnssvod_dataset(gnssvod_ds)


class TestNetcdfRoundTrip:
    """Regression test: writing/reading NetCDF requires a real backend
    (h5netcdf+h5py) to be an installed dependency, not just xarray itself --
    caught during manual verification when the package initially declared
    only xarray/numpy/pandas and to_netcdf() failed with no backend found.
    """

    def test_to_netcdf_and_reopen(self, vod_ds, tmp_path):
        gnssvod_ds = to_gnssvod_dataset(vod_ds)
        gnssvod_ds.attrs.update(build_provenance_attrs("canvodpy_to_gnssvod", "roundtrip_test"))

        nc_path = tmp_path / "roundtrip.nc"
        gnssvod_ds.to_netcdf(nc_path)

        reopened = xr.open_dataset(nc_path)
        assert reopened.attrs["conversion_tool"] == "canvod-adapters.gnssvod"
        for var in ("Azimuth", "Elevation", "VOD1", "VOD2"):
            np.testing.assert_allclose(reopened[var].values, gnssvod_ds[var].values)

        recovered = from_gnssvod_dataset(reopened)
        assert recovered.attrs["vod_reconstructed_code_ambiguous"] is True


class TestProvenance:
    def test_canvodpy_to_gnssvod_direction(self):
        attrs = build_provenance_attrs("canvodpy_to_gnssvod", "canopy_01_vs_reference_01")
        assert attrs["conversion_source"] == "canvodpy"
        assert attrs["conversion_tool"] == "canvod-adapters.gnssvod"
        assert attrs["conversion_direction"] == "canvodpy_to_gnssvod"
        assert attrs["analysis_name"] == "canopy_01_vs_reference_01"
        assert "conversion_timestamp" in attrs

    def test_gnssvod_to_canvodpy_direction(self):
        attrs = build_provenance_attrs("gnssvod_to_canvodpy", "imported_analysis")
        assert attrs["conversion_source"] == "gnssvod"
        assert attrs["conversion_source_url"].endswith("vincenthumphrey/gnssvod")

    def test_invalid_direction_raises(self):
        with pytest.raises(ValueError, match="direction must be"):
            build_provenance_attrs("sideways", "x")  # ty: ignore[invalid-argument-type]
