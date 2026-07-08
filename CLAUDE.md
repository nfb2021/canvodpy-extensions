# canvodpy-extensions — Claude Code Instructions

## Skills — auto-apply when relevant

Apply all skills automatically whenever their domain is relevant — do not
wait to be asked.

| Skill | Apply when |
|---|---|
| `pydantic` | Working with Pydantic models, validators, `BaseModel` (`canvod-filemap` config models) |
| `python-testing-patterns` | Writing or reviewing `pytest` tests |
| `uv-package-manager` | Running `uv`, editing `pyproject.toml`, managing workspace deps |
| `airflow-dag-patterns` | Writing DAGs for `canvod-airflow` (planned) |

## What this repo is

`canvodpy-extensions` is an **optional extension monorepo** for
[canvodpy](https://github.com/nfb2021/canvodpy). Packages here are useful
alongside canvodpy but don't belong in the core monorepo — they're independently
versioned, independently installed (`uv add <package>`), and released on their
own cadence. Do not assume canvodpy core conventions apply 1:1 here; check each
package's own `CLAUDE.md` first.

## Project structure

| Package | Namespace | Status | Role |
|---|---|---|---|
| `canvod-filemap` | `canvod.filemap` | Available | Recipe-based filename mapping for non-canonical GNSS filenames; slots in for canvodpy >= 0.3.0 |
| `canvod-airflow` | — | Planned | Airflow DAG definitions for canvodpy pipelines |

Each package under `packages/*` is a self-contained uv workspace member with its
own `pyproject.toml`, `src/`, `tests/`, `README.md`, and `CLAUDE.md`.

## Tooling

| Tool | Command | Purpose |
|---|---|---|
| `uv` | `uv sync`, `uv run` | Package manager, workspace orchestration |
| `just` | `just --list` | Task runner — see root `Justfile` |
| `ruff` | `uv run ruff check`, `uv run ruff format` | Linting and formatting |
| `ty` | `uv run ty check` | Type checking (Astral's type checker) |
| `pytest` | `uv run pytest` | Test runner |
| `Zensical` | `uv run zensical build` | MkDocs Material-based docs site |
| `commitizen` | `just bump`, `just release` | Version bumps across all packages, conventional commits |

### Common commands

```bash
uv sync              # Install all workspace deps
just check           # Lint + format + type-check
just test            # Run all tests
just test-package canvod-filemap  # Test a single package
just docs            # Preview documentation locally
just build-all        # Build every package into dist/
```

## Conventions

- Monorepo managed with `uv` workspaces (`packages/*`) — all packages share one `.venv` at root
- Packages are versioned in lockstep via commitizen (`[tool.commitizen]` in root `pyproject.toml`)
- Commits: conventional commits (`feat(filemap): ...`, `fix(filemap): ...`, `chore: ...`)
- New packages must be added to `[tool.commitizen] version_files` and the uv workspace picks them up automatically via `packages/*`
- Generated files: do NOT commit `*.png`, `*.svg`, `site/`, `dist/`, `.DS_Store`

## Key documentation — breadcrumb trail

When you need deeper context than this file provides, read these docs **in order**.
Each document cross-references the next, building from repo-level context down to
package-specific details.

1. `README.md` — **start here**: what this repo is, package list, install/dev setup
2. `docs/index.md` — documentation site landing page
3. `CONTRIBUTING.md` — workflow, commit convention, release process
4. `docs/packages/<package>/overview.md` — per-package deep dive (e.g. `docs/packages/filemap/overview.md`)
5. `packages/<package>/CLAUDE.md` — package-specific Claude Code instructions (modules, key classes, gotchas)
6. `docs/api/<package>.md` — generated API reference (mkdocstrings)

**Onboarding rule:** If a user asks you to explain this repo, walk them through
this trail. If you encounter an unfamiliar package, follow the trail to its
`overview.md` and `CLAUDE.md` before answering.

## AI-assisted development

This project uses **Claude Code** as a development and maintenance tool. New
contributors: Claude Code can explain any package, run tests, and help navigate
the monorepo. Start with `claude` in the repo root — it will automatically load
this context.
