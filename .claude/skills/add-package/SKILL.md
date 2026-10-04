---
name: add-package
description: Create a new package in canvodpy-extensions (layout, pyproject, tests, docs, agent files, first release). Use when asked to add a new extension package or to move optional code out of canvodpy into this repo.
---

# Add an extension package

A package belongs here if it serves a specific workflow, data source or
tool, can be installed on its own, and canvodpy works without it. Code
every canvodpy user needs belongs in canvodpy.

Before designing it, read the canvodpy side (root `AGENTS.md`, "canvodpy:
read it before changing an extension"): find the canvodpy interface the
package plugs into and the canvodpy code that will call it.

Names: distribution `canvod-<short>`, import `canvod.<short>`, docs folder
`docs/packages/<short>/`. Copy structure from `packages/canvod-filemap`
(smallest).

## Files

```text
packages/canvod-<short>/
    pyproject.toml
    README.md          # what it is, install from the tag, usage
    AGENTS.md          # for agents: where things are, rules, traps
    CLAUDE.md          # one line: @AGENTS.md
    Justfile           # copy from another package
    pytest.ini         # copy from another package
    src/canvod/<short>/__init__.py   # no src/canvod/__init__.py: namespace package
    tests/
```

`pyproject.toml`: `version = "0.1.0"`, `requires-python = ">=3.14"`,
build backend `uv_build` with `[tool.uv.build-backend] module-name =
"canvod.<short>"`, project URLs pointing at this repo and
`docs/packages/<short>/overview/`. canvodpy packages as dependencies with
lower bounds of a released version; if unreleased code is needed, see the
`canvodpy-dependency` guide. Optional heavy dependencies go into extras.

## Register it

The uv workspace picks it up (`packages/*`); `uv sync`. Then add it to:

- root `pyproject.toml`: `[tool.pytest.ini_options] testpaths` and
  `[tool.coverage.run] source`, and the package list in the header comment;
- `zensical.toml` `nav`: an overview page and an API page;
- `docs/packages/<short>/overview.md`, `docs/api/canvod-<short>.md`
  (`::: canvod.<short>`), `docs/index.md`;
- the package tables in `README.md` and `AGENTS.md`;
- `CONTRIBUTING.md` commit scopes.

## Check and release

```bash
uv sync && just check && just test-package canvod-<short> && just docs-build
python -c "import canvod.<short>"
```

Commit `feat(<short>): ...`, open a PR. After the merge, the first
`just release canvod-<short> 0.1.0` starts its changelog and tags (see the
`release-package` guide).
