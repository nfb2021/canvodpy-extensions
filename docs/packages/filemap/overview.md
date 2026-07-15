# canvod-filemap

Canonical GNSS-T filename parser and data directory validator.

`canvod-filemap` enforces and virtualizes the canVOD filename convention throughout
the processing pipeline. It is the single source of truth for GNSS file naming,
discovery, and pre-pipeline validation — including receiver output that doesn't
follow the canonical convention (Septentrio SBF, RINEX v2 short names, etc.).

## Convention format

```
{SIT}{T}{NN}{AGC}_R_{YYYY}{DOY}{HHMM}_{PERIOD}_{SAMPLING}_{CONTENT}.{TYPE}
```

Example: `ROSA01TUW_R_20250010000_15M_05S_AA.rnx`

## Key components

| Module | Component | Purpose |
|---|---|---|
| `convention.py` | `CanVODFilename` | Pydantic model — parses and validates a single filename |
| `mapping.py` | `FilenameMapper` | Maps physical filenames to canonical names (virtual renaming) |
| `validator.py` | `DataDirectoryValidator` | Pre-pipeline hard gate: blocks on unmatched or overlapping files |
| `patterns.py` | `BUILTIN_PATTERNS` | Glob patterns for all GNSS file types (single source of truth) |
| `config_models.py` | `SiteNamingConfig`, `ReceiverNamingConfig` | Pydantic config models |
| `recipe.py` | `NamingRecipe` | Recipe-based config generation for non-canonical layouts |

## Installation

GitHub-only by design; install via the git-subdirectory pattern:

```bash
uv add "canvod-filemap @ git+https://github.com/nfb2021/canvodpy-extensions.git@v0.1.0#subdirectory=packages/canvod-filemap"
```

## Quick Start

```python
from canvod.filemap import CanVODFilename, DataDirectoryValidator

# Parse a filename
fname = CanVODFilename.from_string("ROSA01TUW_R_20250010000_15M_05S_AA.rnx")
print(fname.site, fname.year, fname.doy)  # ROSA, 2025, 1

# Validate a data directory before processing
validator = DataDirectoryValidator(site_config)
validator.validate()  # raises on unmatched or overlapping files
```

## NamingRecipe YAML format

If your GNSS receiver outputs files in a proprietary or legacy format, a
`NamingRecipe` tells the mapper how to extract canonical fields from a physical
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
layout: yyddd_subdirs   # or yyyyddd_subdirs, flat
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
        recipe: my_site_reference   # → config/recipes/my_site_reference.yaml
```

## Important

- `DataDirMatcher` and `PairDataDirMatcher` in canvod-readers are **deprecated** — use this package instead
- `BUILTIN_PATTERNS` is the single source of truth for file glob patterns

See the [API Reference](../../api/canvod-filemap.md) for the full public API.
