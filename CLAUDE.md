# AutoAX

매일 아침 사용자의 관심 주제를 리서치해 HTML 뉴스레터로 만들고 Gmail로 보내는 에이전트 저장소다. 전체 설계는 `docs/PLAN.md`.

## 뉴스레터 요청을 받으면

"오늘 뉴스레터 만들어 줘", 예약 실행 프롬프트, 특정 주제 뉴스레터 요청이 오면 `.claude/agents/newsletter-orchestrator.md`의 절차를 **메인 세션에서 직접** 따른다. (관점별 리서치를 서브에이전트로 동시에 돌려야 하므로 오케스트레이터 자체를 서브에이전트로 띄우지 않는다.)

단계별 스킬:

| 단계 | 스킬 |
|---|---|
| 리서치 | `newsletter-research` (관점마다 `perspective-researcher` 서브에이전트) |
| HTML 작성 | `newsletter-html` |
| 메일 발송 | `newsletter-send` |
| 예약 실행 | `newsletter-schedule` |

## 업무 폴더 규칙

- 뉴스레터마다 `python3 scripts/make_workdir.py`로 `newsletters/{YYYY-MM-DD}_{주제}/`를 새로 만든다. 날짜는 한국 시간 기준이며 직접 계산하지 않는다.
- 관점별 리서치(`NN_{관점}.md`), `newsletter.html`, `run_log.md`는 만들자마자 그 폴더에 저장한다.
- 기존 업무 폴더를 지우거나 덮어쓰지 않는다.

## 설정

사용자 설정은 `config/newsletter.toml` 한 곳에만 둔다. 받는 사람 주소나 비밀번호를 다른 파일·커밋에 쓰지 않는다.
