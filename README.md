[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21359005.svg)](https://doi.org/10.5281/zenodo.21359005)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.14-blue.svg)](https://www.python.org/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-%23FE5196?logo=conventionalcommits&logoColor=white)](https://conventionalcommits.org)
[![REUSE](https://img.shields.io/badge/REUSE-3.3-blue)](https://reuse.software/)
[![fair-software.eu](https://img.shields.io/badge/fair--software.eu-%E2%97%8F%20%20%E2%97%8F%20%20%E2%97%8B%20%20%E2%97%8F%20%20%E2%97%8B-orange)](https://fair-software.eu)

# canvodpy-extensions

Optional extension packages for [canVODpy](https://github.com/nfb2021/canvodpy).
Not part of the core monorepo, and GitHub-only by design — install individually
via git-subdirectory sources, not PyPI (see each package's README for the exact
command).

## Packages

| Package | Purpose | Status |
|---|---|---|
| [`canvod-filemap`](packages/canvod-filemap) | Recipe-based filename mapping for non-canonical GNSS filenames; slot-in for canvodpy >= 0.3.0 | Available |
| [`canvod-airflow`](packages/canvod-airflow) | Airflow DAG definitions (daily SBF/RINEX/SBF-agency + backfill) for canvodpy pipelines | Available |
| [`canvod-adapters`](packages/canvod-adapters) | Data exchange between canvodpy and other GNSS-T programs (gnssvod) | Available |

## Installation

Each package installs from this repo directly via a git-subdirectory source —
there's no PyPI package to `uv add <name>` for. Each package is released on
its own, under the tag `<package>-v<version>`. Pin to a release tag, not the
default branch, so installs stay reproducible. For `canvod-filemap`:

```bash
uv add "canvod-filemap @ git+https://github.com/nfb2021/canvodpy-extensions.git@v0.1.0#subdirectory=packages/canvod-filemap"
```

The other packages follow the same pattern: swap `canvod-filemap` for
`canvod-airflow` or `canvod-adapters` in the package name and the
`subdirectory=` path, and use that package's release tag. See each package's own README for extras (e.g.
`canvod-airflow[airflow]`, `canvod-adapters[store]`).

`just release` keeps the pins in this README and the docs on the latest
release; downstream consumers' `[tool.uv.sources]` (e.g. canvodpy's root
`pyproject.toml`) are updated by hand. See "Releasing" in
[CONTRIBUTING.md](CONTRIBUTING.md).

## Development Setup

```bash
git clone https://github.com/nfb2021/canvodpy-extensions.git
cd canvodpy-extensions

uv sync
just hooks
```

### Common Commands

```bash
just --list       # Show all commands
just test         # Run all tests
just check        # Lint + format + type-check
just docs         # Preview documentation locally
just build-all    # Build all packages into dist/
```

## Documentation

Full documentation is available at **[nfb2021.github.io/canvodpy-extensions](https://nfb2021.github.io/canvodpy-extensions/)**.

## Contributing

Contributions of all kinds are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

First-time contributors: add yourself to [CONTRIBUTORS.md](CONTRIBUTORS.md) in your PR.

## License

Licensed under the [Apache License 2.0](LICENSE).

This software is provided "as is" without warranty of any kind.

## Affiliation

Founded by **Nicolas François Bader**

[Climate and Environmental Remote Sensing Research Unit (CLIMERS)](https://www.tuwien.at/en/mg/geo/climers)
Department of Geodesy and Geoinformation, TU Wien
