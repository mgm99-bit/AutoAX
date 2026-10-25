# AutoAX 데일리 뉴스레터 에이전트 — 작업 기획서

## 1. 목표

매일 아침 정해진 시각에 사용자의 관심 주제를 웹에서 리서치하고, 결과를 HTML 뉴스레터로 정리해 사용자의 Gmail로 보낸다.

- 뉴스레터 한 편을 만들 때마다 `{오늘 날짜}_{주제}` 업무 폴더를 새로 만든다.
- 관점별 리서치 결과(`.md`)와 완성한 뉴스레터(`newsletter.html`)는 그 폴더에 바로 저장한다.
- 리서치 · HTML 작성 · 메일 발송 · 예약 실행은 각각 독립된 스킬로 나눈다.

## 2. 전체 흐름

```
[예약 실행]  newsletter-schedule 스킬이 등록한 예약 작업 (매일 06:43, 한국 시간 — 07:00 도착 목표)
     │  새 세션을 열고 "오늘 뉴스레터 만들어 줘" 프롬프트 전달
     ▼
[오케스트레이터]  newsletter-orchestrator 에이전트 (메인 세션)
     │
     ├─ 0. 준비      scripts/make_workdir.py
     │               → 오늘의 주제 선택 + newsletters/2026-10-25_AI-에이전트/ 생성
     │
     ├─ 1. 리서치    newsletter-research 스킬
     │               → 관점마다 perspective-researcher 서브에이전트를 동시에 실행
     │               → 01_기술-동향.md, 02_산업-비즈니스.md, 03_정책-규제.md … 저장
     │
     ├─ 2. 작성      newsletter-html 스킬
     │               → 관점별 결과를 합쳐 template.html 양식으로 newsletter.html 저장
     │
     ├─ 3. 발송      newsletter-send 스킬
     │               → Gmail 커넥터(send_message, htmlBody)로 발송
     │               → 실패 시 SMTP 스크립트로 대체 발송
     │
     └─ 4. 기록      run_log.md에 단계별 결과 저장 (+ 선택: 보관용 push / Drive 업로드)
```

## 3. 폴더 구조

```
autoax/
├── CLAUDE.md                          # 저장소 규칙. 뉴스레터 요청이 오면 오케스트레이터 절차를 따르게 함
├── README.md                          # 사용법 요약
├── docs/
│   └── PLAN.md                        # 이 기획서
├── config/
│   └── newsletter.toml                # 받는 사람, 관심 주제, 관점, 발송 시각 등 사용자 설정
├── scripts/
│   ├── make_workdir.py                # 오늘 날짜(KST) + 주제로 업무 폴더 생성, 실행 정보 JSON 출력
│   ├── check_html.py                  # 완성 HTML 점검 (크기, 남은 자리 표시, 링크, 금지 태그)
│   └── send_smtp.py                   # Gmail 커넥터가 없을 때 쓰는 대체 발송 (앱 비밀번호)
├── .claude/
│   ├── agents/
│   │   ├── newsletter-orchestrator.md # 전체 파이프라인 담당 (메인 에이전트)
│   │   └── perspective-researcher.md  # 관점 하나를 맡아 리서치하는 서브에이전트
│   └── skills/
│       ├── newsletter-research/SKILL.md
│       ├── newsletter-html/
│       │   ├── SKILL.md
│       │   └── template.html          # 이메일용 HTML 양식 (인라인 스타일, 표 기반)
│       ├── newsletter-send/SKILL.md
│       └── newsletter-schedule/SKILL.md
└── newsletters/                       # 업무 폴더가 쌓이는 곳
    └── 2026-10-25_AI-에이전트/        # 예시
        ├── 01_기술-동향.md
        ├── 02_산업-비즈니스.md
        ├── 03_정책-규제.md
        ├── newsletter.html
        └── run_log.md
```

## 4. 설정 파일 — `config/newsletter.toml`

| 항목 | 설명 |
|---|---|
| `recipient` | 받을 Gmail 주소. 비어 있거나 예시 값이면 발송 단계에서 멈춘다 |
| `sender_name` | 메일에 표시할 보내는 이름 |
| `language` | 뉴스레터 언어 (기본 `ko`) |
| `timezone` | 날짜 계산 기준 (기본 `Asia/Seoul`) |
| `send_time` | 예약 발송 시각 (예: `07:00`) |
| `topic_mode` | `rotate`(날짜마다 주제 하나씩 돌아가며) 또는 `fixed`(항상 첫 주제) |
| `[[topics]]` | 관심 주제 목록. 주제마다 `name`, `keywords`, `perspectives`(관점 목록), `exclude`(제외어) |
| `items_per_perspective` | 관점마다 뉴스레터에 넣을 기사 수 (기본 3) |
| `lookback_hours` | 리서치 대상 기간 (기본 24시간, 결과가 적으면 72시간까지 늘림) |

