---
name: newsletter-research
description: 데일리 뉴스레터용으로 관심사(주가·경제·AI·반도체·마케팅)를 관점 4개로 나눠, 관점마다 서브에이전트 하나씩 병렬로 리서치하고 업무 폴더에 관점별 .md와 00_시세.json을 저장한다. 업무 폴더를 만든 뒤 자료 조사가 필요할 때 사용한다.
---

# 뉴스레터 병렬 리서치

## 입력

`{workdir}/run.json` (`scripts/make_workdir.py`가 만듦). 업무 폴더가 아직 없으면 먼저 `python3 scripts/make_workdir.py`를 실행한다.

## 절차

1. `run.json`을 읽어 `perspectives`, `interests`, `tickers`, `lookback_hours`, `edition`을 확인한다.
2. 관점마다 `perspective-researcher` 서브에이전트를 **한 메시지에서 한꺼번에** 실행한다 (4개 동시 실행). 관점 하나에 서브에이전트 하나 — 여러 관점을 한 서브에이전트에 몰아 주지 않는다. 호출 메시지 양식:

   ```
   관점: {perspectives[i].name}
   날짜: {date}({weekday}) · {edition}
   기간: 최근 {lookback_hours}시간
   관심사 (섹션 제목은 이 이름 그대로):
   - 주가 추이 — 키워드: …
   - 경제·시장 뉴스 — 키워드: …
   - …
   관심사당 항목 수: {items_per_interest}
   제외 도메인(로그인·결제 필요): {blocked_domains}
   소스 조건: 로그인·결제 없이 읽을 수 있는 공개 소스만
   저장 경로: {perspectives[i].file}
   ```

   첫 번째 관점(핵심 숫자·데이터)에는 다음 두 줄을 더한다.

   ```
   시세 대상: {tickers}
   시세 파일 경로: {prices_file}
   ```

3. 모두 끝나면 점검 스크립트를 돌린다.

   ```bash
   python3 scripts/check_research.py {workdir}
   ```

4. 실패 항목을 처리한다.
   - 파일이 없거나 비어 있는 관점: 그 관점만 한 번 다시 실행한다.
   - 링크 없는 항목, 제외 도메인 링크: 해당 항목을 파일에서 빼고 다시 점검한다.
   - 다시 해도 안 되는 관점: 그 경로에 `자료를 찾지 못함: {이유}`를 저장한다.
5. `{workdir}/run_log.md`에 `- HH:MM 리서치 완료 (관점 성공 n/4, 항목 k건, 시세 m/8)` 를 추가한다.

## 주의

- 결과 파일은 반드시 업무 폴더 안 지정 경로에 저장한다.
- 서브에이전트를 쓸 수 없는 환경(이미 서브에이전트 안에서 실행 중 등)이면 `.claude/agents/perspective-researcher.md` 양식대로 관점을 하나씩 직접 리서치해 저장한다.
- 이 클라우드 환경은 스크립트의 외부 접속과 대부분의 `WebFetch`가 막혀 있다. 그래서 시세도 `WebSearch`(extended)로 공개 출처 두 곳을 대조해 모은다.
