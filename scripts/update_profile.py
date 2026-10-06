"""Fetch public contribution data and generate the two profile panels.

Writes only after a successful fetch. No fallback to another person's data.
python scripts/update_profile.py --placeholder creates honest offline previews.
"""
from pathlib import Path
from datetime import date, datetime, timezone, timedelta
from collections import defaultdict
import html
import json
import os
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
OWNER = os.environ.get("GH_PROFILE_USER", "vitorluancordeiro22-dot")
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]


def fetch_days(owner):
    import requests
    from bs4 import BeautifulSoup

    if not re.fullmatch(r"[A-Za-z0-9-]{1,39}", owner):
        raise ValueError("Invalid GitHub username")
    response = requests.get(f"https://github.com/users/{owner}/contributions",
                            headers={"User-Agent": "github-profile-art/1.0"}, timeout=(10, 30))
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    days = []
    today = datetime.now(timezone.utc).date()
    for cell in soup.select("td.ContributionCalendar-day"):
        day = cell.get("data-date")
        if not day or date.fromisoformat(day) > today:
            continue
        tip = soup.find("tool-tip", attrs={"for": cell.get("id")})
        if tip is None:
            raise ValueError("GitHub markup changed: missing contribution tooltip")
        label = tip.get_text(" ", strip=True)
        if re.search(r"no contributions", label, re.I):
            count = 0
        else:
            match = re.match(r"([\d,]+)\s+contribution", label, re.I)
            if match is None:
                raise ValueError(f"Unexpected contribution label for {day}")
            count = int(match.group(1).replace(",", ""))
        days.append({"date": day, "count": count,
                     "level": max(0, min(4, int(cell.get("data-level") or 0)))})
    days.sort(key=lambda x: x["date"])
    if not days or len({d["date"] for d in days}) != len(days):
        raise ValueError("Missing or duplicate contribution dates")
    for left, right in zip(days, days[1:]):
        if date.fromisoformat(right["date"]) - date.fromisoformat(left["date"]) != timedelta(days=1):
            raise ValueError("Contribution calendar has gaps")
    return days


def compute_stats(days, today=None):
    if not days:
        raise ValueError("Cannot compute statistics from an empty calendar")
    today = today or datetime.now(timezone.utc).date()
    run = longest = 0
    for day in days:
        run = run + 1 if day["count"] else 0
        longest = max(longest, run)
    end = len(days) - 1
    # Allow the current day to remain unfinished, but never forgive an old zero.
    if days[end]["date"] == today.isoformat() and not days[end]["count"]:
        end -= 1
    current = 0
    while end >= 0 and days[end]["count"]:
        current += 1
        end -= 1
    monthly = defaultdict(int)
    for day in days:
        monthly[day["date"][:7]] += day["count"]
    total = sum(d["count"] for d in days)
    active = sum(d["count"] > 0 for d in days)
    return {"total": total, "active": active, "current": current, "longest": longest,
            "best": max(d["count"] for d in days),
            "average": round(total / active, 1) if active else 0,
            "monthly": dict(sorted(monthly.items()))}


def text(x, y, content, size=14, color="#d5d9df", anchor="start"):
    return (f'<text x="{x}" y="{y}" font-family="monospace" font-size="{size}" '
            f'fill="{color}" text-anchor="{anchor}">{html.escape(str(content))}</text>')


def window(width, height, title):
    pieces = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
              f'viewBox="0 0 {width} {height}" role="img">',
              f'<title>{html.escape(title)}</title>',
              f'<rect width="{width}" height="{height}" rx="14" fill="#0d1117"/>',
              f'<rect x=".5" y=".5" width="{width-1}" height="{height-1}" '
              'rx="14" fill="none" stroke="#30363d"/>',
              f'<path d="M0 32H{width}" stroke="#30363d"/>']
    for x, color in [(23, "#ff5f56"), (39, "#ffbd2e"), (55, "#27c93f")]:
        pieces.append(f'<circle cx="{x}" cy="16" r="5" fill="{color}"/>')
    pieces.append(text(width/2, 21, title, 12, "#8b949e", "middle"))
    return pieces


