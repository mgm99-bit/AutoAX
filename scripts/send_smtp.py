#!/usr/bin/env python3
"""Gmail 커넥터를 쓸 수 없을 때의 대체 발송 (Gmail SMTP + 앱 비밀번호).

필요한 환경 변수:
  GMAIL_ADDRESS       보내는 Gmail 주소
  GMAIL_APP_PASSWORD  Google 계정 > 보안 > 앱 비밀번호 (2단계 인증 필요)

사용법:
  python3 scripts/send_smtp.py --to me@gmail.com --subject "제목" \
      --html newsletters/2026-10-25_AI-에이전트/newsletter.html [--text 요약.txt]
"""
import argparse
import os
import smtplib
import ssl
import sys
from email.message import EmailMessage
from email.utils import make_msgid
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--to", required=True)
    ap.add_argument("--subject", required=True)
    ap.add_argument("--html", required=True)
    ap.add_argument("--text", help="텍스트 버전 파일 (없으면 간단한 안내문)")
    ap.add_argument("--sender-name", default="AutoAX 브리핑")
    args = ap.parse_args()

    user = os.environ.get("GMAIL_ADDRESS")
    pw = os.environ.get("GMAIL_APP_PASSWORD")
    if not user or not pw:
        sys.exit("GMAIL_ADDRESS, GMAIL_APP_PASSWORD 환경 변수가 필요합니다.")

    html = Path(args.html).read_text(encoding="utf-8")
    text = (
        Path(args.text).read_text(encoding="utf-8")
        if args.text
        else "HTML을 지원하는 메일 앱에서 열어 주세요."
    )

    msg = EmailMessage()
    msg["From"] = f"{args.sender_name} <{user}>"
    msg["To"] = args.to
    msg["Subject"] = args.subject
    msg["Message-ID"] = make_msgid(domain="autoax.local")
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context()) as s:
        s.login(user, pw)
        s.send_message(msg)
    print(msg["Message-ID"])


if __name__ == "__main__":
    main()
