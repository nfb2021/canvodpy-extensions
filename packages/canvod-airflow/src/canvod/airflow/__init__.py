"""canvod-airflow: Airflow DAG definitions for canvodpy GNSS-T pipelines.

See ``daily_processing.py`` (per-site SBF/RINEX/SBF+agency DAGs) and
``backfill.py`` (manual date-range backfill DAG). No pipeline logic lives
here; every task wraps a stateless function from ``canvodpy.workflows.tasks``.

``daily_processing.py`` and ``backfill.py`` import ``airflow`` at module
level — they require the ``airflow`` extra (``canvod-airflow[airflow]``)
to import at all, since these modules only ever run inside an Airflow
scheduler process. ``canvodpy``-side config/task imports are deferred
inside each DAG-construction function instead, so a missing or
misconfigured ``canvodpy`` config doesn't crash DAG parsing.
"""

__version__ = "0.3.0"
