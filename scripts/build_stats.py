#!/usr/bin/env python3
"""Render activity.svg, a GitHub activity readout for the profile README.

Standard library only. Runs in GitHub Actions with the workflow's GITHUB_TOKEN; the
numbers come from the public GraphQL API (private contributions are included when the
account shows them on its profile).

Usage: GITHUB_TOKEN=... python scripts/build_stats.py <login> <out_dir>
"""
import datetime as dt
import json
import os
import sys
import urllib.request
from collections import Counter

LOGIN, OUT = sys.argv[1], sys.argv[2]
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
if not TOKEN:
    sys.exit("GITHUB_TOKEN is required")
os.makedirs(OUT, exist_ok=True)

BG, PANEL, HAIR, HAIR2 = "#0b0c0e", "#101215", "#262a30", "#1a1d22"
TEXT, MUTED, DIM, AMBER = "#e6e4e1", "#8a8f98", "#5c6168", "#f5a623"
MONO = "'IBM Plex Mono','JetBrains Mono','Cascadia Code',Consolas,'SF Mono',Menlo,monospace"
SANS = "'IBM Plex Sans','Segoe UI',Inter,system-ui,-apple-system,Helvetica,Arial,sans-serif"
LANG_COLORS = [AMBER, "#c8c4bd", "#8a8f98", "#5c6168", "#3a3f47", "#2b2f35"]

