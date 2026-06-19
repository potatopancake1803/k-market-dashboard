# K-Market Dashboard — macOS 네이티브 앱

원본 웹 대시보드(`scripts/market_dashboard3_realtime.py`)를 **수정 없이** 그대로
감싸, Dock 아이콘이 있는 진짜 macOS 앱으로 띄웁니다. 렌더링은 Safari 와 같은
WebKit(WKWebView) 엔진을 쓰므로 UI·인터랙션·3D 그래픽이 원본과 100% 동일합니다.

> 동작 원리: 런처(`app.py`)가 내부 Flask 서버를 백그라운드 데몬 스레드로 띄우고
> (`127.0.0.1:8780`), 그 페이지를 네이티브 단일 창에 표시합니다. 창을 닫으면
> 서버 프로세스까지 즉시 종료됩니다. 원본 파일은 전혀 건드리지 않습니다.

---

## 1. 바로 실행 (빌드 없이)

```bash
cd application_build
uv run app.py
```

또는 Finder 에서 **`launch.command` 더블클릭**.
(처음 한 번은 `chmod +x launch.command` 또는 우클릭 → 열기)

---

## 2. 독립 실행 `.app` 빌드 (PyInstaller)

Python 설치 없이 더블클릭으로 도는 완전한 앱 번들을 만듭니다.

```bash
cd application_build
chmod +x build.sh make_icon.sh
./build.sh
```

산출물:
- **`dist/K-Market Dashboard.app`** — 앱 번들
- **`dist/K-Market Dashboard.dmg`** — 배포용 디스크 이미지 (열어서 앱을 Applications 로 드래그)

빌드 끝에 자동으로 **① 중간물 정리 → ② /Applications 설치 → ③ DMG 패키징**까지 수행합니다.

```bash
open "dist/K-Market Dashboard.app"      # 바로 실행
open "dist/K-Market Dashboard.dmg"      # 배포용 DMG 열기(드래그 설치)
```

> DMG 는 macOS 내장 `hdiutil` 로 만들며 **미서명·미공증**(개인/로컬 배포용)입니다.
> 다른 Mac 에 주면 첫 실행 시 우클릭 → 열기 가 필요할 수 있어요. 어떤 Mac 에서도
> 경고 없이 열리게 하려면 Apple Developer ID 서명 + 공증(notarization)이 필요합니다.

빌드는 반드시 **Apple Silicon Mac(M4 Pro)** 에서 실행하세요. spec 이
`target_arch="arm64"` 네이티브로 설정돼 있습니다.

빌드 시 `icon.png` 가 **앱 아이콘(Dock)** 과 **웹 UI 로고/파비콘** 양쪽 소스로
번들에 포함됩니다(둘이 항상 일치). 로고를 바꾸려면 `icon.png` 교체 후
`./make_icon.sh && ./build.sh`.

---

## 2-0. macOS 네이티브 메뉴바 (HIG) 🍎

Apple Human Interface Guidelines 의 메뉴바 표준에 맞춰, AppKit 네이티브 메뉴를
**HIG 순서**(앱 → 파일 → 편집 → 보기 → 윈도우 → 도움말)로 제공합니다. 메뉴 항목은
WKWebView 웹 UI 의 동작과 연결됩니다(검색·탭·새로고침·인쇄).

| 메뉴 | 항목 (단축키) |
|---|---|
| **K-Market Dashboard** | About · **업데이트 확인…** · Services · Hide/Quit (⌘Q) |
| **파일** | 새 검색(⌘N) · 탭 닫기(⌘W) · PDF로 내보내기…(⌘P) |
| **편집** | 실행취소(⌘Z)·오려두기/복사/붙여넣기·전체 선택 · 찾기(⌘F) |
| **보기** | 새로고침(⌘R) · 확대/축소/실제 크기(⌘+/⌘-/⌘0) · 전체 화면(⌃⌘F) |
| **윈도우** | 최소화(⌘M) · 확대/축소 · 다음/이전 탭(⇧⌘]/⇧⌘[) · 모두 앞으로 |
| **도움말** | K-Market Dashboard 도움말 |

