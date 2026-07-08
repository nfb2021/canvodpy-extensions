# Contributing

Contributions are welcome. This guide covers the development setup and contribution workflow.

## Required Tools

Two external tools must be installed separately (not managed by `uv sync`):

### uv (Python Package Manager)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or via package manager
brew install uv
```

[uv documentation](https://docs.astral.sh/uv/)

### just (Command Runner)

```bash
# macOS/Linux
curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash

# Or via package manager
brew install just
```

[just documentation](https://github.com/casey/just)

## Types of Contributions

### Report Bugs

Report bugs at https://github.com/nfb2021/canvodpy-extensions/issues. Include operating
system, local setup details, and steps to reproduce.

### Fix Bugs / Implement Features

Issues tagged "bug"/"enhancement" and "help wanted" are open for contributions.

### Add a New Package

New extension packages live under `packages/<name>/` and are picked up automatically
by the uv workspace (`packages/*`). Each package is independently versioned and
published to PyPI. See `packages/canvod-filemap` for the expected layout
(`pyproject.toml`, `src/`, `tests/`, `README.md`).

## Development Workflow

1. Install required tools (uv and just).

2. Fork and clone the repository:
   ```bash
   git clone git@github.com:your_name_here/canvodpy-extensions.git
   cd canvodpy-extensions
   ```

3. Install dependencies:
   ```bash
   uv sync
   just hooks
   ```

4. Create a feature branch:
   ```bash
   git checkout -b name-of-your-bugfix-or-feature
   ```

5. Make changes and verify:
   ```bash
   just test
   just check
   ```

6. Commit using conventional commits:
   ```bash
   git commit -m "feat(filemap): add support for recipe overrides"
   ```

7. Push and create a pull request:
   ```bash
   git push origin name-of-your-bugfix-or-feature
   ```

### Commit Message Format

```
<type>(<scope>): <subject>
```

**Types:** `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `ci`

**Scopes:** `filemap`, `airflow`, `deps`, `ci`, `docs`, `release`

**Examples:**
```bash
git commit -m "feat(filemap): add recipe-based mapping for non-canonical filenames"
git commit -m "fix(filemap): handle missing site config gracefully"
git commit -m "docs: update installation instructions"
```

See [Conventional Commits](https://www.conventionalcommits.org/) for the full specification.

## Common Commands

```bash
just --list                    # Show all commands
just test                      # Run all tests
just test-coverage             # With coverage report
just check                     # Lint + format + type-check
just build-all                 # Build all packages into dist/
```

## Pull Request Guidelines

1. Include tests for new functionality — new code must not reduce test coverage.
2. Update the package's `README.md` and the Zensical documentation in `docs/` if
   adding or changing public API or behaviour.
3. Ensure compatibility with Python 3.14+.
4. Add yourself to `CONTRIBUTORS.md` if this is your first contribution.

## Licensing

canvodpy-extensions is licensed under the [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0).
By submitting a pull request, you agree that your contribution is licensed under
the same terms. The `LICENSE` and `NOTICE` files at the repository root apply to
all source files. Per-file license headers are not required.

## Code Quality

- **ruff** for linting and formatting
- **ty** for type checking
- **pytest** for testing with coverage

Run `just check` before committing.

## Releasing (Maintainers)

Packages are versioned in lockstep via [Commitizen](https://commitizen-tools.github.io/commitizen/)
(see `[tool.commitizen]` in the root `pyproject.toml` — `version_files` lists every
package's `pyproject.toml`). To cut a release:

```bash
just release 0.4.0   # runs tests, updates changelog, bumps all packages, tags
git push && git push --tags
```

Pushing a `v*.*.*` tag triggers [`publish_pypi.yml`](.github/workflows/publish_pypi.yml),
which builds every package under `packages/*` and publishes them to PyPI via trusted
publishing (OIDC). Pre-release tags (`-alpha.*`, `-beta.*`, `-rc.*`) publish to
TestPyPI instead via [`publish_testpypi.yml`](.github/workflows/publish_testpypi.yml).
See [`release.yml`](.github/workflows/release.yml) for the accompanying draft GitHub
Release.

When adding a new package under `packages/`, add its `pyproject.toml:version` to
`version_files` in the root `pyproject.toml` so it stays in lockstep.
