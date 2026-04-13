import re
import sys

project_slug = "{{cookiecutter.project_slug}}"
python_version = "{{cookiecutter.python_version}}"

# Validate project slug: lowercase letters, digits, hyphens only
if not re.match(r"^[a-z][a-z0-9\-]+$", project_slug):
    print(f"ERROR: project slug '{project_slug}' must be lowercase letters, digits, and hyphens.")
    sys.exit(1)

# Validate Python version format: X.Y or X.Y.Z
if not re.match(r"^\d+\.\d+(\.\d+)?$", python_version):
    print(f"ERROR: python_version '{python_version}' must be in the form 3.11 or 3.11.9")
    sys.exit(1)
