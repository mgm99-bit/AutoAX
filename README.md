# AutoAX 데일리 뉴스레터 에이전트

매일 아침 관심 주제를 리서치해 HTML 뉴스레터로 만들고 Gmail로 보냅니다. 설계 전체는 [`docs/PLAN.md`](docs/PLAN.md)를 보세요.

## 시작하기

1. `config/newsletter.toml`에서 `recipient`(받을 Gmail)와 `[[topics]]`(관심 주제·관점)를 채웁니다.
2. claude.ai에서 Gmail 커넥터를 연결합니다.
3. Claude Code에서 `오늘 뉴스레터 만들어 줘 (발송 없이)`로 한 번 돌려 결과를 확인합니다.
4. `매일 아침 7시에 보내도록 예약해 줘`로 예약을 등록합니다.

## 결과물

```
newsletters/2026-10-25_AI-에이전트/
├── 01_기술-동향.md
├── 02_산업-비즈니스.md
├── 03_정책-규제.md
├── newsletter.html
├── run.json
└── run_log.md
```

## 구성

| 경로 | 역할 |
|---|---|
| `.claude/agents/newsletter-orchestrator.md` | 전체 진행 (메인 에이전트) |
| `.claude/agents/perspective-researcher.md` | 관점 하나 리서치 (서브에이전트) |
| `.claude/skills/newsletter-research` | 리서치 스킬 |
| `.claude/skills/newsletter-html` | HTML 작성 스킬 + 이메일 양식 |
| `.claude/skills/newsletter-send` | Gmail 발송 스킬 |
| `.claude/skills/newsletter-schedule` | 예약 실행 스킬 |
| `scripts/make_workdir.py` | 업무 폴더 생성 |
| `scripts/check_html.py` | HTML 점검 |
| `scripts/send_smtp.py` | SMTP 대체 발송 |
