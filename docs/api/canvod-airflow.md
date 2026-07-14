# canvod.airflow API Reference

## Package

::: canvod.airflow

!!! note "Why the DAG modules aren't auto-generated below"
    `daily_processing.py` and `backfill.py` import `airflow` at module level
    (required to actually build TaskFlow DAGs), so mkdocstrings can't safely
    import them in an environment without Airflow installed. Their public
    interface is documented by hand below instead.

## daily_processing

Per-site `@daily` DAG factories, called dynamically for every site
configured in canvodpy's `sites.yaml`.

### `create_sbf_dag(site_name: str)`

Builds `canvod_{site_name}_sbf` — broadcast-ephemeris DAG, same-day results.
Chain: `validate_dirs → check_sbf → process_sbf → validate_ingest → calculate_vod → cleanup`.

### `create_rinex_dag(site_name: str)`

Builds `canvod_{site_name}_rinex` — agency SP3/CLK ephemeris DAG. Chain:
`validate_dirs → {wait_for_rinex, wait_for_sp3} → fetch_aux_data → process_rinex → validate_ingest → calculate_vod → cleanup`.

### `create_sbf_agency_dag(site_name: str)`

Builds `canvod_{site_name}_sbf_agency` — SBF observables with agency
geometry. Chain: `validate_dirs → {check_sbf, wait_for_sp3} → fetch_aux_data → process_sbf → validate_ingest → calculate_vod → cleanup`.

## backfill

### `canvod_backfill`

Manually-triggered DAG accepting `site`, `branch` (`sbf`/`rinex`/`sbf_agency`),
`start_date`, and `end_date` (`YYYYDDD` format) as Params. Expands the date
range into one dynamically-mapped `process_day` task per date, serialized
via `max_active_tis_per_dagrun=1`.

See the [Overview](../packages/airflow/overview.md) for full usage examples.