주제 선택 규칙: `rotate`이면 `날짜 순번 % 주제 수`로 고르므로, 같은 날 다시 실행해도 같은 주제가 나온다.

## 5. 업무 폴더 규칙

- 위치: `newsletters/{YYYY-MM-DD}_{주제}/`
- 날짜는 `config`의 `timezone`(한국 시간) 기준. 클라우드 서버 시간(UTC)을 쓰면 오전 9시 전에 날짜가 하루 밀리므로 반드시 스크립트로 계산한다.
- 주제 이름의 공백은 `-`로 바꾸고, 파일 이름에 못 쓰는 문자(`/ \ : * ? " < > |`)는 지운다. 한글은 그대로 둔다.
- 같은 날 같은 주제로 다시 실행하면 기존 폴더를 덮어쓰지 않고 `_2`, `_3`을 붙인 새 폴더를 만든다.
- 폴더 안 파일 이름

| 파일 | 내용 | 만드는 곳 |
|---|---|---|
| `NN_{관점}.md` | 관점별 리서치 결과 (요약, 기사 목록, 출처 링크) | 리서치 스킬 |
| `newsletter.html` | 발송한 그대로의 뉴스레터 | HTML 스킬 |
| `run_log.md` | 실행 시각, 주제, 단계별 성공/실패, Gmail 메시지 ID | 오케스트레이터 |

각 단계는 결과를 만들자마자 이 폴더에 저장한다. 다음 단계는 메모리 대신 이 폴더의 파일을 읽어서 진행하므로, 중간에 끊겨도 어디까지 됐는지 폴더만 보면 알 수 있다.

## 6. 에이전트 정의

### 6-1. `newsletter-orchestrator` (메인)

- 역할: 준비 → 리서치 → 작성 → 발송 → 기록 순서로 진행하고 실패를 처리한다.
- 실행 방법
  - 클라우드 예약 실행: 예약 프롬프트가 "오늘 뉴스레터 만들어 줘"를 보내면, `CLAUDE.md` 지시에 따라 메인 세션이 이 파일의 절차를 그대로 따른다.
  - 로컬 실행: `claude --agent newsletter-orchestrator "오늘 뉴스레터 만들어 줘"`
- 메인 세션에서 돌리는 이유: 서브에이전트는 다른 서브에이전트를 부를 수 없다. 관점별 리서치를 동시에 돌리려면 오케스트레이터가 메인이어야 한다.
- 실패 처리
  - 리서치: 한 관점이 실패해도 나머지로 계속 진행하고, 뉴스레터에 "자료 부족"으로 표시한다. 모든 관점이 실패하면 발송하지 않고 실패 알림 메일만 보낸다.
  - 발송: Gmail 커넥터 실패 → SMTP 대체 → 그래도 실패하면 `run_log.md`에 기록하고 종료한다.

### 6-2. `perspective-researcher` (서브에이전트)

- 입력: 주제, 관점, 키워드, 제외어, 기간, 기사 수, 저장할 파일 경로
- 도구: `WebSearch`, `WebFetch`, `Read`, `Write`
- 출력: 지정 경로에 `.md` 파일을 저장하고, 오케스트레이터에는 한 줄 요약만 돌려준다 (본문은 파일에 있으니 대화 맥락을 아낀다).

## 7. 스킬 설계

| 스킬 | 언제 쓰나 | 입력 | 출력 |
|---|---|---|---|
| `newsletter-research` | 업무 폴더가 생긴 뒤 | 실행 정보 JSON | 관점별 `NN_{관점}.md` |
| `newsletter-html` | 리서치 파일이 모인 뒤 | 업무 폴더 경로 | `newsletter.html` |
| `newsletter-send` | HTML이 저장된 뒤 | `newsletter.html`, 받는 사람 | Gmail 메시지 ID |
| `newsletter-schedule` | 처음 설정할 때, 시각을 바꿀 때 | 발송 시각, 시간대 | 예약 작업 ID |

