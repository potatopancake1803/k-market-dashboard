# CODEMAP — `scripts/market_dashboard3_realtime.py` 내비게이션 인덱스

> 자동 생성(라인 번호 포함). **목적:** 13k줄·736KB 단일 백엔드 파일을 *통째로 읽지 않고*
> 필요한 지점으로 바로 점프하기 위한 인덱스. AI 코딩 에이전트는 이 표에서 라인 번호를 보고
> `Read(offset=…, limit=…)` 또는 grep 으로 해당 구역만 열어 **토큰을 아끼고 컨텍스트 한계를 회피**한다.
> 재생성: `python3 scripts/gen_codemap.py`. 라인 번호는 편집하면 바뀌니 큰 변경 후 재생성할 것.

- 총 라인: **8,131** · 바이트: **396,041** · 라우트: **83** · top-level 함수: **265** · 인라인 템플릿: **20**
- 📦 페이지/위젯 템플릿 **20개(330,311자)** 는 `scripts/ui_templates.py` 로 분리됨(changes_77). 마크업 수정은 거기서, 조립/주입/로직은 main 에서.

## 1. 인라인 템플릿 (HTML/CSS/JS 문자열) → `scripts/ui_templates.py`

| 파일 | 라인 | 이름 | 크기(자) | 용도(추정) |
|---|---:|---|---:|---|
| ui_templates.py | 7 | `_M4_STYLE` | 4,404 | M4 퀀트 다크 콕핏 CSS |
| ui_templates.py | 73 | `_FX_STYLE` | 7,133 | 리포트 비파괴 주입 CSS(글라스·카운트업) |
| ui_templates.py | 171 | `_FX_JS` | 5,486 | 리포트 비파괴 주입 JS(카운트업·틸트·테마) |
| ui_templates.py | 254 | `_MKT_CSS` | 5,622 |  |
| ui_templates.py | 333 | `_SECTOR_HTML` | 5,841 |  |
| ui_templates.py | 438 | `_MARKET_HTML` | 13,113 | 시장 현황(시총상위·상하한가·시황) |
| ui_templates.py | 656 | `_RT_STYLE` | 1,093 |  |
| ui_templates.py | 673 | `_RT_JS` | 6,929 |  |
| ui_templates.py | 807 | `_M4_WIRE` | 3,378 | M4 3D 자동회전 JS(rAF) |
| ui_templates.py | 862 | `_PDF_VIEW_HTML` | 2,263 | PDF 줌 뷰어 |
| ui_templates.py | 895 | `_RESEARCH_HTML` | 9,515 | 증권사 리포트 뷰어 |
| ui_templates.py | 1025 | `_INDEX_HTML` | 16,565 | 지수 상세 페이지 |
| ui_templates.py | 1255 | `_MACRO_HTML` | 15,211 | 경제지표(ECOS·FRED·글로벌) |
| ui_templates.py | 1470 | `_ASK_WIDGET_HTML` | 32,503 | 플로팅 AI 채팅 위젯(Gemini형 입력바·모델팝업·중지) |
| ui_templates.py | 1884 | `_LANDING_HTML` | 70,522 | 랜딩(홈) 페이지 — 검색·탭·테마토글·카드 |
| ui_templates.py | 2910 | `_BACKTEST_HTML` | 25,752 | 백테스터(다크 콕핏·캔들·성과패널) |
| ui_templates.py | 3264 | `_OVERSEAS_HTML` | 44,402 | 해외주식 페이지(히어로·KPI·차트·M4퀀트) |
| ui_templates.py | 4334 | `_REALTIME_HTML` | 28,876 | 실시간 트레이딩 데스크(호가·체결·페이퍼) |
| ui_templates.py | 4857 | `_WORLD_DETAIL_HTML` | 8,845 | 세계 지수 상세/차트 |
| ui_templates.py | 4985 | `_WORLD_HTML` | 22,858 | 세계 시장 3뷰(국내/미국/글로벌) |

## 2. 라우트 (그룹별) — `@app.get/post`

