#!/usr/bin/env bash
# End-to-end smoke tests for the corvus template.
#
# Runs `uvx cookiecutter . --no-input` under several flag combinations and
# asserts the expected file tree + key content. Keeps GCS placeholders so the
# hook does NOT touch real cloud state. pyenv / uv / dvc / git / git-clone
# all run for real.
#
# Usage: scripts/smoke-test.sh [scenario-letter]   # e.g. A, B, ALL (default)
set -o pipefail

export PATH="$HOME/.local/bin:$PATH"

CORVUS_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SMOKE_ROOT="/tmp/corvus-smoke"
WANT="${1:-ALL}"

mkdir -p "$SMOKE_ROOT"

PASS=0
FAIL=0
FAILURES=""

say()   { printf '\n\033[1;36m── %s\033[0m\n' "$*"; }
pass()  { printf '  \033[32m✓\033[0m %s\n' "$*"; PASS=$((PASS+1)); }
fail()  { printf '  \033[31m✗\033[0m %s\n' "$*"; FAIL=$((FAIL+1)); FAILURES="$FAILURES\n  - $*"; }

assert_exists()    { if [ -e "$1" ]; then pass "$1 exists"; else fail "$1 MISSING"; fi; }
assert_missing()   { if [ ! -e "$1" ]; then pass "$1 absent (as expected)"; else fail "$1 PRESENT but should be absent"; fi; }
assert_greps()     { if grep -q "$2" "$1" 2>/dev/null; then pass "$1 contains '$2'"; else fail "$1 missing '$2'"; fi; }
assert_not_greps() { if ! grep -q "$2" "$1" 2>/dev/null; then pass "$1 does NOT contain '$2' (as expected)"; else fail "$1 contains '$2' but shouldn't"; fi; }

bake() {
  local dir="$1"; shift
  # uv venvs sometimes get site-packages with drw------- (no +x) which breaks
  # naive rm -rf — fix permissions first so re-runs are clean.
  [ -d "$dir" ] && chmod -R u+rwX "$dir" 2>/dev/null
  rm -rf "$dir"
  mkdir -p "$dir"
  # Extra overrides come as key=value args.
  say "generating into $dir with overrides: $*"
  (cd "$dir" && uvx cookiecutter "$CORVUS_DIR" --no-input "$@") 2>&1 | tail -40
}

# ── Scenario A — Defaults ────────────────────────────────────────────────────
scenario_A() {
  say "Scenario A — Defaults"
  local out="$SMOKE_ROOT/A"
  bake "$out"
  local proj="$out/my-project"
  assert_exists "$proj/CLAUDE.md"
  assert_greps "$proj/CLAUDE.md" "my_project"
  assert_greps "$proj/CLAUDE.md" "MLflow"
  assert_exists "$proj/src/my_project/tracking.py"
  assert_exists "$proj/.claude/skills/python-quality/pre-mortem/SKILL.md"
  assert_exists "$proj/.claude/skills/python-quality/LICENSE"
  assert_exists "$proj/.claude/skills/data-analytics/01-data-quality-validation/programmatic-eda/SKILL.md"
  assert_missing "$proj/.claude/skills/anthropic"
  assert_exists "$proj/scripts/install-skills.py"
  assert_exists "$proj/.claude/skills/MANIFEST.yaml"
}

# ── Scenario B — Full opt-in incl. Anthropic ─────────────────────────────────
scenario_B() {
  say "Scenario B — Full opt-in (anthropic=yes)"
  local out="$SMOKE_ROOT/B"
  bake "$out" install_claude_skills_anthropic=yes
  local proj="$out/my-project"
  assert_exists "$proj/.claude/skills/python-quality/pre-mortem/SKILL.md"
  assert_exists "$proj/.claude/skills/data-analytics"
  assert_exists "$proj/.claude/skills/anthropic"
  # At least one SKILL.md should have landed from anthropics/skills
  if find "$proj/.claude/skills/anthropic" -name SKILL.md | grep -q .; then
    pass "anthropic pack contains at least one SKILL.md"
  else
    fail "anthropic pack has no SKILL.md files"
  fi
}