### 7-1. 리서치 (`newsletter-research`)
1. 관점마다 `perspective-researcher`를 한 번에 동시에 실행한다.
2. 각 서브에이전트는 기간 안의 기사를 검색어 2~4개로 찾고, 원문을 열어 사실을 확인한 뒤 고른다.
3. 기사마다 제목, 출처, 날짜, URL, 3줄 요약, "왜 중요한가" 한 줄을 적는다.
4. 같은 뉴스를 여러 관점이 다루면 오케스트레이터가 HTML 단계에서 한 번만 싣는다.
5. 품질 기준: 출처 URL이 없는 내용 금지, 기간 밖 기사는 "배경"으로만 표시, 추측은 추측이라고 쓴다.

### 7-2. HTML 작성 (`newsletter-html`)
- 이메일 클라이언트 호환을 위해 표(table) 레이아웃, 인라인 스타일, 최대 폭 640px, 외부 CSS·JS 금지.
- 구성: 머리말(날짜·주제) → 오늘의 핵심 3줄 → 관점별 섹션(기사 카드) → 출처 목록 → 바닥글.
- 저장 직후 점검: 모든 기사에 링크가 있는지, `{{` 같은 양식 자리 표시가 남지 않았는지, 파일 크기가 100KB 미만인지(Gmail은 102KB가 넘으면 본문을 자른다).

### 7-3. 메일 발송 (`newsletter-send`)
- 1순위: Gmail 커넥터 `send_message` — `to`=받는 사람, `subject`=`[AutoAX] {날짜} {주제} 브리핑`, `htmlBody`=HTML 전체, `body`=텍스트 요약(HTML을 못 보는 메일 앱용).
- 2순위: `scripts/send_smtp.py` — 환경 변수 `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`(Google 앱 비밀번호) 사용.
- 같은 폴더로 두 번 보내지 않도록 `run_log.md`에 메시지 ID가 있으면 건너뛴다.

### 7-4. 예약 실행 (`newsletter-schedule`)
- 1순위: 클라우드 예약 작업 — 매일 한국 시간 기준으로 실행, 실행마다 새 세션, Gmail 커넥터 허용. 컴퓨터가 꺼져 있어도 돈다.
- 2순위: 로컬 cron — `claude -p` 비대화 모드로 실행. 컴퓨터가 켜져 있어야 한다.
- 등록 후 예약 작업 ID와 다음 실행 시각을 `config/newsletter.toml` 아래 주석과 사용자에게 알려 준다.

## 8. 결과물 보관

클라우드 세션의 파일은 세션이 끝나면 사라진다. 업무 폴더를 오래 남기려면 아래 중 하나를 켠다.

1. **Git push** (권장): 발송 후 업무 폴더를 커밋해 `newsletters` 브랜치에 올린다. 이 세션에 저장소 쓰기 권한이 있어야 한다 (현재는 Claude GitHub 앱 설치 전이라 막혀 있음).
2. **Google Drive**: Drive 커넥터로 `AutoAX/{날짜}_{주제}/` 폴더에 같은 파일을 올린다.
3. 메일 자체가 보관본 역할도 한다 (HTML 본문 + 원하면 리서치 `.md` 첨부).

## 9. 준비물 체크리스트

- [ ] `config/newsletter.toml`의 `recipient`에 받을 Gmail 주소 입력
- [ ] 관심 주제와 관점 입력 (`[[topics]]`)
- [ ] claude.ai에서 Gmail 커넥터 연결 (예약 작업에 Gmail 허용)
- [ ] (보관용) Claude GitHub 앱을 AutoAX 저장소에 설치 → push 가능
- [ ] `newsletter-schedule` 스킬로 예약 등록
- [ ] 첫 실행을 수동으로 해서 메일 모양 확인

## 10. 단계별 진행 계획

| 단계 | 내용 | 완료 기준 |
|---|---|---|
| 1 | 폴더 구조, 설정, 에이전트·스킬 파일 작성 | 이 저장소의 파일들 |
| 2 | 수동 1회 실행 (발송 없이) | 업무 폴더에 관점별 `.md`와 `newsletter.html`이 생김 |
| 3 | 본인 주소로 테스트 발송 | Gmail·모바일에서 깨짐 없이 보임 |
| 4 | 예약 등록 | 다음 날 아침 메일 도착 |
| 5 | 1주일 운영 후 조정 | 관점·기사 수·발송 시각 확정 |

## 11. 앞으로 확장할 것

- 지난 뉴스레터에 실린 URL을 기억해 중복 기사 제외
- 메일 답장으로 피드백("이 주제 빼 줘") 받아 설정에 반영
- 주간 요약판 (금요일)
