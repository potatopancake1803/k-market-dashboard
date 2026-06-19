# Claude Code 작업 지시 — 로컬 git 초기화 (안전·검증 포함)

> 사용자(코딩 비전문가)가 이 프로젝트에 **로컬 git "되돌리기" 기능**만 도입하기로 했다.
> GitHub 등 원격은 쓰지 않는다(로컬 전용). `.gitignore`는 Cowork 세션에서 이미 보강 완료
> (빌드 가상환경·dist·_archive·API_documents·키파일 제외 → git 추적 대상 ≈ 8.5MB).
> 너는 아래를 **순서대로, 각 단계 확인하며** 수행한다. 파괴적 작업 없음(파일 삭제·이동 금지).

## 전제 / 안전 규약
- 작업 디렉터리: `/Users/minjun1803/Documents/Python/Project_Market_Dashboard/`
- 이 폴더는 아직 git 저장소가 아니다(`.git` 없음). **새로 `git init` 한다.**
- **절대 금지:** `git rm`, 파일 삭제, `git push`, 원격 추가, 강제 작업(`--force`). 순수하게 로컬 첫 커밋까지만.
- 민감정보 보호가 최우선: 커밋 **전에** 키파일이 staged 되지 않았는지 반드시 검증(아래 4번). 하나라도 잡히면 멈추고 사용자에게 보고.

## 수행 단계

### 1. git 존재 확인
```bash
git --version
```
- 없으면(거의 없을 일): 사용자에게 "Xcode 명령행 도구 설치(`xcode-select --install`)가 필요하다"고 안내하고 멈춤. 임의 설치 금지.

### 2. 저장소 초기화
```bash
cd "/Users/minjun1803/Documents/Python/Project_Market_Dashboard"
git init
git config core.autocrlf input   # 줄바꿈 정규화(선택)
```

### 3. `.gitignore` 적용 상태 확인 (무거운 폴더가 제외되는지)
```bash
git status --porcelain | wc -l                       # 추적 대상 파일 수 (수백 개 이내여야 정상)
git check-ignore -v application_build/.venv-build application_build/dist application_build/_archive API_documents .cache .env 2>/dev/null
```
- `.venv-build`/`dist`/`_archive`/`API_documents`/`.cache`/`.env`가 **모두 ignore 로 잡혀야** 한다.
  하나라도 안 잡히면 **멈추고** `.gitignore`를 점검(이미 보강돼 있으니 정상일 것).

### 4. 🔑 민감파일 누출 사전 검증 (커밋 전 필수 게이트)
```bash
git add -A
git status --short | grep -iE '\.env|API.env|API_Key|한국투자증권' && echo "❌ STOP: 키파일이 staged 됨" || echo "✅ 키파일 없음 — 안전"
```
- ❌ 가 뜨면 **커밋하지 말고** 즉시 멈춰 사용자에게 보고(.gitignore 보강 필요).
- ✅ 면 다음으로.

### 5. 추적 용량·파일 수 최종 확인
```bash
git diff --cached --stat | tail -1          # 첫 커밋에 들어갈 파일 수/변경량
du -sh .git 2>/dev/null                      # .git 자체 크기 (수십 MB 이내 정상)
```
- 파일 수가 비정상적으로 많거나(예: 수천 개) `.git`이 수백 MB면 무언가 ignore 안 된 것 → 멈추고 점검.

### 6. 첫 커밋
```bash
git commit -m "chore: initialize local git repo (baseline snapshot)

- Local-only versioning for safe rollback (no remote).
- .gitignore excludes venvs/dist/_archive/API_documents/.cache and all key files.
- Baseline at changes_88 (agent-upgrade: hooks + auto-reflect, reflect mode=auto)."
```

### 7. 검증 & 보고
```bash
git log --oneline -1
git status            # "working tree clean" 확인
```
- 결과를 사용자에게 한국어로 간단 보고: 커밋 해시, 추적 파일 수, `.git` 크기.

## 기록 (RECORD)
- 이건 인프라 변경(코드 로직 불변)이라 Tier-N~S. `_STATUS.md`에 한 줄 추가:
  "로컬 git 초기화됨(원격 없음) — 되돌리기 가능. `.gitignore`로 venv/dist/_archive/키파일 제외." 정도.
- 새 트랩이면 등재. 구조적 코드 변경이 아니므로 smoke_check 의무 대상은 아님(돌려도 무방).

## 사용자가 앞으로 쓰는 법 (참고로 알려줄 것)
- 사용자는 git 명령을 직접 칠 필요 없다. **"지금 상태 저장해줘"(=커밋), "방금 변경 되돌려줘"(=복원)** 처럼
  말로 너에게 시키면 된다. 큰 변경 전마다 커밋해두면 언제든 그 시점으로 되돌릴 수 있다.
