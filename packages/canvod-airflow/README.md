# canvod-airflow

Airflow DAG definitions for canvodpy GNSS-T pipelines.

Part of the [canVODpy](https://github.com/nfb2021/canvodpy) ecosystem.

## Overview

`canvod-airflow` wraps `canvodpy`'s stateless task functions
(`canvodpy.workflows.tasks`) into Airflow TaskFlow DAGs: three daily
per-site DAGs (SBF, RINEX, SBF+agency-ephemeris) and one manually-triggered
backfill DAG. No pipeline logic lives here — every task is a thin call into
`canvodpy.workflows.tasks`, which stays in the core `canvodpy` package and
has zero Airflow dependency of its own.

## DAGs

| DAG | Trigger | Chain |
|---|---|---|
| `canvod_{site}_sbf` | `@daily` | `validate_dirs → check_sbf → process_sbf → validate_ingest → calculate_vod → cleanup` |
| `canvod_{site}_rinex` | `@daily` | `validate_dirs → {wait_for_rinex, wait_for_sp3} → fetch_aux_data → process_rinex → validate_ingest → calculate_vod → cleanup` |
| `canvod_{site}_sbf_agency` | `@daily` | `validate_dirs → {check_sbf, wait_for_sp3} → fetch_aux_data → process_sbf → validate_ingest → calculate_vod → cleanup` |
| `canvod_backfill` | Manual (Params: site, branch, start_date, end_date) | `resolve_dates → process_day` (dynamically mapped, one task per date) |

One DAG set per site configured in `canvodpy`'s `sites.yaml`, generated
dynamically at parse time via `canvod.config.load_config()`.

## Installation

GitHub-only by design; install via the git-subdirectory pattern:

```bash
uv add "canvod-airflow[airflow] @ git+https://github.com/nfb2021/canvodpy-extensions.git@v0.1.0#subdirectory=packages/canvod-airflow"
```

`apache-airflow` is an optional extra, not a hard dependency — install it
alongside whatever Airflow version your deployment environment provides.

## Deployment

Point your Airflow `dags_folder` at a shim module that imports both DAG
modules (the words "airflow" and "dag" must appear in the shim file for
Airflow's DagBag keyword pre-filter):

```python
# <dags_folder>/canvod_dags.py
from canvod.airflow.daily_processing import *  # noqa: F403  (airflow dag)
from canvod.airflow.backfill import *  # noqa: F403
```

Create the `canvod_store_write` pool (serializes Icechunk commits across
all DAGs and backfill runs):

```bash
airflow pools set canvod_store_write 1 "Serialise Icechunk commits"
```

## Concurrency safety

Icechunk stores require serialized commits per branch. Every task that
writes to the store (`calculate_vod`, `process_sbf`, `process_rinex`, and
backfill's `process_day`) uses `pool="canvod_store_write", pool_slots=1`.
Backfill additionally sets `max_active_tis_per_dagrun=1` on its mapped
`process_day` task so dates within one backfill run process sequentially.

## Testing

```bash
uv run pytest packages/canvod-airflow/tests/
```

Structure tests (`test_dag_structure.py`) are AST/string-based and run
without Airflow installed. A guarded `DagBag`-parsing test runs only when
the `airflow` extra is installed (`pytest.importorskip("airflow")`).

## License

Apache License 2.0
