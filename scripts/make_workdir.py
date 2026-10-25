#!/usr/bin/env python3
"""오늘의 주제를 고르고 newsletters/{날짜}_{주제}/ 업무 폴더를 만든다.

결과는 JSON 한 줄로 출력한다. 다음 단계(리서치·HTML·발송)는 이 JSON을 입력으로 쓴다.

사용법:
  python3 scripts/make_workdir.py                 # 설정대로 주제 선택
  python3 scripts/make_workdir.py --topic "AI 에이전트"
  python3 scripts/make_workdir.py --date 2026-10-25 --dry-run
"""
import argparse
import datetime as dt
import json
import re
import sys
import tomllib
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config" / "newsletter.toml"
OUT_DIR = ROOT / "newsletters"


def slug(text: str) -> str:
    """파일 이름에 쓸 수 있게 정리한다. 한글은 그대로 두고 공백은 '-'로."""
    text = re.sub(r'[\\/:*?"<>|]', "", text).strip()
    text = text.replace("·", "-")
    return re.sub(r"[\s-]+", "-", text).strip("-") or "주제"


def pick_topic(cfg: dict, today: dt.date, name: str | None) -> dict:
    topics = cfg.get("topics") or []
    if not topics:
        sys.exit("config/newsletter.toml에 [[topics]]가 없습니다.")
    if name:
        for t in topics:
            if t["name"] == name:
                return t
        sys.exit(f"설정에 없는 주제입니다: {name}")
    if cfg.get("topic_mode", "rotate") == "fixed":
        return topics[0]
    return topics[today.toordinal() % len(topics)]


def unique_dir(base: Path) -> Path:
    """같은 날 같은 주제로 다시 돌리면 _2, _3을 붙여 덮어쓰기를 막는다."""
    if not base.exists():
        return base
    n = 2
    while (base.parent / f"{base.name}_{n}").exists():
        n += 1
    return base.parent / f"{base.name}_{n}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic")
    ap.add_argument("--date", help="YYYY-MM-DD (기본: 설정 시간대의 오늘)")
    ap.add_argument("--dry-run", action="store_true", help="폴더를 만들지 않고 결과만 출력")
    args = ap.parse_args()

    cfg = tomllib.loads(CONFIG.read_text(encoding="utf-8"))
    tz = ZoneInfo(cfg.get("timezone", "Asia/Seoul"))
    today = dt.date.fromisoformat(args.date) if args.date else dt.datetime.now(tz).date()

    topic = pick_topic(cfg, today, args.topic)
    workdir = unique_dir(OUT_DIR / f"{today.isoformat()}_{slug(topic['name'])}")

    rel = workdir.relative_to(ROOT)  # 저장소 위치가 달라도 쓸 수 있게 상대 경로로
    perspectives = [
        {
            "name": p,
            "file": str(rel / f"{i:02d}_{slug(p)}.md"),
        }
        for i, p in enumerate(topic["perspectives"], start=1)
    ]

    info = {
        "date": today.isoformat(),
        "topic": topic["name"],
        "keywords": topic.get("keywords", []),
        "exclude": topic.get("exclude", []),
        "perspectives": perspectives,
        "items_per_perspective": cfg.get("items_per_perspective", 3),
        "lookback_hours": cfg.get("lookback_hours", 24),
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
            f"# 실행 기록 — {info['date']} {info['topic']}\n\n"
            f"- {now} 업무 폴더 생성\n",
            encoding="utf-8",
        )
        (workdir / "run.json").write_text(
            json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    print(json.dumps(info, ensure_ascii=False))


if __name__ == "__main__":
    main()
