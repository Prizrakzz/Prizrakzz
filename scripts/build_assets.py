#!/usr/bin/env python3
"""Generate the animated SVG assets (header, divider, footer) for this profile README.

Standard library only. Palette and type follow leviathanconvexity.com: near-black,
warm off-white, cool gray, one amber accent.

Usage: python scripts/build_assets.py assets
"""
import math
import os
import sys

out_dir = sys.argv[1] if len(sys.argv) > 1 else "assets"
os.makedirs(out_dir, exist_ok=True)

W, H = 1200, 400
BG, PANEL, PANEL2 = "#0b0c0e", "#101215", "#15181c"
HAIR, HAIR2 = "#262a30", "#1a1d22"
TEXT, MUTED, DIM = "#e6e4e1", "#8a8f98", "#5c6168"
AMBER = "#f5a623"
MONO = "'IBM Plex Mono','JetBrains Mono','Cascadia Code',Consolas,'SF Mono',Menlo,monospace"
SANS = "'IBM Plex Sans','Segoe UI',Inter,system-ui,-apple-system,Helvetica,Arial,sans-serif"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def ticks(w, h, inset=14, size=16, color=AMBER):
    i, s = inset, size
    d = (f"M{i} {i + s}V{i}H{i + s}  M{w - i - s} {i}H{w - i}V{i + s}  "
         f"M{i} {h - i - s}V{h - i}H{i + s}  M{w - i - s} {h - i}H{w - i}V{h - i - s}")
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="1.5" stroke-opacity="0.9"/>'


# ---------------------------------------------------------------- typed lines
phrases = [
    "built next to the people who use it, scoping through rollout",
    "quantitative first: statistics, time series, neural networks",
    "production RAG and agents that pass compliance review",
    "data engineering and analytics as one discipline",
    "end-to-end ownership: requirements, terraform, ci/cd, rollout",
]
PER = 5.2                      # seconds each line is on screen
CYCLE = PER * len(phrases)
TYPE_S, HOLD_END_S, OFF_S = 1.9, PER - 0.35, PER - 0.3
k_type, k_hold, k_off = TYPE_S / CYCLE, HOLD_END_S / CYCLE, OFF_S / CYCLE
TX, TY, FS = 60, 232, 16
typed_defs, typed_body = [], []
for i, p in enumerate(phrases):
    begin = i * PER
    w = int((len(p) + 2) * 10.0 + 30)
    typed_defs.append(
        f'<clipPath id="tc{i}"><rect x="{TX}" y="{TY - 22}" width="0" height="32">'
        f'<animate attributeName="width" values="0;{w};{w};0;0" keyTimes="0;{k_type:.4f};{k_hold:.4f};{k_off:.4f};1" '
        f'dur="{CYCLE}s" begin="{begin}s" repeatCount="indefinite"/></rect></clipPath>'
    )
    typed_body.append(
        f'<g opacity="0" clip-path="url(#tc{i})">'
        f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;{k_hold:.4f};{k_off:.4f};1" dur="{CYCLE}s" begin="{begin}s" repeatCount="indefinite"/>'
        f'<text x="{TX}" y="{TY}" font-family="{MONO}" font-size="{FS}" fill="{AMBER}">$ '
        f'<tspan fill="{TEXT}">{esc(p)}</tspan>'
        f'<tspan fill="{AMBER}">▌<animate attributeName="fill-opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1s" repeatCount="indefinite"/></tspan>'
        f'</text></g>'
    )

# ---------------------------------------------------------------- stack chips (monochrome)
chips = ["PYTHON", "PYTORCH", "LANGGRAPH", "CLAUDE", "AWS", "AZURE", "TERRAFORM"]
chip_svg, cx = [], 60
for i, label in enumerate(chips):
    cw = len(label) * 8.2 + 24
    chip_svg.append(
        f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="0.5s" begin="{0.4 + 0.1 * i:.2f}s" fill="freeze"/>'
        f'<rect x="{cx}" y="266" width="{cw:.0f}" height="26" rx="3" fill="{PANEL2}" stroke="{HAIR}"/>'
        f'<text x="{cx + cw / 2:.1f}" y="283" text-anchor="middle" font-family="{MONO}" font-size="11" letter-spacing="1" fill="{MUTED}">{label}</text></g>'
    )
    cx += cw + 8

