"""Post-generation hook for corvus.

Runs inside the newly created project directory after cookiecutter renders
the template. Orchestrates: pyenv, uv, DVC, MLflow config, git, pre-commit.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

# ── Values injected by cookiecutter ──────────────────────────────────────────

PROJECT_SLUG      = "{{cookiecutter.project_slug}}"
PACKAGE_NAME      = "{{cookiecutter.package_name}}"
PYTHON_VERSION    = "{{cookiecutter.python_version}}"
LICENCE           = "{{cookiecutter.licence}}"
AUTHOR_NAME       = "{{cookiecutter.author_name}}"
GCS_BUCKET        = "{{cookiecutter.gcs_bucket}}"
GCP_PROJECT_ID    = "{{cookiecutter.gcp_project_id}}"
GCS_REGION        = "{{cookiecutter.gcs_region}}"
USE_MLFLOW        = "{{cookiecutter.use_mlflow}}" == "yes"
MLFLOW_EXPERIMENT = "{{cookiecutter.mlflow_experiment}}"
USE_SPACY         = "{{cookiecutter.use_spacy}}" == "yes"

# GCS is "real" only if the user changed the placeholder values
GCS_ENABLED = (
    GCS_BUCKET != "gs://my-bucket"
    and GCP_PROJECT_ID != "my-gcp-project"
)

SPDX_URLS = {
    "MIT":            "MIT",
    "BSD-2-Clause":   "BSD-2-Clause",
    "BSD-3-Clause":   "BSD-3-Clause",
    "GPL-3.0-only":   "GPL-3.0-only",
    "LGPL-3.0-only":  "LGPL-3.0-only",
    "AGPL-3.0-only":  "AGPL-3.0-only",
    "CC-BY-4.0":      "CC-BY-4.0",
    "CC-BY-SA-4.0":   "CC-BY-SA-4.0",
    "CC-BY-NC-4.0":   "CC-BY-NC-4.0",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def run(cmd: list[str], check: bool = True, **kwargs) -> subprocess.CompletedProcess:
    print(f"  $ {' '.join(cmd)}")
    return subprocess.run(cmd, check=check, **kwargs)


def warn(msg: str) -> None:
    print(f"\n  ⚠️  WARNING: {msg}\n")


def tool_available(name: str) -> bool:
    return shutil.which(name) is not None


# ── Steps ─────────────────────────────────────────────────────────────────────

def setup_licence() -> None:
    print("\n── Licence ──────────────────────────────────────────────────────────")
    import datetime
    year = datetime.date.today().year
    licence_file = Path("LICENSE")

    if LICENCE in SPDX_URLS:
        spdx_id = SPDX_URLS[LICENCE]
        url = f"https://raw.githubusercontent.com/spdx/license-list-data/main/text/{spdx_id}.txt"
        try:
            with urllib.request.urlopen(url, timeout=10) as r:
                text = r.read().decode()
            text = text.replace("<year>", str(year)).replace("<author>", AUTHOR_NAME)
            licence_file.write_text(text)
            print(f"  ✓ Licence: {LICENCE}")
        except Exception as e:
            warn(f"Could not fetch licence text ({e}). Placeholder written to LICENSE.")
            licence_file.write_text(
                f"SPDX-License-Identifier: {spdx_id}\n\n"
                f"Copyright (c) {year} {AUTHOR_NAME}\n\n"
                "Licence text could not be fetched automatically.\n"
                f"See: https://spdx.org/licenses/{spdx_id}.html\n"
            )
    elif LICENCE == "Proprietary":
        licence_file.write_text(
            f"Copyright (c) {year} {AUTHOR_NAME}. All rights reserved.\n\n"
            "This software is proprietary and confidential. Unauthorised copying,\n"
            "distribution, or use is strictly prohibited.\n"
        )
        print("  ✓ Licence: Proprietary notice written.")
    else:  # Custom
        licence_file.write_text("# Add your licence text here\n")
        print("  ✓ Licence: Custom placeholder written — edit LICENSE before publishing.")


def setup_python() -> None:
    print("\n── Python ───────────────────────────────────────────────────────────")
    if not tool_available("pyenv"):
        warn(
            "pyenv not found. Install it from https://github.com/pyenv/pyenv\n"
            "  Then run: pyenv install <version> && pyenv local <version>"
        )
        return

    # Resolve latest patch version for the requested minor (e.g. 3.11 → 3.11.12)
    if PYTHON_VERSION.count(".") == 1:
        result = run(
            ["pyenv", "install", "--list"],
            capture_output=True, text=True, check=False
        )
        candidates = [
            line.strip() for line in result.stdout.splitlines()
            if line.strip().startswith(PYTHON_VERSION + ".")
            and line.strip().replace(".", "").isdigit()
        ]
        version = candidates[-1] if candidates else PYTHON_VERSION
    else:
        version = PYTHON_VERSION

    # Check if already installed
    installed = run(
        ["pyenv", "versions", "--bare"], capture_output=True, text=True, check=False
    ).stdout
    if version not in installed:
        print(f"  Python {version} not found — installing via pyenv (this may take a moment)...")
        run(["pyenv", "install", version])

    run(["pyenv", "local", version])
    print(f"  ✓ Python {version} set via pyenv.")


def setup_uv() -> None:
    print("\n── uv ───────────────────────────────────────────────────────────────")
    if not tool_available("uv"):
        warn(
            "uv not found. Install with:\n"
            "  curl -LsSf https://astral.sh/uv/install.sh | sh\n"
            "  Then re-run the post-gen setup manually."
        )
        return

    # Runtime deps
    runtime = ["numpy", "pandas", "structlog", "python-dotenv", "pydantic-settings"]
    if USE_MLFLOW:
        runtime.append("mlflow")
    if USE_SPACY:
        runtime.append("spacy")
    run(["uv", "add"] + runtime)

    # Dev deps
    run([
        "uv", "add", "--dev",
        "ruff", "ty", "pre-commit", "nbstripout",
        "pytest", "sphinx", "sphinx-rtd-theme",
    ])
    print("  ✓ uv initialised and dependencies installed.")


def setup_dvc() -> None:
    print("\n── DVC ──────────────────────────────────────────────────────────────")
    if not tool_available("dvc") and not Path(".venv").exists():
        warn("DVC not yet available — run 'uv sync' first, then 'uv run dvc init'.")
        return

    dvc = ["uv", "run", "dvc"]
    run(dvc + ["init"])

    if GCS_ENABLED:
        dvc_remote = f"{GCS_BUCKET}/dvc"
        run(dvc + ["remote", "add", "-d", "gcs_remote", dvc_remote])
        run(dvc + ["remote", "modify", "gcs_remote", "projectname", GCP_PROJECT_ID])
        print(f"  ✓ DVC remote configured: {dvc_remote}")
    else:
        warn(
            "GCS not configured — DVC remote not set.\n"
            "  Set GCS_BUCKET and GCP_PROJECT_ID in .env, then run:\n"
            "  uv run dvc remote add -d gcs_remote gs://<bucket>/dvc"
        )

    # Track data directories (generates .dvc pointer files)
    for path in ["data/raw", "data/processed", "models"]:
        run(dvc + ["add", path], check=False)


def setup_gcs_bucket() -> None:
    """Create the GCS bucket if it doesn't exist and tools are available."""
    print("\n── GCS bucket ───────────────────────────────────────────────────────")
    if not GCS_ENABLED:
        print("  Skipped — GCS not configured.")
        return
    if not tool_available("gsutil"):
        warn(
            "gsutil not found. Install Google Cloud SDK:\n"
            "  https://cloud.google.com/sdk/docs/install\n"
            f"  Then create the bucket manually:\n"
            f"  gsutil mb -l {GCS_REGION} {GCS_BUCKET}"
        )
        return

    # Check if bucket exists
    result = run(
        ["gsutil", "ls", "-b", GCS_BUCKET],
        check=False, capture_output=True
    )
    if result.returncode == 0:
        print(f"  ✓ Bucket {GCS_BUCKET} already exists.")
    else:
        print(f"  Creating bucket {GCS_BUCKET} in region {GCS_REGION}...")
        result = run(
            ["gsutil", "mb", "-l", GCS_REGION, GCS_BUCKET],
            check=False
        )
        if result.returncode != 0:
            warn(
                f"Could not create bucket. You may need to run manually:\n"
                f"  gsutil mb -l {GCS_REGION} {GCS_BUCKET}"
            )
        else:
            print(f"  ✓ Bucket created.")


