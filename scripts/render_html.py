#!/usr/bin/env python3
"""업무 폴더의 content.json + 00_시세.json → newsletter.html (이메일 본문용).

- content.json: Claude가 리서치 파일에서 고른 내용 (핵심 3줄, 관심사별 항목, 일정)
- 00_시세.json: 시세 표는 이 파일에서 직접 읽는다 (옮겨 적기 오류 방지)
- 스타일은 전부 인라인 style 속성. 외부 파일·스크립트·이미지 없음.
- 점검 스크립트(check_html.py)가 쓰는 표시 주석(HIGHLIGHTS, ARTICLE)을 넣는다.

사용법: python3 scripts/render_html.py newsletters/{날짜}_데일리브리핑
"""
import datetime as dt
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 색: 오르면 빨강, 내리면 파랑 (한국식)
UP, DOWN, FLAT = "#dc2626", "#2563eb", "#6b7280"
INK, SUB, LINE, BG, ACCENT = "#111827", "#6b7280", "#e5e7eb", "#f3f4f6", "#1d4ed8"
FONT = "-apple-system,'Apple SD Gothic Neo','Malgun Gothic',sans-serif"
TAG_COLORS = {
    "숫자": ("#1e40af", "#dbeafe"),
    "원인": ("#9a3412", "#ffedd5"),
    "시사점": ("#065f46", "#d1fae5"),
    "전망": ("#6b21a8", "#f3e8ff"),
}
WEEKDAYS = "월화수목금토일"


def e(text) -> str:
    return html.escape(str(text), quote=True)


def link(url: str, label: str, style: str = "") -> str:
    if not str(url).startswith("https://"):
        sys.exit(f"https://가 아닌 링크: {url}")
    return f'<a href="{e(url)}" target="_blank" style="{style}">{e(label)}</a>'


def fmt_value(name: str, v: float) -> str:
    if name in ("삼성전자", "SK하이닉스"):
        return f"{v:,.0f}원"
    if name == "엔비디아":
        return f"${v:,.2f}"
    if "환율" in name:
        return f"{v:,.1f}원"
    return f"{v:,.2f}"


def fmt_pct(p) -> str:
    if p is None:
        return f'<span style="color:{FLAT};">-</span>'
    color = UP if p > 0 else DOWN if p < 0 else FLAT
    mark = "▲" if p > 0 else "▼" if p < 0 else ""
    return f'<span style="color:{color};">{mark}{abs(p):.2f}%</span>'


def prices_table(prices: dict, warnings: dict, weekend: bool) -> str:
    th = f"padding:6px 4px;font-size:12px;color:{SUB};font-weight:600;border-bottom:1px solid {LINE};"
    td = f"padding:7px 3px;font-size:13px;border-bottom:1px solid {LINE};"
    nw = "white-space:nowrap;"
    rows, notes, checks = [], [], []
    for it in prices.get("items", []):
        name = it["name"]
        if it.get("value") is None:
            rows.append(
                f'<tr><td style="{td}">{e(name)}</td>'
                f'<td colspan="{3 if weekend else 2}" style="{td}color:{SUB};">데이터 없음</td></tr>'
            )
            continue
        flag = ""
        if it.get("verified") is False:
            if name not in warnings:
                sys.exit(f"시세 '{name}'이 verified=false인데 content.json의 price_warnings에 설명이 없습니다.")
            flag = " ⚠"
            notes.append(f"⚠ {name}: {warnings[name]}")
        # 좁은 화면을 위해 출처 열은 두지 않는다: 이름 자체가 출처 링크, 대조 링크는 표 아래 한 줄로
        if it.get("source_check"):
            checks.append(link(it["source_check"], name, f"color:{SUB};"))
        weekly = fmt_pct(it.get("weekly_change_pct")) if weekend else ""
        name_link = link(it["source"], name, f"color:{INK};text-decoration:none;")
        rows.append(
            f'<tr><td style="{td}{nw}font-weight:600;">{name_link}{flag}</td>'
            f'<td style="{td}{nw}text-align:right;color:{INK};">{e(fmt_value(name, it["value"]))}</td>'
            f'<td style="{td}{nw}text-align:right;">{fmt_pct(it.get("change_pct"))}</td>'
            + (f'<td style="{td}{nw}text-align:right;">{weekly}</td>' if weekend else "")
            + "</tr>"
        )
    as_of = next((i.get("as_of") for i in prices.get("items", []) if i.get("as_of")), "")
    head = (
        f'<tr><th align="left" style="{th}">구분 (누르면 출처)</th><th align="right" style="{th}">종가</th>'
        f'<th align="right" style="{th}">전일 대비</th>'
        + (f'<th align="right" style="{th}">주간</th>' if weekend else "")
        + "</tr>"
    )
    note_html = "".join(
        f'<div style="font-size:12px;color:#92400e;margin-top:4px;padding:0 12px;">{e(n)}</div>' for n in notes
    )
    if checks:
        note_html += (
            f'<div style="font-size:11px;color:{SUB};margin-top:6px;padding:0 12px;line-height:1.7;">'
            f'대조 출처: {" · ".join(checks)}</div>'
        )
    return (
        f'<tr><td style="padding:20px 16px 4px;">'
        f'<div style="font-size:15px;font-weight:700;color:{ACCENT};margin-bottom:8px;padding-left:12px;">시세 '
        f'<span style="font-size:12px;font-weight:400;color:{SUB};">기준: {e(as_of)} · 해외는 미 동부시간</span></div>'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">{head}{"".join(rows)}</table>'
        f"{note_html}</td></tr>"
    )


