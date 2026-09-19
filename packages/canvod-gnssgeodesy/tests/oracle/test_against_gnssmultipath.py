"""MP1 (not NMRI) oracle validation against gnssmultipath.

gnssmultipath ships actual `TestData/` + `Results_example/` (MIT
licensed, can be vendored freely with attribution) -- valid for MP1
comparison. There is no NMRI oracle anywhere: gnssrefl's own MP1 path
shells out to the deprecated `teqc` binary and never computes NMRI in
code. MP1rms -> MP1max -> NMRI must be validated by construction
(synthetic monotonicity/sign/range tests in test_code_multipath.py) and,
ideally, by reproducing a published figure from Small et al. 2014 --
never by comparing against any existing package's output, because none
computes it.

Not yet implemented (Phase 2).
"""

from __future__ import annotations

import pytest

pytest.importorskip("gnssmultipath")

pytestmark = pytest.mark.oracle


@pytest.mark.skip(
    reason="Phase 2: requires vendoring gnssmultipath's MIT-licensed TestData/ fixtures"
)
def test_mp1_matches_gnssmultipath_reference() -> None:
    raise NotImplementedError
