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
by the uv workspace (`packages/*`). Each package is independently versioned.
canvodpy-extensions is GitHub-only by design (see "Releasing" below) — packages
install via git-subdirectory sources, not PyPI. See `packages/canvod-filemap`
for the expected layout (`pyproject.toml`, `src/`, `tests/`, `README.md`).

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

**Scopes:** `filemap`, `airflow`, `adapters`, `deps`, `ci`, `docs`, `release`

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
```

## Coding agents

`AGENTS.md` (root and per package) holds the instructions for coding
agents; the `CLAUDE.md` files import it. Task guides for agents are in
`.claude/skills/`. Keep them correct when you change what they describe;
`just check-agent-docs` checks that the paths and recipes they name exist.

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

Each package is versioned and released on its own. A release is the git tag
`<package>-v<version>`, e.g. `canvod-filemap-v0.2.0`, on `main`.

```bash
just versions                         # current version of every package
just changelog canvod-filemap         # changes since its last release
just release canvod-filemap minor     # or major, patch, or e.g. 0.2.0
```

`just release` runs the package's tests and makes one commit that

- sets the version in `packages/<package>/pyproject.toml` (and `uv.lock`),
- writes `packages/<package>/CHANGELOG.md` from the commits that changed
  `packages/<package>/` ([git-cliff](https://git-cliff.org), `cliff.toml`),
- pins the package's install snippets in the READMEs and docs to the new tag.

Commit messages become the changelog, so follow the commit convention above
and mark breaking changes (`feat!:` or a `BREAKING CHANGE:` footer).

`main` requires a PR (branch protection), so the tag is set after the merge:

```bash
git checkout -b chore/release-canvod-filemap-0.2.0   # before just release
just release canvod-filemap 0.2.0
git push -u origin chore/release-canvod-filemap-0.2.0
gh pr create --fill
# once merged:
git checkout main && git pull
just tag canvod-filemap                # tags main and pushes the tag
```

(Don't tag before the PR merges: a merge can produce a different commit SHA
than the one you tagged, orphaning the tag.)

Pushing the tag runs [`release.yml`](.github/workflows/release.yml), which
checks that the tag matches the package version and drafts a GitHub Release
with the package's changes. Publish the draft by hand. Then update the pin in
downstream `[tool.uv.sources]`, e.g. canvodpy's root `pyproject.toml`.

canvodpy-extensions is deliberately GitHub-only. It is where logic for
specific needs, workflows and data realities lives, looser than the canvodpy
core, so a PyPI release would imply a stability contract it doesn't make.
Nothing is published to PyPI or TestPyPI. Users install packages via the
git-subdirectory pattern, pinned to a release tag (see each package's README).

A new package under `packages/` needs nothing else: its first `just release`
starts its changelog and tags.
