#!/usr/bin/env bash
# 더블클릭으로 바로 실행 (빌드 없이) — uv 가 의존성을 자동 처리.
# Finder 에서 더블클릭하거나 터미널에서:  ./launch.command
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

if command -v uv >/dev/null 2>&1; then
  exec uv run "$HERE/app.py"
else
  echo "uv 가 없어 venv 로 실행합니다…"
  VENV="$HERE/.venv-run"
  [ -d "$VENV" ] || python3 -m venv "$VENV"
  # shellcheck disable=SC1091
  source "$VENV/bin/activate"
  python -m pip install -q --upgrade pip >/dev/null
  python -m pip install -q -r "$HERE/requirements.txt"
  exec python "$HERE/app.py"
fi
