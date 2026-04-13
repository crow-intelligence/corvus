"""MLflow experiment tracking helpers.

Tracking store : local  (.mlruns/ — gitignored)
Artifact store : GCS    ({{cookiecutter.gcs_bucket}}/mlflow)
"""

from __future__ import annotations

import mlflow

from {{cookiecutter.package_name}}.config import settings
from {{cookiecutter.package_name}}.logging import get_logger

log = get_logger(__name__)


def init_experiment(experiment_name: str | None = None) -> str:
    """Configure MLflow tracking URI and experiment. Returns experiment name."""
    name = experiment_name or settings.mlflow_experiment
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    mlflow.set_experiment(name)
    log.info("mlflow.experiment.set", name=name, tracking_uri=settings.mlflow_tracking_uri)
    return name


def start_run(run_name: str | None = None, tags: dict | None = None):
    """Context manager wrapping mlflow.start_run with GCS artifact location."""
    return mlflow.start_run(
        run_name=run_name,
        tags=tags or {},
        artifact_location=settings.mlflow_artifact_location,
    )
