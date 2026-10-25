#!/usr/bin/env python3
"""업무 폴더의 리서치 결과를 점검한다.

관점별 .md
- run.json의 관점 파일이 모두 있는지
- 관심사 섹션(## 관심사 이름)이 모두 있는지
- 항목(### 제목)마다 '링크:' 줄이 있는지
- 로그인·결제가 필요한 제외 도메인(blocked_domains) 링크가 없는지

00_시세.json
- 시세 대상이 모두 있는지, 값이 있는 대상은 기준 시각·출처가 있는지
- 출처가 제외 도메인이 아닌지

사용법: python3 scripts/check_research.py newsletters/{날짜}_데일리브리핑
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


def sections(text: str) -> dict[str, str]:
    """'## 제목' 기준으로 나눈다."""
    out = {}
    for chunk in re.split(r"\n(?=## )", "\n" + text):
        if chunk.startswith("## "):
            title, _, body = chunk[3:].partition("\n")
            out[title.strip()] = body
    return out


def check_perspective(p: dict, interests: list[str], domains: list[str], problems: list) -> int:
    f = ROOT / p["file"]
    name = p["name"]
    if not f.exists() or not f.read_text(encoding="utf-8").strip():
        problems.append(f"{name}: 파일이 없거나 비어 있음 ({p['file']})")
        return 0
    text = f.read_text(encoding="utf-8")
    if "자료를 찾지 못함" in text:
        print(f"- {name}: 자료 없음으로 표시됨")
        return 0

    secs = sections(text)
    count = 0
    for interest in interests:
        if interest not in secs:
            problems.append(f"{name}: '## {interest}' 섹션이 없음")
            continue
        body = secs[interest]
        items = re.split(r"\n(?=### )", "\n" + body)
        items = [i for i in items if i.startswith("### ")]
        if not items and "새 소식 없음" not in body:
            problems.append(f"{name} / {interest}: 항목도 '새 소식 없음' 표시도 없음")
        for it in items:
            title = it.splitlines()[0][4:].strip()
            m = re.search(r"링크:\s*(https?://\S+)", it)
            if not m:
                problems.append(f"{name} / {interest} / {title}: 출처 링크 없음")
            elif blocked(m.group(1), domains):
                problems.append(f"{name} / {interest} / {title}: 로그인·결제 필요 소스 ({m.group(1)})")
            count += 1
    return count


def check_prices(info: dict, domains: list[str], problems: list) -> tuple[int, int]:
    path = ROOT / info["prices_file"]
    tickers = info.get("tickers", [])
    if not tickers:
        return 0, 0
    if not path.exists():
        problems.append(f"시세 파일이 없음 ({info['prices_file']})")
        return 0, len(tickers)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        problems.append(f"시세 파일 JSON 오류: {e}")
        return 0, len(tickers)
    items = {i.get("name"): i for i in data.get("items", [])}
    ok = 0
    for t in tickers:
        it = items.get(t)
        if it is None:
            problems.append(f"시세: '{t}' 항목이 없음")
            continue
        if it.get("value") is None:
            continue  # '데이터 없음'으로 표시된 경우 허용
        for key in ("as_of", "source"):
            if not it.get(key):
                problems.append(f"시세: '{t}'에 {key} 없음")
        for key in ("source", "source_check"):
            url = it.get(key) or ""
            if url and blocked(url, domains):
                problems.append(f"시세: '{t}' {key}가 로그인·결제 필요 소스 ({url})")
        ok += 1
    return ok, len(tickers)


def main() -> None:
    workdir = Path(sys.argv[1])
    if not workdir.is_absolute():
        workdir = ROOT / workdir
    info = json.loads((workdir / "run.json").read_text(encoding="utf-8"))
    domains = [d.lower() for d in info.get("blocked_domains", [])]
    interests = [i["name"] for i in info.get("interests", [])]
    problems: list[str] = []

    total, done = 0, 0
    for p in info["perspectives"]:
        n = check_perspective(p, interests, domains, problems)
        total += n
        done += n > 0
    price_ok, price_all = check_prices(info, domains, problems)

    summary = f"관점 {done}/{len(info['perspectives'])}, 항목 {total}건, 시세 {price_ok}/{price_all}"
    if problems:
        print(f"점검 실패 — {summary}")
        for x in problems:
            print(f"- {x}")
        sys.exit(1)
    print(f"점검 통과 — {summary}")


if __name__ == "__main__":
    main()
