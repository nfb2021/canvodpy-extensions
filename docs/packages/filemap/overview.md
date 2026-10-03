# canvod-filemap

Naming recipes for receiver files that don't follow the canVOD filename
convention.

`canvodpy run` processes files whose names follow the canVOD convention, in any
folder layout. For a receiver whose files are named differently (Septentrio SBF,
RINEX v2 short names, etc.), a naming recipe translates each filename to its
canonical name, without renaming any file on disk.

`canvodpy config validate --site <site>` checks before a run which files the
run would process.

## Convention format

```
{SIT}{T}{NN}{AGC}_R_{YYYY}{DOY}{HHMM}_{PERIOD}_{SAMPLING}_{CONTENT}.{TYPE}
```

Example: `ROSA01TUW_R_20250010000_15M_05S_AA.rnx`

## Key components

| Module | Component | Purpose |
|---|---|---|
| `convention.py` | `CanVODFilename` | Pydantic model — parses and validates a single filename |
| `recipe.py` | `NamingRecipe` | Translates a receiver's own filenames to canonical names |
| `recipe_files.py` | `find_recipe`, `create_recipe` | Where recipe files live; new recipes from the template |
| `mapping.py` | `VirtualFile` | A physical file paired with its canonical name (`NamingRecipe.to_virtual_file`) |

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

Before a run, check which files the run would process:

```bash
canvodpy config validate --site rosalia
```

## NamingRecipe YAML format

If your GNSS receiver outputs files in a proprietary or legacy format, a
`NamingRecipe` tells canvodpy how to extract canonical fields from a physical
filename:

```yaml
name: rosalia_reference
description: Septentrio RINEX v2 files from Rosalia reference receiver
site: ROS
agency: TUW
receiver_number: 1
receiver_type: reference
sampling: "05S"
period: "15M"
file_type: rnx
glob: "*.??o"
fields:
  - skip: 4          # "rref"
  - doy: 3           # "001"
  - hour_letter: 1   # "a"
  - minute: 2        # "15"
  - skip: 1          # "."
  - yy: 2            # "25"
  - skip: 1          # "o"
```

| Field key | Description |
|-----------|-------------|
| `year` | 4-digit year |
| `yy` | 2-digit year (80–99 = 19xx, 00–79 = 20xx) |
| `doy` | Day of year |
| `month` / `day` | Month + day of month (converted to DOY) |
| `hour` | Hour (0–23) |
| `hour_letter` | RINEX v2 hour letter (a–x = 0–23) |
| `minute` | Minute (0–59) |
| `skip` | Ignore N characters |

Reference a recipe from canvodpy's `canvod-settings.yaml`:

```yaml
sites:
  my_site:
    receivers:
      reference_01:
        recipe: my_site_reference   # → <config dir>/recipes/my_site/my_site_reference.yaml
```

Recipe files are kept per site in the configuration directory, at
`<config dir>/recipes/<site>/<name>.yaml`. `find_recipe(config_dir, site, name)`
returns that path, and raises `RecipeNotFoundError` if the file does not exist.
A recipe saved directly in `<config dir>/recipes/` is not used; the error says
where to move it. `create_recipe(config_dir, site, name)` creates a new recipe
from the template shipped with this package, with `name` filled in.

A recipe has no `layout` field: `canvodpy run` finds the files in any folder
layout and takes each file's day from its name. An older recipe that still
sets `layout` loads unchanged; the field is ignored.

## Important

- `DataDirMatcher` and `PairDataDirMatcher` in canvod-readers are **deprecated**: `canvodpy run` finds the files itself

See the [API Reference](../../api/canvod-filemap.md) for the full public API.
