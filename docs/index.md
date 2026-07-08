---
title: canvodpy-extensions
description: Optional extension packages for the canVODpy ecosystem
---

<div class="hero" markdown>

# canvodpy-extensions

**Optional extension packages for the [canVODpy](https://github.com/nfb2021/canvodpy) ecosystem**

canvodpy-extensions hosts packages that are useful alongside canVODpy but don't
belong in the core monorepo — non-canonical filename handling, orchestration glue,
and other slot-in components. Install only what you need.

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![REUSE](https://img.shields.io/badge/REUSE-3.3-blue)](https://reuse.software/)

[Browse packages :fontawesome-solid-arrow-right:](packages/filemap/overview.md){ .md-button .md-button--primary }
[Contribute :fontawesome-solid-arrow-right:](CONTRIBUTING.md){ .md-button }

</div>

---

## Packages

<div class="grid cards" markdown>

-   :fontawesome-solid-tag: &nbsp; **canvod-filemap**

    ---

    Recipe-based filename mapping for non-canonical GNSS filenames. Virtualises
    physical filenames to canonical canVOD names without renaming anything on disk.
    Slots in for canvodpy >= 0.3.0.

    [:octicons-arrow-right-24: Overview](packages/filemap/overview.md)

-   :fontawesome-solid-diagram-project: &nbsp; **canvod-airflow** *(planned)*

    ---

    Airflow DAG definitions for canvodpy pipelines.

</div>

---

## Installation

```bash
uv add canvod-filemap
```

## Why a separate repo?

Packages here are optional: not every canVODpy deployment needs them, and they
evolve on their own release cadence. Keeping them out of the core monorepo keeps
`canvodpy` lean while still giving these packages the same tooling, licensing, and
publishing pipeline.

---

## Affiliation

**Climate and Environmental Remote Sensing Research Unit (CLIMERS)**
Department of Geodesy and Geoinformation, TU Wien

[tuwien.at/en/mg/geo/climers](https://www.tuwien.at/en/mg/geo/climers){ .md-button }
