# AI Agent Collaboration Guidelines (Claude & Antigravity)

**Important Directive for all AI Agents working on this project.**

> 🧭 **Canonical workflow (2026-06-17, changes_77):** read in order —
> `application_build/CLAUDE.md` (protocol; **§12 = structure-change → guideline sync + regression gate**) →
> `application_build/changes_history/_STATUS.md` (state/traps) → `docs/CODEMAP.md` (backend line index) →
> `docs/DEBUG_JOURNAL.md` (**grep symptoms before re-debugging; append after solving**).
> Entry = `scripts/market_dashboard3_realtime.py` (logic) + `scripts/ui_templates.py` (templates).
> **After any import/structure/route/template change, run `uv run scripts/smoke_check.py` → `SMOKE PASS ✓`
> before "verified" (py_compile alone is not verification).** When structure changes, sync the guideline
> files in the same session.

This project is co-developed by multiple LLM agents (Claude, Antigravity, etc.) and the user. 
When another LLM (e.g., Claude or Antigravity) takes over the work, you MUST FIRST refer to this guideline file (`CLAUDE.md`) and the `changes_history` folder to understand the context and progress before making any modifications.

To maintain synchronization, context, and continuity across different sessions and agents, all LLMs MUST adhere to the following logging protocol.

## 💻 Coding & Environment Rules

1. **Python Version:** 반드시 `python3` 명령어를 명시적으로 사용해야 합니다. (절대로 `python` 혹은 `python2`를 사용하지 마세요).
2. **Dependency Management (uv):** 코드를 작성하거나 의존성을 추가/변경할 때는 패키지 매니저로 `uv`를 사용하며, 추가되는 의존성 패키지들은 스크립트 내부나 `requirements.txt` / `pyproject.toml` 등에 빠짐없이 명시적으로 기록해야 합니다.
3. **API Specifications:** API 연동 및 명세 확인 시 반드시 `/Users/minjun1803/Documents/Python/Project_Market_Dashboard/api_documents` 폴더 내의 파일들을 우선적으로 참고하여 코드를 작성해야 합니다.

## 🎨 UI/UX Design Guidelines

UI/UX 작업을 수행할 때는 **반드시** 다음의 원칙을 준수해야 합니다:
1. **Apple Human Interface Guidelines (HIG):** [https://developer.apple.com/design/human-interface-guidelines](https://developer.apple.com/design/human-interface-guidelines)의 가이드를 엄격히 따릅니다.
2. **macOS Design Format via MCP:** 피그마(Figma)에 정의된 macOS 디자인 포맷과 시스템 컴포넌트(반투명 Blur, Vibrant 재질, 코너 라운딩, 타이포그래피 등)를 적용할 때, 사용자의 Figma 디자인 내용을 직접 읽기 위해 **반드시 MCP (Model Context Protocol) 도구(`figma-dev-mode-mcp-server`)를 호출하여 연결·조회하는 방식을 사용**해야 합니다. 이를 바탕으로 네이티브 앱과 구별할 수 없을 정도의 고품질 디자인을 지향합니다.

## 📝 Mandatory Logging Protocol (MUST BE IN ENGLISH)

Whenever you perform any tasks (coding, refactoring, feature implementation, debugging, or design adjustments) in this project, you MUST document your work by creating or updating a markdown file in the `changes_history` directory.
**CRITICAL: All content within the `changes_history` folder MUST be written in English.** This is to ensure maximum comprehension, reasoning capability, and context retention for LLMs taking over the project.

### Location
`/Users/minjun1803/Documents/Python/Project_Market_Dashboard/application_build/changes_history`

### 1. Implementation Plan Storage & Updates
- Before starting a major feature, if you or the user creates an "Implementation Plan", DO NOT just output it in the chat. You MUST save it as `changes_X_plan_feature_name.md` (where `X` is the next available sequential number in the folder) in the `changes_history` directory.
- The implementation plan must be highly detailed so that another LLM can understand exactly what structural or architectural changes are planned.
- If the plan changes during execution or after user feedback, update the file immediately so the history remains accurate.

### 2. History Log Format
- Create a new `.md` file for your session when work is completed or paused.
- **CRITICAL NAMING CONVENTION:** The filename MUST start with `changes_X_`, where `X` is the next sequential integer in the folder (e.g., `changes_0_feature.md`, `changes_1_bugfix.md`).
- **Understanding History:** When starting a task, ALWAYS list the files in `changes_history`, sort them by the `X` index, and read them in chronological order to perfectly grasp the project's evolution before making any modifications.
- Inside the document, include the following sections to provide **rich, in-depth technical context** for the next LLM:

```markdown
# [Task Title]
- **Date & Time:** YYYY-MM-DD HH:MM (KST)
- **Agent/Author:** (e.g., Antigravity, Claude, User)

## 🛠️ What was done
- A concise summary of the features implemented, bugs fixed, or refactoring performed.
- Provide the absolute paths of the files that were modified.

## ⚙️ How it was done (Technical Details)
- Extremely detailed explanation of the core logic, architecture changes, and algorithms used.
- Mention specific libraries, APIs, endpoints, variable names, and design patterns introduced.
- If an error was resolved, detail the root cause and the specific technical fix applied.
- This section should be detailed enough that another LLM can reconstruct your thought process and understand the codebase's current state without reading the entire source code.

## ⚠️ Notes & Pending Issues
- Critical constraints or warnings for the next agent (e.g., specific library version limits, hardcoded paths, OS-specific behaviors).
- Unfinished tasks or areas that require future optimization.
```

By strictly following this protocol and writing exclusively in English, you ensure that the next LLM picking up the task can seamlessly continue the work with full technical context.
