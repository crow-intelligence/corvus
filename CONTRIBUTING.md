# Contributing to corvus

Thanks for your interest in contributing. Corvus is maintained by
[Crow Intelligence](https://crow-intelligence.github.io/) and built for our own
research workflow — but we're happy to accept improvements that keep the template
focused and useful for others doing similar work.

---

## How to contribute

1. Fork the repo and create a branch: `git checkout -b my-improvement`
2. Make your changes (see development setup below)
3. Run the template tests: `make test`
4. Open a pull request with a clear description of what changed and why

For anything non-trivial, open an issue first so we can discuss before you invest
the time building it.

---

## Development setup

```bash
git clone git@github.com:crow-intelligence/corvus.git
cd corvus
uv sync
make test
```

Tests use [pytest-cookies](https://github.com/hackebrot/pytest-cookies) to bake
the template and verify the rendered output without running the post-gen hook.

```bash
uv run pytest tests/ -v
```

To manually test the full flow including the post-gen hook (pyenv, uv, DVC, git):

```bash
uvx cookiecutter . --no-input
```

---

## What we'll accept

**Good candidates for PRs:**

- Bug fixes in the post-gen hook (pyenv, uv, DVC, GCS setup)
- Improvements to the `.gitignore` or `.dvcignore` defaults
- Better error messages or recovery in the hook
- Additional test coverage for the template
- Fixes to generated config files (ruff, ty, pyproject.toml)
- Documentation improvements

**Please open an issue to discuss first:**

- New optional features or prompts (we want to keep the prompt list short)
- Changes to the default dependency set
- Changes to the project structure

---

## Roadmap / v2 wishlist

These are explicitly out of scope for v1 and would be considered for a future version.
If you'd like to work on one, open an issue first.

- **Remote MLflow tracking server** — e.g. Cloud Run + GCS backend, so the whole team
  shares one tracking server rather than each having local `.mlruns/`
- **Docker / devcontainer** — a `Dockerfile` and `.devcontainer/` for reproducible
  environments
- **Windows support** — the post-gen hook currently assumes a Unix shell
- **Automatic GitHub repo creation** — via `gh` CLI
- **MkDocs variant** — an alternative to the Sphinx scaffold for those who prefer it
- **PyPI publishing** — so corvus can be run with `uvx corvus` rather than
  `uvx cookiecutter https://...`

---

## Code style

The corvus repo itself follows its own standards:

```bash
make lint       # ruff check
make fmt        # ruff format
```

Pre-commit hooks are installed via `make install`.

---

## Licence

By contributing, you agree that your contributions will be licenced under the
[MIT Licence](LICENSE).