# ---------------------------------------------------------------- convexity panel
# A convex payoff: flat on the left, accelerating on the right, drawn beneath its chord.
PX, PY, PW, PH = 760, 68, 400, 236
X0, X1 = PX + 28, PX + PW - 28
Y_BASE, Y_TOP = PY + PH - 46, PY + 58
K = 2.7
N = 48
pts = []
for i in range(N):
    t = i / (N - 1)
    y = Y_BASE - (Y_BASE - Y_TOP) * (math.exp(K * t) - 1) / (math.exp(K) - 1)
    pts.append((X0 + (X1 - X0) * t, y))
curve_d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
gap_d = curve_d + f" L{X0} {Y_BASE} Z"                     # region between chord and curve
area_d = curve_d + f" L{X1} {Y_BASE} L{X0} {Y_BASE} Z"
grid_lines = "".join(
    f'<line x1="{X0}" y1="{y:.0f}" x2="{X1}" y2="{y:.0f}" stroke="#ffffff" stroke-opacity="0.05" stroke-dasharray="2 6"/>'
    for y in (Y_TOP, (Y_TOP + Y_BASE) / 2)
)
# a point on the chord above its image on the curve, to show the gap
tm = 0.5
cx_m = X0 + (X1 - X0) * tm
y_chord_m = Y_BASE - (Y_BASE - Y_TOP) * tm
y_curve_m = Y_BASE - (Y_BASE - Y_TOP) * (math.exp(K * tm) - 1) / (math.exp(K) - 1)

# ---------------------------------------------------------------- ticker tape: the stack
groups = [
    ("ML", ["PyTorch", "TensorFlow", "scikit-learn", "XGBoost", "SHAP", "MLflow"]),
    ("LLM", ["LangGraph", "Claude API", "Bedrock", "Azure OpenAI", "Microsoft Agent Framework", "RAG / GraphRAG", "pgvector", "Cohere Rerank"]),
    ("DATA", ["Airflow", "Spark", "dbt", "Snowflake", "Redshift", "PostgreSQL", "DynamoDB", "Playwright"]),
    ("AWS", ["S3", "Glue", "Athena", "Step Functions", "EventBridge", "AWS Batch", "ECS Fargate", "SageMaker", "Lambda", "Cognito"]),
    ("AZURE", ["AI Foundry", "AI Search", "Logic Apps", "SharePoint", "Teams", "Dynamics 365"]),
    ("INFRA", ["Terraform", "Docker", "GitHub Actions", "Linux"]),
    ("CODE", ["Python", "SQL", "C++", "TypeScript", "React", "FastAPI"]),
]
parts, chars = [], 0
for label, items in groups:
    parts.append(f'<tspan fill="{AMBER}" font-weight="600">{label}</tspan><tspan fill="{DIM}">  </tspan>')
    chars += len(label) + 2
    for j, it in enumerate(items):
        parts.append(f'<tspan fill="{TEXT}">{esc(it)}</tspan>')
        chars += len(it)
        if j < len(items) - 1:
            parts.append(f'<tspan fill="{DIM}"> / </tspan>')
            chars += 3
    parts.append(f'<tspan fill="{HAIR}">    │    </tspan>')
    chars += 10
tape_tspans = "".join(parts)
TL = int(chars * 9.6)
tape_dur = round(TL / 62, 1)

header = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="title desc">
<title id="title">Shahem Hiasat</title>
<desc id="desc">Machine Learning Engineer in Amman. Enterprise LLM systems, data platforms and MLOps on AWS and Azure.</desc>
<defs>
  <linearGradient id="area" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{AMBER}" stop-opacity="0.22"/><stop offset="1" stop-color="{AMBER}" stop-opacity="0"/></linearGradient>
  <linearGradient id="hair" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{AMBER}" stop-opacity="0"/><stop offset="0.5" stop-color="{AMBER}" stop-opacity="0.9"/><stop offset="1" stop-color="{AMBER}" stop-opacity="0"/></linearGradient>
  <radialGradient id="vig" cx="0.75" cy="0.35" r="0.9"><stop offset="0" stop-color="#ffffff" stop-opacity="0.035"/><stop offset="1" stop-color="#ffffff" stop-opacity="0"/></radialGradient>
  <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M40 0H0V40" fill="none" stroke="#ffffff" stroke-opacity="0.028"/></pattern>
  <filter id="glow" x="-20%" y="-40%" width="140%" height="180%"><feGaussianBlur stdDeviation="2.5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  <clipPath id="frame"><rect width="{W}" height="{H}" rx="6"/></clipPath>
  {"".join(typed_defs)}
</defs>
<rect width="{W}" height="{H}" rx="6" fill="{BG}"/>
<rect width="{W}" height="{H}" rx="6" fill="url(#grid)"/>
<rect width="{W}" height="{H}" rx="6" fill="url(#vig)"/>
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="6" fill="none" stroke="{HAIR}"/>
{ticks(W, H)}

<!-- top bar -->
<rect x="44" y="20" width="6" height="6" fill="{AMBER}"/>
<text x="58" y="26" font-family="{MONO}" font-size="11" letter-spacing="2" fill="{DIM}">PRIZRAKZZ // PROFILE</text>
<text x="{W - 44}" y="26" text-anchor="end" font-family="{MONO}" font-size="11" letter-spacing="2" fill="{DIM}">AMMAN, JO · UTC+3</text>
<line x1="44" y1="42" x2="{W - 44}" y2="42" stroke="{HAIR}"/>

<!-- identity -->
<text x="60" y="84" font-family="{MONO}" font-size="11" letter-spacing="3" fill="{AMBER}">01 / IDENTITY</text>
<line x1="170" y1="80" x2="720" y2="80" stroke="{HAIR}"/>
<text x="58" y="146" font-family="{SANS}" font-size="58" font-weight="600" letter-spacing="-0.5" fill="{TEXT}">Shahem Hiasat</text>
<text x="60" y="180" font-family="{SANS}" font-size="19" fill="{MUTED}">Machine Learning Engineer — LLM Systems · Data Platforms · MLOps</text>
{"".join(typed_body)}
{"".join(chip_svg)}

<!-- convexity panel -->
<rect x="{PX}" y="{PY}" width="{PW}" height="{PH}" rx="4" fill="{PANEL}" stroke="{HAIR}"/>
<text x="{PX + 16}" y="{PY + 22}" font-family="{MONO}" font-size="11" letter-spacing="3" fill="{AMBER}">02 / CONVEXITY</text>
<text x="{PX + PW - 16}" y="{PY + 22}" text-anchor="end" font-family="{MONO}" font-size="10" letter-spacing="2" fill="{DIM}">f'' &gt; 0</text>
<line x1="{PX + 12}" y1="{PY + 34}" x2="{PX + PW - 12}" y2="{PY + 34}" stroke="{HAIR2}"/>
{grid_lines}
<line x1="{X0}" y1="{Y_BASE}" x2="{X1}" y2="{Y_BASE}" stroke="{HAIR}"/>
<line x1="{X0}" y1="{Y_TOP - 10}" x2="{X0}" y2="{Y_BASE}" stroke="{HAIR}"/>
<line x1="{X0}" y1="{Y_BASE}" x2="{X1}" y2="{Y_TOP}" stroke="{MUTED}" stroke-opacity="0.55" stroke-dasharray="3 5"/>
<text x="{X0 + 118}" y="{Y_BASE - 112}" font-family="{MONO}" font-size="9" letter-spacing="2" fill="{DIM}">LINEAR</text>
<path d="{gap_d}" fill="{AMBER}" fill-opacity="0.07" opacity="0"><animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;0.3;0.42;0.9;1" dur="12s" repeatCount="indefinite"/></path>
<path d="{area_d}" fill="url(#area)" opacity="0"><animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;0.3;0.42;0.9;1" dur="12s" repeatCount="indefinite"/></path>
<line x1="{cx_m:.1f}" y1="{y_chord_m:.1f}" x2="{cx_m:.1f}" y2="{y_curve_m:.1f}" stroke="{AMBER}" stroke-opacity="0.5" stroke-dasharray="2 3" opacity="0"><animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;0.34;0.42;0.9;1" dur="12s" repeatCount="indefinite"/></line>
<path d="{curve_d}" fill="none" stroke="{AMBER}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" pathLength="100" stroke-dasharray="100" stroke-dashoffset="100" filter="url(#glow)">
  <animate attributeName="stroke-dashoffset" values="100;0;0;100" keyTimes="0;0.3;0.92;1" dur="12s" repeatCount="indefinite"/>
