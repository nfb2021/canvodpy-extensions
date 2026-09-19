"""Tests for canvod.gnssgeodesy.qc -- both functions are Phase 2/3 stubs."""

from __future__ import annotations

import numpy as np
import pytest
from canvod.gnssgeodesy.qc import compute_fap_baluev, mad_outlier_mask


def test_compute_fap_baluev_not_yet_implemented() -> None:
    with pytest.raises(NotImplementedError):
        compute_fap_baluev(np.array([1.0]), np.array([1.0]), 10)


def test_mad_outlier_mask_not_yet_implemented() -> None:
    with pytest.raises(NotImplementedError):
        mad_outlier_mask(np.array([1.0, 2.0, 3.0]), threshold=3.0)
