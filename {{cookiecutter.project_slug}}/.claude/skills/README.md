# Claude Code skills for this project

Skills in this directory are discovered automatically by Claude Code when you open this project. Each skill is a `SKILL.md` file (with optional helper scripts alongside) inside a directory whose path determines the skill name.

The canonical list of installed / available packs is in `MANIFEST.yaml`. To change what's installed, edit the `install:` flag for a pack and run `make install-skills` from the project root.

## Packs

### python-quality — vendored, MIT

Matthew Honnibal's Python code-quality skills, copied into this repo:

- `pre-mortem` — identifies fragile code by writing fictional post-mortems for future bugs
- `contract-docstrings` — writes docstrings that document preconditions, raises, and silenced errors
- `try-except` — audits exception handling for scope, specificity, and silent-failure risk
- `tighten-types` — reviews and improves Python type annotations
- `hypothesis-tests` — designs property-based tests with the `hypothesis` library
- `mutation-testing` — assesses test-suite strength by deliberate bug injection
- `stub-package` — emits a condensed structural overview of a Python package

Upstream: https://github.com/honnibal/claude-skills

### data-analytics — fetched from upstream

Nimrod Fisher's analytics skills (30 skills, 6 categories). Fetched by `scripts/install-skills.py`; upstream has no LICENSE file, so use at your own discretion.

Upstream: https://github.com/nimrodfisher/data-analytics-skills

### anthropic — fetched, Apache-2.0

Anthropic's official skill library. Opt-in.

Upstream: https://github.com/anthropics/skills

## Adding more skills

To add a skill of your own, create a new directory under this one with a `SKILL.md` file inside. Frontmatter minimum:

```markdown
---
name: my-skill
description: One short sentence explaining what the skill does.
---

# Skill body in markdown...
```

To pull in an additional third-party pack, append an entry to `MANIFEST.yaml` and extend `scripts/install-skills.py` if its upstream layout is unusual.

## Scoping (user-level vs. project-level)

These skills live at `.claude/skills/` — project-scoped, committed to git, shared with collaborators. If you want a skill available across **all** your projects, symlink it into `~/.claude/skills/`:

```
ln -s "$PWD/.claude/skills/python-quality/pre-mortem" ~/.claude/skills/pre-mortem
```
