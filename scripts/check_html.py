#!/usr/bin/env python3
"""완성한 newsletter.html이 이메일로 보내기에 괜찮은지 점검한다.

사용법: python3 scripts/check_html.py newsletters/{날짜}_{주제}/newsletter.html
통과하면 종료 코드 0, 문제가 있으면 항목을 출력하고 1.
"""
import re
import sys
from pathlib import Path

MAX_BYTES = 100 * 1024  # Gmail은 약 102KB를 넘으면 본문을 자른다


def main() -> None:
    path = Path(sys.argv[1])
    html = path.read_text(encoding="utf-8")
    size = len(html.encode("utf-8"))
    problems = []

    if size >= MAX_BYTES:
        problems.append(f"파일이 너무 큽니다: {size/1024:.1f}KB (100KB 미만이어야 함)")
    left = sorted(set(re.findall(r"\{\{[A-Z0-9_]+\}\}", html)))
    if left:
        problems.append(f"채우지 않은 자리 표시: {', '.join(left)}")
    if re.search(r"<script\b", html, re.I):
        problems.append("<script>는 이메일에서 쓸 수 없습니다")
    if re.search(r"<style\b|<link\b[^>]*stylesheet", html, re.I):
        problems.append("<style>/외부 CSS 대신 인라인 스타일을 쓰세요")

    hrefs = re.findall(r'href="([^"]*)"', html)
    bad = [h for h in hrefs if not h.startswith("https://")]
    if bad:
        problems.append(f"https://가 아닌 링크 {len(bad)}개: {bad[:3]}")
    if len(hrefs) == 0:
        problems.append("기사 링크가 하나도 없습니다")

    if problems:
        print("점검 실패")
        for p in problems:
            print(f"- {p}")
        sys.exit(1)
    print(f"점검 통과 — {size/1024:.1f}KB, 링크 {len(hrefs)}개")


if __name__ == "__main__":
    main()
