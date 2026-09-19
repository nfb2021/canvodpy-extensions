# Oracle test fixtures

**Never vendor gnssrefl's own `test/data/` fixtures here** — gnssrefl is
GPLv3; comparing our independently-computed numbers against its output is
legally clean, but vendoring its test-fixture *files* is a separate,
narrower question this repo avoids entirely by regenerating fixtures from
the original public IGS/UNAVCO RINEX instead of copying them from
gnssrefl.

gnssmultipath's `TestData/`/`Results_example/` (MIT licensed) may be
vendored here freely, with attribution, once Phase 2's MP1 oracle tests
are implemented.

If anything from a GPLv3 source is ever vendored here despite the above,
the root `REUSE.toml`'s blanket `path = "**"` rule will mis-stamp it as
Apache-2.0 — an explicit `[[annotations]]` override for that path is then
mandatory, not optional.