</path>
<circle cx="{X1}" cy="{Y_TOP}" r="3.5" fill="{AMBER}" opacity="0"><animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;0.29;0.33;0.9;1" dur="12s" repeatCount="indefinite"/></circle>
<circle cx="{X1}" cy="{Y_TOP}" r="3.5" fill="none" stroke="{AMBER}" stroke-width="1"><animate attributeName="r" values="3.5;14" dur="2s" repeatCount="indefinite"/><animate attributeName="opacity" values="0.6;0" dur="2s" repeatCount="indefinite"/></circle>
<text x="{PX + 16}" y="{PY + PH - 16}" font-family="{MONO}" font-size="10" letter-spacing="1" fill="{DIM}">f(λx + (1−λ)y) ≤ λf(x) + (1−λ)f(y)</text>

<!-- ticker tape -->
<g clip-path="url(#frame)">
  <rect x="0" y="352" width="{W}" height="48" fill="#08090b"/>
  <rect x="0" y="351" width="{W}" height="1" fill="url(#hair)"/>
  <g font-family="{MONO}" font-size="13" letter-spacing="1">
    <animateTransform attributeName="transform" type="translate" from="0 0" to="-{TL} 0" dur="{tape_dur}s" repeatCount="indefinite"/>
    <text x="0" y="381" textLength="{TL}" lengthAdjust="spacing">{tape_tspans}</text>
    <text x="{TL}" y="381" textLength="{TL}" lengthAdjust="spacing">{tape_tspans}</text>
  </g>
</g>
</svg>
'''

footer = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 104" width="1200" height="104" role="img" aria-label="Open to ML systems, LLM agents and data platform work">
<rect width="1200" height="104" rx="6" fill="{BG}"/>
<rect x="0.5" y="0.5" width="1199" height="103" rx="6" fill="none" stroke="{HAIR}"/>
{ticks(1200, 104, inset=12, size=12)}
<text x="60" y="38" font-family="{MONO}" font-size="11" letter-spacing="3" fill="{AMBER}">05 / CONTACT</text>
<line x1="168" y1="34" x2="1140" y2="34" stroke="{HAIR}"/>
<text x="60" y="72" font-family="{MONO}" font-size="16" fill="{AMBER}">$ <tspan fill="{TEXT}">open to ML systems, LLM agents and data platform work</tspan><tspan fill="{AMBER}">▌<animate attributeName="fill-opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1s" repeatCount="indefinite"/></tspan></text>
<text x="1140" y="72" text-anchor="end" font-family="{MONO}" font-size="11" letter-spacing="2" fill="{DIM}">GITHUB.COM/PRIZRAKZZ</text>
</svg>
'''

divider = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 12" width="1200" height="12" role="presentation">
<rect x="0" y="6" width="1200" height="1" fill="{HAIR}"/>
<rect x="0" y="5" width="56" height="3" fill="{AMBER}"/>
</svg>
'''

for name, body in (("header.svg", header), ("footer.svg", footer), ("divider.svg", divider)):
    with open(os.path.join(out_dir, name), "w", encoding="utf-8") as f:
        f.write(body)
    print(f"wrote {name}: {len(body.encode('utf-8'))} bytes")
