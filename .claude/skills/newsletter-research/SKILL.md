---
name: newsletter-research
description: 뉴스레터 주제를 여러 관점에서 동시에 리서치해 업무 폴더에 관점별 .md 파일로 저장한다. 업무 폴더(newsletters/{날짜}_{주제}/)를 만든 뒤, 뉴스레터용 자료 조사가 필요할 때 사용한다.
---

# 뉴스레터 리서치

## 입력

`scripts/make_workdir.py`가 출력한 실행 정보 (또는 `{workdir}/run.json`).

업무 폴더가 아직 없으면 먼저 `python3 scripts/make_workdir.py`를 실행한다.

## 절차

1. `run.json`을 읽어 `perspectives` 목록을 확인한다.
2. 관점마다 `perspective-researcher` 서브에이전트를 **한 메시지에서 한꺼번에** 실행한다 (동시 실행). 각 호출 메시지에는 다음을 모두 넣는다.

   ```
   주제: {topic}
   관점: {perspectives[i].name}
   키워드: {keywords}
   제외어: {exclude}
   기준일: {date}
   기간: 최근 {lookback_hours}시간
   기사 수: {items_per_perspective}
   언어: {language}
   저장 경로: {perspectives[i].file}
   ```

3. 모두 끝나면 각 `file`이 있는지, 비어 있지 않은지, `링크:` 줄이 있는지 확인한다.
4. 빠진 관점은 한 번만 다시 실행한다. 그래도 실패하면 그 경로에 아래처럼 저장한다.

   ```markdown
   # {관점} — {주제} ({날짜})

   자료를 찾지 못함: {이유}
   ```

5. `{workdir}/run_log.md`에 `- HH:MM 리서치 완료 (성공 n / 전체 m)` 을 추가한다.

## 주의

- 서브에이전트를 쓸 수 없는 환경(예: 서브에이전트 안에서 실행됨)이면, 같은 양식(`.claude/agents/perspective-researcher.md`)으로 관점을 하나씩 직접 리서치해 저장한다.
- 결과 파일은 반드시 업무 폴더 안 지정 경로에 저장한다.
