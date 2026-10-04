# canvodpy-extensions: instructions for coding agents

Optional packages for [canvodpy](https://github.com/nfb2021/canvodpy), the
GNSS-Transmissometry (GNSS-T) toolkit that computes vegetation optical depth
(VOD) from GNSS receivers below and above a canopy. Code that serves specific
workflows or data lives here, not in the canvodpy core. Packages are
GitHub-only: never published to PyPI.

`CLAUDE.md` files only import this file; edit `AGENTS.md`.

## Packages

| Package | Import | What it does | Read first |
|---|---|---|---|
| canvod-filemap | `canvod.filemap` | Naming recipes: map a receiver's own file names to canonical canVOD names | `packages/canvod-filemap/AGENTS.md` |
| canvod-airflow | `canvod.airflow` | Airflow DAGs that run canvodpy per site and day | `packages/canvod-airflow/AGENTS.md` |
| canvod-adapters | `canvod.adapters` | Data exchange between canvodpy and other GNSS-T programs (gnssvod) | `packages/canvod-adapters/AGENTS.md` |

Each package has its own `pyproject.toml`, version, changelog, tests and
docs page (`docs/packages/<short name>/overview.md`). `canvod` is a namespace
package shared by all of them: its `canvod` folder under `src` never gets
an init module, only the folder below it does.

## Task guides

Step-by-step guides for recurring tasks. Claude Code loads them as skills;
other agents read the files directly.

| Task | Guide |
|---|---|
| Release a package, or several | `.claude/skills/release-package/SKILL.md` |
| Change what the extensions need from canvodpy (sources, bounds, relock) | `.claude/skills/canvodpy-dependency/SKILL.md` |
| Write or debug a naming recipe for a receiver | `.claude/skills/naming-recipe/SKILL.md` |
| Support another GNSS-T program in canvod-adapters | `.claude/skills/add-adapter/SKILL.md` |
| Add a new extension package | `.claude/skills/add-package/SKILL.md` |

## Development workflow

For every change; `CONTRIBUTING.md` has the long form for people.

1. Branch from an up-to-date `main`: `git checkout main && git pull`, then
   `git checkout -b <type>/<topic>`, type as in the commit convention.
   `main` is protected; nothing is pushed to it directly.
2. Read the package's `AGENTS.md`, and the task guide if one fits.
3. Change code and tests together. A bug fix gets a test that failed
   before the fix.
4. Same PR: the package `README.md`, its `docs/packages/<short name>/overview.md`
   and the `AGENTS.md` files, wherever the change makes them wrong.
5. Verify: `just check`, then `just test-package <package>` (or `just test`
   when several packages changed). Report failures; don't skip tests.
6. Commit in conventional form with the package scope (see Rules). Mark
   breaking changes; they end up in the package changelog.
7. Push the branch and open a PR (`gh pr create`). CI must pass on all
   three platforms before merging.

Releasing is a separate step after merging: see the `release-package` guide.

## Commands

```bash
uv sync                               # all packages, one .venv at the root
just check                            # ruff lint + format, ty
just test                             # all tests
just test-package canvod-filemap      # one package
just docs                             # preview the docs site
just versions                         # version of every package
```

CI runs `just check-lock`, `just check-lint-only`, `just check-format-only`,
`just check-types` and `uv run pytest` on Linux, macOS and Windows. Use
`pathlib` and `re.escape` on paths in tests: Windows paths contain `\`.

## Rules

- **Fail loudly.** No silent fallbacks or defaults that hide a missing
  input. Raise with a message that says what to do.
- **canvodpy owns the contracts.** Dataset structure, the canonical file
  name and the configuration are defined in canvodpy (canvod-readers,
  canvod-preflight, canvod-config). Import and check against them; never
  copy them here.
- **No pipeline logic in the extensions.** Processing belongs in canvodpy;
  extensions call it (Airflow calls `canvodpy.workflows.tasks`).
- **Interfaces are ABCs**, settings are frozen pydantic models; prefer
  passing objects in over subclassing for reuse.
- **Delete, don't deprecate.** Unlike canvodpy, the extensions make no
  stability promise: remove old code and say so in the changelog
  (`feat!:` / `BREAKING CHANGE:`).
- **Conventional commits**, scope = package short name: `feat(filemap): ...`,
  `fix(adapters): ...`, `docs(airflow): ...`. Per-package changelogs are
  generated from them (`cliff.toml`); a commit that changes several packages
  appears in each of their changelogs.
- `main` is protected: every change goes through a PR.

## Dependency on canvodpy

The extensions import canvodpy packages (canvod-preflight, canvod-readers,
canvod-store, canvod-utils, canvodpy). Root `[tool.uv.sources]` decides
where they come from: a canvodpy branch while the code the extensions need
is unreleased, PyPI otherwise. Read the `canvodpy-dependency` guide before
touching those sources or relocking.

canvodpy in turn installs canvod-filemap as its workspace dependency group
`filemap` (`uv sync --group filemap` in the canvodpy repo), pinned to a tag
of this repo.

## Background on canvodpy

- Docs: <https://nfb2021.github.io/canvodpy/>
- Canonical file name (canvod-preflight, `canvod.preflight.convention`):
  `{SIT}{T}{NN}{AGC}_R_{YYYY}{DOY}{HHMM}_{PERIOD}_{SAMPLING}_{CONTENT}.{TYPE}`,
  e.g. `ROSA01TUW_R_20250010000_15M_05S_AA.rnx`. canvodpy finds files by
  this name, or through a naming recipe.
- Observation datasets: dims `(epoch, sid)`, sid `"{sv}|{band}|{code}"`
  (e.g. `G01|L1|C`); checked by `canvod.readers.validate_dataset`. VOD
  datasets: `VOD`, `theta`, `phi` (radians) on `(epoch, sid)`; checked by
  `canvod.readers.validate_vod_dataset`.
- Processing: `canvodpy run --site ... --start ... --end ...`, one day at a
  time, results in Icechunk stores.

## Keeping these files useful

- Write what an agent cannot see quickly in the code: decisions, invariants,
  traps, where things live. Don't list functions or restate docstrings.
- Every path and `just` recipe named in `AGENTS.md` and the guides must
  exist: `just check-agent-docs` verifies this (also a pre-commit hook).
- When a change makes a statement here wrong, fix it in the same PR.
