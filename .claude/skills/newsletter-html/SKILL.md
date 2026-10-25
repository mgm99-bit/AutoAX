---
name: newsletter-html
description: 업무 폴더의 관점별 리서치 .md 파일을 모아 이메일용 HTML 뉴스레터(newsletter.html)를 작성해 같은 폴더에 저장한다. 리서치가 끝난 뒤 뉴스레터 본문을 만들 때 사용한다.
---

# 뉴스레터 HTML 작성

## 입력

업무 폴더 경로 (`newsletters/{날짜}_{주제}/`). 그 안의 `run.json`과 `NN_*.md` 파일.

## 절차

1. `run.json`과 모든 `NN_*.md`를 읽는다.
2. 내용을 정리한다.
   - **오늘의 핵심 3줄**: 관점들을 가로질러 가장 중요한 흐름 3개. 각 줄은 근거 기사로 이어지는 링크를 단다.
   - **관점별 섹션**: 관점 순서대로. 기사마다 제목(링크), 출처·날짜, 요약 2~3줄, "왜 중요한가".
   - 여러 관점에 같은 기사가 있으면 처음 나온 곳에만 싣는다.
   - "자료를 찾지 못함" 관점은 섹션에 "오늘은 새 소식이 없습니다" 한 줄만 둔다.
3. `.claude/skills/newsletter-html/template.html`을 뼈대로 `{{...}}` 자리를 채운다. 반복되는 블록(`<!-- ARTICLE -->`, `<!-- SECTION -->`)은 필요한 만큼 복제한다.
4. `{workdir}/newsletter.html`로 저장한다.
5. 점검 스크립트를 돌린다.

   ```bash
   python3 scripts/check_html.py newsletters/{날짜}_{주제}/newsletter.html
   ```

   실패 항목이 있으면 고쳐서 다시 저장하고 통과할 때까지 반복한다.
6. `{workdir}/run_log.md`에 `- HH:MM HTML 저장 (n KB, 기사 k건)` 을 추가한다.

## 이메일 HTML 규칙

- 표(`<table>`) 레이아웃, 최대 폭 640px, 가운데 정렬.
- 스타일은 모두 인라인(`style="..."`). `<style>` 블록, 외부 CSS, 웹폰트, JavaScript, `<form>` 금지.
- 이미지는 쓰지 않는다 (Gmail이 외부 이미지를 막는 경우가 많다).
- 글꼴: `-apple-system, 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif`.
- 모든 링크는 `https://`로 시작하는 절대 경로, `target="_blank"`.
- 전체 파일 100KB 미만 (Gmail은 102KB를 넘으면 본문을 자른다).
- 미리보기 문구(`{{PREHEADER}}`)에는 오늘의 핵심 첫 줄을 넣는다.
