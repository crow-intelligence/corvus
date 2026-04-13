"""Project configuration loaded from environment variables / .env file."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # GCP / GCS
    google_application_credentials: str = ""
    gcp_project_id: str = "{{cookiecutter.gcp_project_id}}"
    gcs_bucket: str = "{{cookiecutter.gcs_bucket}}"

    # MLflow
    mlflow_experiment: str = "{{cookiecutter.mlflow_experiment}}"
    mlflow_tracking_uri: str = "mlruns"
    mlflow_artifact_location: str = "{{cookiecutter.gcs_bucket}}/mlflow"

    # General
    log_level: str = "INFO"
    random_seed: int = 42


settings = Settings()
