# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow"]
# ///
"""K-Market Dashboard 앱 아이콘 빌드 — 완성형 PNG를 그대로 사용.

소스: app_real_final_1.png (1024 RGBA, 투명 코너의 macOS 스퀴클 타일 — 이미 여백·라운딩
      완성됨). 흰 글라스 템플릿 재합성(build_macos26_icon.py)과 달리 **가공 없이** 그대로
      아이콘으로 쓴다. 사용자가 지정한 그 아이콘이 Dock/DMG/웹 로고에 그대로 나온다.

출력: icon.png(마스터·웹 로고/파비콘 소스), icon.icns(.app 번들 아이콘),
      application_icon/ 갱신, (옵션) 설치된 앱에 즉시 적용.

실행: uv run make_app_icon.py [--no-apply]
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
# 사용자가 지정한 최종 아이콘. Downloads 원본이 있으면 그것을 application_build/ 로 동기화.
DOWNLOADS_SRC = Path("/Users/minjun1803/Documents/Python/Project_Market_Dashboard/application_build/app_icon_final/squircle_fixed.png")
SRC = HERE / "app_icon_final" / "squircle_fixed.png"
CANVAS = 1024


def _resolve_source() -> Path:
    if DOWNLOADS_SRC.is_file():
        # 빌드를 self-contained 하게 — 원본을 application_build/ 로 복사해 둔다.
        try:
            if (not SRC.exists()) or DOWNLOADS_SRC.read_bytes() != SRC.read_bytes():
                shutil.copy2(DOWNLOADS_SRC, SRC)
                print(f"  • 소스 동기화: {DOWNLOADS_SRC} → {SRC.name}")
        except Exception as e:  # noqa: BLE001
            print(f"  (소스 동기화 생략: {e})")
    if not SRC.is_file():
        raise SystemExit(f"아이콘 소스를 찾을 수 없습니다: {SRC}")
    return SRC


def build_master() -> Image.Image:
    im = Image.open(_resolve_source()).convert("RGBA")
    if im.size != (CANVAS, CANVAS):
        im = im.resize((CANVAS, CANVAS), Image.LANCZOS)
    return im


def make_icns(master: Image.Image, out_png: Path, out_icns: Path) -> None:
    master.save(out_png)
    print(f"  • 마스터 저장 → {out_png.name}")
    iconset = HERE / "icon.iconset"
    if iconset.exists():
        shutil.rmtree(iconset)
    iconset.mkdir()
    for pt in (16, 32, 128, 256, 512):
        for scale in (1, 2):
            px = pt * scale
            name = f"icon_{pt}x{pt}{'@2x' if scale == 2 else ''}.png"
            master.resize((px, px), Image.LANCZOS).save(iconset / name)
    r = subprocess.run(["iconutil", "-c", "icns", str(iconset), "-o", str(out_icns)],
                       capture_output=True, text=True)
    shutil.rmtree(iconset, ignore_errors=True)
    if r.returncode != 0:
        raise SystemExit(f"iconutil 실패: {r.stderr}")
    print(f"  • icns 생성 → {out_icns.name}")


def apply_to_app(icns: Path) -> None:
    app = Path("/Applications/K-Market Dashboard.app")
    plist = app / "Contents" / "Info.plist"
    if not plist.exists():
        print("  ⚠️ 설치된 앱 없음 — 적용 생략")
        return
    import plistlib
    name = plistlib.loads(plist.read_bytes()).get("CFBundleIconFile", "AppIcon")
    if not name.endswith(".icns"):
        name += ".icns"
    dest = app / "Contents" / "Resources" / name
    shutil.copy2(icns, dest)
    subprocess.run(["touch", str(app)], check=False)
    subprocess.run([
        "/System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/"
        "LaunchServices.framework/Versions/A/Support/lsregister", "-f", str(app)
    ], check=False)
    subprocess.run(["killall", "Dock"], check=False)
    subprocess.run(["killall", "Finder"], check=False)
    print(f"  • 설치앱 적용 → {dest}  (LaunchServices·Dock·Finder 갱신)")


def main() -> None:
    print("앱 아이콘 빌드 (완성형 PNG 직접 사용)")
    master = build_master()

    # 미리보기(검증): 어두운/밝은 배경 합성
    prev = Image.new("RGBA", (CANVAS * 2 + 30, CANVAS), (0, 0, 0, 0))
    for i, bg in enumerate([(20, 20, 24, 255), (235, 235, 240, 255)]):
        cell = Image.new("RGBA", (CANVAS, CANVAS), bg)
        cell.alpha_composite(master)
        prev.alpha_composite(cell, (i * (CANVAS + 30), 0))
    prev.convert("RGB").save("/tmp/icon_preview.png")
    print("  • 미리보기 → /tmp/icon_preview.png")

    make_icns(master, HERE / "icon.png", HERE / "icon.icns")

    aidir = HERE / "application_icon"
    if aidir.is_dir():
        master.save(aidir / "AppIcon.png")
        shutil.copy2(HERE / "icon.icns", aidir / "AppIcon.icns")
        print("  • application_icon/ 갱신 (AppIcon.png, AppIcon.icns)")

    if "--no-apply" not in sys.argv:
        apply_to_app(HERE / "icon.icns")
    print("완료.")


if __name__ == "__main__":
    main()
