# canvod-airflow

Airflow DAG definitions — thin TaskFlow wrappers around `canvodpy.workflows.tasks`.

## Key modules

| Module | Purpose |
|---|---|
| `daily_processing.py` | 3 per-site `@daily` DAG factories (`create_sbf_dag`, `create_rinex_dag`, `create_sbf_agency_dag`) + shared `_wire_analysis_pipeline` tail (`validate_ingest → calculate_vod → cleanup`); dynamic per-site DAG generation at module level via `canvod.config.load_config()` |
| `backfill.py` | `canvod_backfill` — manually-triggered, `Param`-driven date-range backfill using dynamic task mapping (`.expand(yyyydoy=dates)`) |

## Important

- Do not add pipeline logic here; add it to `canvodpy.workflows.tasks`
  instead and these DAGs pick it up automatically.
- `airflow` is a top-level import in both modules — importing
  `canvod.airflow.daily_processing` or `canvod.airflow.backfill` requires
  the `airflow` extra installed. Only `canvodpy`-side config/task imports
  are deferred (inside functions), so a missing/misconfigured `canvodpy`
  config doesn't crash DAG parsing.
- All store-writing tasks use `pool="canvod_store_write", pool_slots=1` to
  serialize Icechunk commits (create the pool once: see README).
- `cleanup` uses `trigger_rule=TriggerRule.ALL_DONE` — always runs regardless
  of upstream failure.

## Testing

```bash
uv run pytest packages/canvod-airflow/tests/
```

`test_dag_structure.py` is AST/string-based — no Airflow needed. A separate
`pytest.importorskip("airflow")`-guarded test parses both modules through a
real `DagBag` when the `airflow` extra is installed.