def remove_mlflow_files() -> None:
    """Remove tracking.py if MLflow was not requested."""
    tracking = Path(f"src/{PACKAGE_NAME}/tracking.py")
    if not USE_MLFLOW and tracking.exists():
        tracking.unlink()


def setup_precommit() -> None:
    print("\n── pre-commit ───────────────────────────────────────────────────────")
    result = run(["uv", "run", "pre-commit", "install"], check=False)
    if result.returncode != 0:
        warn("pre-commit install failed — run 'uv run pre-commit install' manually.")
        return
    run(["uv", "run", "nbstripout", "--install", "--attributes", ".gitattributes"],
        check=False)
    print("  ✓ pre-commit hooks installed.")


def setup_git() -> None:
    print("\n── git ──────────────────────────────────────────────────────────────")
    run(["git", "init"])
    run(["git", "add", "."])
    mlflow_note = f"- MLflow (local tracking, GCS artifacts)\n" if USE_MLFLOW else ""
    gcs_note = f"- DVC remote at {GCS_BUCKET}/dvc\n" if GCS_ENABLED else "- DVC (GCS remote not yet configured)\n"
    msg = (
        "chore: initialise corvus project scaffold\n\n"
        f"- Python {PYTHON_VERSION} via pyenv\n"
        "- uv + ruff + ty + pre-commit\n"
        "- structlog logging, pydantic-settings config\n"
        f"{mlflow_note}"
        f"{gcs_note}"
        "- Sphinx docs scaffold\n"
        f"- Licence: {LICENCE}\n"
    )
    run(["git", "commit", "-m", msg])
    print("  ✓ Initial commit created.")


def print_summary() -> None:
    gcs_line = f"  Data       : DVC → {GCS_BUCKET}/dvc" if GCS_ENABLED else "  Data       : DVC (configure GCS in .env)"
    mlflow_line = f"  MLflow     : local tracking / GCS artifacts" if USE_MLFLOW else "  MLflow     : not enabled"
    print(f"""
╔════════════════════════════════════════════════╗
║           corvus scaffold complete             ║
╠════════════════════════════════════════════════╣
║  Project    : {PROJECT_SLUG:<31} ║
║  Python     : {PYTHON_VERSION:<31} ║
║  Licence    : {LICENCE:<31} ║
╠════════════════════════════════════════════════╣
{gcs_line}
{mlflow_line}
╠════════════════════════════════════════════════╣
║  Next steps:                                   ║
║    cp .env.template .env   # add GCP creds     ║
║    uv sync                                     ║
║    uv run dvc pull         # once data exists  ║
║    make help                                   ║
╚════════════════════════════════════════════════╝
""")


def main() -> None:
    remove_mlflow_files()
    setup_licence()
    setup_python()
    setup_uv()
    setup_gcs_bucket()
    setup_dvc()
    setup_precommit()
    setup_git()
    print_summary()


if __name__ == "__main__":
    main()
