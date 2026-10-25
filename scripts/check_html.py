#!/usr/bin/env python3
"""완성한 newsletter.html이 이메일 본문으로 보내기에 괜찮은지 점검한다.

점검 항목
- 항목마다 출처 링크: 기사 블록(<!-- ARTICLE -->)과 핵심 항목(<li>)마다 https 링크가 있는지
- 외부 파일·스크립트 금지: <script>, <link>, @import, src=, CSS url() 이 없는지
  (스타일은 HTML 안 style 속성에만 둔다)
- 채우지 않은 {{자리 표시}}가 없는지, 크기가 100KB 미만인지

사용법: python3 scripts/check_html.py newsletters/{날짜}_{주제}/newsletter.html
통과하면 종료 코드 0, 문제가 있으면 항목을 출력하고 1.
"""
import re
import sys
from pathlib import Path

MAX_BYTES = 100 * 1024  # Gmail은 약 102KB를 넘으면 본문을 자른다
LINK = re.compile(r'<a\b[^>]*href="(https://[^"]+)"', re.I)


def blocks(html: str, name: str) -> list[str]:
    return re.findall(rf"<!-- {name} -->(.*?)<!-- /{name} -->", html, re.S)


def main() -> None:
    html = Path(sys.argv[1]).read_text(encoding="utf-8")
    size = len(html.encode("utf-8"))
    problems = []

    # 크기·자리 표시
    if size >= MAX_BYTES:
        problems.append(f"파일이 너무 큽니다: {size/1024:.1f}KB (100KB 미만이어야 함)")
    left = sorted(set(re.findall(r"\{\{[A-Z0-9_]+\}\}", html)))
    if left:
        problems.append(f"채우지 않은 자리 표시: {', '.join(left)}")

    # 외부 파일·스크립트
    rules = {
        r"<script\b": "<script> 태그",
        r"\son[a-z]+\s*=": "onclick 같은 스크립트 속성",
        r"javascript:": "javascript: 링크",
        r"<link\b": "<link> 태그 (외부 CSS·폰트)",
        r"@import": "CSS @import",
        r"\ssrc\s*=": "src= 외부 자원 (이미지·iframe 등)",
        r"url\s*\(": "CSS url() 외부 자원",
        r"<(iframe|object|embed|form)\b": "iframe/object/embed/form",
    }
    for pat, label in rules.items():
        if re.search(pat, html, re.I):
            problems.append(f"쓸 수 없는 요소: {label}")

    # 링크 형식
    hrefs = re.findall(r'href="([^"]*)"', html)
    bad = [h for h in hrefs if not h.startswith("https://")]
    if bad:
        problems.append(f"https://가 아닌 링크 {len(bad)}개: {bad[:3]}")

    # 항목마다 출처 링크
    articles = blocks(html, "ARTICLE")
    if not articles:
        problems.append("기사 블록(<!-- ARTICLE -->)이 없습니다")
    for i, a in enumerate(articles, 1):
        if not LINK.search(a):
            problems.append(f"{i}번째 기사에 출처 링크가 없습니다")
    for hl in blocks(html, "HIGHLIGHTS"):
        for i, li in enumerate(re.findall(r"<li\b.*?</li>", hl, re.S), 1):
            if not LINK.search(li):
                problems.append(f"오늘의 핵심 {i}번째 줄에 출처 링크가 없습니다")

    if problems:
        print("점검 실패")
        for p in problems:
            print(f"- {p}")
        sys.exit(1)
    print(f"점검 통과 — {size/1024:.1f}KB, 기사 {len(articles)}건, 링크 {len(hrefs)}개")


if __name__ == "__main__":
    main()
