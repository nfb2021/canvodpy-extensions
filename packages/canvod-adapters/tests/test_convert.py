"""Tests for canvod.adapters.gnssvod.convert."""

import numpy as np
import pytest
import xarray as xr
from canvod.adapters.gnssvod.convert import (
    from_gnssvod_observations,
    from_gnssvod_vod,
    to_gnssvod_observations,
    to_gnssvod_vod,
)
from canvod.readers import validate_vod_dataset

BANDS = {"VOD_L1": ["S1C", "S1W"], "VOD_L2": ["S2W"], "VOD_E1": ["S1C"]}


class TestObservations:
    def test_codes_and_satellites(self, obs_ds):
        out = to_gnssvod_observations(obs_ds)

        assert set(out.dims) == {"Epoch", "SV"}
        assert list(out["SV"].values) == ["E05", "G01", "G02"]
        assert {"S1C", "S1W", "S2W", "S5Q", "C1C", "C5Q"} <= set(out.data_vars)
        np.testing.assert_array_equal(
            out["S5Q"].sel(SV="E05").values,
            obs_ds["SNR"].sel(sid="E05|E5a|Q").values,
        )
        # G02 has no L1|C
        assert np.all(np.isnan(out["S1C"].sel(SV="G02").values))

    def test_angles(self, obs_ds):
        out = to_gnssvod_observations(obs_ds)

        g01 = obs_ds.sel(sid="G01|L1|C")
        np.testing.assert_allclose(
            out["Elevation"].sel(SV="G01").values, 90.0 - np.degrees(g01["theta"].values)
        )
        np.testing.assert_allclose(
            out["Azimuth"].sel(SV="G01").values, np.degrees(g01["phi"].values) % 360.0
        )

    def test_round_trip(self, obs_ds):
        back = from_gnssvod_observations(to_gnssvod_observations(obs_ds))

        back = back.sel(sid=obs_ds["sid"].values)
        for name in ("SNR", "Pseudorange", "theta", "phi"):
            np.testing.assert_allclose(back[name].values, obs_ds[name].values)
        assert list(back["sv"].values) == list(obs_ds["sv"].values)

    def test_empty_sids_are_left_out(self, obs_ds):
        """canvodpy pads to a global sid set; RINEX 2 markers collide when empty."""
        padded = xr.concat(
            [
                obs_ds,
                obs_ds.isel(sid=[0, 1]).assign_coords(
                    sid=["G01|L1|p", "G01|L1|u"], sv=("sid", ["G01", "G01"])
                )
                * np.nan,
            ],
            dim="sid",
        )
        out = to_gnssvod_observations(padded)

        assert "S1" not in out.data_vars
        xr.testing.assert_identical(out, to_gnssvod_observations(obs_ds))

    def test_missing_sv_coordinate_raises(self, obs_ds):
        with pytest.raises(ValueError, match="'sv' coordinate"):
            to_gnssvod_observations(obs_ds.drop_vars("sv"))

    def test_two_sids_one_code_raises(self):
        """RINEX 2 P2 and C2 are both C2 in RINEX 3 terms."""
        ds = xr.Dataset(
            {"Pseudorange": (["epoch", "sid"], np.ones((1, 2)))},
            coords={
                "epoch": [np.datetime64("2025-01-01T00:00", "ns")],
                "sid": ["G01|L2|l", "G01|L2|p"],
                "sv": ("sid", ["G01", "G01"]),
            },
        )
        with pytest.raises(ValueError, match="both map to observation code 'C2'"):
            to_gnssvod_observations(ds)

    def test_rinex2_codes(self):
        """gnssvod's RINEX 2 columns map to the sids of canvodpy's v2 reader."""
        gnssvod_ds = xr.Dataset(
            {"S1": (["Epoch", "SV"], [[40.0, 41.0]]), "P2": (["Epoch", "SV"], [[2e7, 2e7]])},
            coords={"Epoch": [np.datetime64("2025-01-01T00:00", "ns")], "SV": ["G01", "R03"]},
        )
        out = from_gnssvod_observations(gnssvod_ds)

        assert set(out["sid"].values) == {"G01|L1|u", "G01|L2|p", "R03|G1|u", "R03|G2|P"}

    def test_data_for_a_band_the_system_lacks_raises(self):
        gnssvod_ds = xr.Dataset(
            {"S2W": (["Epoch", "SV"], [[40.0, 41.0]])},
            coords={"Epoch": [np.datetime64("2025-01-01T00:00", "ns")], "SV": ["G01", "E05"]},
        )
        with pytest.raises(ValueError):
            from_gnssvod_observations(gnssvod_ds)

    def test_empty_columns_get_no_sid(self):
        gnssvod_ds = xr.Dataset(
            {"S2W": (["Epoch", "SV"], [[40.0, np.nan]])},
            coords={"Epoch": [np.datetime64("2025-01-01T00:00", "ns")], "SV": ["G01", "E05"]},
        )
        out = from_gnssvod_observations(gnssvod_ds)

        assert list(out["sid"].values) == ["G01|L2|W"]

    def test_not_gnssvod_dims_raises(self, obs_ds):
        with pytest.raises(ValueError, match="Not a gnssvod dataset"):
            from_gnssvod_observations(obs_ds)


