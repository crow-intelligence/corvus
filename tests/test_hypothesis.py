"""Property-based tests for corvus template generation.

Uses hypothesis to throw random inputs at the template and verify invariants
hold across the entire input space — not just hand-picked examples.
"""

from __future__ import annotations

import re
import string

from hypothesis import HealthCheck, given, settings, assume
from hypothesis import strategies as st

from pytest_cookies.plugin import Cookies

# ── Strategies ────────────────────────────────────────────────────────────────

LICENCES = [
    "MIT", "BSD-2-Clause", "BSD-3-Clause",
    "GPL-3.0-only", "LGPL-3.0-only", "AGPL-3.0-only",
    "CC-BY-4.0", "CC-BY-SA-4.0", "CC-BY-NC-4.0",
    "Proprietary", "Custom",
]

# Valid project slugs: starts with a letter, then lowercase alphanumeric + hyphens,
# at least 2 chars total (the pre_gen_project regex requires [a-z][a-z0-9\-]+).
valid_slug = st.from_regex(r"^[a-z][a-z0-9\-]{1,30}$", fullmatch=True).filter(
    lambda s: not s.endswith("-")  # avoid trailing hyphens — legal but ugly
)

valid_python_version = st.sampled_from(["3.10", "3.11", "3.12", "3.13", "3.10.1", "3.11.9"])

# Strings that should be rejected by the pre-gen hook
invalid_slug = st.text(
    alphabet=string.ascii_letters + string.digits + " !@#$%^&*()_+.",
    min_size=1, max_size=40,
).filter(lambda s: not re.match(r"^[a-z][a-z0-9\-]+$", s.lower().replace(" ", "-").replace("_", "-")))


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
}


def bake(cookies: Cookies, extra: dict | None = None):
    context = {**DEFAULTS, **(extra or {})}
    return cookies.bake(extra_context=context)


# Bump deadline — cookiecutter rendering is I/O-bound
SLOW = settings(
    max_examples=25,
    deadline=5000,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)


# ── Properties ────────────────────────────────────────────────────────────────

@given(name=valid_slug)
@SLOW
def test_any_valid_slug_bakes_successfully(cookies, name):
    """Every syntactically valid slug should produce a project without error."""
    result = bake(cookies, {"project_name": name})
    assert result.exit_code == 0, f"Failed for slug {name!r}: {result.exception}"


@given(name=valid_slug)
@SLOW
def test_package_dir_is_slug_underscored(cookies, name):
    """The src package directory should be the slug with hyphens → underscores."""
    result = bake(cookies, {"project_name": name})
    assume(result.exit_code == 0)
    expected_package = name.replace("-", "_")
    assert (result.project_path / "src" / expected_package).is_dir()


@given(name=valid_slug)
@SLOW
def test_project_dir_matches_slug(cookies, name):
    """The top-level directory name should equal the slug."""
    result = bake(cookies, {"project_name": name})
    assume(result.exit_code == 0)
    assert result.project_path.name == name


@given(
    licence=st.sampled_from(LICENCES),
    mlflow=st.sampled_from(["yes", "no"]),
    spacy=st.sampled_from(["yes", "no"]),
)
@SLOW
def test_all_option_combos_bake(cookies, licence, mlflow, spacy):
    """Every combination of licence × mlflow × spacy should bake cleanly."""
    result = bake(cookies, {
        "licence": licence,
        "use_mlflow": mlflow,
        "use_spacy": spacy,
    })
    assert result.exit_code == 0, (
        f"Failed for licence={licence}, mlflow={mlflow}, spacy={spacy}: "
        f"{result.exception}"
    )


@given(
    mlflow=st.sampled_from(["yes", "no"]),
    spacy=st.sampled_from(["yes", "no"]),
)
@SLOW
def test_pyproject_deps_match_flags(cookies, mlflow, spacy):
    """pyproject.toml should list mlflow/spacy iff the flags say so."""
    result = bake(cookies, {"use_mlflow": mlflow, "use_spacy": spacy})
    assume(result.exit_code == 0)
    pyproject = (result.project_path / "pyproject.toml").read_text()

    if mlflow == "yes":
        assert "mlflow" in pyproject
    else:
        assert "mlflow" not in pyproject

    if spacy == "yes":
        assert "spacy" in pyproject
    else:
        assert "spacy" not in pyproject


@given(mlflow=st.sampled_from(["yes", "no"]))
@SLOW
def test_tracking_py_iff_mlflow(cookies, mlflow):
    """tracking.py should exist exactly when mlflow is enabled."""
    result = bake(cookies, {"use_mlflow": mlflow})
    assume(result.exit_code == 0)
    tracking = result.project_path / "src" / "test_project" / "tracking.py"
    if mlflow == "yes":
        assert tracking.exists()
    else:
        assert not tracking.exists()


@given(version=valid_python_version)
@SLOW
def test_python_version_flows_into_pyproject(cookies, version):
    """The chosen Python version should appear in requires-python."""
    result = bake(cookies, {"python_version": version})
    assume(result.exit_code == 0)
    pyproject = (result.project_path / "pyproject.toml").read_text()
    assert f">={version}" in pyproject


@given(name=invalid_slug)
@SLOW
def test_invalid_names_always_rejected(cookies, name):
    """Anything that doesn't match the slug regex should fail pre-gen."""
    result = bake(cookies, {"project_name": name})
    assert result.exit_code != 0, f"Should have rejected {name!r}"


@given(
    description=st.text(min_size=1, max_size=120).filter(lambda s: s.strip()),
    author=st.text(
        alphabet=st.characters(categories=("L", "Zs"), min_codepoint=32),
        min_size=1, max_size=60,
    ).filter(lambda s: s.strip()),
)
@SLOW
def test_freeform_text_survives_rendering(cookies, description, author):
    """Descriptions and author names with unicode shouldn't crash rendering."""
    result = bake(cookies, {"description": description, "author_name": author})
    assert result.exit_code == 0, (
        f"Crashed on description={description!r}, author={author!r}: "
        f"{result.exception}"
    )


@given(name=valid_slug)
@SLOW
def test_scaffold_is_complete(cookies, name):
    """Every baked project should have the full directory skeleton."""
    result = bake(cookies, {"project_name": name})
    assume(result.exit_code == 0)
    root = result.project_path
    pkg = name.replace("-", "_")
    for path in [
        "data/raw/.gitkeep",
        "data/processed/.gitkeep",
        "data/external/.gitkeep",
        "models/.gitkeep",
        "reports/figures/.gitkeep",
        "notebooks/00-exploration.ipynb",
        "tests/test_placeholder.py",
        "docs/conf.py",
        "docs/index.rst",
        ".gitignore",
        ".dvcignore",
        ".env.template",
        ".pre-commit-config.yaml",
        "Makefile",
        "README.md",
        "LICENSE",
        "pyproject.toml",
        f"src/{pkg}/__init__.py",
        f"src/{pkg}/config.py",
        f"src/{pkg}/logging.py",
        f"src/{pkg}/py.typed",
        ".dvc/config",
        ".github/workflows/ci.yml",
    ]:
        assert (root / path).exists(), f"Missing {path} for project {name!r}"
