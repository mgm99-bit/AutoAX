#!/usr/bin/env python3
"""발송 경로 B — Gmail SMTP로 뉴스레터를 보낸다.

- 계정 정보는 저장소 루트의 .env 파일에서만 읽는다
  (GMAIL_ADDRESS, GMAIL_APP_PASSWORD, SMTP_HOST, SMTP_PORT — 587이면 STARTTLS, 465면 SSL).
  비밀번호를 코드·명령줄·로그에 쓰지 않는다. .env는 .gitignore에 있어 커밋되지 않는다.
- newsletter.html은 첨부가 아니라 메일 본문(text/html)으로 넣는다.
  구조: multipart/alternative = text/plain(요약) + text/html(뉴스레터). 첨부 파일 없음.

사용법:
  python3 scripts/send_smtp.py newsletters/2026-10-25_AI-에이전트
  python3 scripts/send_smtp.py newsletters/2026-10-25_AI-에이전트 --dry-run   # 보내지 않고 구조만 확인
  python3 scripts/send_smtp.py --test            # 본문(텍스트)만 있는 테스트 메일을 내 주소로
"""
import argparse
import datetime as dt
import html as htmllib
import json
import re
import smtplib
import ssl
import sys
from email.message import EmailMessage
from email.utils import formataddr, make_msgid
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / ".env"
PLACEHOLDER = "your-address@gmail.com"


def load_env(path: Path) -> dict:
    """KEY=VALUE 형식의 .env를 읽는다. 따옴표와 # 주석을 처리한다."""
    if not path.exists():
        sys.exit(f".env 파일이 없습니다: {path}\n.env.example을 복사해 .env를 만들고 값을 채우세요.")
    env = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "'\"":
            val = val[1:-1]
        else:
            val = val.split(" #", 1)[0].strip()
        env[key.strip()] = val
    return env


def plain_text(html: str) -> str:
    """HTML을 못 보는 메일 앱용 텍스트 버전: 제목과 링크 위주로."""
    links = re.findall(r'<a\b[^>]*href="(https://[^"]+)"[^>]*>(.*?)</a>', html, re.S)
    lines, seen = [], set()
    for url, label in links:
        label = htmllib.unescape(re.sub(r"<[^>]+>", "", label)).strip()
        if url in seen or label in ("", "출처"):
            continue
        seen.add(url)
        lines.append(f"- {label}\n  {url}")
    return "HTML을 지원하는 메일 앱에서 보면 더 보기 좋습니다.\n\n" + "\n".join(lines)


def smtp_send(env: dict, msg: EmailMessage) -> None:
    """.env의 SMTP_HOST/SMTP_PORT로 접속해 보낸다. 비밀번호는 출력하지 않는다."""
    host = env.get("SMTP_HOST") or "smtp.gmail.com"
    port = int(env.get("SMTP_PORT") or 587)
    user = env.get("GMAIL_ADDRESS", "")
    pw = env.get("GMAIL_APP_PASSWORD", "").replace(" ", "")  # Google이 4자리씩 띄워 보여 줌
    if not user or not pw:
        sys.exit(".env에 GMAIL_ADDRESS와 GMAIL_APP_PASSWORD를 채우세요.")
    if len(pw) != 16:
        print("주의: 앱 비밀번호는 보통 16자리입니다. Google 계정 비밀번호가 아닌 앱 비밀번호를 넣었는지 확인하세요.")

    ctx = ssl.create_default_context()
    try:
        if port == 465:
            server = smtplib.SMTP_SSL(host, port, context=ctx, timeout=30)
        else:
            server = smtplib.SMTP(host, port, timeout=30)
            server.starttls(context=ctx)
    except OSError as e:
        sys.exit(f"{host}:{port}에 연결하지 못했습니다 ({type(e).__name__}). 네트워크에서 SMTP가 막혀 있는지 확인하세요.")
    with server:
        try:
            server.login(user, pw)
        except smtplib.SMTPAuthenticationError:
            sys.exit("Gmail 로그인 실패: .env의 주소와 앱 비밀번호를 확인하세요 (2단계 인증 + 앱 비밀번호 필요).")
        server.send_message(msg)


def show(msg: EmailMessage) -> None:
    print(f"보내지 않음(dry-run) — 받는 사람: {msg['To']}, 제목: {msg['Subject']}")
    for part in msg.walk():
        print(f"  {part.get_content_type():24} {part.get_content_disposition() or '본문'}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("workdir", nargs="?", help="업무 폴더 (newsletters/{날짜}_{주제})")
    ap.add_argument("--test", action="store_true", help="본문만 있는 테스트 메일을 GMAIL_ADDRESS로 보냄")
    ap.add_argument("--dry-run", action="store_true", help="보내지 않고 메일 구조만 출력")
    args = ap.parse_args()
    if not args.test and not args.workdir:
        ap.error("업무 폴더를 주거나 --test를 쓰세요.")

    env = load_env(ENV_FILE)
    user = env.get("GMAIL_ADDRESS", "")
    msg = EmailMessage()
    msg["Message-ID"] = make_msgid(domain="autoax.local")

    if args.test:
        if not user:
            sys.exit(".env에 GMAIL_ADDRESS를 채우세요.")
        now = dt.datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M")
        msg["From"] = formataddr(("AutoAX 브리핑", user))
        msg["To"] = user
        msg["Subject"] = f"[AutoAX] SMTP 테스트 메일 ({now})"
        msg.set_content(
            "AutoAX 뉴스레터 에이전트의 SMTP 발송 테스트입니다.\n"
            "이 메일이 보이면 경로 B(Gmail SMTP) 설정이 정상입니다.\n"
        )  # text/plain 본문만, 첨부 없음
    else:
        workdir = Path(args.workdir)
        if not workdir.is_absolute():
            workdir = ROOT / workdir
        info = json.loads((workdir / "run.json").read_text(encoding="utf-8"))
        html = (workdir / "newsletter.html").read_text(encoding="utf-8")
        to = info.get("recipient", "")
        if not to or to == PLACEHOLDER:
            sys.exit("config/newsletter.toml의 recipient가 비어 있거나 예시 값입니다.")
        msg["From"] = formataddr((info.get("sender_name", "AutoAX 브리핑"), user or "sender@example.com"))
        msg["To"] = to
        msg["Subject"] = f"[AutoAX] {info['date']} {info['topic']} 브리핑"
        msg.set_content(plain_text(html))           # text/plain 본문
        msg.add_alternative(html, subtype="html")   # text/html 본문 (첨부 아님)

    if args.dry_run:
        show(msg)
        return
    smtp_send(env, msg)
    print(f"발송 완료 → {msg['To']} ({msg['Message-ID']})")


if __name__ == "__main__":
    main()