class TestVod:
    def test_bands_merge_like_calc_vod(self, vod_ds):
        """Codes merge in sorted order, each filling the gaps of the previous."""
        out = to_gnssvod_vod(vod_ds, BANDS)

        vod = vod_ds["VOD"]
        l1c, l1w = vod.sel(sid="G01|L1|C").values, vod.sel(sid="G01|L1|W").values
        np.testing.assert_allclose(
            out["VOD_L1"].sel(SV="G01").values, np.where(np.isnan(l1c), l1w, l1c)
        )
        np.testing.assert_allclose(
            out["VOD_L1"].sel(SV="G02").values, vod.sel(sid="G02|L1|W").values
        )
        # The bands are what the user names: VOD_E1 merges S1C of every system
        np.testing.assert_allclose(
            out["VOD_E1"].sel(SV="E05").values, vod.sel(sid="E05|E1|C").values
        )
        assert np.all(np.isnan(out["VOD_L2"].sel(SV="E05").values))
        assert {"Azimuth", "Elevation"} <= set(out.data_vars)

    def test_codes_not_in_the_data_are_ignored(self, vod_ds):
        """As in calc_vod, a band's codes absent from the data are skipped."""
        out = to_gnssvod_vod(vod_ds, {"VOD_L5": ["S5I"]})

        assert np.all(np.isnan(out["VOD_L5"].values))

    def test_round_trip(self, vod_ds):
        gnssvod_ds = to_gnssvod_vod(vod_ds, {"VOD_L2": ["S2W"], "VOD_E5a": ["S5Q"]})
        back = from_gnssvod_vod(gnssvod_ds, {"VOD_L2": "S2W", "VOD_E5a": "S5Q"})

        sids = ["E05|E5a|Q", "G01|L2|W", "G02|L2|W"]
        assert list(back["sid"].values) == sids
        np.testing.assert_allclose(back["VOD"].values, vod_ds["VOD"].sel(sid=sids).values)
        np.testing.assert_allclose(back["theta"].values, vod_ds["theta"].sel(sid=sids).values)

    def test_merged_band_gets_the_unknown_code_marker(self, vod_ds):
        gnssvod_ds = to_gnssvod_vod(vod_ds, {"VOD_L1": ["S1C", "S1W"]})
        back = from_gnssvod_vod(gnssvod_ds, {"VOD_L1": "S1"})

        # S1C is also Galileo E1, so the band holds E05 as in calc_vod
        assert list(back["sid"].values) == ["E05|E1|u", "G01|L1|u", "G02|L1|u"]

    def test_result_meets_the_vod_contract(self, vod_ds):
        """Converted VOD carries canvodpy's sid coordinates."""
        back = from_gnssvod_vod(to_gnssvod_vod(vod_ds, {"VOD_L2": ["S2W"]}), {"VOD_L2": "S2W"})

        validate_vod_dataset(back)
        assert list(back["band"].values) == ["L2", "L2"]
        assert back["freq_center"].dtype == np.float32

    def test_missing_band_raises(self, vod_ds):
        gnssvod_ds = to_gnssvod_vod(vod_ds, {"VOD_L1": ["S1C"]})
        with pytest.raises(ValueError, match="not in the gnssvod dataset"):
            from_gnssvod_vod(gnssvod_ds, {"VOD_L2": "S2"})


class TestNetcdf:
    def test_round_trip_through_netcdf(self, vod_ds, tmp_path):
        path = tmp_path / "vod.nc"
        to_gnssvod_vod(vod_ds, {"VOD_L2": ["S2W"]}).to_netcdf(path)
        with xr.open_dataset(path) as reopened:
            back = from_gnssvod_vod(reopened.load(), {"VOD_L2": "S2W"})

        np.testing.assert_allclose(
            back["VOD"].values, vod_ds["VOD"].sel(sid=back["sid"].values).values
        )