### `/api/dev`  (10)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 170 | POST | `/api/dev/locate` | `_dev_locate_route` |
| 182 | POST | `/api/dev/note` | `_dev_note_route` |
| 198 | GET | `/api/dev/session/state` | `_dev_session_state` |
| 205 | POST | `/api/dev/session/add` | `_dev_session_add` |
| 214 | POST | `/api/dev/session/remove` | `_dev_session_remove` |
| 224 | POST | `/api/dev/session/update` | `_dev_session_update` |
| 236 | POST | `/api/dev/session/new` | `_dev_session_new` |
| 248 | GET | `/api/dev/session/list` | `_dev_session_list` |
| 256 | POST | `/api/dev/session/load` | `_dev_session_load` |
| 271 | POST | `/api/dev/session/save` | `_dev_session_save` |

### `/api/quant`  (2)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 3066 | GET | `/api/quant/stock` | `api_quant_stock` |
| 3074 | GET | `/api/quant/etf` | `api_quant_etf` |

### `/api/realtime`  (1)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 3082 | GET | `/api/realtime` | `api_realtime` |

### `/api/index`  (1)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 3091 | GET | `/api/index` | `api_index` |

### `/api/index_chart`  (1)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 3112 | GET | `/api/index_chart` | `api_index_chart` |

### `/api/macro`  (1)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 3119 | GET | `/api/macro` | `api_macro` |

### `/api/global_macro`  (1)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 3125 | GET | `/api/global_macro` | `api_global_macro` |

### `/api/research`  (1)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 3519 | GET | `/api/research` | `api_research` |

### `/research_pdf2`  (1)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 3573 | GET | `/research_pdf2` | `research_pdf2` |

### `/pdf_view`  (1)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 3590 | GET | `/pdf_view` | `pdf_view` |

### `/api/research_summary`  (1)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 3619 | GET | `/api/research_summary` | `api_research_summary` |

### `/research_page`  (1)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 3689 | GET | `/research_page` | `research_page` |

### `/api/etf_nav`  (1)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 3696 | GET | `/api/etf_nav` | `api_etf_nav` |

### `/api/sectors`  (1)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 3705 | GET | `/api/sectors` | `api_sectors` |

### `/api/sector_stocks`  (1)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 3715 | GET | `/api/sector_stocks` | `api_sector_stocks` |

### `/sector`  (1)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 3722 | GET | `/sector` | `sector_page` |

### `/api/market_top`  (1)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 3728 | GET | `/api/market_top` | `api_market_top` |

### `/api/updown`  (1)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 3739 | GET | `/api/updown` | `api_updown` |

### `/api/market_news`  (1)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 3819 | GET | `/api/market_news` | `api_market_news` |

### `/api/market_overview`  (1)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 3825 | GET | `/api/market_overview` | `api_market_overview` |

### `/api/opinions_feed`  (1)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 3831 | GET | `/api/opinions_feed` | `api_opinions_feed` |

### `/api/marketmap`  (1)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 3837 | GET | `/api/marketmap` | `api_marketmap` |

### `/api/usmap`  (1)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 3846 | GET | `/api/usmap` | `api_usmap` |

### `/plotly.js`  (1)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 3858 | GET | `/plotly.js` | `plotly_js` |

### `/index_page`  (1)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 3871 | GET | `/index_page` | `index_page` |

### `/macro_page`  (1)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 3879 | GET | `/macro_page` | `macro_page` |

### `/market`  (1)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 3885 | GET | `/market` | `market_page` |

### `/logo.png`  (1)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 3892 | GET | `/logo.png` | `logo` |

### `/favicon.ico`  (1)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 3893 | GET | `/favicon.ico` | `logo` |

### `/(root)`  (1)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 3906 | GET | `/` | `index` |

### `/suggest`  (1)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 3911 | GET | `/suggest` | `suggest` |

### `/api/llm_ask`  (1)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 5191 | POST | `/api/llm_ask` | `llm_ask` |

### `/api/llm_commentary`  (1)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 5648 | POST | `/api/llm_commentary` | `llm_commentary` |

### `/api/llm`  (5)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 5954 | GET | `/api/llm/status` | `api_llm_status` |
| 5959 | GET | `/api/llm/loaded` | `api_llm_loaded` |
| 6029 | POST | `/api/llm/load` | `api_llm_load` |
| 6049 | POST | `/api/llm/unload` | `api_llm_unload` |
| 6060 | GET | `/api/llm/hardware` | `api_llm_hardware` |

### `/api/ai`  (2)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 5992 | GET | `/api/ai/prefs` | `api_ai_prefs_get` |
| 5997 | POST | `/api/ai/prefs` | `api_ai_prefs_set` |

