# canvod-adapters

Data exchange between canvodpy and other GNSS-T programs.

Part of the [canVODpy](https://github.com/nfb2021/canvodpy) ecosystem.

## Overview

`canvod-adapters` converts observations and VOD between canvodpy and
other programs, in both directions. Every import is checked against
canvodpy's own contract for that data, and every conversion records its
provenance (program, versions, direction, source, time) in the dataset
attributes.

| Adapter | Program | Data |
|---|---|---|
| `canvod.adapters.gnssvod` | [gnssvod](https://github.com/vincenthumphrey/gnssvod) (Humphrey et al.) | observations, VOD |

```python
from canvod.adapters.gnssvod import GnssvodVod
from canvod.adapters.store import import_vod

adapter = GnssvodVod(bands={"VOD_L1": ["S1C", "S1W"], "VOD_L2": ["S2W"]})
vod = adapter.import_file("vod_rosalia.nc")
import_vod(adapter, "vod_rosalia.nc", site.vod_store, "canopy_01_vs_reference_01")
```

## Installation

GitHub-only by design; install via the git-subdirectory pattern:

```bash
uv add "canvod-adapters @ git+https://github.com/nfb2021/canvodpy-extensions.git@v0.1.0#subdirectory=packages/canvod-adapters"
uv add "canvod-adapters[store] @ git+https://github.com/nfb2021/canvodpy-extensions.git@v0.1.0#subdirectory=packages/canvod-adapters"  # for VOD store I/O
```

## Documentation

[Full documentation](https://nfb2021.github.io/canvodpy-extensions/packages/adapters/overview/)

## License

Apache License 2.0
