# ============================================================================
# canvodpy-extensions Monorepo - Root Justfile
# ============================================================================

# ANSI color codes
GREEN := '\033[0;32m'
BOLD := '\033[1m'
NORMAL := '\033[0m'

# Default command lists all available recipes
_default:
    @just --list --unsorted

alias c := clean
alias h := hooks
alias q := check
alias t := test

# ============================================================================
# Setup
# ============================================================================

# install dependencies and ensure all git hooks are active
sync:
    uv sync
    uv run pre-commit install --hook-type pre-commit --hook-type commit-msg --hook-type pre-push

# install pre-commit, commit-msg and pre-push git hooks
hooks:
    uv run pre-commit install --hook-type pre-commit --hook-type commit-msg --hook-type pre-push

# ============================================================================
# Code Quality
# ============================================================================

# check uv.lock is up to date (for CI)
check-lock:
    uv lock --check

# lint python code using ruff
[private]
check-lint:
    uv run ruff check . --fix

# lint python code without auto-fixing (for CI)
check-lint-only:
    uv run ruff check .

# format python code using ruff
[private]
check-format:
    uv run ruff format .

# check formatting without modifying files (for CI)
check-format-only:
    uv run ruff format --check .

# run the type checker ty (config lives in [tool.ty] in pyproject.toml)
check-types:
    uv run ty check

# lint, format and type-check all packages
check: check-lint check-format check-types

# run all tests
test:
    uv run pytest

# run all tests with coverage report
test-coverage:
    uv run pytest

# run tests for a single package, e.g. `just test-package canvod-filemap`
test-package PKG:
    uv run pytest packages/{{PKG}}/tests

# ============================================================================
# Cleanup
# ============================================================================

# remove build artifacts, caches and bytecode
clean:
    rm -fr dist/ build/ .eggs/
    find . -name '*.egg-info' -exec rm -fr {} +
    find . -name '__pycache__' -exec rm -fr {} +
    find . -name '.pytest_cache' -exec rm -fr {} +
    find . -name '.ruff_cache' -exec rm -fr {} +

# ============================================================================
# Documentation
# ============================================================================

# preview the documentation locally
docs:
    uv run zensical serve --open

# build the documentation
docs-build:
    uv run zensical build

# deploy the documentation via GitHub Actions
docs-deploy:
    gh workflow run "Deploy Docs"

# ============================================================================
# Release Management
# ============================================================================

# generate CHANGELOG.md from git commits (VERSION can be "auto" or specific like "v0.2.0")
changelog VERSION="auto":
    uvx git-changelog -Tio CHANGELOG.md -B="{{VERSION}}" -c angular

# bump version across all packages (major, minor, patch, or explicit like 0.2.0)
bump VERSION:
    @echo "{{GREEN}}{{BOLD}}Bumping all packages to {{VERSION}}{{NORMAL}}"
    uv run cz bump {{VERSION}} --yes
    uv lock
    @echo "{{GREEN}}Version bumped to {{VERSION}}{{NORMAL}}"

# create a new release (runs tests, updates changelog, bumps version, tags)
release VERSION: test
    @echo "{{GREEN}}{{BOLD}}Creating release {{VERSION}}{{NORMAL}}"
    @just changelog "v{{VERSION}}"
    git add CHANGELOG.md
    git commit -m "chore: update changelog for v{{VERSION}}"
    @just bump {{VERSION}}
    git add .
    git commit -m "chore: bump version to {{VERSION}}"
    git tag -a "v{{VERSION}}" -m "Release v{{VERSION}}"
    @echo ""
    @echo "{{GREEN}}{{BOLD}}Release v{{VERSION}} created!{{NORMAL}}"
    @echo ""
    @echo "Next steps:"
    @echo "  1. Review the commits and tag"
    @echo "  2. Push with: git push && git push --tags"
    @echo "  3. GitHub Actions will draft a GitHub Release (GitHub-only, no PyPI)"