QUERY = """
query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    repositories(first: 100, ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name } } }
      }
    }
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
      totalPullRequestContributions
      totalIssueContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


def gql(query, variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json", "User-Agent": "profile-readme"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.load(r)
    if data.get("errors"):
        sys.exit("GraphQL errors: " + json.dumps(data["errors"]))
    return data["data"]


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


user = gql(QUERY, {"login": LOGIN})["user"]
cc = user["contributionsCollection"]
weeks = cc["contributionCalendar"]["weeks"]
days = [(dt.date.fromisoformat(d["date"]), d["contributionCount"]) for w in weeks for d in w["contributionDays"]]
days.sort()

total = cc["contributionCalendar"]["totalContributions"]
commits = cc["totalCommitContributions"] + cc["restrictedContributionsCount"]
active = sum(1 for _, c in days if c > 0)

# streaks (within the calendar year the API returns)
longest = run = 0
for _, c in days:
    run = run + 1 if c > 0 else 0
    longest = max(longest, run)
current = 0
for i in range(len(days) - 1, -1, -1):
    d, c = days[i]
    if i == len(days) - 1 and c == 0:
        continue  # today has nothing yet; a streak can still be alive
    if c > 0:
        current += 1
    else:
        break

repos = user["repositories"]
repo_count = repos["totalCount"]
stars = sum(n["stargazerCount"] for n in repos["nodes"])
lang_bytes = Counter()
for n in repos["nodes"]:
    for e in n["languages"]["edges"]:
        lang_bytes[e["node"]["name"]] += e["size"]
lang_total = sum(lang_bytes.values()) or 1
langs = lang_bytes.most_common(5)
other = lang_total - sum(v for _, v in langs)
if other > 0:
    langs.append(("Other", other))

weekly = [sum(d["contributionCount"] for d in w["contributionDays"]) for w in weeks]
week_starts = [dt.date.fromisoformat(w["contributionDays"][0]["date"]) for w in weeks]
wmax = max(weekly) or 1

now = dt.datetime.now(dt.timezone.utc)
stamp = now.strftime("%Y-%m-%d %H:%M UTC")

# ------------------------------------------------------------------ layout
W, H = 1200, 262
readouts = [
    ("CONTRIBUTIONS · 12 MO", f"{total:,}", AMBER),
    ("COMMITS · 12 MO", f"{commits:,}", TEXT),
    ("CURRENT STREAK", f"{current} d", TEXT),
    ("LONGEST STREAK · 12 MO", f"{longest} d", TEXT),
    ("ACTIVE DAYS · 12 MO", f"{active}", TEXT),
    ("PUBLIC REPOS", f"{repo_count}", TEXT),
]
cells = []
cell_w = (W - 80) / len(readouts)
for i, (label, value, col) in enumerate(readouts):
    x = 40 + i * cell_w
    if i:
        cells.append(f'<line x1="{x:.0f}" y1="66" x2="{x:.0f}" y2="128" stroke="{HAIR2}"/>')
    cells.append(f'<text x="{x + 14:.0f}" y="84" font-family="{MONO}" font-size="10" letter-spacing="2" fill="{DIM}">{label}</text>')
    cells.append(f'<text x="{x + 14:.0f}" y="120" font-family="{SANS}" font-size="32" font-weight="600" fill="{col}">{esc(value)}</text>')

# weekly bars
bx0, bx1, by0, by1 = 40, 760, 170, 226
n = len(weekly)
slot = (bx1 - bx0) / n
bw = max(slot - 2.5, 2)
bars = []
for i, v in enumerate(weekly):
    x = bx0 + i * slot
    if v == 0:
        bars.append(f'<rect x="{x:.1f}" y="{by1 - 1}" width="{bw:.1f}" height="1" fill="{HAIR}"/>')
        continue
    h = max(2, (by1 - by0) * v / wmax)
    op = 0.35 + 0.65 * v / wmax
    bars.append(f'<rect x="{x:.1f}" y="{by1 - h:.1f}" width="{bw:.1f}" height="{h:.1f}" fill="{AMBER}" fill-opacity="{op:.2f}"/>')
# month labels every ~13 weeks
labels = []
for i in range(0, n, 13):
    d = week_starts[i]
    labels.append(f'<text x="{bx0 + i * slot:.0f}" y="246" font-family="{MONO}" font-size="9" letter-spacing="1.5" fill="{DIM}">{d.strftime("%b %y").upper()}</text>')

# languages
lx0, lw = 800, 360
segs, lx = [], lx0
legend = []
for i, (name, size) in enumerate(langs):
    pct = 100 * size / lang_total
    w = lw * size / lang_total
    segs.append(f'<rect x="{lx:.1f}" y="170" width="{max(w, 1):.1f}" height="6" fill="{LANG_COLORS[i % len(LANG_COLORS)]}"/>')
    lx += w
    col = i % 2
    row = i // 2
    x = lx0 + col * 185
    y = 196 + row * 18
    legend.append(f'<rect x="{x}" y="{y - 7}" width="7" height="7" fill="{LANG_COLORS[i % len(LANG_COLORS)]}"/>')
    legend.append(f'<text x="{x + 14}" y="{y}" font-family="{MONO}" font-size="11" fill="{TEXT}">{esc(name)}</text>')
    legend.append(f'<text x="{x + 170}" y="{y}" text-anchor="end" font-family="{MONO}" font-size="11" fill="{MUTED}">{pct:.1f}%</text>')

ticks = (f'M14 30V14H30 M{W - 30} 14H{W - 14}V30 M14 {H - 30}V{H - 14}H30 M{W - 30} {H - 14}H{W - 14}V{H - 30}')

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="GitHub activity: {total} contributions in the last 12 months">
<rect width="{W}" height="{H}" rx="6" fill="{BG}"/>
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="6" fill="none" stroke="{HAIR}"/>
<path d="{ticks}" fill="none" stroke="{AMBER}" stroke-width="1.5" stroke-opacity="0.9"/>
<text x="40" y="40" font-family="{MONO}" font-size="11" letter-spacing="3" fill="{AMBER}">04 / ACTIVITY</text>
<text x="{W - 40}" y="40" text-anchor="end" font-family="{MONO}" font-size="10" letter-spacing="2" fill="{DIM}">UPDATED {stamp} · PUBLIC + PRIVATE CONTRIBUTIONS</text>
<line x1="40" y1="52" x2="{W - 40}" y2="52" stroke="{HAIR}"/>
{"".join(cells)}
<line x1="40" y1="144" x2="{W - 40}" y2="144" stroke="{HAIR2}"/>
<text x="40" y="160" font-family="{MONO}" font-size="10" letter-spacing="2" fill="{DIM}">WEEKLY CONTRIBUTIONS</text>
{"".join(bars)}
<line x1="{bx0}" y1="{by1}" x2="{bx1}" y2="{by1}" stroke="{HAIR}"/>
{"".join(labels)}
<text x="{lx0}" y="160" font-family="{MONO}" font-size="10" letter-spacing="2" fill="{DIM}">TOP LANGUAGES · PUBLIC REPOS</text>
<rect x="{lx0}" y="170" width="{lw}" height="6" fill="{HAIR2}"/>
{"".join(segs)}
{"".join(legend)}
</svg>
'''
path = os.path.join(OUT, "activity.svg")
with open(path, "w", encoding="utf-8") as f:
    f.write(svg)
print(f"wrote {path}: total={total} commits={commits} current={current} longest={longest} active={active} repos={repo_count} stars={stars} langs={langs}")
