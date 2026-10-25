#!/usr/bin/env python3
"""업무 폴더의 관점별 리서치 파일을 점검한다.

- run.json에 적힌 관점 파일이 모두 있는지
- 기사(### 제목)마다 '링크:' 줄이 있는지
- 로그인·결제가 필요한 제외 도메인(blocked_domains) 링크가 없는지

사용법: python3 scripts/check_research.py newsletters/{날짜}_{주제}
"""
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent


def blocked(url: str, domains: list[str]) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return any(host == d or host.endswith("." + d) for d in domains)


def main() -> None:
    workdir = Path(sys.argv[1])
    if not workdir.is_absolute():
        workdir = ROOT / workdir
    info = json.loads((workdir / "run.json").read_text(encoding="utf-8"))
    domains = [d.lower() for d in info.get("blocked_domains", [])]
    problems, ok = [], 0

    for p in info["perspectives"]:
        f = ROOT / p["file"]
        if not f.exists() or not f.read_text(encoding="utf-8").strip():
            problems.append(f"{p['name']}: 파일이 없거나 비어 있음 ({p['file']})")
            continue
        text = f.read_text(encoding="utf-8")
        if "자료를 찾지 못함" in text:
            print(f"- {p['name']}: 자료 없음으로 표시됨")
            continue
        # '## 기사' 구역의 기사 블록만 본다 (참고·메모 제외)
        body = text.split("## 기사", 1)[-1].split("\n## ", 1)[0]
        articles = re.split(r"\n### ", "\n" + body)[1:]
        reported = set()
        if not articles:
            problems.append(f"{p['name']}: 기사가 없음")
        for a in articles:
            title = a.splitlines()[0].strip()
            m = re.search(r"링크:\s*(https?://\S+)", a)
            if not m:
                problems.append(f"{p['name']} / {title}: 출처 링크 없음")
            elif blocked(m.group(1), domains):
                reported.add(m.group(1))
                problems.append(f"{p['name']} / {title}: 로그인·결제 필요 소스 ({m.group(1)})")
        for url in re.findall(r"https?://[^\s)>\]]+", text):
            if blocked(url, domains) and url not in reported:
                reported.add(url)
                problems.append(f"{p['name']}: 제외 도메인 링크 ({url})")
        ok += 1

    if problems:
        print("점검 실패")
        for x in problems:
            print(f"- {x}")
        sys.exit(1)
    print(f"점검 통과 — 관점 {ok}/{len(info['perspectives'])}개")


if __name__ == "__main__":
    main()
