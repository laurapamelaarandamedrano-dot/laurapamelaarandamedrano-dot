#!/usr/bin/env python3
"""Build the "language spectrum" card from the languages of public repositories.

Method (shown on the card, so the numbers are honest about what they mean):
  * public, non-fork repositories owned by the account (the profile repo excluded);
  * bytes per language per repo, capped at CAP so one generated file
    (e.g. a large exported HTML report) cannot dominate the picture;
  * score = sqrt(capped bytes x number of repos using the language);
  * share = score / sum of scores.

    python scripts/update_languages.py          # uses GITHUB_TOKEN if set

Runs weekly in .github/workflows/languages.yml. Output is deterministic, so the
workflow only commits when the underlying data actually changes.
"""

from __future__ import annotations

import html
import json
import math
import os
import random
import sys
import urllib.request
from pathlib import Path

USER = "laurapamelaarandamedrano-dot"
EXCLUDE = {USER}
CAP = 100_000
TOP = 8

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

FONTS = (
    ".m{font-family:'JetBrains Mono','SF Mono','Cascadia Mono',Consolas,'Liberation Mono',Menlo,monospace}"
    ".r{font-family:'Iowan Old Style','Palatino Linotype',Palatino,Georgia,'Times New Roman',serif}"
)

THEMES = {
    "dark": dict(bg="#070b1c", panel="#0a0e20", edge="#2a305a", ink="#ecebf8", dim="#9a9dc2", faint="#4b507c",
                 cyan="#86dcea", stars=["#ffffff", "#e4ecff", "#ffe7c7", "#efe6ff"],
                 spectrum=["#b7a6f2", "#86dcea", "#e6a8c6", "#ffd6a3", "#a9c2a2", "#cddcff", "#d9b4f0", "#f0c9a8", "#8f95c2"]),
    "light": dict(bg="#f6f2ea", panel="#fcfbf7", edge="#d2cbe0", ink="#1d2148", dim="#5c5f88", faint="#b3aecb",
                  cyan="#1d8296", stars=["#2b2f5c", "#46407e", "#7b5c48"],
                  spectrum=["#6a55c8", "#1d8296", "#b25683", "#ad6d22", "#4f7d4a", "#3d5f9e", "#8a4fb0", "#a8643a", "#6b6f96"]),
}


def api(path: str):
    req = urllib.request.Request(f"https://api.github.com{path}",
                                 headers={"Accept": "application/vnd.github+json", "User-Agent": "lpam-profile"})
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def collect() -> tuple[list[tuple[str, float]], int]:
    repos = [r for r in api(f"/users/{USER}/repos?per_page=100&type=owner")
             if not r["fork"] and r["name"] not in EXCLUDE]
    size: dict[str, int] = {}
    count: dict[str, int] = {}
    for r in repos:
        for lang, b in api(f"/repos/{USER}/{r['name']}/languages").items():
            size[lang] = size.get(lang, 0) + min(b, CAP)
            count[lang] = count.get(lang, 0) + 1
    score = {k: math.sqrt(size[k] * count[k]) for k in size}
    total = sum(score.values()) or 1
    ranked = sorted(((k, v / total) for k, v in score.items()), key=lambda kv: (-kv[1], kv[0]))
    if len(ranked) > TOP:
        rest = sum(v for _, v in ranked[TOP - 1:])
        ranked = ranked[:TOP - 1] + [("Other", rest)]
    return ranked, len(repos)


def n(x: float) -> str:
    s = f"{x:.1f}"
    return s[:-2] if s.endswith(".0") else s


def txt(x, y, s, size, fill, anchor="start", ls=0, cls="m", extra=""):
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    return (f'<text x="{n(x)}" y="{n(y)}" class="{cls}" font-size="{size}" fill="{fill}"{a} '
            f'letter-spacing="{ls}" {extra}>{html.escape(s)}</text>')