### `/api/screener`  (1)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 6213 | GET | `/api/screener` | `_api_screener` |

### `/screener_page`  (1)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 6241 | GET | `/screener_page` | `screener_page` |

### `/dashboard`  (1)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 6328 | GET | `/dashboard` | `dashboard` |

### `/report_pdf`  (1)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 6401 | GET | `/report_pdf` | `report_pdf` |

### `/__ping`  (1)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 6433 | GET | `/__ping` | `__ping` |

### `/__bye`  (2)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 6441 | POST | `/__bye` | `__bye` |
| 6442 | GET | `/__bye` | `__bye` |

### `/api/backtest`  (1)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 6632 | GET | `/api/backtest` | `api_backtest` |

### `/backtest_page`  (1)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 6648 | GET | `/backtest_page` | `backtest_page` |

### `/api/ov`  (6)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 6982 | GET | `/api/ov/suggest` | `api_ov_suggest` |
| 6987 | GET | `/api/ov/detail` | `api_ov_detail` |
| 7000 | GET | `/api/ov/news` | `api_ov_news` |
| 7006 | GET | `/api/ov/resolve` | `api_ov_resolve` |
| 7011 | GET | `/api/ov/chart` | `api_ov_chart` |
| 7018 | GET | `/api/ov/price` | `api_ov_price` |

### `/overseas`  (1)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 7033 | GET | `/overseas` | `overseas_page` |

### `/api/rt`  (5)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 7447 | GET | `/api/rt/history` | `api_rt_history` |
| 7461 | GET | `/api/rt/orderbook` | `api_rt_orderbook` |
| 7466 | GET | `/api/rt/stream` | `api_rt_stream` |
| 7486 | GET | `/api/rt/screener` | `api_rt_screener` |
| 7491 | GET | `/api/rt/flows` | `api_rt_flows` |

### `/api/paper`  (3)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 7496 | GET | `/api/paper/state` | `api_paper_state` |
| 7501 | POST | `/api/paper/order` | `api_paper_order` |
| 7508 | POST | `/api/paper/reset` | `api_paper_reset` |

### `/realtime_page`  (1)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 7513 | GET | `/realtime_page` | `realtime_page` |

### `/api/world`  (3)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 7519 | GET | `/api/world` | `api_world` |
| 7558 | GET | `/api/world/chart` | `api_world_chart` |
| 7565 | GET | `/api/world/spark` | `api_world_spark` |

### `/world_detail`  (1)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 7585 | GET | `/world_detail` | `world_detail_page` |

### `/api/world_view`  (1)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 7804 | GET | `/api/world_view` | `api_world_view` |

### `/api/us_list`  (1)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 7905 | GET | `/api/us_list` | `api_us_list` |

### `/api/global_list`  (1)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 7964 | GET | `/api/global_list` | `api_global_list` |

### `/world_page`  (1)
| 라인 | 메서드 | 경로 | 핸들러 |
|---:|:--|--|--|
| 7969 | GET | `/world_page` | `world_page` |

## 3. `_inject_*` 비파괴 주입 — 순서/앵커 (취약 지점)

| 라인 | 함수 | 앵커(문자열 수술) |
|---:|--|--|
| 2273 | `_inject_m4_tab` | `</nav>`/`<footer` + `class="tab-btn"` 카운팅 |
| 2440 | `_inject_fx` | `</head>`/`</body>` |
| 2502 | `_inject_realtime` | swap |
| 6363 | `_ask_setter` | KMKT_ASK 스크립트 |
| 6370 | `_inject_ask` | 마지막 `</body>` |
| 6383 | `_inject_profile` | 카드 주입 |
| 7996 | `_inject_loader` | `<head>`/swap |
| 8071 | `_inject_floating_ai` | `</body>` |

> ⚠️ 이 함수들은 원본 빌더 HTML 을 문자열 `.replace()`/카운팅으로 사후 수술한다. 앵커가 바뀌면
> **조용히 실패**(에러 없이 주입 누락)할 수 있다. changes_72 가 앵커 미발견 시 `logger.warning` 추가.

## 4. 재생성

`python3 scripts/gen_codemap.py` 로 재생성(라인 번호 최신화). 큰 편집/이동 후 갱신 권장.
