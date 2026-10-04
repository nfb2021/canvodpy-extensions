# canvod-filemap

Naming recipes: translate non-canonical receiver filenames to canonical canVOD names, without renaming files. `canvodpy run` does the file discovery (any folder layout, day from the filename).

## Key modules

| Module | Purpose |
|---|---|
| `convention.py` | `CanVODFilename` — parses `{SIT}{T}{NN}{AGC}_R_{YYYY}{DOY}{HHMM}_{PERIOD}_{SAMPLING}_{CONTENT}.{TYPE}` |
| `recipe.py` | `NamingRecipe` — filename → canonical name (`to_virtual_file`) |
| `mapping.py` | `VirtualFile` — physical file + canonical name |
| `patterns.py` | `hour_letter_to_int`, `resolve_year_from_yy` |
| `recipe_files.py` | `find_recipe`, `create_recipe` — recipes live at `<config dir>/recipes/<site>/<name>.yaml`; template in `templates/recipe.yaml` |

## Convention format

`{SIT}{T}{NN}{AGC}_R_{YYYY}{DOY}{HHMM}_{PERIOD}_{SAMPLING}_{CONTENT}.{TYPE}`

Example: `ROSA01TUW_R_20250010000_15M_05S_AA.rnx`

## Removed

`FilenameMapper`, `DataDirectoryValidator`, the pattern registry
(`BUILTIN_PATTERNS`, `match_pattern`), `SiteNamingConfig`/`ReceiverNamingConfig`
and the recipe field `layout` were removed, not deprecated: this is an
extension, not core code. An old recipe with `layout:` still loads (ignored).

## Important

- `DataDirMatcher` and `PairDataDirMatcher` in canvod-readers are **deprecated**: `canvodpy run` finds the files itself
- Test data files use canonical names

## Testing

```bash
uv run pytest packages/canvod-filemap/tests/
```
