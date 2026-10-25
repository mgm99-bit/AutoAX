---
name: newsletter-send
description: 업무 폴더의 newsletter.html을 사용자의 Gmail로 발송하고 결과를 run_log.md에 기록한다. Gmail 커넥터를 먼저 쓰고, 안 되면 SMTP 스크립트로 대체한다. 뉴스레터 HTML이 완성된 뒤 메일을 보낼 때 사용한다.
---

# 뉴스레터 메일 발송

## 입력

업무 폴더 경로. 그 안의 `run.json`(받는 사람, 날짜, 주제), `newsletter.html`, `run_log.md`.

## 발송 전 확인

1. `run_log.md`에 `메시지 ID`가 이미 있으면 **보내지 않는다** (중복 발송 방지). 사용자가 "다시 보내 줘"라고 명시한 경우만 예외.
2. `recipient`가 비었거나 `your-address@gmail.com`이면 보내지 말고 `config/newsletter.toml`을 채워 달라고 알린 뒤 멈춘다.
3. `python3 scripts/check_html.py {workdir}/newsletter.html` 이 통과해야 한다.

## 1순위 — Gmail 커넥터

Gmail 커넥터의 `send_message` 도구를 호출한다. (도구가 안 보이면 도구 검색으로 `send_message`를 불러온다.)

| 필드 | 값 |
|---|---|
| `to` | `[recipient]` |
| `subject` | `[AutoAX] {date} {topic} 브리핑` |
| `htmlBody` | `newsletter.html` 파일 내용 전체 (그대로, 고치지 않음) |
| `body` | 텍스트 버전: 오늘의 핵심 3줄 + 기사 제목과 URL 목록. 마크다운 기호 금지 |

성공하면 응답의 `id`를 기록한다.

## 2순위 — SMTP 대체 발송

Gmail 커넥터가 없거나 실패했고, 환경 변수 `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`가 있으면:

```bash
python3 scripts/send_smtp.py --to "{recipient}" \
  --subject "[AutoAX] {date} {topic} 브리핑" \
  --html "{workdir}/newsletter.html" --sender-name "{sender_name}"
```

출력된 Message-ID를 기록한다.

## 기록

`{workdir}/run_log.md`에 추가한다.

- 성공: `- HH:MM 발송 성공 (Gmail 커넥터|SMTP) → {recipient}, 메시지 ID: {id}`
- 실패: `- HH:MM 발송 실패: {방법별 오류 요약}`

## 실패 알림

리서치가 전부 실패해 뉴스레터를 만들지 못한 경우에는, 같은 방법으로 제목 `[AutoAX] {date} 뉴스레터 생성 실패`, 본문에 실패 이유와 업무 폴더 경로만 담아 보낸다.
