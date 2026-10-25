---
name: newsletter-send
description: 업무 폴더의 newsletter.html을 메일 본문으로 사용자의 Gmail에 발송하고 결과를 run_log.md에 기록한다. 경로 A(연결된 Gmail 커넥터)를 먼저 쓰고, 안 되면 경로 B(Gmail SMTP, 루트 .env의 계정 정보)로 보낸다. 뉴스레터 HTML이 완성된 뒤 메일을 보낼 때 사용한다.
---

# 뉴스레터 메일 발송

## 공통 원칙

- **HTML은 첨부가 아니라 메일 본문으로** 보낸다. 두 경로 모두 첨부 파일을 쓰지 않는다.
- `newsletter.html` 내용을 고치지 않고 그대로 본문에 넣는다.
- 제목: `[AutoAX] {date} {topic} 브리핑`
- 계정 비밀번호를 대화, 로그, `run_log.md`, 커밋 어디에도 쓰지 않는다.

## 발송 전 확인

1. `run_log.md`에 `메시지 ID`가 이미 있으면 **보내지 않는다** (중복 발송 방지). 사용자가 "다시 보내 줘"라고 명시한 경우만 예외.
2. `run.json`의 `recipient`가 비었거나 `your-address@gmail.com`이면 보내지 말고 `config/newsletter.toml`을 채워 달라고 알린 뒤 멈춘다.
3. `python3 scripts/check_html.py {workdir}/newsletter.html` 이 통과해야 한다.

## 경로 A — 연결된 Gmail 커넥터 (1순위)

Gmail 커넥터의 `send_message` 도구를 호출한다. 도구가 안 보이면 도구 검색으로 `send_message`를 불러온다.

| 필드 | 값 |
|---|---|
| `to` | `[recipient]` |
| `subject` | `[AutoAX] {date} {topic} 브리핑` |
| `htmlBody` | `newsletter.html` 파일 내용 전체 |
| `body` | 텍스트 버전: 오늘의 핵심 3줄 + 기사 제목과 URL 목록. 마크다운 기호 금지 |
| `attachments` | **넣지 않는다** |

- 메일은 커넥터에 연결된 Gmail 계정에서 나간다.
- 성공하면 응답의 `id`를 기록한다.
- 커넥터가 연결되지 않았거나 오류가 나면 경로 B로 넘어간다.

## 경로 B — Gmail SMTP (대체)

계정 정보는 **저장소 루트의 `.env`** 에서만 읽는다.

```
GMAIL_ADDRESS=보내는 Gmail 주소
GMAIL_APP_PASSWORD=(16자리 앱 비밀번호 — 사용자가 직접 입력)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587        # 587이면 STARTTLS, 465면 SSL
```

- `.env`는 `.gitignore`에 있어 커밋되지 않는다. 형식 예시는 `.env.example`(빈 값)에 있다.
- 앱 비밀번호를 코드, 명령줄 인자, 기획서, 대화에 적지 않는다. `.env` 내용을 출력(`cat` 등)하지 않는다.
- `.env`가 없으면 사용자에게 `.env.example`을 복사해 직접 채워 달라고 안내하고 멈춘다. 대신 만들어 주겠다며 비밀번호를 물어보지 않는다.

```bash
# 처음 설정했을 때: 본문만 있는 테스트 메일을 내 주소로
python3 scripts/send_smtp.py --test
# 먼저 구조 확인 (보내지 않음): text/plain + text/html 본문만 있고 첨부가 없어야 한다
python3 scripts/send_smtp.py {workdir} --dry-run
# 실제 발송
python3 scripts/send_smtp.py {workdir}
```

출력된 Message-ID를 기록한다.

## 기록

`{workdir}/run_log.md`에 추가한다.

- 성공: `- HH:MM 발송 성공 (경로 A: Gmail 커넥터 | 경로 B: SMTP) → {recipient}, 메시지 ID: {id}`
- 실패: `- HH:MM 발송 실패: {경로별 오류 요약}` (비밀번호·토큰은 적지 않음)

## 실패 알림

리서치가 전부 실패해 뉴스레터를 만들지 못한 경우에는, 같은 순서(A → B)로 제목 `[AutoAX] {date} 뉴스레터 생성 실패`, 본문에 실패 이유와 업무 폴더 경로만 담아 보낸다.

## 환경 제약

클라우드 세션은 웹(HTTPS) 연결만 허용해 `smtp.gmail.com`에 닿지 않는다 (주소 조회 실패). 클라우드에서는 경로 A를 쓰고, 경로 B는 사용자 컴퓨터에서 실행한다.
