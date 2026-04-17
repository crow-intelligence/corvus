"""Tests for corvus template generation.

Uses pytest-cookies to bake the template without running the post-gen hook,
then asserts the rendered file structure and content.
"""

import pytest
from pytest_cookies.plugin import Cookies


DEFAULTS = {
    "project_name": "test-project",
    "description": "A test project",
    "author_name": "Test Author",
    "author_email": "test@example.com",
    "python_version": "3.11",
    "licence": "MIT",
    "gcs_bucket": "gs://my-bucket",
    "gcp_project_id": "my-gcp-project",
    "gcs_region": "EU",
    "use_mlflow": "yes",
    "mlflow_experiment": "test-project",
    "use_spacy": "no",
    "install_claude_skills_python": "yes",
    "install_claude_skills_analytics": "yes",
    "install_claude_skills_anthropic": "no",
}


def bake(cookies: Cookies, extra: dict | None = None) -> object:
    context = {**DEFAULTS, **(extra or {})}
    return cookies.bake(extra_context=context)


def test_bakes_without_error(cookies):
    result = bake(cookies)
    assert result.exit_code == 0
    assert result.exception is None


def test_project_structure(cookies):
    result = bake(cookies)
    root = result.project_path
    assert (root / "src" / "test_project").is_dir()
    assert (root / "data" / "raw" / ".gitkeep").exists()
    assert (root / "data" / "processed" / ".gitkeep").exists()
    assert (root / "models" / ".gitkeep").exists()
    assert (root / "notebooks").is_dir()
    assert (root / "docs" / "conf.py").exists()
    assert (root / "Makefile").exists()
    assert (root / "pyproject.toml").exists()
    assert (root / ".gitignore").exists()
    assert (root / ".dvcignore").exists()
    assert (root / ".env.template").exists()
    assert (root / "LICENSE").exists()


def test_mlflow_tracking_present_when_enabled(cookies):
    result = bake(cookies, {"use_mlflow": "yes"})
    assert (result.project_path / "src" / "test_project" / "tracking.py").exists()


def test_mlflow_tracking_absent_when_disabled(cookies):
    result = bake(cookies, {"use_mlflow": "no"})
    assert not (result.project_path / "src" / "test_project" / "tracking.py").exists()


def test_package_name_derived_from_project_name(cookies):
    result = bake(cookies, {"project_name": "my-nlp-project"})
    assert (result.project_path / "src" / "my_nlp_project").is_dir()


def test_licence_in_pyproject(cookies):
    result = bake(cookies, {"licence": "MIT"})
    pyproject = (result.project_path / "pyproject.toml").read_text()
    assert "MIT" in pyproject


def test_spacy_in_pyproject_when_enabled(cookies):
    result = bake(cookies, {"use_spacy": "yes"})
    assert "spacy" in (result.project_path / "pyproject.toml").read_text()


def test_spacy_not_in_pyproject_when_disabled(cookies):
    result = bake(cookies, {"use_spacy": "no"})
    assert "spacy" not in (result.project_path / "pyproject.toml").read_text()


def test_invalid_project_name_fails(cookies):
    result = bake(cookies, {"project_name": "My Invalid Project!"})
    assert result.exit_code != 0


def test_claude_md_always_created(cookies):
    result = bake(cookies)
    assert (result.project_path / "CLAUDE.md").exists()


def test_claude_md_templates_package_name(cookies):
    result = bake(cookies, {"project_name": "my-nlp-project"})
    claude_md = (result.project_path / "CLAUDE.md").read_text()
    assert "my_nlp_project" in claude_md
    assert "my-nlp-project" in claude_md


def test_python_skills_bundled_when_enabled(cookies):
    result = bake(cookies, {"install_claude_skills_python": "yes"})
    pack = result.project_path / ".claude" / "skills" / "python-quality"
    assert (pack / "pre-mortem" / "SKILL.md").exists()
    assert (pack / "LICENSE").exists()


def test_python_skills_absent_when_disabled(cookies):
    result = bake(cookies, {"install_claude_skills_python": "no"})
    assert not (
        result.project_path / ".claude" / "skills" / "python-quality"
    ).exists()


def test_claude_manifest_and_settings_always_present(cookies):
    result = bake(cookies)
    assert (result.project_path / ".claude" / "settings.json").exists()
    assert (result.project_path / ".claude" / "skills" / "MANIFEST.yaml").exists()
    assert (result.project_path / ".claude" / "skills" / "README.md").exists()


def test_install_skills_script_present(cookies):
    result = bake(cookies)
    assert (result.project_path / "scripts" / "install-skills.py").exists()


def test_install_skills_make_target_present(cookies):
    result = bake(cookies)
    makefile = (result.project_path / "Makefile").read_text()
    assert "install-skills" in makefile
