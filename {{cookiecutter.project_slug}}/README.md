# {{cookiecutter.project_name}}

{{cookiecutter.description}}

## Setup

```bash
cp .env.template .env   # fill in your credentials
uv sync
make help
```

## Project structure

```
├── data/
│   ├── raw/          ← original, immutable data (DVC-tracked)
│   ├── processed/    ← transformed data (DVC-tracked)
│   └── external/
├── docs/             ← Sphinx docs
├── models/           ← serialised models (DVC-tracked)
├── notebooks/        ← exploratory analysis
├── reports/figures/  ← generated graphics
└── src/{{cookiecutter.package_name}}/
    ├── config.py     ← typed settings via pydantic-settings
    ├── logging.py    ← structlog setup
    └── tracking.py   ← MLflow helpers (if enabled)
```

## Common commands

```bash
make lint       # ruff check
make fmt        # ruff format
make typecheck  # ty check
make test       # pytest
make docs       # sphinx build
make dvc-push   # push data to GCS
make dvc-pull   # pull data from GCS
```

---

*Scaffolded with [corvus](https://github.com/crow-intelligence/corvus).*
