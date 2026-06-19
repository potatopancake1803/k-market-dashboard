#!/usr/bin/env python3
"""아이콘 정규화 — 투명 여백을 잘라 macOS 표준 비율로 다시 채운다.

소스 이미지가 캔버스 안에서 작게 떠 있으면(투명 여백 과다) Dock/Finder 에서
'타일 안의 또 다른 타일'처럼 테두리가 이상해 보인다. 이 스크립트는:
  ① 알파(투명) 기준 실제 그림의 경계(bbox)만 잘라내고
  ② 정사각으로 보정한 뒤
  ③ 1024 캔버스에 지정 비율(FILL, 기본 0.92)로 가운데 배치한다.
→ macOS 스퀴클 아이콘이 타일을 꽉 채우는 자연스러운 모양이 된다.

사용:  python icon_normalize.py <src> <dst.png> [fill=0.92] [size=1024]
PIL(Pillow) 이 없으면 종료코드 2 로 끝나 호출측(make_icon.sh)이 폴백한다.
"""
import sys

try:
    from PIL import Image
except Exception:  # noqa: BLE001
    sys.exit(2)


def main() -> None:
    if len(sys.argv) < 3:
        sys.exit("usage: icon_normalize.py <src> <dst.png> [fill] [size]")
    src, dst = sys.argv[1], sys.argv[2]
    fill = float(sys.argv[3]) if len(sys.argv) > 3 else 0.92
    size = int(sys.argv[4]) if len(sys.argv) > 4 else 1024

    im = Image.open(src).convert("RGBA")
    bbox = im.split()[3].getbbox()      # 불투명 영역 경계
    if bbox:
        im = im.crop(bbox)

    # 정사각 보정(긴 변 기준, 가운데 배치)
    w, h = im.size
    s = max(w, h)
    square = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    square.alpha_composite(im, ((s - w) // 2, (s - h) // 2))

    side = max(1, int(size * fill))
    square = square.resize((side, side), Image.LANCZOS)

    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    off = (size - side) // 2
    out.alpha_composite(square, (off, off))
    out.save(dst)


if __name__ == "__main__":
    main()
