"""Guarded DAG-parsing test — only runs when the ``airflow`` extra is installed.

Inert (skipped) without Airflow; activates automatically once ``apache-airflow``
is available (e.g. a CI job or dev environment with ``canvod-airflow[airflow]``
installed).
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("airflow")

import canvod.airflow


def test_dagbag_imports_cleanly():
    from airflow.models import DagBag

    bag = DagBag(dag_folder=str(Path(canvod.airflow.__file__).parent))
    assert not bag.import_errors, bag.import_errors
    assert "canvod_backfill" in bag.dags
