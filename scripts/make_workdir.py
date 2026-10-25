#!/usr/bin/env python3
"""오늘의 업무 폴더 newsletters/{날짜}_{주제}/ 를 만들고 실행 정보(run.json)를 저장한다.

결과는 JSON 한 줄로도 출력한다. 다음 단계(리서치·HTML·발송)는 run.json을 입력으로 쓴다.

사용법:
  python3 scripts/make_workdir.py
  python3 scripts/make_workdir.py --date 2026-10-27 --dry-run
"""
import argparse
import datetime as dt
import json
import re
import tomllib
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config" / "newsletter.toml"
OUT_DIR = ROOT / "newsletters"
WEEKDAYS = "월화수목금토일"


def slug(text: str) -> str:
    """파일 이름에 쓸 수 있게 정리한다. 한글은 그대로 두고 공백·가운뎃점은 '-'로."""
    text = re.sub(r'[\\/:*?"<>|()]', "", text).strip().replace("·", "-")
    return re.sub(r"[\s-]+", "-", text).strip("-") or "주제"


def unique_dir(base: Path) -> Path:
    """같은 날 다시 돌리면 _2, _3을 붙여 덮어쓰기를 막는다."""
    if not base.exists():
        return base
    n = 2
    while (base.parent / f"{base.name}_{n}").exists():
        n += 1
    return base.parent / f"{base.name}_{n}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="YYYY-MM-DD (기본: 설정 시간대의 오늘)")
    ap.add_argument("--dry-run", action="store_true", help="폴더를 만들지 않고 결과만 출력")
    args = ap.parse_args()

    cfg = tomllib.loads(CONFIG.read_text(encoding="utf-8"))
    tz = ZoneInfo(cfg.get("timezone", "Asia/Seoul"))
    today = dt.date.fromisoformat(args.date) if args.date else dt.datetime.now(tz).date()
    weekday = today.weekday()  # 월=0 … 일=6
    weekend = weekday >= 5

    if weekend:
        lookback = cfg.get("weekend_lookback_hours", 168)
    elif weekday == 0:
        lookback = max(cfg.get("lookback_hours", 24), 72)  # 월요일은 주말 포함
    else:
        lookback = cfg.get("lookback_hours", 24)

    topic = cfg.get("folder_topic", "데일리브리핑")
    workdir = unique_dir(OUT_DIR / f"{today.isoformat()}_{slug(topic)}")
    rel = workdir.relative_to(ROOT)  # 저장소 위치가 달라도 쓸 수 있게 상대 경로로

    interests = cfg.get("interests", [])
    tickers = next((i.get("tickers", []) for i in interests if i.get("tickers")), [])

    info = {
        "date": today.isoformat(),
        "weekday": WEEKDAYS[weekday],
        "edition": "주말판" if weekend else "평일판",
        "topic": topic,
        "interests": [
            {"name": i["name"], "keywords": i.get("keywords", [])} for i in interests
        ],
        "tickers": tickers,
        "perspectives": [
            {"name": p, "file": str(rel / f"{n:02d}_{slug(p)}.md")}
            for n, p in enumerate(cfg.get("perspectives", []), start=1)
        ],
        "prices_file": str(rel / "00_시세.json"),
        "items_per_interest": cfg.get("items_per_interest", 2),
        "lookback_hours": lookback,
        "blocked_domains": cfg.get("blocked_domains", []),
        "language": cfg.get("language", "ko"),
        "recipient": cfg.get("recipient", ""),
        "sender_name": cfg.get("sender_name", "AutoAX 브리핑"),
        "workdir": str(rel),
        "html": str(rel / "newsletter.html"),
        "log": str(rel / "run_log.md"),
    }

    if not args.dry_run:
        workdir.mkdir(parents=True)
        now = dt.datetime.now(tz).strftime("%Y-%m-%d %H:%M %Z")
        (ROOT / info["log"]).write_text(
            f"# 실행 기록 — {info['date']}({info['weekday']}) {topic} {info['edition']}\n\n"
            f"- {now} 업무 폴더 생성\n",
            encoding="utf-8",
        )
        (workdir / "run.json").write_text(
            json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    print(json.dumps(info, ensure_ascii=False))


if __name__ == "__main__":
    main()
