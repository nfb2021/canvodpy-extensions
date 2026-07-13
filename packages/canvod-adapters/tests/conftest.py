"""Shared test fixtures for canvod-adapters."""

import numpy as np
import pytest
import xarray as xr


@pytest.fixture
def vod_ds() -> xr.Dataset:
    """Synthetic canvodpy VOD dataset matching the real VOD store shape.

    Two satellites (G01, G02), two bands (L1|C, L2|W), five epochs.
    Matches ``canvod.vod.calculator.TauOmegaZerothOrder.calculate_vod()``'s
    output: dims (epoch, sid), variables VOD/delta_snr/phi/theta.
    """
    rng = np.random.default_rng(0)
    epochs = np.array(
        [f"2025-01-01T00:{i:02d}:00" for i in range(5)],
        dtype="datetime64[ns]",
    )
    prns = ["G01", "G02"]
    bands = ["L1|C", "L2|W"]
    sids = [f"{prn}|{band}" for band in bands for prn in prns]

    n_epoch, n_prn = len(epochs), len(prns)
    # Same-satellite geometry is physically identical across bands -- only
    # SNR/VOD differ per band. Generate per-PRN theta/phi, then broadcast
    # across both bands (matches real GNSS data; independently random
    # per-SID phi/theta would make round-trip assertions physically
    # meaningless, since to_gnssvod_dataset() correctly shares one band's
    # Azimuth/Elevation across all bands for the same satellite).
    theta_per_prn = rng.uniform(0.1, 1.4, (n_epoch, n_prn))  # rad, [0, pi/2)
    phi_per_prn = rng.uniform(0, 2 * np.pi, (n_epoch, n_prn))
    theta = np.tile(theta_per_prn, (1, len(bands)))
    phi = np.tile(phi_per_prn, (1, len(bands)))

    n_sid = len(sids)
    delta_snr = rng.uniform(-2.0, 2.0, (n_epoch, n_sid))
    vod = -np.log(10 ** (delta_snr / 10)) * np.cos(theta)

    return xr.Dataset(
        {
            "VOD": (["epoch", "sid"], vod),
            "delta_snr": (["epoch", "sid"], delta_snr),
            "phi": (["epoch", "sid"], phi),
            "theta": (["epoch", "sid"], theta),
        },
        coords={"epoch": epochs, "sid": sids},
    )
