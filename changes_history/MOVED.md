# ⚠️ 이 디렉터리의 changes 로그는 통합되었습니다

이 루트 `changes_history/`(Claude lineage 분기, seq 7~15)의 모든 changes 로그는
**canonical 디렉터리** `application_build/changes_history/` 로 통합·재넘버링되었습니다.

- **통합일:** 2026-06-17
- **사유:** 두 디렉터리에 같은 번호(7~15)가 존재해 내용이 갈라지는 drift 발생.
  새 세션 에이전트가 한쪽만 읽으면 최신 변경을 놓치는 문제를 제거하기 위함.

## 재넘버링 매핑 (루트 → canonical)

| 루트 (구) | canonical (신) |
|-----------|----------------|
| changes_7  | changes_62 |
| changes_8  | changes_63 |
| changes_9  | changes_64 |
| changes_10 | changes_65 |
| changes_11 | changes_66 |
| changes_12 | changes_67 |
| changes_13 | changes_68 |
| changes_14 | changes_69 |
| changes_15 | changes_70 |

> 각 canonical 파일 상단에는 원래 위치/통합일 메타가 추가되어 있습니다.
> 파일 내부 frontmatter 의 `id:` 값은 역사 보존을 위해 원본(7~15) 그대로 두고,
> **파일명만 새 번호(62~70)** 로 통일했습니다.

## 원본 보존 정책

이 디렉터리의 원본 파일들은 **삭제하지 않고 그대로 둡니다**(복사 통합).
검증이 끝난 뒤 별도 세션에서 정리(삭제)할 예정입니다.
**새 changes 로그는 이 디렉터리에 추가하지 말고 `application_build/changes_history/` 에만 작성하세요.**
