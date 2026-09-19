"""Tropospheric / mapping-function products -- Phase 7, stub only.

Exposes `refraction.py`'s refraction/mapping-function correction as its
own standalone product (ZHD/ZWD/mapping functions per epoch), not just an
internal RH input as it is today. Depends on `snr_multipath.py`/
`refraction.py` (Phase 3) being complete first.
"""

from __future__ import annotations