def render_stats(stats=None):
    pieces = window(840, 880, "vitin@github: ~$ ./stats.sh")
    labels = [("contribuições", "total", "no período exibido"),
              ("dias ativos", "active", "dias com contribuições"),
              ("sequência atual", "current", "dias consecutivos"),
              ("maior sequência", "longest", "no período exibido"),
              ("melhor dia", "best", "contribuições em um dia"),
              ("média / dia ativo", "average", "contribuições")]
    for i, (label, key, caption) in enumerate(labels):
        x, y = 20 + (i % 2) * 408, 54 + (i // 2) * 172
        value = str(stats[key]) if stats else "—"
        pieces.append(f'<g><animate attributeName="opacity" from="0" to="1" dur=".7s" fill="freeze"/>'
                      f'<rect x="{x}" y="{y}" width="392" height="156" rx="10" '
                      'fill="#161b22" stroke="#30363d"/>')
        pieces.append(text(x+22, y+36, "$ " + label, 22, "#8b949e"))
        pieces.append(text(x+22, y+102, value, 52, "#f0f2f5"))
        pieces.append(text(x+22, y+137, caption if stats else "aguardando primeira atualização", 17, "#8b949e"))
        pieces.append('</g>')
    pieces.append('<rect x="20" y="585" width="800" height="273" rx="10" fill="#161b22" stroke="#30363d"/>')
    pieces.append(text(44, 626, "$ contributions / month", 22, "#8b949e"))
    if stats:
        monthly = list(stats["monthly"].items())
        peak = max(value for _, value in monthly) or 1
        slot = 752 / len(monthly)
        for i, (month, value) in enumerate(monthly):
            h = 157 * value / peak
            x = 44 + i * slot + slot * .18
            pieces.append(f'<rect x="{x:.2f}" y="{813-h:.2f}" width="{slot*.64:.2f}" height="{h:.2f}" '
                          'rx="3" fill="#39d353"><animate attributeName="opacity" from="0" to="1" dur="1s" fill="freeze"/></rect>')
            pieces.append(text(x + slot*.32, 840, month[5:], 15, "#8b949e", "middle"))
    else:
        pieces.append(text(44, 690, "Os números reais aparecem após", 23))
        pieces.append(text(44, 730, "a primeira execução no GitHub.", 23))
        pieces.append(text(44, 811, "atualização diária · sem chave de API", 19, "#8b949e"))
    pieces.append('</svg>')
    return "".join(pieces)


def render_heatmap(days=None):
    pieces = window(888, 204, "vitin@github: ~/contributions --graph")
    if days:
        start = date.fromisoformat(days[0]["date"])
        sunday = start - timedelta(days=(start.weekday()+1) % 7)
        span = (date.fromisoformat(days[-1]["date"]) - sunday).days
        columns = span // 7 + 1
        step = min(15, 815 / columns)
        for i, day in enumerate(days):
            offset = (date.fromisoformat(day["date"]) - sunday).days
            x, y = 51 + (offset // 7) * step, 48 + (offset % 7) * 17
            pieces.append(f'<rect x="{x:.2f}" y="{y}" width="{step-3:.2f}" height="13" '
                          f'rx="2" fill="{PALETTE[day["level"]]}"><title>{day["date"]}: '
                          f'{day["count"]} contribuições</title><animate attributeName="opacity" '
                          'from="0" to="1" dur="1s" fill="freeze"/></rect>')
        for label, row in [("Seg",1), ("Qua",3), ("Sex",5)]:
            pieces.append(text(14, 59 + row*17, label, 11, "#8b949e"))
        pieces.append(text(51, 190, f'{sum(d["count"] for d in days):,} contribuições · {days[0]["date"]} a {days[-1]["date"]}', 13))
    else:
        pieces.append(text(28, 93, "$ aguardando dados reais do seu GitHub…", 19))
        pieces.append(text(28, 137, "O calendário será preenchido pela atualização automática.", 16, "#8b949e"))
    pieces.append('</svg>')
    return "".join(pieces)


if __name__ == "__main__":
    placeholder = "--placeholder" in sys.argv
    days = None if placeholder else fetch_days(OWNER)
    stats = compute_stats(days) if days else None
    (ROOT / "assets").mkdir(exist_ok=True)
    (ROOT / "assets/stats.svg").write_text(render_stats(stats), encoding="utf-8")
    (ROOT / "assets/heatmap.svg").write_text(render_heatmap(days), encoding="utf-8")
    if days:
        (ROOT / "data").mkdir(exist_ok=True)
        (ROOT / "data/contributions.json").write_text(json.dumps({
            "username": OWNER, "generated_at": datetime.now(timezone.utc).isoformat(),
            "days": days, "stats": stats}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Profile panels generated" + (" (waiting for real data)" if placeholder else ""))
