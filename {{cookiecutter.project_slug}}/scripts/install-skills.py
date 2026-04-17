"""Install (or refresh) Claude Code skill packs listed in .claude/skills/MANIFEST.yaml.

Vendored packs (source: vendored) are left alone. Fetched packs (source: fetched)
are cloned with `git clone --depth=1` from their upstream repo; the relevant skill
tree is copied into `.claude/skills/<pack>/` and the upstream LICENSE is preserved
alongside. If a LICENSE isn't present upstream, an UPSTREAM.md pointer is written
instead so attribution stays visible.

Idempotent: re-running with the same manifest replaces the fetched trees in place.
Soft-failing: if git or network is unavailable, prints a warning and continues —
the rest of the project still works.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    import yaml
except ModuleNotFoundError:
    print("install-skills: PyYAML not installed — run `uv add --dev pyyaml` or `pip install pyyaml`.")
    sys.exit(1)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = PROJECT_ROOT / ".claude" / "skills" / "MANIFEST.yaml"
SKILLS_DIR = PROJECT_ROOT / ".claude" / "skills"


# Packs often don't keep every SKILL.md at the repo root — some keep them under
# a subdirectory (e.g. `skills/`). Tell the installer where to look per-pack.
# Default is "copy whatever's at the repo root that looks like skill content".
PACK_COPY_RULES: dict[str, dict] = {
    "data-analytics": {
        # nimrodfisher keeps skills in numbered top-level dirs
        "include_glob": "[0-9]*",
    },
    "anthropic": {
        # anthropics/skills lives under `skills/<skill>/SKILL.md` — copy the
        # contents of that subdir into our pack root, flattening one level.
        "subdir": "skills",
    },
}


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    print(f"  $ {' '.join(cmd)}")
    return subprocess.run(cmd, **kwargs)


def truthy(value) -> bool:
    """Accept YAML-booleans, strings 'yes/no/true/false', ints 0/1."""
    return str(value).strip().lower() in ("yes", "true", "1", "on")


def fetch_pack(pack: dict) -> bool:
    """Clone upstream, copy skill tree into .claude/skills/<name>/. Returns True on success."""
    name = pack["name"]
    url = pack["upstream"]
    ref = pack.get("ref", "main")
    dest = SKILLS_DIR / name

    if shutil.which("git") is None:
        print(f"  ⚠️  git not found on PATH — skipping pack '{name}'.")
        return False

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp) / name
        result = run(
            ["git", "clone", "--depth=1", "--branch", ref, url, str(tmp_dir)],
            check=False,
        )
        if result.returncode != 0:
            print(f"  ⚠️  git clone failed for '{name}' — skipping.")
            return False

        # Wipe any prior content so the install is a clean copy, not a merge.
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True)

        rule = PACK_COPY_RULES.get(name, {})
        source_root = tmp_dir / rule["subdir"] if rule.get("subdir") else tmp_dir
        if not source_root.is_dir():
            print(f"  ⚠️  source subdir '{rule.get('subdir')}' missing in upstream — skipping.")
            shutil.rmtree(dest)
            return False

        include_glob = rule.get("include_glob")
        if include_glob:
            copied_any = False
            for entry in sorted(source_root.glob(include_glob)):
                target = dest / entry.name
                if entry.is_dir():
                    shutil.copytree(entry, target)
                else:
                    shutil.copy2(entry, target)
                copied_any = True
            if not copied_any:
                print(f"  ⚠️  no entries matched glob '{include_glob}' in upstream — skipping.")
                shutil.rmtree(dest)
                return False
        else:
            # Copy everything except the upstream's own .git directory.
            for entry in source_root.iterdir():
                if entry.name == ".git":
                    continue
                target = dest / entry.name
                if entry.is_dir():
                    shutil.copytree(entry, target)
                else:
                    shutil.copy2(entry, target)

        # Preserve licence if upstream shipped one; otherwise leave a pointer.
        for licence_name in ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING"):
            src = tmp_dir / licence_name
            if src.exists():
                shutil.copy2(src, dest / licence_name)
                break
        else:
            (dest / "UPSTREAM.md").write_text(
                f"# {name}\n\n"
                f"Fetched from {url} (ref: {ref}).\n\n"
                f"Upstream did not ship a LICENSE file; see the repo for current licence status.\n"
            )

    print(f"  ✓ installed pack '{name}' from {url}")
    return True


def main() -> int:
    if not MANIFEST_PATH.exists():
        print(f"install-skills: no manifest at {MANIFEST_PATH} — nothing to do.")
        return 0

    manifest = yaml.safe_load(MANIFEST_PATH.read_text())
    packs = manifest.get("packs", [])
    if not packs:
        print("install-skills: manifest has no packs.")
        return 0

    failures = 0
    for pack in packs:
        name = pack["name"]
        wanted = truthy(pack.get("install", "no"))
        source = pack.get("source", "fetched")

        if source == "vendored":
            if wanted:
                print(f"── {name} (vendored, already in repo) ─────────────────────────")
            else:
                print(f"── {name} (vendored, but install=no — consider `rm -r .claude/skills/{name}`) ─")
            continue

        print(f"── {name} ({source}, install={'yes' if wanted else 'no'}) ──────────────────────")
        if not wanted:
            # Remove any stale fetched copy so the flag flipping off takes effect.
            dest = SKILLS_DIR / name
            if dest.exists():
                print(f"  removing stale {dest}")
                shutil.rmtree(dest)
            continue

        ok = fetch_pack(pack)
        if not ok:
            failures += 1

    if failures:
        print(f"\ninstall-skills: completed with {failures} pack(s) skipped due to errors.")
        # Soft-fail: don't return non-zero — generation should still succeed.
    return 0


if __name__ == "__main__":
    sys.exit(main())
