"""Manual backfill DAG for reprocessing historical GNSS-T data.

Triggered manually with parameters.  Each date in the range becomes an
independent Airflow task instance via dynamic task mapping (Airflow 2.7+).
A failure on one date retries that date only — the rest of the batch
continues unaffected.

**Concurrency safety** — Icechunk stores require serialised commits on a
branch.  ``max_active_tis_per_dagrun=1`` enforces this within a single
backfill run.  The ``canvod_store_write`` pool (create it with one slot in
the Airflow UI) provides the same guarantee across simultaneous backfill
runs and the daily DAGs::

    airflow pools set canvod_store_write 1 "Serialise Icechunk commits"

Usage (Airflow UI or CLI)::

    airflow dags trigger canvod_backfill --conf '{
        "site": "Rosalia",
        "start_date": "2025-001",
        "end_date": "2025-010"
    }'

Or via ``af``::

    af runs trigger canvod_backfill \\
        -F site=Rosalia \\
        -F start_date=2025-001 -F end_date=2025-010
"""

from __future__ import annotations

from datetime import datetime, timedelta

import structlog

from airflow.decorators import dag, task  # type: ignore[unresolved-import]
from airflow.models.param import Param  # type: ignore[unresolved-import]

logger = structlog.get_logger(__name__)


def _task_failure_callback(context):
    """Log structured failure info."""
    ti = context["task_instance"]
    logger.error(
        "BACKFILL TASK FAILED | dag=%s task=%s map_index=%s error=%s",
        ti.dag_id,
        ti.task_id,
        ti.map_index,
        context.get("exception", "unknown"),
    )


@dag(
    dag_id="canvod_backfill",
    schedule=None,  # manual trigger only
    start_date=datetime(2025, 1, 1),
    catchup=False,
    max_active_runs=3,  # allow a few concurrent backfill runs (pool controls writes)
    default_args={
        "owner": "canvod",
        "retries": 2,
        "retry_delay": timedelta(minutes=10),
        "retry_exponential_backoff": True,
        "max_retry_delay": timedelta(hours=1),
        "on_failure_callback": _task_failure_callback,
    },
    tags=["canvod", "gnss", "backfill"],
    params={
        "site": Param("Rosalia", type="string", description="Site name from sites.yaml"),
        "start_date": Param(
            "2025-001",
            type="string",
            description="Start date in YYYYDDD format",
        ),
        "end_date": Param(
            "2025-010",
            type="string",
            description="End date in YYYYDDD format (inclusive)",
        ),
    },
    doc_md=__doc__,
)
def canvod_backfill():
    """Process a date range for a single site."""

    @task
    def t_resolve_dates(**context) -> list[str]:
        """Expand start_date..end_date into a list of YYYYDDD strings."""
        import datetime as dt

        from canvod.utils.tools import YYYYDOY

        params = context["params"]
        start = YYYYDOY.from_str(params["start_date"])
        end = YYYYDOY.from_str(params["end_date"])

        if start.date is None:
            raise ValueError(f"Invalid start_date: {params['start_date']!r}")
        if end.date is None:
            raise ValueError(f"Invalid end_date: {params['end_date']!r}")

        dates: list[str] = []
        current = start.date
        while current <= end.date:
            doy = (current - dt.date(current.year, 1, 1)).days + 1
            dates.append(f"{current.year}{doy:03d}")
            current += dt.timedelta(days=1)

        logger.info(
            "backfill: %s — %d days (%s → %s)",
            params["site"],
            len(dates),
            params["start_date"],
            params["end_date"],
        )
        return dates

    @task(
        execution_timeout=timedelta(hours=6),
        # Serialise commits within this DAG run.  One date at a time prevents
        # concurrent Icechunk writes to the same branch.
        max_active_tis_per_dagrun=1,
        # Optional pool for cross-run serialisation (create with slot=1 in UI).
        pool="canvod_store_write",
        pool_slots=1,
    )
    def t_process_day(yyyydoy: str, **context) -> dict:
        """Process the full ingest + VOD pipeline for a single date.

        Idempotent: already-processed dates are skipped by the store's
        three-layer dedup (hash match → temporal overlap → intra-batch).
        """
        from canvodpy.workflows.tasks import (
            calculate_vod,
            check_day,
            process_day,
            validate_ingest,
        )

        site = context["params"]["site"]
        check_day(site, yyyydoy)
        process_day(site, yyyydoy)
        validate_ingest(site, yyyydoy)
        calculate_vod(site, yyyydoy)

        logger.info("backfill: %s %s — ok", site, yyyydoy)
        return {"site": site, "yyyydoy": yyyydoy, "status": "ok"}

    dates = t_resolve_dates()
    t_process_day.expand(yyyydoy=dates)


# Instantiate
canvod_backfill()