def card(langs, repo_count, t) -> str:
    W = 1000
    rows = math.ceil(len(langs) / 2)
    H = 190 + rows * 42 + 50
    x0, bw = 48, 904
    rng = random.Random("|".join(k for k, _ in langs))
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">',
        '<title id="t">Language spectrum</title>',
        f'<desc id="d">Most-used languages across public repositories: '
        + html.escape(", ".join(f"{k} {v * 100:.1f}%" for k, v in langs)) + "</desc>",
        f"<style>{FONTS}</style>",
        f'<defs><clipPath id="bar"><rect x="{x0}" y="92" width="{bw}" height="40" rx="6"/></clipPath>'
        f'<linearGradient id="sw" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
        f'<stop offset="1" stop-color="#fff" stop-opacity=".55"/></linearGradient>'
        f'<filter id="glow" x="-400%" y="-400%" width="900%" height="900%"><feGaussianBlur stdDeviation="2.4" result="g"/>'
        f'<feMerge><feMergeNode in="g"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>',
        f'<rect width="{W}" height="{H}" fill="{t["bg"]}"/>',
    ]
    for _ in range(90):
        out.append(f'<circle cx="{n(rng.uniform(0, W))}" cy="{n(rng.uniform(0, H))}" r="{rng.uniform(.3, 1.1):.2f}" '
                   f'fill="{rng.choice(t["stars"])}" opacity="{rng.uniform(.1, .5):.2f}"/>')
    out.append(f'<rect x="24" y="22" width="952" height="{H - 44}" rx="12" fill="{t["panel"]}" fill-opacity=".9" stroke="{t["edge"]}"/>')
    out.append(txt(48, 56, "SPECTRAL ANALYSIS // LANGUAGES", 14, t["ink"], ls=3.2, extra='font-weight="600"'))
    out.append(txt(952, 56, f"EMISSION LINES · {repo_count} PUBLIC REPOS", 11.5, t["dim"], anchor="end", ls=2.4))

    # The spectrum: one segment per language, textured with emission lines.
    seg, x = [], x0
    for i, (lang, share) in enumerate(langs):
        w = share * bw
        col = t["spectrum"][i % len(t["spectrum"])]
        seg.append(f'<rect x="{n(x)}" y="92" width="{n(w + .6)}" height="40" fill="{col}" opacity=".9"/>')
        for _ in range(max(2, int(w / 9))):
            lx = x + rng.uniform(1, max(1.5, w - 1))
            seg.append(f'<rect x="{n(lx)}" y="92" width="{rng.uniform(.6, 2.2):.1f}" height="40" fill="#fff" opacity="{rng.uniform(.08, .35):.2f}"/>')
        x += w
    seg.append(f'<g><rect x="-70" y="92" width="70" height="40" fill="url(#sw)" opacity=".5"/>'
               f'<animateTransform attributeName="transform" type="translate" values="{x0} 0;{x0 + bw + 70} 0" dur="8s" repeatCount="indefinite"/></g>')
    out.append(f'<g clip-path="url(#bar)">{"".join(seg)}</g>')
    out.append(f'<rect x="{x0}" y="92" width="{bw}" height="40" rx="6" fill="none" stroke="{t["edge"]}"/>')
    ticks = "".join(f"M{n(x0 + bw * k / 20)} 138v{6 if k % 5 == 0 else 3}" for k in range(21))
    out.append(f'<path d="{ticks}" stroke="{t["dim"]}" stroke-width=".8" opacity=".7"/>')
    for k, lab in ((0, "0"), (10, "50"), (20, "100 %")):
        out.append(txt(x0 + bw * k / 20, 158, lab, 10, t["dim"], anchor={0: "start", 10: "middle", 20: "end"}[k], ls=1))

    # Legend: two columns, each with a growing bar.
    top = langs[0][1]
    for i, (lang, share) in enumerate(langs):
        col_i, row = i % 2, i // 2
        cx = 48 + col_i * 470
        y = 196 + row * 42
        c = t["spectrum"][i % len(t["spectrum"])]
        out.append(f'<circle cx="{cx + 6}" cy="{y - 5}" r="4.5" fill="{c}" filter="url(#glow)"/>')
        out.append(txt(cx + 22, y, lang, 15, t["ink"], ls=1))
        out.append(txt(cx + 420, y, f"{share * 100:.1f}%", 14, t["dim"], anchor="end", ls=1))
        full = 398 * share / top
        out.append(f'<rect x="{cx + 22}" y="{y + 9}" width="398" height="3" rx="1.5" fill="{t["faint"]}" opacity=".3"/>')
        out.append(f'<rect x="{cx + 22}" y="{y + 9}" width="{n(full)}" height="3" rx="1.5" fill="{c}">'
                   f'<animate attributeName="width" values="0;{n(full)}" dur="2.4s" begin="{i * .12:.2f}s" fill="freeze"/></rect>')
    out.append(f'<path d="M24 {H - 60}H976" stroke="{t["edge"]}"/>')
    out.append(txt(48, H - 36, f"share = √(bytes × repos) · bytes capped at {CAP // 1000} kB per repo · regenerated weekly",
                   11, t["dim"], ls=.6, cls="r", extra='font-style="italic"'))
    out.append("</svg>")
    return "".join(out)


def main() -> int:
    try:
        langs, repo_count = collect()
    except Exception as exc:  # keep the previous card if the API is unavailable
        print(f"GitHub API unavailable, keeping existing card: {exc}", file=sys.stderr)
        return 0
    for k, v in langs:
        print(f"{k:12s} {v * 100:5.1f}%")
    for mode, theme in THEMES.items():
        (ASSETS / f"languages-{mode}.svg").write_text(card(langs, repo_count, theme), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
