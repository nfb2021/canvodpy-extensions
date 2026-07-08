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

# install dependencies
sync:
    uv sync

# install pre-commit hooks
hooks:
    uvx pre-commit install

# ============================================================================
# Code Quality
# ============================================================================

# lint, format and type-check all packages
check:
    uv run ruff check . --fix
    uv run ruff format .
    uv run ty check

# run all tests
test:
    uv run pytest

# run all tests with coverage report
test-coverage:
    uv run pytest --cov --cov-report=term-missing

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
    uv run cz bump --increment {{VERSION}} --yes
    uv lock
    @echo "{{GREEN}}Version bumped to $(uv version --short){{NORMAL}}"

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
    @echo "  3. GitHub Actions will build, publish to PyPI and draft the release"

# ============================================================================
# Build & Publish
# ============================================================================

# build every package under packages/* into dist/
build-all:
    @echo "Building all packages..."
    @rm -rf dist/
    @mkdir -p dist/
    @for pkg in packages/*/; do \
        name=$(basename "$pkg"); \
        if [ -f "$pkg/pyproject.toml" ]; then \
            echo "  - $name"; \
            uv build --package "$name" --out-dir dist/; \
        fi; \
    done
    @echo "{{GREEN}}Built packages:{{NORMAL}}"
    @ls -lh dist/*.whl

# publish all built packages to TestPyPI (requires credentials)
publish-testpypi: build-all
    @echo "Publishing to TestPyPI..."
    uv tool run twine upload --repository testpypi dist/*
    @echo "{{GREEN}}Published to https://test.pypi.org{{NORMAL}}"

# publish all built packages to PyPI (requires credentials)
publish-pypi: build-all
    @echo "Publishing to PyPI..."
    uv tool run twine upload dist/*
    @echo "{{GREEN}}Published to https://pypi.org{{NORMAL}}"
