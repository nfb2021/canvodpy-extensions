"""Shared test fixtures for canvod-adapters."""

import numpy as np
import pytest
import xarray as xr
from canvod.readers import SignalID, sid_coords
from canvod.readers.gnss_specs.signals import SignalIDMapper


@pytest.fixture
def vod_ds() -> xr.Dataset:
    """Synthetic canvodpy VOD dataset meeting the VOD dataset contract.

    Satellites G01, G02, E05; GPS L1|C, L1|W, L2|W and Galileo E1|C, E5a|Q;
    five epochs. dims (epoch, sid) with canvodpy's sid coordinates,
    variables VOD/phi/theta. G02 has no L1|C, so its L1 VOD comes from
    L1|W only.
    """
    rng = np.random.default_rng(0)
    epochs = np.array(
        [f"2025-01-01T00:{i:02d}:00" for i in range(5)],
        dtype="datetime64[ns]",
    )
    sids = [
        "E05|E1|C",
        "E05|E5a|Q",
        "G01|L1|C",
        "G01|L1|W",
        "G01|L2|W",
        "G02|L1|W",
        "G02|L2|W",
    ]
    svs = [sid.split("|")[0] for sid in sids]
    sv_index = sorted(set(svs))
    n_epoch = len(epochs)
    # Geometry is per satellite, identical for all its sids
    theta_sv = rng.uniform(0.1, 1.4, (n_epoch, len(sv_index)))
    phi_sv = rng.uniform(0, 2 * np.pi, (n_epoch, len(sv_index)))
    cols = [sv_index.index(sv) for sv in svs]
    vod = rng.uniform(0.0, 1.0, (n_epoch, len(sids)))
    vod[1, sids.index("G01|L1|C")] = np.nan
    return xr.Dataset(
        {
            "VOD": (["epoch", "sid"], vod),
            "phi": (["epoch", "sid"], phi_sv[:, cols]),
            "theta": (["epoch", "sid"], theta_sv[:, cols]),
        },
        coords={
            "epoch": epochs,
            **sid_coords([SignalID.from_string(s) for s in sids], mapper=SignalIDMapper()),
        },
    )


@pytest.fixture
def obs_ds(vod_ds) -> xr.Dataset:
    """Synthetic canvodpy observations: SNR and Pseudorange per sid."""
    rng = np.random.default_rng(1)
    shape = (vod_ds.sizes["epoch"], vod_ds.sizes["sid"])
    return vod_ds.drop_vars("VOD").assign(
        SNR=(["epoch", "sid"], rng.uniform(20, 50, shape)),
        Pseudorange=(["epoch", "sid"], rng.uniform(2e7, 2.5e7, shape)),
    )