def article(item: dict) -> str:
    fg, bg = TAG_COLORS.get(item["tag"], ("#374151", "#e5e7eb"))
    warn = (
        f'<div style="font-size:12px;color:#92400e;margin-top:6px;">⚠ {e(item["warning"])}</div>'
        if item.get("warning")
        else ""
    )
    return (
        "<!-- ARTICLE -->"
        f'<tr><td style="padding:8px 28px;">'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
        f'style="background:#f9fafb;border:1px solid {LINE};border-radius:6px;"><tr><td style="padding:12px 14px;">'
        f'<span style="display:inline-block;font-size:11px;font-weight:700;color:{fg};background:{bg};'
        f'border-radius:3px;padding:1px 6px;margin-bottom:6px;">{e(item["tag"])}</span><br>'
        + link(item["url"], item["title"], f"font-size:15px;font-weight:700;color:{INK};text-decoration:none;line-height:1.45;")
        + f'<div style="font-size:12px;color:{SUB};margin:4px 0 8px;">출처: '
        + link(item["url"], item["source"], f"color:{SUB};")
        + f' · {e(item["date"])}</div>'
        f'<div style="font-size:14px;line-height:1.65;color:#374151;">{e(item["summary"])}</div>'
        f'<div style="font-size:13px;line-height:1.6;color:#065f46;background:#ecfdf5;border-radius:4px;'
        f'padding:6px 10px;margin-top:8px;"><b>왜 중요한가</b> · {e(item["why"])}</div>'
        f"{warn}</td></tr></table></td></tr>"
        "<!-- /ARTICLE -->"
    )