- **PDF로 내보내기(⌘P)**: 활성 리포트를 macOS 인쇄 패널로 띄웁니다 → 좌하단 **"PDF로 저장"**.
- 표준 동작(편집·전체화면·최소화)은 시스템 셀렉터를 그대로 써서 동작이 일관됩니다.
- 구현: `app.py` 의 `_install_native_menu()` 가 `NSApp.setMainMenu_()` 로 설치.

---

## 2-1. 업데이트 (재빌드 없이 소스 반영) 🔄

앱은 실행할 때마다 **원본 라이브 소스**
(`scripts/market_dashboard3_realtime.py`)를 직접 로드합니다. 따라서 기능을 고친 뒤:

1. 메뉴바 **`K-Market Dashboard ▸ 업데이트 확인…`** 클릭
   (VS Code 의 `Code ▸ Check for Updates` 와 같은 위치 — 앱 이름 메뉴 안)
2. 변경이 감지되면 **"지금 재시작"** → 앱이 스스로 재시작하며 최신 코드 반영

즉 `app.py`/빌드를 다시 만들 필요 없이, **소스만 고치고 메뉴에서 재시작**하면 됩니다.

- 원본 경로는 `app.py` 의 `DEFAULT_LIVE_ROOT` 에 기본값이 있고,
  `KMKT_SOURCE_ROOT`(프로젝트 루트) 또는 `KMKT_SOURCE`(파일 경로) 환경변수로 덮어쓸 수 있습니다.
- 라이브 소스를 못 찾으면(다른 Mac 등) 번들에 동결된 버전으로 안전하게 폴백합니다.
- ⚠️ 라이브 반영 대상은 `market_dashboard3_realtime.py` 입니다.
  `archive/` · `market_intel/` 패키지를 고쳤다면 `.app` 재빌드가 필요합니다.

---

## 3. 구성 파일

| 파일 | 역할 |
|---|---|
| `app.py` | pywebview 네이티브 창 런처 (원본 모듈 import) |
| `market_dashboard.spec` | PyInstaller 빌드 정의 (.app 번들) |
| `build.sh` | 가상환경 생성 → 의존성 설치 → 빌드 |
| `launch.command` | 빌드 없이 더블클릭 실행 (uv 우선) |
| `requirements.txt` | 앱/빌드 의존성 |
| `make_icon.sh` | `icon.png` → `icon.icns` 변환 |
| `icon.png` | 앱 아이콘 + 웹 UI 로고/파비콘 **단일 소스**(1024px) |

---

## 4. 사전 준비 / 주의사항

- **KIS 실시간 시세 키**: 프로젝트 루트 `.env` 의 `KIS_APP_KEY` / `KIS_APP_SECRET`
  를 읽습니다. `build.sh` 는 이 `.env`(와 `API.env`)를 앱 번들에 포함합니다.
  키를 바꾸면 `.app` 을 다시 빌드하거나, 환경변수로 덮어쓰세요.
- **포트 8780**: macOS `sharingd` 가 점유한 8770 을 피해 8780 을 씁니다.
  충돌 시 `MARKET_PORT=8790 uv run app.py` 처럼 변경 가능.
- **Gatekeeper**: 서명되지 않은 앱이라 처음 실행 시 우클릭 → "열기" 가 필요할 수
  있습니다. `build.sh` 가 quarantine 속성을 제거하지만, 다른 Mac 으로 옮기면
  `xattr -dr com.apple.quarantine "K-Market Dashboard.app"` 를 실행하세요.
- **첫 빌드 용량/시간**: plotly·scipy·pandas 등을 포함해 번들이 수백 MB,
  빌드는 수 분 걸릴 수 있습니다(정상).

---

## 5. 문제 해결

| 증상 | 해결 |
|---|---|
| 창이 흰 화면 | 서버 기동 지연 — 잠시 대기. 콘솔(`uv run`)에서 KIS 키 로드 로그 확인 |
| `ModuleNotFoundError: market_intel` | `app.py` 를 `application_build/` 안에서 실행했는지 확인(상대경로로 루트 탐색) |
| `.app` 실행 시 즉시 종료 | 터미널에서 `./dist/K-Market\ Dashboard.app/Contents/MacOS/K-Market\ Dashboard` 직접 실행해 오류 로그 확인 |
| 아이콘이 기본값 | `./make_icon.sh` 로 `icon.icns` 생성 후 재빌드 |
