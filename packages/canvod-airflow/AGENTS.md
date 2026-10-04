# canvod-airflow

Airflow DAGs that run canvodpy: thin TaskFlow wrappers around
`canvodpy.workflows.tasks`, the same code as `canvodpy run`.

## Where things are

- `src/canvod/airflow/daily_processing.py`: one `@daily` DAG per site in
  the canvodpy configuration, `canvod_<site>`, made by `create_daily_dag`:
  `validate_dirs → wait_for_data (→ wait_for_sp3) → process_day →
  validate_ingest → calculate_vod`. `wait_for_sp3` is only added when
  `processing.params.ephemeris_source` is not `broadcast`.
- `src/canvod/airflow/backfill.py`: `canvod_backfill`, triggered by hand
  with `site`, `start_date`, `end_date` params; one mapped `process_day`
  per day.

## Rules

- **No pipeline logic here.** Add it to `canvodpy.workflows.tasks`; the
  DAGs only call those functions and pass the day as `YYYYDOY`.
- **Parse-time safety:** import canvodpy inside tasks, not at module top.
  `_get_configured_sites` returns no sites, with a warning, when the
  configuration cannot load, so the scheduler can still parse the file.
  `airflow` itself is a top-level import: the modules need the `airflow`
  extra.
- **One store writer at a time:** tasks that write a store use
  `pool="canvod_store_write", pool_slots=1` (Icechunk commits must not run
  concurrently). The pool is created by the user (see `README.md`).

## Tests

`just test-package canvod-airflow`. `tests/test_dag_structure.py` checks
the DAG files as source text and AST, without Airflow installed.
`tests/test_dagbag.py` loads them into a real `DagBag` and is skipped
unless the `airflow` extra is installed.
