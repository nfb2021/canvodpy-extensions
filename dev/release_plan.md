# Release plan: canvodpy-extensions 1.0.0

Started 2026-10-04. Living document; update the status markers as work lands.
The canvodpy side is in canvodpy's `dev/release_plan.md` (section E points
here).

## Decision

All three packages are released as **1.0.0**, after canvodpy 1.0.0 is on
PyPI (user, 2026-10-04):

| Package | Tag | Today |
|---|---|---|
| canvod-filemap | `canvod-filemap-v1.0.0` | 0.1.0 |
| canvod-airflow | `canvod-airflow-v1.0.0` | 0.1.0 |
| canvod-adapters | `canvod-adapters-v1.0.0` | 0.1.0 |

Each package is released on its own from now on (`just release`, `just tag`,
see "Releasing" in `CONTRIBUTING.md`). 1.0.0 is the first per-package
release; after it, versions move independently. The packages stay
GitHub-only (no PyPI).

## Precondition: canvodpy 1.0.0 on PyPI

The extensions need canvodpy code that is not on PyPI today (2026-10-04:
canvod-readers 0.2.3, canvod-store 0.2.3, canvod-utils 0.3.0, canvodpy 0.3.0,
canvod-preflight not published):

| Package | Needs from canvodpy 1.0.0 |
|---|---|
| canvod-filemap | canvod-preflight (`convention`, recipe helpers; A8) |
| canvod-airflow | `canvodpy.workflows.tasks`: `check_day` / `process_day` (A14) |
| canvod-adapters | `validate_dataset`, `validate_vod_dataset`, `sid_coords` (canvod-readers), `deprecated` (canvod-utils), VOD store contract check (canvod-store; A19) |

Until then `[tool.uv.sources]` takes canvod-preflight, -readers, -store and
-utils from the canvodpy branch `fix/gnssgeodesy-upstream-bugs`.

## Steps

### 1. Finish PR #45 (`feat/filemap-recipes`)

- [x] filemap recipes, airflow one DAG per site, adapters restructure
- [x] CI: relock after merging `main`, Windows path in a test regex (142ea77)
- [x] per-package release tooling (7102c8d)
- [ ] After canvodpy 1.0.0 is on PyPI: drop the canvodpy git sources from
      the root `[tool.uv.sources]` and relock against PyPI. Check that no
      canvodpy git URL is left: `grep -c "nfb2021/canvodpy.git" uv.lock` is 0.
- [ ] Lower bounds on canvodpy 1.0.0 in the package `pyproject.toml`s:
  - canvod-filemap: `canvod-preflight>=1.0.0`
  - canvod-airflow: `canvodpy>=1.0.0`
  - canvod-adapters: `canvod-readers>=1.0.0`, `canvod-utils>=1.0.0`,
    extra `store = ["canvod-store>=1.0.0"]`
- [ ] "slots in for canvodpy >= 0.3.0" -> 1.0.0 in `README.md`,
      `CLAUDE.md`, `docs/index.md`
- [ ] `CLAUDE.md`: drop `just build-all` (no such recipe)
- [ ] CI green, merge PR #45

### 2. Release commits (one PR)

```bash
git checkout main && git pull
git checkout -b chore/release-1.0.0
just release canvod-filemap 1.0.0
just release canvod-airflow 1.0.0
just release canvod-adapters 1.0.0
git push -u origin chore/release-1.0.0
gh pr create --fill
```

- [ ] Read the three `packages/<package>/CHANGELOG.md`: breaking changes
      marked, nothing missing (commits outside `packages/<package>/` are not
      listed).
- [ ] Install pins in the READMEs and docs point at the 1.0.0 tags.
- [ ] CI green, merge.

### 3. Tags and GitHub Releases

```bash
git checkout main && git pull
just tag canvod-filemap
just tag canvod-airflow
just tag canvod-adapters
```

- [ ] Three draft releases with the right notes; publish them.
- [ ] Smoke test from the tags in a fresh environment, outside the
      workspace:

```bash
uv venv /tmp/ext-check && source /tmp/ext-check/bin/activate
uv pip install \
  "canvod-filemap @ git+https://github.com/nfb2021/canvodpy-extensions.git@canvod-filemap-v1.0.0#subdirectory=packages/canvod-filemap" \
  "canvod-airflow @ git+https://github.com/nfb2021/canvodpy-extensions.git@canvod-airflow-v1.0.0#subdirectory=packages/canvod-airflow" \
  "canvod-adapters[store] @ git+https://github.com/nfb2021/canvodpy-extensions.git@canvod-adapters-v1.0.0#subdirectory=packages/canvod-adapters"
python -c "import canvod.filemap, canvod.airflow, canvod.adapters.gnssvod, canvod.adapters.store"
```

### 4. Downstream

- [ ] canvodpy root `[tool.uv.sources]`: canvod-filemap
      `tag = "canvod-filemap-v1.0.0"` (today: branch `feat/filemap-recipes`),
      canvod-adapters `tag = "canvod-adapters-v1.0.0"` (today: `v0.1.0`);
      relock. Resolves A8 (two URLs for canvod-preflight) since both sides
      then take canvod-preflight from PyPI.
- [ ] canvodpy demo: notebooks that use filemap install it from the tag.
- [ ] Paper: the extensions section says the packages are pinned via Git
      tag; name the tag form `<package>-v<version>` if the text names one.

## Open questions

- canvodpy's extra `canvodpy[filemap] = ["canvod-filemap"]` cannot resolve
  from PyPI (no such project there) and leaves the name open to anyone who
  registers it. Inside the canvodpy repo `uv sync --extra filemap` works
  (root `[tool.uv.sources]`) and must stay (user, 2026-10-04). Options:
  (a) keep the extra and reserve the name with a placeholder on PyPI
  (recommended); (b) publish canvod-filemap to PyPI; (c) dependency group
  instead of the extra (`uv sync --group filemap`, nothing published).
- canvodpy's deprecated `FluentWorkflow` still imports
  `canvod.filemap.FilenameMapper`, which PR #45 removes; it then falls back
  to globbing `*.25o` (2025 only). Must be fixed before release (user,
  2026-10-04): use canvodpy's shared `discover_files`. Same for
  `DataDirMatcher` (canvod-readers `dir_matcher.py`), which imports
  `canvod.filemap.patterns.BUILTIN_PATTERNS` and silently skips SBF folders.