def main() -> None:
    workdir = Path(sys.argv[1])
    if not workdir.is_absolute():
        workdir = ROOT / workdir
    info = json.loads((workdir / "run.json").read_text(encoding="utf-8"))
    content = json.loads((workdir / "content.json").read_text(encoding="utf-8"))
    prices_path = workdir / "00_시세.json"
    prices = json.loads(prices_path.read_text(encoding="utf-8")) if prices_path.exists() else {}
    weekend = info.get("edition") == "주말판"

    date = dt.date.fromisoformat(info["date"])
    date_label = f"{date.month}/{date.day}({WEEKDAYS[date.weekday()]})"
    edition = info.get("edition", "")

    # 오늘의 핵심
    hl = "".join(
        f'<li style="margin-bottom:8px;">{e(h["text"])} '
        + link(h["url"], "출처", f"color:{ACCENT};font-size:12px;")
        + "</li>"
        for h in content["highlights"]
    )
    highlights = (
        f'<tr><td style="padding:20px 28px 4px;">'
        f'<div style="font-size:15px;font-weight:700;color:{ACCENT};margin-bottom:8px;">오늘의 핵심</div>'
        "<!-- HIGHLIGHTS -->"
        f'<ol style="margin:0;padding-left:20px;font-size:15px;line-height:1.65;color:{INK};">{hl}</ol>'
        "<!-- /HIGHLIGHTS --></td></tr>"
    )

    # 관심사별 섹션
    sections = []
    for sec in content["sections"]:
        if not sec.get("items"):
            body = f'<tr><td style="padding:4px 28px;font-size:14px;color:{SUB};">이번에는 새 소식이 없습니다.</td></tr>'
        else:
            body = "".join(article(i) for i in sec["items"])
        sections.append(
            f'<tr><td style="padding:24px 28px 4px;">'
            f'<div style="font-size:18px;font-weight:700;color:{INK};border-left:4px solid {ACCENT};padding-left:10px;">'
            f'{e(sec["interest"])}</div></td></tr>{body}'
        )

    # 일정
    sched_rows = "".join(
        f'<tr><td style="padding:6px 8px 6px 0;font-size:13px;font-weight:700;color:{INK};white-space:nowrap;'
        f'vertical-align:top;border-bottom:1px solid {LINE};">{e(s["when"])}</td>'
        f'<td style="padding:6px 0;font-size:13px;color:#374151;border-bottom:1px solid {LINE};">'
        + link(s["url"], s["event"], f"color:#374151;text-decoration:none;")
        + (f' <span style="color:#92400e;">⚠ {e(s["warning"])}</span>' if s.get("warning") else "")
        + "</td></tr>"
        for s in content.get("schedule", [])
    )
    schedule = (
        f'<tr><td style="padding:24px 28px 4px;">'
        f'<div style="font-size:18px;font-weight:700;color:{INK};border-left:4px solid {ACCENT};padding-left:10px;'
        f'margin-bottom:8px;">{e(content.get("schedule_title", "다가오는 일정"))}</div>'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">{sched_rows}</table>'
        "</td></tr>"
        if sched_rows
        else ""
    )

    footer_notes = "".join(f"{e(n)}<br>" for n in content.get("footer_notes", []))
    page = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<title>AutoAX 데일리 브리핑 {e(date_label)}</title>
</head>
<body style="margin:0;padding:0;background:{BG};">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;">{e(content["preheader"])}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{BG};">
<tr><td align="center" style="padding:20px 10px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:640px;background:#ffffff;border-radius:8px;font-family:{FONT};color:{INK};">
<tr><td style="padding:26px 28px 18px;border-bottom:3px solid {ACCENT};">
<div style="font-size:13px;color:{SUB};">AutoAX 데일리 브리핑 · {e(info["date"])} ({e(info.get("weekday", ""))}) · {e(edition)}</div>
<div style="font-size:22px;font-weight:700;margin-top:6px;color:{INK};line-height:1.4;">{e(content["headline"])}</div>
</td></tr>
{highlights}
{prices_table(prices, content.get("price_warnings", {}), weekend) if prices else ""}
{"".join(sections)}
{schedule}
<tr><td style="padding:24px 28px 26px;border-top:1px solid {LINE};margin-top:16px;font-size:12px;line-height:1.7;color:#9ca3af;">
이 메일은 AutoAX 뉴스레터 에이전트가 공개 소스를 리서치해 자동으로 작성했습니다. 투자 권유가 아니며, 중요한 내용은 원문 링크로 확인하세요.<br>
{footer_notes}리서치 원본: {e(info["workdir"])}/
</td></tr>
</table>
</td></tr>
</table>
</body>
</html>
"""
    out = workdir / "newsletter.html"
    out.write_text(page, encoding="utf-8")
    n = sum(len(s.get("items", [])) for s in content["sections"])
    print(f"저장: {out.relative_to(ROOT)} ({len(page.encode('utf-8')) / 1024:.1f}KB, 항목 {n}건)")


if __name__ == "__main__":
    main()
