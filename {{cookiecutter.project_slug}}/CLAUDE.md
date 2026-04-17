# {{ cookiecutter.project_slug }}

{{ cookiecutter.description }}

- **Package:** `{{ cookiecutter.package_name }}` (importable as `from {{ cookiecutter.package_name }} import ...`)
- **Python:** {{ cookiecutter.python_version }} (managed by uv, pinned in `.python-version`)
- **Package manager:** uv — all commands prefixed with `uv run`
- **Linter / formatter:** ruff (line length 88) — `make lint`, `make fmt`
- **Type checker:** ty — `make typecheck`
- **Logging:** structlog — get a logger via `from {{ cookiecutter.package_name }}.logging import get_logger`
- **Config:** pydantic-settings reading `.env` — see `src/{{ cookiecutter.package_name }}/config.py`

## Layout

```
data/
  raw/        — original, immutable (DVC-tracked)
  processed/  — transformed (DVC-tracked)
  external/   — third-party inputs
models/       — serialised models / embeddings (DVC-tracked)
notebooks/    — exploratory, run via `uv run jupyter`
reports/      — generated figures and write-ups
src/{{ cookiecutter.package_name }}/ — the importable package
docs/         — Sphinx scaffold
tests/        — pytest
```

## Commands

```
make help          show all targets
make install       sync deps + install pre-commit hooks
make lint          ruff check
make fmt           ruff format
make typecheck     ty type check
make test          pytest
make docs          sphinx build → docs/_build/html
make dvc-pull      pull data+models from GCS
make dvc-push      push data+models to GCS
make install-skills  (re)install Claude Code skill packs per .claude/skills/MANIFEST.yaml
```

## Data and artifacts

DVC remote is `{{ cookiecutter.gcs_bucket }}/dvc`. To track a new raw file:

```
uv run dvc add data/raw/<file>
git add data/raw/<file>.dvc data/raw/.gitignore
uv run dvc push
```
{% if cookiecutter.use_mlflow == "yes" %}
MLflow tracking is **local** (`mlruns/`, gitignored); artifacts go to `{{ cookiecutter.gcs_bucket }}/mlflow`. Use the helpers in `{{ cookiecutter.package_name }}.tracking`:

```python
from {{ cookiecutter.package_name }}.tracking import init_experiment, start_run
import mlflow

init_experiment()
with start_run("run-name"):
    mlflow.log_param(...)
```

View runs with `uv run mlflow ui`.
{% endif %}

## Claude Code skills

This project ships with skill packs under `.claude/skills/`. See `.claude/skills/README.md` for what's installed and how to add more.

{% if cookiecutter.install_claude_skills_python == "yes" -%}
- **python-quality** (vendored, MIT) — `pre-mortem`, `contract-docstrings`, `try-except`, `tighten-types`, `hypothesis-tests`, `mutation-testing`, `stub-package`
{% endif -%}
{% if cookiecutter.install_claude_skills_analytics == "yes" -%}
- **data-analytics** (fetched) — 30 analytics skills across data quality, documentation, analysis, visualisation, stakeholder comms, workflow
{% endif -%}
{% if cookiecutter.install_claude_skills_anthropic == "yes" -%}
- **anthropic** (fetched, Apache-2.0) — Anthropic's official skill library
{% endif %}
To change what's installed, edit `.claude/skills/MANIFEST.yaml` and run `make install-skills`.

## Conventions

- Keep `src/{{ cookiecutter.package_name }}/` importable and test-covered; ad-hoc scripts live in `notebooks/` or `scripts/`.
- Notebooks are stripped of outputs on commit by `nbstripout`.
- pre-commit runs ruff + nbstripout on every commit; don't `--no-verify`.
- Secrets and GCP creds belong in `.env` (gitignored, template at `.env.template`).
