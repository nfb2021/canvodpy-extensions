---
name: canvodpy-dependency
description: Change or update what canvodpy-extensions takes from canvodpy (root [tool.uv.sources], version bounds, relocking against a canvodpy branch or PyPI). Use when the extensions need new canvodpy code, a canvodpy branch moved or was deleted, canvodpy was released, or uv lock fails with conflicting URLs.
---

# The extensions' dependency on canvodpy

## What depends on what

| Package | Needs from canvodpy |
|---|---|
| canvod-filemap | canvod-preflight (canonical file name) |
| canvod-airflow | canvodpy (`canvodpy.workflows.tasks`), canvod-config |
| canvod-adapters | canvod-readers (contracts, readers, sid coordinates), canvod-utils; canvod-store with the `store` extra |

The package `pyproject.toml`s state version bounds. The root
`pyproject.toml` `[tool.uv.sources]` decides where the packages come from
in this workspace: a canvodpy git branch while the extensions need unreleased
canvodpy code, PyPI once it is released. Sources are not published: an
install from a tag of this repo resolves canvodpy from PyPI, by the bounds.
So a release here must only need canvodpy code that is on PyPI.

## See what is locked

```bash
just canvodpy-ref
```

Version and source tree of every canvodpy package. They can differ per
package: a package not in root `[tool.uv.sources]` comes from PyPI even
while others come from a branch.

## Pick up new commits of a canvodpy branch

```bash
just lock-canvodpy
```

It upgrades every package that comes from the canvodpy repository at once
and prints the locked commit. Don't run `uv lock --upgrade-package
canvod-readers` alone: uv keeps the locked commit of a git repository while
any package from it is not upgraded, so the lock silently stays on the old
commit. Then `uv sync` and `just test`.

## Point at another branch, or back to PyPI

- Another branch: change `branch = "..."` on every canvodpy line in root
  `[tool.uv.sources]`, then `just lock-canvodpy`. All lines name the same
  branch; mixed branches give conflicting URLs.
- canvodpy released: delete the canvodpy lines from root
  `[tool.uv.sources]`, raise the lower bounds in the package
  `pyproject.toml`s to that release (e.g. `canvod-readers>=1.0.0`), then
  `uv lock` and check `grep -c "nfb2021/canvodpy.git" uv.lock` is 0.
- A branch was deleted after its PR merged: switch to PyPI if released,
  otherwise to `branch = "main"` or a `rev = "<merge commit>"`.

## The other direction: canvodpy installs canvod-filemap

canvodpy's root `pyproject.toml` installs canvod-filemap from a tag of this
repo (dependency group `filemap`). canvod-filemap needs canvod-preflight,
which canvodpy has as a local workspace package. While this repo takes
canvod-preflight from canvodpy's git, canvodpy's lock sees two URLs for it
and fails ("conflicting URLs for package `canvod-preflight`"). canvodpy
fixes that with `override-dependencies = ["canvod-preflight"]` and
`canvod-preflight = { workspace = true }` in its root `pyproject.toml`;
both go once canvod-preflight is on PyPI.

## Checklist

- [ ] `just lock-canvodpy` (or `uv lock`) succeeds; the printed commit is the one wanted
- [ ] `just test` passes
- [ ] The root `[tool.uv.sources]` comment says why the source is a branch
- [ ] Commit: `build(deps): ...`
