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
make lint            # ruff check
make fmt             # ruff format
make typecheck       # ty check
make test            # pytest
make docs            # sphinx build
make dvc-push        # push data to GCS
make dvc-pull        # pull data from GCS
make install-skills  # (re)install Claude Code skill packs
```

## Claude Code

This project ships with a `CLAUDE.md` at the root and skill packs under `.claude/skills/`:
{% if cookiecutter.install_claude_skills_python == "yes" %}
- `python-quality` — Python code-quality skills (vendored from [honnibal/claude-skills](https://github.com/honnibal/claude-skills), MIT)
{%- endif %}
{%- if cookiecutter.install_claude_skills_analytics == "yes" %}
- `data-analytics` — analytics workflow skills (fetched from [nimrodfisher/data-analytics-skills](https://github.com/nimrodfisher/data-analytics-skills))
{%- endif %}
{%- if cookiecutter.install_claude_skills_anthropic == "yes" %}
- `anthropic` — Anthropic's official skills (fetched from [anthropics/skills](https://github.com/anthropics/skills), Apache-2.0)
{%- endif %}

See `.claude/skills/README.md` for details. Edit `.claude/skills/MANIFEST.yaml` and re-run `make install-skills` to change which packs are installed.

---

*Scaffolded with [corvus](https://github.com/crow-intelligence/corvus).*
