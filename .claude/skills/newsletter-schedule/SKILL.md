---
name: newsletter-schedule
description: 뉴스레터 에이전트가 매일 아침 자동으로 실행되도록 예약 작업을 등록·변경·해제한다. "매일 아침 보내 줘", "발송 시각 바꿔 줘", "예약 멈춰 줘"처럼 자동 실행 설정을 요청받았을 때 사용한다.
---

# 뉴스레터 예약 실행

## 설정값

`config/newsletter.toml`의 `send_time`(예: `07:00`)과 `timezone`(예: `Asia/Seoul`).

리서치와 작성에 10~20분이 걸리므로, 실행 시각은 `send_time`보다 **약 15분 앞**으로 잡는다. 정각·30분은 서버가 붐비니 몇 분 비튼다. 예: 발송 07:00 → 실행 06:43.

## 1순위 — 클라우드 예약 작업 (컴퓨터가 꺼져 있어도 실행)

Claude Code 클라우드 세션의 예약 작업 생성 도구(`create_trigger`)를 쓴다. 이 저장소가 연결된 클라우드 세션에서 등록해야 새 세션이 같은 저장소와 환경으로 열린다.

| 항목 | 값 |
|---|---|
| `name` | `AutoAX 데일리 뉴스레터` |
| `cron_expression` | `CRON_TZ=Asia/Seoul 43 6 * * *` (위 계산대로) |
| `create_new_session_on_fire` | `true` (매번 깨끗한 새 세션) |
| `connectors` | `["Gmail"]` (보관을 Drive로 하면 `"Google Drive"` 추가) |
| `notifications` | `{"push": true}` |
| `initiation` | `human_request` |
| `prompt` | 아래 프롬프트 |

```text
AutoAX 저장소의 데일리 뉴스레터를 만들어 발송해 줘.
CLAUDE.md와 .claude/agents/newsletter-orchestrator.md의 절차를 처음부터 끝까지 그대로 따른다:
python3 scripts/make_workdir.py로 오늘 업무 폴더를 만들고,
newsletter-research → newsletter-html → newsletter-send 스킬 순서로 진행하며,
관점별 리서치 결과와 newsletter.html은 newsletters/{오늘 날짜}_{주제}/ 폴더에 바로 저장한다.
가능하면 업무 폴더를 커밋해 newsletters 브랜치에 push해 보관한다.
끝나면 주제, 업무 폴더, 발송 결과를 세 줄로 보고한다.
```

등록 후:
1. 응답의 예약 작업 ID와 다음 실행 시각을 사용자에게 알린다.
2. `config/newsletter.toml`의 `# schedule_id = ""` 줄을 실제 ID로 바꾼다.
3. 결과 경고에 "커넥터가 저장되지 않음"이 있으면 그대로 사용자에게 전하고 해결 방법을 안내한다.

### 변경·해제

- 시각 변경: 예약 작업 수정 도구(`update_trigger`)로 `cron_expression`만 바꾼다. 지우고 다시 만들지 않는다.
- 일시 중지: `update_trigger`로 `enabled: false`.
- 완전 삭제: 사용자가 명시적으로 요청할 때만 `delete_trigger`.
- 바로 한 번 돌려 보기: `fire_trigger`.

## 2순위 — 로컬 cron (사용자 컴퓨터, 켜져 있어야 실행)

```cron
CRON_TZ=Asia/Seoul
43 6 * * * cd /path/to/autoax && claude -p "오늘 뉴스레터 만들어 줘" --agent newsletter-orchestrator --permission-mode acceptEdits >> newsletters/cron.log 2>&1
```

- Gmail 커넥터를 쓸 수 없는 환경이면 `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`를 cron 환경에 넣어 SMTP로 보낸다.
- macOS는 cron 대신 `launchd`, Windows는 작업 스케줄러에 같은 명령을 등록한다.

## 확인

등록 직후 사용자가 원하면 한 번 바로 실행해서 메일이 오는지 확인한다.
