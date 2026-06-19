#!/usr/bin/env bash
# K-Market Dashboard — macOS .app 빌드 스크립트 (Apple Silicon / M4 Pro)
# 원본 소스는 건드리지 않고 application_build/ 안에서만 동작한다.
#
#   사용법:  cd application_build && ./build.sh
#   산출물:  application_build/dist/K-Market Dashboard.app
set -euo pipefail

# 공백이 포함된 경로 대비 — 항상 큰따옴표
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

VENV="$HERE/.venv-build"
PYBIN="python3"

echo "▶ [1/5] 빌드용 가상환경 준비: $VENV"
if [ ! -d "$VENV" ]; then
  "$PYBIN" -m venv "$VENV"
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"

echo "▶ [2/5] 의존성 설치 (pip)"
python -m pip install --upgrade pip wheel >/dev/null
python -m pip install -r "$HERE/requirements.txt"
python -m pip install "pyinstaller>=6.6"
python -m pip install "pillow>=10.0"   # 빌드 전용: 아이콘 여백 정규화(icon_normalize.py)

echo "▶ [3/5] 아이콘 준비 (app_icon_final/squircle_fixed.png → icon.icns + icon.png)"
# 사용자가 지정한 완성형 아이콘(app_icon_final/squircle_fixed.png, 투명 코너 1024 스퀴클)을 가공 없이
# 그대로 사용한다 → Dock/DMG/웹 로고가 모두 이 아이콘으로 통일. --no-apply 로 빌드 중엔
# 설치앱 적용을 건너뛰고(아래 PyInstaller 산출물에 icon.icns 가 들어감) 파일만 생성.
if command -v uv >/dev/null 2>&1 && uv run "$HERE/make_app_icon.py" --no-apply; then
  :
elif python "$HERE/make_app_icon.py" --no-apply; then
  :
else
  echo "  (아이콘 빌더 실패 — 기존 icon.icns/icon.png 사용)"
fi

echo "▶ [4/5] 이전 산출물 정리"
# 실행 중인 앱을 먼저 종료 (파일 핸들 해제) — 없으면 무시
osascript -e 'tell application "K-Market Dashboard" to quit' 2>/dev/null || true
pkill -f "K-Market Dashboard" 2>/dev/null || true
sleep 0.5
# macOS locked 플래그 해제 후 삭제 (Finder/Spotlight가 잠근 경우 대비)
chflags -R nouchg "$HERE/build" "$HERE/dist" 2>/dev/null || true
rm -rf "$HERE/build" "$HERE/dist"

echo "▶ [5/5] PyInstaller 빌드"
pyinstaller "$HERE/market_dashboard.spec" --noconfirm --clean

APP="$HERE/dist/K-Market Dashboard.app"
if [ -d "$APP" ]; then
  # Gatekeeper quarantine 속성 제거(로컬 실행 편의)
  xattr -dr com.apple.quarantine "$APP" 2>/dev/null || true

  # ── 정리: 중간 산출물 제거 → dist 에는 .app 만 남긴다 ──
  echo "▶ 정리: 중간 산출물 제거"
  rm -rf "$HERE/build" "$HERE/dist/K-Market Dashboard"

  # ── 설치: 응용 프로그램(/Applications)에 추가 ──
  echo "▶ 설치: /Applications 에 추가"
  DEST="/Applications/K-Market Dashboard.app"
  if rm -rf "$DEST" 2>/dev/null && cp -R "$APP" "/Applications/" 2>/dev/null; then
    xattr -dr com.apple.quarantine "$DEST" 2>/dev/null || true
    INSTALLED=1
  else
    INSTALLED=0
  fi

  # ── 배포용 DMG 패키징 ("드래그 → 응용 프로그램" 설치 디스크 이미지) ──
  # macOS 내장 hdiutil 만 사용(추가 설치 불필요). 미서명/미공증 — 개인·로컬 배포용.
  echo "▶ DMG 패키징"
  DMG="$HERE/dist/K-Market Dashboard.dmg"
  STAGING="$(mktemp -d)"
  if cp -R "$APP" "$STAGING/" 2>/dev/null; then
    ln -s /Applications "$STAGING/Applications"
    rm -f "$DMG"
    if hdiutil create -volname "K-Market Dashboard" -srcfolder "$STAGING" \
         -ov -format UDZO "$DMG" >/dev/null 2>&1; then
      xattr -dr com.apple.quarantine "$DMG" 2>/dev/null || true
      DMG_OK=1
    else
      DMG_OK=0
    fi
  else
    DMG_OK=0
  fi
  rm -rf "$STAGING"

  echo ""
  echo "✅ 빌드 완료:"
  echo "   $APP"
  if [ "${INSTALLED:-0}" = "1" ]; then
    echo "   /Applications 에 설치됨 — Launchpad·Spotlight 에서 'K-Market Dashboard' 실행"
  else
    echo "   (⚠ /Applications 설치 실패 — 권한 문제일 수 있음. 수동: cp -R \"$APP\" /Applications/)"
  fi
  if [ "${DMG_OK:-0}" = "1" ]; then
    echo "   배포용 DMG:  $DMG"
    echo "                (열어서 앱을 Applications 폴더로 드래그)"
  else
    echo "   (⚠ DMG 생성 실패 — hdiutil 로그 확인)"
  fi
  echo ""
  echo "   더블클릭 또는:  open \"$APP\""
else
  echo "❌ 빌드 실패 — 위 로그를 확인하세요."
  exit 1
fi
