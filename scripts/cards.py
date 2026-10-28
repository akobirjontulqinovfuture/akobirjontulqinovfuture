"""Draw the profile's stats and languages cards from the public GitHub API (no third-party card service).

    GH_TOKEN=... python scripts/cards.py      # writes assets/stats-{dark,light}.svg, assets/langs-{dark,light}.svg
"""
import json
import os
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from html import escape

USER = "akobirjontulqinovfuture"
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")


def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}", headers={"Accept": "application/vnd.github+json"})
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


user = api(f"/users/{USER}")
repos = [r for r in api(f"/users/{USER}/repos?per_page=100&type=owner") if not r["fork"]]
stars = sum(r["stargazers_count"] for r in repos)
langs = Counter()
for r in repos:
    for k, v in api(f"/repos/{USER}/{r['name']}/languages").items():
        langs[k] += v
since = datetime.fromisoformat(user["created_at"].replace("Z", "+00:00"))
stats = [("Public repositories", len(repos)), ("Stars earned", stars), ("Followers", user["followers"]),
         ("On GitHub since", since.strftime("%b %Y"))]
COLORS = {"HTML": "#E34F26", "CSS": "#663399", "JavaScript": "#F7DF1E", "Python": "#3776AB", "TypeScript": "#3178C6",
          "Shell": "#89E051", "GLSL": "#5686A5"}
THEMES = {"dark": dict(bg="#0D0D0D", line="#262626", txt="#F6F5F0", mut="#9A9A93", acc="#3DDC84"),
          "light": dict(bg="#FFFFFF", line="#E5E4DE", txt="#111111", mut="#5E5E58", acc="#178A52")}
FONT = "font-family='Segoe UI,Inter,Helvetica,Arial,sans-serif'"
stamp = datetime.now(timezone.utc).strftime("%d %b %Y")
for name, t in THEMES.items():
    rows = "".join(
        f"<text x='28' y='{86 + i * 32}' fill='{t['mut']}' font-size='14' {FONT}>{escape(k)}</text>"
        f"<text x='392' y='{86 + i * 32}' fill='{t['txt']}' font-size='14' font-weight='600' text-anchor='end' {FONT}>{v}</text>"
        for i, (k, v) in enumerate(stats))
    svg = (f"<svg xmlns='http://www.w3.org/2000/svg' width='420' height='230' viewBox='0 0 420 230'>"
           f"<rect x='.5' y='.5' width='419' height='229' rx='14' fill='{t['bg']}' stroke='{t['line']}'/>"
           f"<rect x='28' y='26' width='26' height='4' rx='2' fill='{t['acc']}'/>"
           f"<text x='28' y='50' fill='{t['txt']}' font-size='16' font-weight='700' {FONT}>GitHub at a glance</text>"
           f"{rows}<text x='392' y='218' fill='{t['mut']}' font-size='10' text-anchor='end' {FONT}>public data · {stamp}</text></svg>")
    open(f"assets/stats-{name}.svg", "w").write(svg)
    total = sum(langs.values()) or 1
    top = [(k, v) for k, v in langs.most_common(6) if v / total >= 0.001]
    bar, x = "", 28.0
    for k, v in top:
        w = 364 * v / total
        bar += f"<rect x='{x:.1f}' y='66' width='{max(w, 2):.1f}' height='8' fill='{COLORS.get(k, t['mut'])}'/>"
        x += w
    items = "".join(
        f"<circle cx='{34 + (i % 2) * 186}' cy='{102 + (i // 2) * 26}' r='5' fill='{COLORS.get(k, t['mut'])}'/>"
        f"<text x='{46 + (i % 2) * 186}' y='{107 + (i // 2) * 26}' fill='{t['txt']}' font-size='13' {FONT}>{escape(k)} "
        f"<tspan fill='{t['mut']}'>{100 * v / total:.1f}%</tspan></text>"
        for i, (k, v) in enumerate(top))
    svg = (f"<svg xmlns='http://www.w3.org/2000/svg' width='420' height='230' viewBox='0 0 420 230'>"
           f"<rect x='.5' y='.5' width='419' height='229' rx='14' fill='{t['bg']}' stroke='{t['line']}'/>"
           f"<rect x='28' y='26' width='26' height='4' rx='2' fill='{t['acc']}'/>"
           f"<text x='28' y='50' fill='{t['txt']}' font-size='16' font-weight='700' {FONT}>Languages in public repos</text>"
           f"<clipPath id='c'><rect x='28' y='66' width='364' height='8' rx='4'/></clipPath><g clip-path='url(#c)'>{bar}</g>"
           f"{items}<text x='392' y='218' fill='{t['mut']}' font-size='10' text-anchor='end' {FONT}>by bytes · {stamp}</text></svg>")
    open(f"assets/langs-{name}.svg", "w").write(svg)
print(stats, langs.most_common(6))
