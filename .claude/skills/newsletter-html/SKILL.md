---
name: newsletter-html
description: 업무 폴더의 관점별 리서치 .md와 00_시세.json을 바탕으로 실을 내용을 골라 content.json에 적고, scripts/render_html.py로 이메일용 newsletter.html을 만들어 같은 폴더에 저장한다. 리서치가 끝난 뒤 뉴스레터 본문을 만들 때 사용한다.
---

# 뉴스레터 HTML 작성

HTML을 직접 쓰지 않는다. **Claude는 내용만 고르고(content.json), 화면은 스크립트가 그린다.** 숫자 옮겨 적기 오류와 스타일 흔들림을 막기 위해서다. 시세 표는 스크립트가 `00_시세.json`에서 직접 읽는다.

## 입력

업무 폴더 (`newsletters/{날짜}_데일리브리핑/`): `run.json`, `00_시세.json`, `01~04_*.md`.

## 절차

1. 관점별 `.md` 4개와 `00_시세.json`을 모두 읽는다.
2. `{workdir}/content.json`을 쓴다 (형식은 아래). 고르는 기준:
   - **관심사마다 최대 3항목**, 가능하면 관점 꼬리표가 겹치지 않게 (`숫자` `원인` `시사점` `전망`).
   - 주가 추이 → 경제·시장 뉴스 → AI·업무 자동화(AX) → 반도체·하드웨어 → 마케팅·콘텐츠 순서.
   - 여러 관점 파일에 같은 소식이 있으면 한 번만 싣는다.
   - **오늘의 핵심 3줄**: 관심사를 가로지르는 가장 중요한 흐름 3개, 줄마다 근거 기사 링크.
   - **일정**: 04 파일의 일정을 날짜순으로. 한국 시간 기준으로 적는다 (미 현지 발표는 한국 날짜·시각으로 바꾸고 괄호에 현지 표기).
   - **링크는 리서치 파일에 있는 URL을 그대로** 쓴다. 새로 만들거나 고치지 않는다.
   - 리서치 파일에 없는 사실·숫자를 더하지 않는다. "단일 출처", "추측" 표시는 그대로 살린다.
   - 확인 필요한 값(`00_시세.json`의 `verified: false`, 출처끼리 엇갈린 날짜 등)은 `price_warnings` 또는 항목의 `warning`으로 ⚠ 표시한다.
   - 투자 권유 표현을 쓰지 않는다.
3. 렌더링하고 점검한다.

   ```bash
   python3 scripts/render_html.py {workdir}
   python3 scripts/check_html.py {workdir}/newsletter.html
   ```

   점검이 실패하면 `content.json`을 고쳐 다시 렌더링한다.
4. 링크 출처 확인: `newsletter.html`의 모든 링크가 리서치 파일(`0*.md`, `00_시세.json`)에 있는 URL인지 확인한다.
5. `{workdir}/run_log.md`에 `- HH:MM HTML 저장 (n KB, 항목 k건, 링크 m개) — check_html.py 통과` 를 추가한다.

## content.json 형식

```json
{
  "headline": "메일 제목에도 쓰는 오늘의 한 줄",
  "preheader": "메일 목록 미리보기 문구",
  "highlights": [{"text": "핵심 1", "url": "https://…"}, {…}, {…}],
  "price_warnings": {"삼성전자": "⚠ 옆에 붙일 설명 (verified=false인 대상은 필수)"},
  "sections": [
    {
      "interest": "주가 추이",
      "items": [
        {
          "tag": "숫자 | 원인 | 시사점 | 전망",
          "title": "항목 제목",
          "url": "https://…",
          "source": "매체 이름",
          "date": "2026-10-25",
          "summary": "2~3문장",
          "why": "왜 중요한가 한 줄",
          "warning": "(선택) 확인 필요 내용"
        }
      ]
    }
  ],
  "schedule_title": "다음 주 일정 (10/26~10/30, 한국 시간)",
  "schedule": [{"when": "10/29(목) 03:00", "event": "FOMC 금리 결정", "url": "https://…", "warning": "(선택)"}],
  "footer_notes": ["(선택) 바닥글에 덧붙일 안내"]
}
```

## 스크립트가 지키는 이메일 규칙 (고치지 말 것)

- 표(table) 레이아웃, 최대 폭 640px, 360px 화면에서도 가로 스크롤 없음.
- 스타일은 모두 HTML 안의 인라인 `style` 속성. `<style>`, `<script>`, `<link>`, `@import`, `src=`(이미지), CSS `url()`, `<form>` 없음.
- 항목·핵심 줄·일정마다 출처 링크. 시세 표는 대상 이름이 출처 링크, 대조 출처는 표 아래 한 줄.
- 오르면 빨강 ▲, 내리면 파랑 ▼ (한국식). 주말판은 주간 등락 열을 더한다.
- 바닥글에 "투자 권유가 아님" 안내와 리서치 원본 폴더 이름.
- 100KB 미만 (Gmail은 102KB를 넘으면 본문을 자른다).
