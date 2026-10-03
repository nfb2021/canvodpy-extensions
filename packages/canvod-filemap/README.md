# canvod-filemap

Naming recipes for receiver files that don't follow the canVOD filename
convention.

Part of the [canVODpy](https://github.com/nfb2021/canvodpy) ecosystem.

## Overview

`canvodpy run` processes files whose names follow the canVOD convention, in
any folder layout. For a receiver whose files are named differently, a naming
recipe translates each filename to its canonical name, without renaming any
file on disk.

**Convention format:**
```
{SIT}{T}{NN}{AGC}_R_{YYYY}{DOY}{HHMM}_{PERIOD}_{SAMPLING}_{CONTENT}.{TYPE}
```
Example: `ROSA01TUW_R_20250010000_15M_05S_AA.rnx`

## Key components

| Component | Purpose |
|---|---|
| `NamingRecipe` | Translates a receiver's own filenames to canonical names |
| `find_recipe`, `create_recipe` | Recipe files at `<config dir>/recipes/<site>/<name>.yaml`; new ones from the template |

`canvodpy config validate --site <site>` checks before a run which files the
run would process.

## Installation

GitHub-only by design; install via the git-subdirectory pattern:

```bash
uv add "canvod-filemap @ git+https://github.com/nfb2021/canvodpy-extensions.git@v0.1.0#subdirectory=packages/canvod-filemap"
```

## Quick Start

```python
from pathlib import Path

from canvod.filemap import NamingRecipe

recipe = NamingRecipe.load(Path("config/recipes/rosalia/rosalia_reference.yaml"))
vf = recipe.to_virtual_file(Path("rref001a15.25o"))
print(vf.conventional_name)  # canonical canVOD name; the file keeps its name
```

## Documentation

[Full documentation](https://nfb2021.github.io/canvodpy/packages/naming/overview/)

## License

Apache License 2.0
