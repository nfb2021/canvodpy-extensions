# canvod-filemap

Naming recipes: a recipe maps the file names one receiver writes to the
canonical canVOD name, without renaming files on disk. canvodpy does the
file discovery; this package only answers "which canonical name does this
file have?" and "where is the recipe file?".

## Where things are

- `src/canvod/filemap/recipe.py`: `NamingRecipe`, the recipe model and the
  left-to-right field walk over a file name.
- `src/canvod/filemap/recipe_files.py`: where recipe files live,
  `<config dir>/recipes/<site>/<name>.yaml`, and creating one from
  `src/canvod/filemap/templates/recipe.yaml`.
- `src/canvod/filemap/mapping.py`: `VirtualFile`, a physical file with its
  canonical name.
- The canonical name itself (`CanVODFilename`) is canvod-preflight's
  (`canvod.preflight.convention`). Never redefine it here.

## How canvodpy uses it

`canvodpy.orchestrator.discovery` (canvodpy repo) calls `find_recipe`,
`NamingRecipe.load` and `to_virtual_file` for a receiver with a `recipe:`
setting. A file belongs to the recipe if its name matches `glob` **and**
`NamingRecipe.matches` (exact length, all fields parse). canvodpy's
`just naming-init SITE NAME` creates a recipe from the template; `just
config-check-data SITE` shows which files it recognizes. Changing a public
name here breaks canvodpy: search the canvodpy repo for it first.

## Traps

- `matches` requires the file name length to equal the sum of the field
  widths. A recipe for compressed files (`.gz`) must count the suffix.
- A recipe without an `hour`/`hour_letter` field produces daily files
  (`period` becomes `01D`).
- `yy` resolves 80-99 to 19xx and 00-79 to 20xx.
- Recipe files are user data in the config directory, never in a
  repository. `find_recipe` refuses a recipe placed directly in the
  `recipes` folder and says where to move it.

## Removed

`FilenameMapper`, `DataDirectoryValidator`, the pattern registry,
`SiteNamingConfig`/`ReceiverNamingConfig`, the convention module (now in
canvod-preflight) and the recipe field `layout` were removed, not
deprecated. An old recipe with `layout:` still loads; the field is
ignored.

## Tests

`just test-package canvod-filemap`. Test files in `tests/test_data/` use
canonical names; non-canonical cases are built in `tmp_path`.
