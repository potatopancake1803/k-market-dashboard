# 타이틀바 투명화 (신호등 버튼 흰색 배경 제거) 패치 노트

## 1. 문제 현상
macOS 네이티브 앱 실행 시, 좌측 상단의 윈도우 컨트롤(일명 '신호등 버튼' - 닫기, 최소화, 확대) 뒤쪽으로 앱의 본래 배경과 이질적인 **불투명한 흰색(또는 회색) 띠**가 나타나며 앱 인터페이스의 상단 부분이 잘려 보이는 현상이 있었습니다.

## 2. 원인 분석
K-Market Dashboard 앱은 파이썬 라이브러리인 `pywebview`를 기반으로 네이티브 윈도우를 생성합니다. 
기존 `app.py`의 `_style_native_window` 함수에서는 윈도우 콘텐츠를 최상단까지 확장하고(`NSWindowStyleMaskFullSizeContentView`) 타이틀바를 투명하게(`titlebarAppearsTransparent=True`) 처리하도록 설정되어 있었습니다.

하지만 `pywebview` 라이브러리의 macOS(Cocoa) 백엔드 구현체를 살펴보면, 완전 프레임리스(`frameless=True`) 모드를 켜지 않은 기본 상태에서는 macOS 시스템의 기본 윈도우 배경색(`windowBackgroundColor()`)을 타이틀바 영역에 **강제로 덧칠하는 로직**이 내장되어 있습니다.
프레임리스 모드를 켜면 신호등 버튼 자체를 숨겨버리기 때문에 프레임리스 모드를 사용할 수 없었고, 결과적으로 `pywebview`가 강제로 입힌 색상이 투명해야 할 타이틀바 영역을 덮어버리면서 불투명한 띠로 나타난 것입니다.

## 3. 해결 방식
앱 내부에서 타이틀바 영역을 그리는 하위 뷰(View) 객체에 직접 접근하여, `pywebview`가 설정한 배경색을 다시 **완전 투명(`clearColor`)으로 덮어쓰는 방식**을 적용했습니다.

### 적용된 코드 (`app.py` 내부 `_style_native_window` 함수)
```python
        # ⑤ pywebview가 frameless가 아닐 때 강제로 입힌 타이틀바 배경색을 투명으로 덮어씀
        try:
            win.contentView().superview().subviews().lastObject().setBackgroundColor_(
                AppKit.NSColor.clearColor()
            )
            win.setOpaque_(False)
            win.setBackgroundColor_(AppKit.NSColor.clearColor())
        except Exception:  # noqa: BLE001
            pass
```

### 작동 원리
1. `win.contentView().superview().subviews().lastObject()`: `pywebview`가 생성한 뷰 계층 구조를 거슬러 올라가, 타이틀바 역할을 하는 최상단 컨테이너 뷰를 찾습니다.
2. `setBackgroundColor_(AppKit.NSColor.clearColor())`: 해당 컨테이너의 배경색을 투명하게 지워버립니다.
3. `win.setOpaque_(False)` 및 `win.setBackgroundColor_(AppKit.NSColor.clearColor())`: 윈도우 창 자체의 바탕색도 완전히 투명화하여, 모서리나 여백에 시스템 배경색이 노출되는 것을 원천 차단합니다. 
4. 결과적으로 윈도우 창과 타이틀바는 완전히 투명해지고, 그 아래에 꽉 차게 렌더링된 웹 브라우저(`WKWebView`)의 HTML `body` 배경색과 UI만이 사용자에게 보여지게 됩니다. (신호등 버튼은 OS 단에서 최상단에 렌더링되므로 예쁘게 떠 있게 됩니다.)

## 4. 빌드 및 배포
수정된 런처(`app.py`)가 `.app` 패키지 안으로 동결되어야 하므로, 코드 수정 후 `application_build/build.sh` 스크립트를 재실행하여 앱을 완전히 재빌드하고 `/Applications` 경로에 덮어씌우는 것으로 작업을 완료했습니다.
