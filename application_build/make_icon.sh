#!/usr/bin/env bash
# 앱 아이콘 생성 — application_icon/ 폴더의 이미지를 소스로 사용.
#   · application_icon/ 안의 이미지(.icns 우선, 그다음 .png/.jpg/.jpeg)를 찾아
#     앱 아이콘(icon.icns) + 웹 UI 로고/파비콘(icon.png, 1024px)을 생성한다.
#   · 폴더가 없거나 비어 있으면 기존 icon.png 를 소스로 폴백한다.
#   · macOS 전용: sips + iconutil 사용.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

ICONDIR="$HERE/application_icon"
SRC=""

# 정사각형(±10%)인지 검사 — 가로형 시트(preview_sheet.png 등)를 아이콘으로 오인하지 않도록.
is_squareish() {
  local w h
  w="$(sips -g pixelWidth  "$1" 2>/dev/null | awk '/pixelWidth/{print $2}')"
  h="$(sips -g pixelHeight "$1" 2>/dev/null | awk '/pixelHeight/{print $2}')"
  [ -n "$w" ] && [ -n "$h" ] && [ "$h" -gt 0 ] || return 1
  # |w-h| <= 0.1 * max(w,h)
  local m=$(( w > h ? w : h )); local d=$(( w > h ? w-h : h-w ))
  [ $(( d * 10 )) -le "$m" ]
}

# 1) application_icon/ 에서 소스 이미지 탐색 (.icns 우선 → 정사각 .png/.jpg/.jpeg)
if [ -d "$ICONDIR" ]; then
  SRC="$(find "$ICONDIR" -maxdepth 1 -type f -iname '*.icns' | sort | head -n1)"
  if [ -z "$SRC" ]; then
    while IFS= read -r cand; do
      [ -z "$cand" ] && continue
      if is_squareish "$cand"; then SRC="$cand"; break; fi
      echo "  건너뜀(정사각형 아님): $(basename "$cand")"
    done < <(find "$ICONDIR" -maxdepth 1 -type f \
              \( -iname '*.png' -o -iname '*.jpg' -o -iname '*.jpeg' \) | sort)
  fi
fi

# 2) 폴더에 없으면 기존 icon.png 폴백
if [ -z "$SRC" ] && [ -f "$HERE/icon.png" ]; then
  SRC="$HERE/icon.png"
fi

if [ -z "$SRC" ]; then
  echo "  아이콘 소스 없음 (application_icon/ 또는 icon.png) — 기본 아이콘 사용"
  exit 0
fi
echo "  아이콘 소스: $SRC"

EXT="$(printf '%s' "${SRC##*.}" | tr '[:upper:]' '[:lower:]')"

# 작업용 PNG 확보 (.icns 면 png 로 변환)
WORK="$HERE/.icon_src.png"
if [ "$EXT" = "icns" ]; then
  sips -s format png "$SRC" --out "$WORK" >/dev/null
else
  sips -s format png "$SRC" --out "$WORK" >/dev/null
fi

# 투명 여백 정규화 → icon.png(1024). macOS 타일을 꽉 채워 '이중 테두리'를 없앤다.
# (PIL 필요. 없으면 원본 비율 그대로 1024 로만 맞춤 — 폴백)
PYBIN="$HERE/.venv-build/bin/python"
[ -x "$PYBIN" ] || PYBIN="python3"
if "$PYBIN" "$HERE/icon_normalize.py" "$WORK" "$HERE/icon.png" "${ICON_FILL:-0.805}" 1024 2>/dev/null; then
  echo "  정규화: 투명 여백 제거 → ${ICON_FILL:-0.805} 비율로 채움"
else
  echo "  (Pillow 없음 — 정규화 생략, 원본 비율 유지)"
  sips -s format png -z 1024 1024 "$WORK" --out "$HERE/icon.png" >/dev/null
fi
rm -f "$WORK"

# icon.png(1024) → iconset → icon.icns
ICONSET="$HERE/icon.iconset"
rm -rf "$ICONSET"; mkdir -p "$ICONSET"
for sz in 16 32 128 256 512; do
  sips -z $sz $sz             "$HERE/icon.png" --out "$ICONSET/icon_${sz}x${sz}.png"    >/dev/null
  sips -z $((sz*2)) $((sz*2)) "$HERE/icon.png" --out "$ICONSET/icon_${sz}x${sz}@2x.png" >/dev/null
done
iconutil -c icns "$ICONSET" -o "$HERE/icon.icns"
rm -rf "$ICONSET"

echo "  ✅ icon.icns (앱 아이콘) + icon.png (웹 로고) 생성 완료"
