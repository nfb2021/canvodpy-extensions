"""RH oracle validation against gnssrefl.

gnssrefl ships no precomputed reference numbers -- its own regression
tests generate "golden" output by re-running gnssrefl at a pinned commit
at test time. This requires actually running gnssrefl (env vars, orbit
downloads), budgeted for Phase 3, not a fixtures-directory comparison.

Comparing our independently-computed *numbers* against gnssrefl's own
output is legally clean (output of a program is not a derivative work of
the program). Test fixtures are the separate, narrower question: do not
vendor gnssrefl's own `test/data/` fixtures here -- regenerate them from
the original public IGS/UNAVCO RINEX instead (see `fixtures/README.md`).

Not yet implemented (Phase 3).
"""

from __future__ import annotations

import pytest

pytest.importorskip("gnssrefl")

pytestmark = pytest.mark.oracle


@pytest.mark.skip(
    reason="Phase 3: requires running gnssrefl end-to-end against regenerated public fixtures"
)
def test_rh_matches_gnssrefl_reference() -> None:
    raise NotImplementedError
