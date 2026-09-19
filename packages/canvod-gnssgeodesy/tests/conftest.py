"""Shared test fixtures for canvod-gnssgeodesy."""

from __future__ import annotations

import numpy as np
import pytest
import xarray as xr


@pytest.fixture
def reader_shaped_ds() -> xr.Dataset:
    """Synthetic reader-shaped Dataset: one GPS satellite, L1 C-code and
    L2 W-code, rising then setting through the elevation mask.

    Matches canvod-readers' actual output shape: `theta`/`phi` in
    radians (`theta = pi/2 - elevation`), `sid` as `f"{sv}|{band}|{code}"`,
    dims `(epoch, sid)`. Includes `SNR`, `Pseudorange_raw`, `Phase_raw` --
    the raw (not firmware-derived) observables `code_multipath.py`
    requires on SBF-sourced data.
    """
    n_epoch = 60
    epochs = np.array(
        [f"2025-01-01T00:{i:02d}:00" for i in range(n_epoch)],
        dtype="datetime64[ns]",
    )
    sids = ["G01|L1|C", "G01|L2|W"]

    rng = np.random.default_rng(0)
    # Rise from 5 deg to 35 deg then back down -- theta = pi/2 - elevation.
    elevation_deg = np.concatenate(
        [np.linspace(5, 35, n_epoch // 2), np.linspace(35, 5, n_epoch - n_epoch // 2)]
    )
    theta = np.deg2rad(90.0 - elevation_deg)
    phi = np.deg2rad(np.linspace(0, 40, n_epoch))

    theta_2d = np.tile(theta[:, None], (1, len(sids)))
    phi_2d = np.tile(phi[:, None], (1, len(sids)))
    snr = (
        40.0
        + 5.0 * np.sin(np.deg2rad(elevation_deg))[:, None]
        + rng.normal(0, 0.1, (n_epoch, len(sids)))
    )
    pseudorange_raw = rng.uniform(2.0e7, 2.1e7, (n_epoch, len(sids)))
    phase_raw = rng.uniform(1.0e8, 1.1e8, (n_epoch, len(sids)))

    return xr.Dataset(
        {
            "SNR": (["epoch", "sid"], snr),
            "Pseudorange_raw": (["epoch", "sid"], pseudorange_raw),
            "Phase_raw": (["epoch", "sid"], phase_raw),
            "theta": (["epoch", "sid"], theta_2d),
            "phi": (["epoch", "sid"], phi_2d),
        },
        coords={"epoch": epochs, "sid": sids},
    )
