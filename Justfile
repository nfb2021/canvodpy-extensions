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

# Each package is released on its own, under the tag <package>-v<version>
# (e.g. canvod-filemap-v0.2.0). See "Releasing" in CONTRIBUTING.md.

# show the version of every package
versions:
    @for pkg in packages/*/; do pkg=$(basename "$pkg"); echo "$pkg $(uv version --package "$pkg" --short --frozen)"; done

# show the changes to PKG since its last release
changelog PKG:
    uvx git-cliff --include-path "packages/{{PKG}}/**" --tag-pattern "^{{PKG}}-v[0-9]" --unreleased

# release commit for PKG: bump (major, minor, patch or e.g. 0.2.0), changelog, install pins
release PKG VERSION: (test-package PKG)
    #!/usr/bin/env bash
    set -euo pipefail
    test -d "packages/{{PKG}}" || { echo "No package packages/{{PKG}}" >&2; exit 1; }
    test -z "$(git status --porcelain)" || { echo "Commit or discard your changes first" >&2; exit 1; }
    case "{{VERSION}}" in
        major|minor|patch) uv version --package "{{PKG}}" --bump "{{VERSION}}" ;;
        *) uv version --package "{{PKG}}" "{{VERSION}}" ;;
    esac
    version=$(uv version --package "{{PKG}}" --short --frozen)
    tag="{{PKG}}-v${version}"
    if git rev-parse -q --verify "refs/tags/${tag}" >/dev/null; then
        echo "Tag ${tag} exists already" >&2; exit 1
    fi
    uvx git-cliff --include-path "packages/{{PKG}}/**" --tag-pattern "^{{PKG}}-v[0-9]" \
        --tag "${tag}" --output "packages/{{PKG}}/CHANGELOG.md"
    # Pin the install snippets of PKG to the new tag
    pin='canvodpy-extensions\.git@[^#]*#subdirectory=packages/{{PKG}}"'
    files=$(grep -rlE "${pin}" README.md docs "packages/{{PKG}}/README.md" || true)
    for f in ${files}; do
        sed -i.bak -E "s|(canvodpy-extensions\.git@)[^#]*(#subdirectory=packages/{{PKG}}\")|\1${tag}\2|g" "${f}"
        rm "${f}.bak"
    done
    git add "packages/{{PKG}}" uv.lock ${files}
    git commit -m "chore(release): {{PKG}} ${version}"
    echo ""
    echo -e "{{GREEN}}{{BOLD}}Release commit for ${tag} created.{{NORMAL}}"
    echo ""
    echo "Next steps (main requires a PR, see CONTRIBUTING.md):"
    echo "  1. Push this branch, open a PR and merge it"
    echo "  2. git checkout main && git pull, then: just tag {{PKG}}"
    echo "  3. Publish the draft GitHub Release that the tag creates"
    echo "  4. Update the pin in downstream [tool.uv.sources] (canvodpy's root pyproject.toml)"

# tag the current version of PKG on an up-to-date main and push the tag
tag PKG:
    #!/usr/bin/env bash
    set -euo pipefail
    git fetch --quiet origin main --tags
    test "$(git branch --show-current)" = main || { echo "Check out main first" >&2; exit 1; }
    test "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)" || { echo "main differs from origin/main: git pull first" >&2; exit 1; }
    version=$(uv version --package "{{PKG}}" --short --frozen)
    tag="{{PKG}}-v${version}"
    grep -q "\[${tag}\]" "packages/{{PKG}}/CHANGELOG.md" || { echo "${tag} is not in packages/{{PKG}}/CHANGELOG.md: run just release first" >&2; exit 1; }
    git tag -a "${tag}" -m "{{PKG}} ${version}"
    git push origin "${tag}"
