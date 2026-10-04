---
name: naming-recipe
description: Write, check or debug a canvod-filemap naming recipe, the YAML file that maps a receiver's own GNSS file names (e.g. rref001a15.25o, STATION_2025_042_00_15.rinex) to canonical canVOD names. Use when a user's files are not found by canvodpy, have non-canonical names, or a recipe does not match.
---

# Naming recipes

A recipe tells canvodpy the canonical name of each file one receiver writes,
`{SIT}{T}{NN}{AGC}_R_{YYYY}{DOY}{HHMM}_{PERIOD}_{SAMPLING}_{CONTENT}.{TYPE}`.
Files keep their names on disk. Only receivers with non-canonical names
need one.

## Where it lives and how it is used

- File: `<config dir>/recipes/<site>/<name>.yaml`. `<site>` is the site
  name in `canvod-settings.yaml`, `<name>` the receiver's `recipe:`
  setting. User data, never committed to a repository.
- Create from the template, in the canvodpy repo:
  `just naming-init SITE NAME` (template:
  `packages/canvod-filemap/src/canvod/filemap/templates/recipe.yaml`).
- canvodpy takes a file for the receiver if the name matches `glob` and
  the field walk fits (`NamingRecipe.matches`).

## Write one

1. Get at least three real file names: different days, and different hours
   if the receiver writes several files a day.
2. Fill in the identity: `site` and `agency` (3 characters each),
   `receiver_number` (1-99, unique per role at the site), `receiver_type`
   (`reference` or `canopy`), and `sampling`, `period`, `content`,
   `file_type`. These are not read from the file name.
3. Write `fields` as a left-to-right walk. Each entry consumes that many
   characters: `year` (4), `yy` (2), `doy` (3), `month` + `day` instead of
   `doy`, `hour` or `hour_letter` (RINEX `a`-`x`), `minute`, `skip`.
   Count characters on a real name, including the extension.
4. Set `glob` so it selects this receiver's files and nothing else.

Example for `rref001a15.25o`:

```yaml
glob: "rref*.??o"
fields:
  - skip: 4        # rref
  - doy: 3         # 001
  - hour_letter: 1 # a
  - minute: 2      # 15
  - skip: 1        # .
  - yy: 2          # 25
  - skip: 1        # o
```

## Check it

```python
from fnmatch import fnmatch
from pathlib import Path
from canvod.filemap import NamingRecipe

recipe = NamingRecipe.load(Path("<config dir>/recipes/<site>/<name>.yaml"))
print("length", recipe.expected_length)
for name in ["rref001a15.25o", "rref032x45.25o"]:
    ok = fnmatch(name, recipe.glob) and recipe.matches(name)
    print(name, ok, recipe.to_virtual_file(Path(name)).canonical_str if ok else "")
```

Then on the real data, in the canvodpy repo: `just config-check-data SITE`.
It lists the files each receiver gets and the ones nothing recognizes.

## Why a file does not match

- **Length.** `matches` needs the name to be exactly `expected_length`
  characters. Compressed copies (`.gz`, `.Z`) are longer: they need their
  own recipe, or a `skip` that counts the suffix.
- **Skipped characters are not checked.** `skip` accepts any characters;
  only `glob` filters on literal text. A loose glob lets another receiver's
  files of the same length in.
- **Numbers.** Fields other than `hour_letter` and `skip` must be digits.
- **Two-digit years:** 80-99 become 19xx, 00-79 20xx.
- **Daily vs sub-daily.** Without an `hour`/`hour_letter` field the period
  becomes `01D`. With one, every file gets the recipe's `period`, so RINEX 2
  daily files (session `0`) and hourly files need separate recipes.
- **Placement.** A recipe directly in the `recipes` folder is refused;
  the error says where to move it.
- **Two receivers, one identity.** canvodpy refuses receivers whose files
  start with the same `{SIT}{T}{NN}{AGC}`: give each its own
  `receiver_number`.