# ── Scenario C — Full skills opt-out ─────────────────────────────────────────
scenario_C() {
  say "Scenario C — Full skills opt-out"
  local out="$SMOKE_ROOT/C"
  bake "$out" \
    install_claude_skills_python=no \
    install_claude_skills_analytics=no \
    install_claude_skills_anthropic=no
  local proj="$out/my-project"
  assert_exists "$proj/CLAUDE.md"                                     # always-on
  assert_exists "$proj/.claude/skills/MANIFEST.yaml"                  # always-on
  assert_missing "$proj/.claude/skills/python-quality"
  assert_missing "$proj/.claude/skills/data-analytics"
  assert_missing "$proj/.claude/skills/anthropic"
}

# ── Scenario D — NLP-heavy, no MLflow ────────────────────────────────────────
scenario_D() {
  say "Scenario D — NLP-heavy, no MLflow"
  local out="$SMOKE_ROOT/D"
  bake "$out" use_mlflow=no use_spacy=yes
  local proj="$out/my-project"
  assert_missing "$proj/src/my_project/tracking.py"
  assert_greps "$proj/pyproject.toml" "spacy"
  assert_not_greps "$proj/CLAUDE.md" "MLflow tracking"
  assert_exists "$proj/.claude/skills/python-quality/pre-mortem/SKILL.md"
  assert_exists "$proj/.claude/skills/data-analytics"
}

# ── Scenario F — install-skills make target idempotency ──────────────────────
scenario_F() {
  say "Scenario F — install-skills make target from within a generated project"
  local out="$SMOKE_ROOT/F"
  # Start from skills-off, then re-enable via MANIFEST + make install-skills
  bake "$out" \
    install_claude_skills_python=no \
    install_claude_skills_analytics=no \
    install_claude_skills_anthropic=no
  local proj="$out/my-project"
  assert_missing "$proj/.claude/skills/data-analytics"

  # Flip analytics to yes in the manifest, then run make install-skills
  sed -i 's|install: no|install: yes|' "$proj/.claude/skills/MANIFEST.yaml"
  (cd "$proj" && make install-skills) 2>&1 | tail -20
  assert_exists "$proj/.claude/skills/data-analytics/01-data-quality-validation/programmatic-eda/SKILL.md"

  # Second run should be idempotent
  (cd "$proj" && make install-skills) 2>&1 | tail -5
  assert_exists "$proj/.claude/skills/data-analytics/01-data-quality-validation/programmatic-eda/SKILL.md"
}

# ── Scenario E — Offline fallback ────────────────────────────────────────────
scenario_E() {
  say "Scenario E — Offline fallback (HTTPS_PROXY=bogus)"
  local out="$SMOKE_ROOT/E"
  rm -rf "$out"; mkdir -p "$out"
  (cd "$out" && HTTPS_PROXY="http://127.0.0.1:1" GIT_TERMINAL_PROMPT=0 \
     uvx cookiecutter "$CORVUS_DIR" --no-input \
     install_claude_skills_analytics=yes \
     install_claude_skills_anthropic=no) 2>&1 | tail -40 || true
  local proj="$out/my-project"
  assert_exists "$proj/CLAUDE.md"
  assert_exists "$proj/.claude/skills/python-quality/pre-mortem/SKILL.md"
  assert_missing "$proj/.claude/skills/data-analytics"
}

case "$WANT" in
  A) scenario_A ;;
  B) scenario_B ;;
  C) scenario_C ;;
  D) scenario_D ;;
  E) scenario_E ;;
  F) scenario_F ;;
  ALL)
    scenario_A
    scenario_C
    scenario_D
    scenario_F
    scenario_B
    scenario_E
    ;;
  *) echo "unknown scenario: $WANT" >&2; exit 2 ;;
esac

printf '\n\033[1m== RESULT ==\033[0m  \033[32m%d passed\033[0m / \033[31m%d failed\033[0m\n' "$PASS" "$FAIL"
if [ "$FAIL" -gt 0 ]; then
  printf '%b\n' "$FAILURES"
  exit 1
fi
