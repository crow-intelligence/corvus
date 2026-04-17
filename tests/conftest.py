"""Test configuration for corvus template tests.

Patches the post-generation hook so that tests validate the rendered file tree
without running the heavy automation (uv, DVC, git). The pre-generation
hook (input validation) still runs normally.
"""

import os

import pytest

import cookiecutter.generate

_original_run_hook = cookiecutter.generate.run_hook_from_repo_dir


@pytest.fixture(autouse=True)
def skip_post_gen_hook(monkeypatch):
    """Skip the post-gen hook but replicate its file-cleanup logic."""

    def patched(repo_dir, hook_name, project_dir, context, delete_project_on_failure):
        if hook_name == "post_gen_project":
            # Replicate remove_mlflow_files() so tracking.py tests pass
            cc = context.get("cookiecutter", {})
            if cc.get("use_mlflow") != "yes":
                tracking = os.path.join(
                    str(project_dir), "src", cc.get("package_name", ""), "tracking.py"
                )
                if os.path.exists(tracking):
                    os.remove(tracking)
            # Replicate prune_python_skills() so skills tests pass
            if cc.get("install_claude_skills_python") != "yes":
                import shutil
                python_skills = os.path.join(
                    str(project_dir), ".claude", "skills", "python-quality"
                )
                if os.path.isdir(python_skills):
                    shutil.rmtree(python_skills)
            return
        return _original_run_hook(
            repo_dir, hook_name, project_dir, context, delete_project_on_failure
        )

    monkeypatch.setattr(
        "cookiecutter.generate.run_hook_from_repo_dir", patched
    )
