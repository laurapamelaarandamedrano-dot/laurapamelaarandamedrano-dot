#!/usr/bin/env python3
"""Generate the animated SVG artwork for the LPAM profile README.

Every image is drawn procedurally with a fixed random seed, so the output is
deterministic: re-running the script only changes files when the code changes.
Animation uses SVG-native SMIL (<animate>, <animateTransform>, <animateMotion>),
which GitHub renders inside <img>. Every animated element has a meaningful
static state, so the artwork still reads correctly if animation is stripped.

    python scripts/build_assets.py
"""

from __future__ import annotations

import html
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

FONTS = (
    ".m{font-family:'JetBrains Mono','SF Mono','Cascadia Mono',Consolas,'Liberation Mono',Menlo,monospace}"
    ".s{font-family:'Inter','Segoe UI','Helvetica Neue',Arial,sans-serif}"
    ".r{font-family:'Iowan Old Style','Palatino Linotype',Palatino,Georgia,'Times New Roman',serif}"
)

# --------------------------------------------------------------------------- #
# Palettes
# --------------------------------------------------------------------------- #

DARK_SKY = dict(
    lav="#b7a6f2", pink="#e6a8c6", cyan="#86dcea", warm="#ffd6a3",
    stars=["#ffffff", "#fff6ea", "#ffe7c7", "#ffd3a1", "#e4ecff", "#cddcff", "#efe6ff"],
    dust="#03040b", dust_op=0.62,
)
DAWN_SKY = dict(
    lav="#e2d6ff", pink="#ffd0e2", cyan="#c9f1f8", warm="#fff0d6",
    stars=["#ffffff", "#fff8ef", "#fff0dc", "#eef3ff", "#f6f0ff"],
    dust="#262c66", dust_op=0.28,
)

THEMES = {
    "dark": dict(
        mode="dark", sky=DARK_SKY,
        ink="#ecebf8", dim="#9a9dc2", faint="#4b507c", hair="#262b4d",
        lav="#b7a6f2", pink="#e6a8c6", cyan="#86dcea", warm="#ffd6a3", flow="#9fe8f2",
        bg=("#03040a", "#070b1c", "#0c1028"), panel="#0a0e20", panel_edge="#2a305a",
        plate=("#05071a", "#0b1030"), plate_star=DARK_SKY["stars"],
        ink_stars=DARK_SKY["stars"],
        ocean=("#4f8bbb", "#173f6a", "#06162d"), land="#a9c2a2", night="#01030c",
    ),
    "light": dict(
        mode="light", sky=DAWN_SKY,
        ink="#1d2148", dim="#5c5f88", faint="#b3aecb", hair="#e0dbe9",
        lav="#6a55c8", pink="#b25683", cyan="#1d8296", warm="#ad6d22", flow="#1f7f96",
        bg=("#f6f2ea", "#f3eee6", "#efe9e0"), panel="#fcfbf7", panel_edge="#d2cbe0",
        plate=("#1c2352", "#2c2f66"), plate_star=DAWN_SKY["stars"],
        ink_stars=["#2b2f5c", "#46407e", "#5d4a8a", "#7b5c48", "#2f4f7a"],
        ocean=("#79b0dc", "#2f6699", "#163862"), land="#a7c3a0", night="#0b1230",
    ),
}


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #

def n(x: float) -> str:
    """Compact number formatting for coordinates."""
    s = f"{x:.1f}"
    if s.endswith(".0"):
        s = s[:-2]
    return "0" if s == "-0" else s


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def open_svg(w: int, h: int, title: str, desc: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
        f'role="img" aria-labelledby="t d"><title id="t">{esc(title)}</title><desc id="d">{esc(desc)}</desc>'
        f"<style>{FONTS}</style>"
    )


def text(x, y, s, size, fill, cls="m", anchor="start", ls=0.0, weight=None,
         op=None, halo=None, italic=False, extra="", inner=""):
    a = [f'x="{n(x)}"', f'y="{n(y)}"', f'class="{cls}"', f'font-size="{size}"', f'fill="{fill}"']
    if anchor != "start":
        a.append(f'text-anchor="{anchor}"')
    if ls:
        a.append(f'letter-spacing="{ls}"')
    if weight:
        a.append(f'font-weight="{weight}"')
    if op is not None:
        a.append(f'opacity="{op}"')
    if italic:
        a.append('font-style="italic"')
    if halo:
        a.append(f'stroke="{halo}" stroke-width="4" stroke-linejoin="round" paint-order="stroke"')
    if extra:
        a.append(extra)
    return f'<text {" ".join(a)}>{esc(s)}{inner}</text>'


def blur_filters(*sds: float) -> str:
    out = []
    for sd in sds:
        pad = "-60%" if sd >= 8 else "-400%"
        size = "220%" if sd >= 8 else "900%"
        out.append(
            f'<filter id="b{str(sd).replace(".", "_")}" x="{pad}" y="{pad}" width="{size}" height="{size}">'
            f'<feGaussianBlur stdDeviation="{sd}"/></filter>'
        )
    return "".join(out)


def B(sd) -> str:
    return f'filter="url(#b{str(sd).replace(".", "_")})"'


GLOW = (
    '<filter id="glow" x="-400%" y="-400%" width="900%" height="900%">'
    '<feGaussianBlur stdDeviation="2.4" result="g"/>'
    '<feMerge><feMergeNode in="g"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
)


def smooth(pts, closed=True) -> str:
    """Catmull-Rom spline through points, as cubic Béziers."""
    m = len(pts)
    d = f"M{n(pts[0][0])} {n(pts[0][1])}"
    for i in range(m if closed else m - 1):
        p0 = pts[(i - 1) % m] if closed or i > 0 else pts[0]
        p1 = pts[i]
        p2 = pts[(i + 1) % m]
        p3 = pts[(i + 2) % m] if closed or i + 2 < m else pts[-1]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f"C{n(c1[0])} {n(c1[1])} {n(c2[0])} {n(c2[1])} {n(p2[0])} {n(p2[1])}"
    return d + ("Z" if closed else "")


def circle_path(cx, cy, r) -> str:
    return f"M{n(cx + r)} {n(cy)}A{n(r)} {n(r)} 0 1 1 {n(cx - r)} {n(cy)}A{n(r)} {n(r)} 0 1 1 {n(cx + r)} {n(cy)}"


def starfield(rng, count, colors, box=None, dist=None, r=(0.25, 1.4), o=(0.15, 0.9),
              twinkle=0.06, skew=3.2) -> str:
    """Stars of varied size, opacity and colour temperature; a share twinkle."""
    groups: dict[str, list[str]] = {}
    for _ in range(count):
        if dist:
            x, y = dist(rng)
        else:
            x0, y0, w, h = box
            x, y = x0 + rng.random() * w, y0 + rng.random() * h
        rad = r[0] + (r[1] - r[0]) * rng.random() ** skew
        op = o[0] + (o[1] - o[0]) * rng.random()
        c = rng.choice(colors)
        head = f'<circle cx="{n(x)}" cy="{n(y)}" r="{rad:.2f}" opacity="{op:.2f}"'
        if rng.random() < twinkle:
            dur = rng.uniform(2.8, 9.5)
            lo = op * rng.uniform(0.12, 0.4)
            el = (f'{head}><animate attributeName="opacity" values="{op:.2f};{lo:.2f};{op:.2f}" '
                  f'dur="{dur:.1f}s" begin="-{rng.uniform(0, dur):.1f}s" repeatCount="indefinite"/></circle>')
        else:
            el = head + "/>"
        groups.setdefault(c, []).append(el)
    return "".join(f'<g fill="{c}">{"".join(v)}</g>' for c, v in groups.items())


def bright_star(x, y, s, color, flare=None) -> str:
    """A star with diffraction spikes; optionally brightens now and then."""
    k = s * 5.5
    w = s * 0.32
    inner = (
        f'<circle r="{n(s * 3.2)}" fill="{color}" opacity=".22" {B(3)}/>'
        f'<path d="M0 {n(-k)}L{n(w)} 0 0 {n(k)} {n(-w)} 0ZM{n(-k)} 0 0 {n(w)} {n(k)} 0 0 {n(-w)}Z" fill="{color}" opacity=".6"/>'
        f'<circle r="{n(s)}" fill="{color}"/>'
    )
    if flare:
        dur, beg = flare
        kt = 'keyTimes="0;.80;.85;.93;1"'
        inner = (
            f'<g opacity=".6">{inner}'
            f'<animateTransform attributeName="transform" type="scale" values="1;1;1.9;1;1" {kt} dur="{dur}s" begin="{beg}s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values=".6;.6;1;.6;.6" {kt} dur="{dur}s" begin="{beg}s" repeatCount="indefinite"/></g>'
        )
    return f'<g transform="translate({n(x)} {n(y)})">{inner}</g>'


def star4(x, y, r) -> str:
    """Concave four-point star path (constellation marker)."""
    return (f"M{n(x)} {n(y - r)}Q{n(x)} {n(y)} {n(x + r)} {n(y)}Q{n(x)} {n(y)} {n(x)} {n(y + r)}"
            f"Q{n(x)} {n(y)} {n(x - r)} {n(y)}Q{n(x)} {n(y)} {n(x)} {n(y - r)}Z")


def drifting_particles(rng, count, box, colors) -> str:
    x0, y0, w, h = box
    out = []
    for _ in range(count):
        x, y = x0 + rng.random() * w, y0 + rng.random() * h
        dx, dy = rng.uniform(40, 140) * rng.choice([1, -1]), rng.uniform(-30, 30)
        dur = rng.uniform(38, 95)
        beg = -rng.uniform(0, dur)
        op = rng.uniform(0.35, 0.8)
        out.append(
            f'<circle cx="{n(x)}" cy="{n(y)}" r="{rng.uniform(0.6, 1.3):.2f}" fill="{rng.choice(colors)}" opacity="0">'
            f'<animateTransform attributeName="transform" type="translate" values="0 0;{n(dx)} {n(dy)}" dur="{dur:.0f}s" begin="{beg:.0f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0;{op:.2f};{op:.2f};0" keyTimes="0;.2;.8;1" dur="{dur:.0f}s" begin="{beg:.0f}s" repeatCount="indefinite"/></circle>'
        )
    return "".join(out)


def meteors() -> str:
    """Rare, slow meteors: each is visible for about a second of a long cycle."""
    out = ['<linearGradient id="met" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
           '<stop offset="1" stop-color="#fff"/></linearGradient>']
    for path, dur, beg in (("M930 30L1130 118", 23, -9), ("M420 150L560 226", 31, -27)):
        kt = 'keyTimes="0;.9;.95;1"'
        out.append(
            f'<g opacity="0"><path d="M-80 0H0" stroke="url(#met)" stroke-width="1.3" stroke-linecap="round"/>'
            f'<circle r="1.3" fill="#fff"/>'
            f'<animateMotion path="{path}" keyPoints="0;0;1;1" {kt} calcMode="linear" rotate="auto" dur="{dur}s" begin="{beg}s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0;0;.9;0;0" keyTimes="0;.9;.92;.95;1" dur="{dur}s" begin="{beg}s" repeatCount="indefinite"/></g>'
        )
    return "".join(out)


def ticks_frame(W, H, color, op=0.5) -> str:
    """Atlas-style graduated border."""
    d = []
    for x in range(20, W, 20):
        L = 9 if x % 100 == 0 else 4
        d.append(f"M{x} 12v{L}M{x} {H - 12}v-{L}")
    for y in range(20, H, 20):
        L = 9 if y % 100 == 0 else 4
        d.append(f"M12 {y}h{L}M{W - 12} {y}h-{L}")
    c = 26
    corners = (f"M12 {12 + c}V12H{12 + c}M{W - 12 - c} 12H{W - 12}V{12 + c}"
               f"M{W - 12} {H - 12 - c}V{H - 12}H{W - 12 - c}M{12 + c} {H - 12}H12V{H - 12 - c}")
    return (f'<path d="{"".join(d)}" stroke="{color}" stroke-width=".7" opacity="{op}" fill="none"/>'
            f'<path d="{corners}" stroke="{color}" stroke-width="1.2" opacity="{min(1, op + .25)}" fill="none"/>')


# --------------------------------------------------------------------------- #
# The Milky Way
# --------------------------------------------------------------------------- #

def band_gradient(sky, half, gid) -> str:
    return (
        f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{-half}" y1="0" x2="{half}" y2="0">'
        f'<stop offset="0" stop-color="{sky["lav"]}" stop-opacity=".25"/>'
        f'<stop offset=".3" stop-color="{sky["pink"]}" stop-opacity=".8"/>'
        f'<stop offset=".52" stop-color="{sky["warm"]}"/>'
        f'<stop offset=".72" stop-color="{sky["lav"]}" stop-opacity=".8"/>'
        f'<stop offset="1" stop-color="{sky["cyan"]}" stop-opacity=".25"/></linearGradient>'
    )


def milky_way(rng, sky, cx, cy, ang, length, gid, n_stars=1100, n_faint=900,
              intensity=1.0, clusters=6, core=40) -> str:
    """Layered galactic band: haze, glow, bulge, drifting dust, rifts, stars."""
    I = intensity
    h = length / 2
    p = [
        f'<ellipse rx="{n(h * 1.15)}" ry="150" fill="{sky["lav"]}" opacity="{.10 * I:.2f}" {B(40)}/>',
        f'<ellipse rx="{n(h)}" ry="64" fill="url(#{gid})" opacity="{.30 * I:.2f}" {B(22)}/>',
        f'<ellipse cx="{core}" rx="240" ry="72" fill="{sky["warm"]}" opacity="{.26 * I:.2f}" {B(26)}/>',
        f'<ellipse cx="{core}" rx="100" ry="27" fill="#fff4e4" opacity="{.40 * I:.2f}" {B(12)}/>',
    ]
    # Luminous dust: two cloud layers drifting in opposite directions.
    for vals, dur in (("0 0;40 0;0 0", 150), ("0 0;-32 5;0 0", 115)):
        cl = []
        for _ in range(26):
            u = max(-h, min(h, rng.gauss(core, h * 0.45)))
            v = rng.gauss(0, 34)
            rx = rng.uniform(24, 95)
            c = rng.choice([sky["lav"], sky["pink"], sky["cyan"], sky["warm"], sky["lav"]])
            cl.append(
                f'<ellipse cx="{n(u)}" cy="{n(v)}" rx="{n(rx)}" ry="{n(rx * rng.uniform(.25, .55))}" fill="{c}" '
                f'opacity="{rng.uniform(.06, .16) * I:.2f}" transform="rotate({n(rng.uniform(-8, 8))} {n(u)} {n(v)})"/>'
            )
        p.append(f'<g {B(14)}>{"".join(cl)}<animateTransform attributeName="transform" type="translate" '
                 f'values="{vals}" dur="{dur}s" repeatCount="indefinite"/></g>')
    # Dark rifts (like the Great Rift) - layered translucent lanes.
    for off, th, ph in ((-4, 9, 0.0), (15, 5, 2.1), (-22, 3.5, 4.0)):
        top, bot = [], []
        u = -h * 0.8
        while u <= h * 0.8:
            mid = off + 7 * math.sin(u / 90 + ph) + 3 * math.sin(u / 31 + ph * 2)
            taper = max(0.0, 1 - (abs(u - core) / (h * 0.8)) ** 2)
            t_ = th * taper * (0.6 + 0.4 * math.sin(u / 47 + ph)) + 0.5
            top.append((u, mid - t_))
            bot.append((u, mid + t_))
            u += 24
        p.append(f'<path d="{smooth(top + bot[::-1])}" fill="{sky["dust"]}" opacity="{sky["dust_op"]:.2f}" {B(5)}/>')

    def band_pt(r_):
        u = r_.gauss(core, h * 0.42)
        while abs(u) > h * 1.05:
            u = r_.gauss(core, h * 0.42)
        spread = 24 + 30 * math.exp(-((u - core) / 190) ** 2)
        return u, r_.gauss(0, spread)

    # Unresolved star haze, then resolved stars, then tight clusters.
    p.append(starfield(rng, n_faint, sky["stars"], dist=band_pt, r=(0.18, 0.45), o=(0.12, 0.42), twinkle=0, skew=1))
    p.append(starfield(rng, n_stars, sky["stars"], dist=band_pt, r=(0.25, 1.15), o=(0.25, 0.9), twinkle=0.035))
    for _ in range(clusters):
        cu, cv = rng.uniform(-h * .8, h * .8), rng.gauss(0, 26)
        p.append(starfield(rng, 22, sky["stars"], dist=lambda r_: (r_.gauss(cu, 7), r_.gauss(cv, 5)),
                           r=(0.25, 0.9), o=(0.35, 0.95), twinkle=0.1))
    return f'<g transform="translate({n(cx)} {n(cy)}) rotate({ang})">{"".join(p)}</g>'


# --------------------------------------------------------------------------- #
# Earth
# --------------------------------------------------------------------------- #

CONTINENTS = [
    [(0.06, -0.62), (0.12, -0.78), (0.22, -0.82), (0.30, -0.70), (0.27, -0.55), (0.22, -0.45),
     (0.21, -0.32), (0.17, -0.22), (0.13, -0.30), (0.09, -0.45)],
    [(0.20, -0.14), (0.26, -0.10), (0.31, 0.02), (0.29, 0.20), (0.25, 0.40), (0.22, 0.58),
     (0.20, 0.42), (0.19, 0.18), (0.17, 0.0)],
    [(0.33, -0.88), (0.38, -0.90), (0.40, -0.80), (0.35, -0.76)],
    [(0.46, -0.62), (0.50, -0.74), (0.57, -0.76), (0.60, -0.62), (0.55, -0.52), (0.49, -0.50)],
    [(0.46, -0.40), (0.53, -0.44), (0.60, -0.38), (0.64, -0.18), (0.61, 0.08), (0.57, 0.38),
     (0.53, 0.42), (0.50, 0.18), (0.47, -0.05), (0.44, -0.22)],
    [(0.60, -0.70), (0.70, -0.84), (0.84, -0.80), (0.93, -0.62), (0.90, -0.44), (0.84, -0.30),
     (0.78, -0.14), (0.73, -0.26), (0.66, -0.36), (0.61, -0.50)],
    [(0.82, 0.22), (0.88, 0.18), (0.93, 0.26), (0.92, 0.40), (0.85, 0.42), (0.81, 0.32)],
]


def earth(rng, t, cx, cy, R, uid) -> tuple[str, str]:
    """Small stylised Earth: tilted, slowly rotating land, clouds, terminator, atmosphere."""
    Wm = 2 * math.pi * R
    oc = t["ocean"]
    defs = (
        f'<radialGradient id="oc{uid}" cx=".38" cy=".34" r=".75"><stop offset="0" stop-color="{oc[0]}"/>'
        f'<stop offset=".55" stop-color="{oc[1]}"/><stop offset="1" stop-color="{oc[2]}"/></radialGradient>'
        f'<radialGradient id="sh{uid}" cx=".32" cy=".32" r=".95"><stop offset=".45" stop-color="{t["night"]}" stop-opacity="0"/>'
        f'<stop offset="1" stop-color="{t["night"]}" stop-opacity=".88"/></radialGradient>'
        f'<clipPath id="ec{uid}"><circle r="{R}"/></clipPath>'
    )

    def land(x0):
        return "".join(f'<path d="{smooth([(x0 + px * Wm, py * R) for px, py in poly])}"/>' for poly in CONTINENTS)

    clouds = []
    for _ in range(11):
        x, y = rng.uniform(0, Wm), rng.uniform(-0.8, 0.8) * R
        rx, ry = rng.uniform(5, 16), rng.uniform(1.2, 2.6)
        for k in (0, Wm):
            clouds.append(f'<ellipse cx="{n(x - R + k)}" cy="{n(y)}" rx="{n(rx)}" ry="{n(ry)}"/>')
    lat = "".join(
        f'<ellipse cy="{n(R * math.sin(math.radians(a)) * .98)}" rx="{n(R * math.cos(math.radians(a)))}" ry="{n(R * .16 * math.cos(math.radians(a)))}"/>'
        for a in (-60, -30, 0, 30, 60)
    )
    body = (
        f'<g transform="translate({n(cx)} {n(cy)})">'
        f'<circle r="{R + 16}" fill="{t["cyan"]}" opacity=".16" {B(8)}/>'
        f'<circle r="{R}" fill="url(#oc{uid})"/>'
        f'<g clip-path="url(#ec{uid})"><g transform="rotate(-20)">'
        f'<g fill="{t["land"]}" opacity=".72">{land(-R)}{land(-R + Wm)}'
        f'<animateTransform attributeName="transform" type="translate" from="0 0" to="{n(-Wm)} 0" dur="160s" repeatCount="indefinite"/></g>'
        f'<g fill="none" stroke="#ffffff" stroke-opacity=".13" stroke-width=".6">{lat}</g>'
        f'<g fill="#ffffff" opacity=".28">{"".join(clouds)}'
        f'<animateTransform attributeName="transform" type="translate" from="0 0" to="{n(-Wm)} 0" dur="95s" repeatCount="indefinite"/></g>'
        f'</g><circle r="{R}" fill="url(#sh{uid})"/></g>'
        f'<circle r="{R}" fill="none" stroke="{t["cyan"]}" stroke-opacity=".6" stroke-width="1.1"/>'
        f'<circle r="{R + 2.6}" fill="none" stroke="{t["cyan"]}" stroke-opacity=".18" stroke-width="3"/>'
        f'</g>'
    )
    return defs, body


def satellite(color, panel) -> str:
    return (f'<rect x="-2.2" y="-1.6" width="4.4" height="3.2" rx=".6" fill="{color}"/>'
            f'<rect x="-9" y="-1" width="5.6" height="2" fill="{panel}" opacity=".9"/>'
            f'<rect x="3.4" y="-1" width="5.6" height="2" fill="{panel}" opacity=".9"/>'
            f'<circle r="1" cy="-2.6" fill="#ff9fb6"><animate attributeName="opacity" values="1;.1;1" dur="1.6s" repeatCount="indefinite"/></circle>')


def scope(t, cx, cy, r, color, fill, fill_op) -> str:
    """Small radar instrument with a rotating sweep and fading blips."""
    ticks = "".join(
        f"M{n(cx + (r - (5 if a % 90 == 0 else 2.5)) * math.cos(math.radians(a)))} {n(cy + (r - (5 if a % 90 == 0 else 2.5)) * math.sin(math.radians(a)))}"
        f"L{n(cx + r * math.cos(math.radians(a)))} {n(cy + r * math.sin(math.radians(a)))}"
        for a in range(0, 360, 15)
    )
    wedge = f"M{cx} {cy}L{n(cx + r)} {cy}A{r} {r} 0 0 0 {n(cx + r * math.cos(math.radians(-38)))} {n(cy + r * math.sin(math.radians(-38)))}Z"
    blips = ""
    for ang, rr in ((-120, .55), (35, .72), (160, .38)):
        bx, by = cx + r * rr * math.cos(math.radians(ang)), cy + r * rr * math.sin(math.radians(ang))
        frac = ((ang % 360) / 360)
        blips += (f'<circle cx="{n(bx)}" cy="{n(by)}" r="1.6" fill="{color}" opacity=".2">'
                  f'<animate attributeName="opacity" values="1;.12;.12;1" keyTimes="0;.6;.99;1" dur="6s" begin="{n(frac * 6 - 6)}s" repeatCount="indefinite"/></circle>')
    return (
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" fill-opacity="{fill_op}" stroke="{color}" stroke-opacity=".55"/>'
        f'<g fill="none" stroke="{color}" stroke-opacity=".25" stroke-width=".7"><circle cx="{cx}" cy="{cy}" r="{n(r * 2 / 3)}"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{n(r / 3)}"/><path d="M{cx - r} {cy}H{cx + r}M{cx} {cy - r}V{cy + r}"/></g>'
        f'<path d="{ticks}" stroke="{color}" stroke-opacity=".6" stroke-width=".8"/>'
        f'<g><path d="{wedge}" fill="{color}" opacity=".22"/><path d="M{cx} {cy}H{cx + r}" stroke="{color}" stroke-width="1.2" opacity=".9"/>'
        f'<animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" to="360 {cx} {cy}" dur="6s" repeatCount="indefinite"/></g>'
        f'{blips}'
    )


def pulse_node(x, y, color, core="#ffffff", r=5) -> str:
    rings = "".join(
        f'<circle cx="{n(x)}" cy="{n(y)}" r="{r + 2}" fill="none" stroke="{color}" stroke-width="1.2" opacity="0">'
        f'<animate attributeName="r" values="{r + 2};{r * 6}" dur="4.4s" begin="{b}s" repeatCount="indefinite"/>'
        f'<animate attributeName="opacity" values=".75;0" dur="4.4s" begin="{b}s" repeatCount="indefinite"/></circle>'
        for b in (0, -2.2)
    )
    return (
        f'<circle cx="{n(x)}" cy="{n(y)}" r="{r * 4}" fill="{color}" opacity=".18" {B(8)}/>'
        f'{rings}'
        f'<g><circle cx="{n(x)}" cy="{n(y)}" r="{r * 3}" fill="none" stroke="{color}" stroke-opacity=".6" stroke-dasharray="2 4"/>'
        f'<animateTransform attributeName="transform" type="rotate" from="0 {n(x)} {n(y)}" to="360 {n(x)} {n(y)}" dur="30s" repeatCount="indefinite"/></g>'
        f'<circle cx="{n(x)}" cy="{n(y)}" r="{r}" fill="{core}" filter="url(#glow)">'
        f'<animate attributeName="r" values="{r};{r * 1.3:.1f};{r}" dur="4.4s" repeatCount="indefinite"/></circle>'
    )


def traveller(path, color, dur, begin, r=1.8) -> str:
    """A light point that travels a path, fading in and out."""
    return (f'<circle r="{r}" fill="{color}" filter="url(#glow)" opacity="0">'
            f'<animateMotion path="{path}" dur="{dur}s" begin="{begin}s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.1;.85;1" dur="{dur}s" begin="{begin}s" repeatCount="indefinite"/></circle>')


# --------------------------------------------------------------------------- #
# HERO
# --------------------------------------------------------------------------- #

def hero(t) -> str:
    W, H = 1400, 540
    dark = t["mode"] == "dark"
    sky = t["sky"]
    rng = random.Random(1308)

    # Text colour depends on the sky behind it (the dawn sky brightens downward).
    def lc(y):
        if dark or y < 255:
            return ("#f2efff", "#c9c4ea") if not dark else (t["ink"], t["dim"])
        return (t["ink"], t["dim"])

    def halo(y):
        if dark:
            return "#05060f"
        return "#3a3f80" if y < 255 else "#f6e4dc"

    defs = [blur_filters(3, 5, 8, 12, 14, 22, 26, 40), GLOW, band_gradient(sky, 860, "bandG")]
    if dark:
        defs.append(
            f'<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{t["bg"][0]}"/>'
            f'<stop offset=".55" stop-color="{t["bg"][1]}"/><stop offset="1" stop-color="{t["bg"][2]}"/></linearGradient>'
            '<radialGradient id="vig" cx=".5" cy=".45" r=".75"><stop offset=".6" stop-color="#000" stop-opacity="0"/>'
            '<stop offset="1" stop-color="#000" stop-opacity=".55"/></radialGradient>'
        )
    else:
        defs.append(
            '<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2d3876"/>'
            '<stop offset=".3" stop-color="#6b69a8"/><stop offset=".58" stop-color="#c3a8c8"/>'
            '<stop offset=".8" stop-color="#f1d8d0"/><stop offset="1" stop-color="#fbf2ea"/></linearGradient>'
            '<linearGradient id="skyFade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff"/>'
            '<stop offset=".35" stop-color="#fff" stop-opacity=".85"/><stop offset=".78" stop-color="#fff" stop-opacity="0"/></linearGradient>'
            f'<mask id="skyMask" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">'
            f'<rect width="{W}" height="{H}" fill="url(#skyFade)"/></mask>'
        )

    body = [f'<rect width="{W}" height="{H}" fill="url(#bg)"/>']
    if dark:
        body.append(f'<ellipse cx="740" cy="200" rx="520" ry="200" fill="#2a1f55" opacity=".35" {B(40)}/>')
    else:
        body.append(f'<ellipse cx="700" cy="610" rx="780" ry="230" fill="#ffe3c6" opacity=".6" {B(40)}/>')

    # ---- the sky: stars, galaxy, flares, drifting particles ---------------
    skyl = [
        starfield(rng, 520, sky["stars"], box=(0, 0, W, H), r=(0.25, 1.5), o=(0.12, 0.85), twinkle=0.07),
        milky_way(rng, sky, 700, 205, -14, 1720, "bandG", intensity=1.0 if dark else 1.25),
    ]
    for (x, y, s, c, fl) in ((302, 74, 1.5, "#fff2dc", (19, -3)), (1012, 286, 1.3, "#dfe9ff", (23, -14)),
                             (548, 316, 1.1, "#ffe0f0", None), (1318, 214, 1.0, "#ffffff", None),
                             (126, 186, 1.2, "#e6ecff", (29, -21)), (868, 58, 0.9, "#fff6ea", None)):
        skyl.append(bright_star(x, y, s, c, fl))
    skyl.append(drifting_particles(rng, 34, (0, 0, W, H), sky["stars"]))
    skyl.append(meteors())
    body.append(f'<g{"" if dark else " mask=" + chr(34) + "url(#skyMask)" + chr(34)}>{"".join(skyl)}</g>')
    if dark:
        body.append(f'<rect width="{W}" height="{H}" fill="url(#vig)"/>')

    frame_c = t["dim"] if dark else "#ffffff"
    body.append(ticks_frame(W, H, frame_c, .45 if dark else .55))

    # ---- HUD ---------------------------------------------------------------
    ink0, dim0 = lc(40)
    body.append(text(34, 44, "LPAM · DEEP-FIELD OBSERVATORY", 14, ink0, ls=3.2, op=.9))
    body.append(text(34, 64, "OBSERVING THE MILKY WAY FROM EARTH · EPOCH J2000", 11, dim0, ls=2.2, op=.85))
    body.append(
        f'<circle cx="1262" cy="39.5" r="3.4" fill="#ff9fb6"><animate attributeName="opacity" values="1;.25;1" dur="2.4s" repeatCount="indefinite"/></circle>'
    )
    body.append(text(1366, 44, "SKY LIVE", 14, ink0, anchor="end", ls=3.2, op=.9))
    body.append(text(1366, 64, "FOV 120° · CONCEPTUAL RENDER", 11, dim0, anchor="end", ls=2.2, op=.85))

    # Galactic centre annotation (real coordinates of Sgr A*).
    a = math.radians(-14)
    gx, gy = 700 + 40 * math.cos(a), 205 + 40 * math.sin(a)
    body.append(f'<path d="M{n(gx - 6)} {n(gy - 8)}L{n(gx - 70)} 112H486" fill="none" stroke="{ink0}" stroke-opacity=".45" stroke-width=".8"/>'
                f'<circle cx="{n(gx)}" cy="{n(gy)}" r="9" fill="none" stroke="{ink0}" stroke-opacity=".5" stroke-dasharray="2 3"/>')
    body.append(text(482, 106, "GALACTIC CENTER · SGR A*", 12, ink0, anchor="end", ls=2.4, halo=halo(100), op=.9))
    body.append(text(482, 124, "RA 17h45m40s · DEC −29°00′28″", 11, dim0, anchor="end", ls=1.6, halo=halo(120)))

    # ---- Earth, orbits, satellite, moon -------------------------------------
    ex, ey, R = 250, 390, 40
    ed, eb = earth(rng, t, ex, ey, R, "h")
    defs.append(ed)
    oc = t["cyan"] if dark else "#2c5e8a"
    body.append(
        f'<g><ellipse cx="{ex}" cy="{ey}" rx="150" ry="44" fill="none" stroke="{oc}" stroke-opacity=".32" stroke-dasharray="2 6"/>'
        f'<g transform="translate({ex} {ey})"><circle r="4.6" fill="#d7d6e0"/><circle r="4.6" fill="#1a1d33" opacity=".45" transform="translate(1.6 -1)"/>'
        f'<animateMotion path="M150 0A150 44 0 1 1 -150 0A150 44 0 1 1 150 0" dur="80s" repeatCount="indefinite"/></g>'
        f'<animateTransform attributeName="transform" type="rotate" from="-16 {ex} {ey}" to="344 {ex} {ey}" dur="300s" repeatCount="indefinite"/></g>'
    )
    oa, ob = 86, 24
    orbit_back = f"M{ex - oa} {ey}A{oa} {ob} 0 0 1 {ex + oa} {ey}"
    orbit_front = f"M{ex + oa} {ey}A{oa} {ob} 0 0 1 {ex - oa} {ey}"
    body.append(f'<g transform="rotate(-16 {ex} {ey})"><path d="{orbit_back}" fill="none" stroke="{oc}" stroke-opacity=".25"/></g>')
    body.append(eb)
    body.append(
        f'<g transform="rotate(-16 {ex} {ey})"><path d="{orbit_front}" fill="none" stroke="{oc}" stroke-opacity=".6"/>'
        f'<g opacity="1">{satellite("#f3f1ff" if dark else "#ffffff", t["cyan"])}'
        f'<animateMotion path="M{ex + oa} {ey}A{oa} {ob} 0 1 1 {ex - oa} {ey}A{oa} {ob} 0 1 1 {ex + oa} {ey}" dur="26s" rotate="auto" repeatCount="indefinite"/>'
        f'<animate attributeName="opacity" values="1;1;0;0;1" keyTimes="0;.47;.53;.97;1" dur="26s" repeatCount="indefinite"/></g></g>'
    )
    ink_e, dim_e = lc(ey)
    body.append(text(ex, ey + R + 34, "EARTH", 13, ink_e, anchor="middle", ls=4, halo=halo(ey)))
    body.append(text(ex, ey + R + 50, "origin · observation", 10.5, dim_e, anchor="middle", ls=1.6, halo=halo(ey)))

    # ---- Earth → knowledge → research node ---------------------------------
    nx, ny = 710, 488
    domains = [("LAW", 560), ("DATA", 660), ("SPACE", 760), ("POLITICS", 860)]
    fc = t["flow"]
    flows, trav, marks = [], [], []
    for i, (name, dx) in enumerate(domains):
        curve = f"M{ex + 28} {ey - 30}C{360 + i * 40} {300 + i * 8} {dx - 110} 372 {dx} 420"
        flows.append(f'<path d="{curve}" fill="none" stroke="{fc}" stroke-opacity=".35" stroke-dasharray="1 6"/>'
                     f'<path d="M{dx} 420L{nx} {ny}" stroke="{fc}" stroke-opacity=".32"/>')
        full = f"{curve}L{nx} {ny}"
        trav.append(traveller(full, fc, 9 + i * 0.8, -i * 2.1))
        trav.append(traveller(full, sky["warm"] if dark else t["warm"], 9 + i * 0.8, -i * 2.1 - 4.6, r=1.4))
        ink_d, _ = lc(420)
        marks.append(f'<path d="{star4(dx, 420, 6)}" fill="{ink_d}"/>'
                     f'<circle cx="{dx}" cy="420" r="9" fill="none" stroke="{ink_d}" stroke-opacity=".35"/>')
        marks.append(text(dx, 400, name, 14, ink_d, anchor="middle", ls=3.4, halo=halo(400)))
    body += flows + marks + trav
    body.append(pulse_node(nx, ny, t["lav"] if not dark else "#c9b8ff", core="#ffffff"))
    ink_n, dim_n = lc(ny)
    body.append(text(nx, ny + 36, "LPAM RESEARCH NODE", 13, ink_n, anchor="middle", ls=4.2, weight="600", halo=halo(ny)))

    # ---- Research constellation ---------------------------------------------
    nodes = {
        "SPACE": (1150, 140, 0, -16, "middle"),
        "DATA": (1046, 236, -14, 5, "end"),
        "TECHNOLOGY": (1254, 236, 14, 5, "start"),
        "RESEARCH": (1150, 322, 16, 5, "start"),
        "LAW": (1060, 406, -14, 5, "end"),
        "POLITICS": (1240, 406, 14, 5, "start"),
        "SOCIETY": (1122, 476, -14, 5, "end"),
    }
    edges = [("SPACE", "DATA"), ("SPACE", "TECHNOLOGY"), ("DATA", "RESEARCH"), ("TECHNOLOGY", "RESEARCH"),
             ("RESEARCH", "LAW"), ("RESEARCH", "POLITICS"), ("LAW", "SOCIETY")]
    cyc = 26
    for i, (a_, b_) in enumerate(edges):
        x1, y1 = nodes[a_][:2]
        x2, y2 = nodes[b_][:2]
        L = math.hypot(x2 - x1, y2 - y1)
        s = .04 + i * .06
        col = lc((y1 + y2) / 2)[0]
        body.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{col}" stroke-opacity=".2" stroke-width=".8"/>')
        body.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{col}" stroke-opacity=".62" stroke-width="1" '
            f'stroke-dasharray="{n(L)}" stroke-dashoffset="0"><animate attributeName="stroke-dashoffset" '
            f'values="{n(L)};{n(L)};0;0;{n(L)}" keyTimes="0;{s:.2f};{s + .08:.2f};.9;1" dur="{cyc}s" repeatCount="indefinite"/></line>'
        )
    for i, (name, (x, y, ox, oy, anc)) in enumerate(nodes.items()):
        ink_c, _ = lc(y)
        rr = 7.5 if name == "RESEARCH" else 5.2
        s = .04 + i * .06
        body.append(
            f'<g><circle cx="{x}" cy="{y}" r="{rr * 2.6:.1f}" fill="{ink_c}" opacity=".16" {B(5)}/>'
            f'<path d="{star4(x, y, rr)}" fill="{ink_c}"/><circle cx="{x}" cy="{y}" r="{rr * .32:.1f}" fill="{ink_c}"/>'
            f'<animate attributeName="opacity" values=".75;.75;1;1;.75" keyTimes="0;{s:.2f};{s + .06:.2f};.9;1" dur="{cyc}s" repeatCount="indefinite"/></g>'
        )
        body.append(text(x + ox, y + oy, name, 13 if name != "RESEARCH" else 13.5, ink_c, anchor=anc, ls=3,
                         weight="600" if name == "RESEARCH" else None, halo=halo(y)))
    P = lambda *ks: "M" + "L".join(f"{nodes[k][0]} {nodes[k][1]}" for k in ks)
    body.append(traveller(P("SPACE", "DATA", "RESEARCH", "LAW", "SOCIETY"), fc, 12, -1))
    body.append(traveller(P("TECHNOLOGY", "RESEARCH", "POLITICS"), sky["warm"] if dark else t["warm"], 9, -5))
    body.append(traveller(P("SOCIETY", "LAW", "RESEARCH", "TECHNOLOGY", "SPACE"), fc, 14, -8, r=1.4))
    ink_t, dim_t = lc(500)
    body.append(text(1366, 500, "RESEARCH CONSTELLATION", 12.5, ink_t, anchor="end", ls=3.6, weight="600", halo=halo(500)))
    body.append(text(1366, 518, "CONCEPTUAL MAP · NOT EMPIRICAL DATA", 10.5, dim_t, anchor="end", ls=2.2, halo=halo(518)))

    # ---- Instrument ----------------------------------------------------------
    sc = t["cyan"] if dark else "#2a5a86"
    body.append(scope(t, 70, 468, 30, sc, "#000" if dark else "#ffffff", .35))
    body.append(text(70, 518, "SIGNAL SCOPE", 10.5, lc(518)[1], anchor="middle", ls=2.4, halo=halo(518)))

    desc = ("A living deep-space panorama: the Milky Way's luminous band with dust lanes and thousands of stars, "
            "a slowly rotating Earth with an orbiting satellite and moon, research signals flowing from Earth through "
            "Law, Data, Space and Politics into the LPAM research node, and a research constellation linking Space, "
            "Data, Technology, Research, Law, Politics and Society.")
    return (open_svg(W, H, "LPAM · Deep-field observatory", desc)
            + f'<defs>{"".join(defs)}</defs>' + "".join(body) + "</svg>")


# --------------------------------------------------------------------------- #
# TYPING HEADER
# --------------------------------------------------------------------------- #

def typing(t) -> str:
    W, H = 1000, 150
    lines = [
        "Law · International Relations · Computational Research",
        "Astropolitics · Space Policy · Technology",
        "Data · Scientific Visualization · Open Research",
    ]
    cw, slot, T = 11.4, 6.0, 18.0
    type_d, hold_end, erase_end = 2.6, 4.7, 5.4
    body, cursor = [], []
    for k, ln in enumerate(lines):
        L = len(ln) * cw
        x0 = W / 2 - L / 2
        s = k * slot
        kt, vals = [0.0], [0.0]
        steps = len(ln)
        for i in range(1, steps + 1):
            kt.append((s + type_d * i / steps) / T)
            vals.append(i * cw)
        kt.append((s + hold_end) / T)
        vals.append(L)
        es = 12
        for i in range(1, es + 1):
            kt.append((s + hold_end + (erase_end - hold_end) * i / es) / T)
            vals.append(L * (1 - i / es))
        # discrete steps: drop the duplicate leading key for the first line
        pairs = sorted(set(zip(kt, vals)), key=lambda p: (p[0], -p[1] if p[0] == 0 else 0))
        clean = []
        for p in pairs:
            if clean and abs(clean[-1][0] - p[0]) < 1e-9:
                continue
            clean.append(p)
        kts = ";".join(f"{p[0]:.4f}" for p in clean)
        vs = ";".join(n(p[1]) for p in clean)
        body.append(
            f'<clipPath id="c{k}"><rect x="{n(x0)}" y="92" height="40" width="{n(L) if k == 0 else 0}">'
            f'<animate attributeName="width" values="{vs}" keyTimes="{kts}" dur="{T}s" calcMode="discrete" repeatCount="indefinite"/></rect></clipPath>'
        )
        body.append(text(x0, 120, ln, 19, t["dim"], extra=f'textLength="{n(L)}" lengthAdjust="spacing" clip-path="url(#c{k})"'))
        cursor += [(p[0], x0 + p[1]) for p in clean]
    cursor.sort()
    ck, cv = [], []
    for tk, x in cursor:
        if ck and abs(ck[-1] - tk) < 1e-9:
            cv[-1] = x
            continue
        ck.append(tk)
        cv.append(x)
    first_x = cursor[0][1]
    body.append(
        f'<rect x="{n(W / 2 + len(lines[0]) * cw / 2 + 3)}" y="103" width="10" height="21" fill="{t["cyan"]}">'
        f'<animate attributeName="x" values="{";".join(n(x + 3) for x in cv)}" keyTimes="{";".join(f"{k:.4f}" for k in ck)}" dur="{T}s" calcMode="discrete" repeatCount="indefinite"/>'
        f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.5;.5;1" dur="1.05s" repeatCount="indefinite"/></rect>'
    )
    _ = first_x
    head = [
        text(W / 2, 54, "Laura Pamela Aranda Medrano", 42, t["ink"], cls="r", anchor="middle", ls=0.6,
             inner='<animate attributeName="opacity" values="0;1" dur="1.8s" fill="freeze"/>'),
        f'<path d="M{W / 2 - 150} 77H{W / 2 - 18}M{W / 2 + 18} 77H{W / 2 + 150}" stroke="{t["faint"]}" stroke-width=".8"/>',
        f'<path d="{star4(W / 2, 77, 6)}" fill="{t["lav"]}"><animate attributeName="opacity" values="1;.4;1" dur="5s" repeatCount="indefinite"/></path>',
    ]
    desc = "Laura Pamela Aranda Medrano. " + " / ".join(lines)
    return open_svg(W, H, "Laura Pamela Aranda Medrano", desc) + "".join(head + body) + "</svg>"


# --------------------------------------------------------------------------- #
# WHOAMI · observatory console
# --------------------------------------------------------------------------- #

def whoami(t) -> str:
    W, H = 1000, 560
    dark = t["mode"] == "dark"
    rng = random.Random(42)
    defs = [blur_filters(3, 5, 8, 12, 14, 22, 26, 40), GLOW, band_gradient(t["sky"], 700, "wBand"),
            band_gradient(DARK_SKY if dark else DAWN_SKY, 420, "fBand"),
            f'<clipPath id="fv"><rect x="572" y="112" width="356" height="280" rx="6"/></clipPath>',
            f'<linearGradient id="scan" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{t["cyan"]}" stop-opacity="0"/>'
            f'<stop offset="1" stop-color="{t["cyan"]}" stop-opacity=".35"/></linearGradient>']
    body = []
    if dark:
        body.append(f'<rect width="{W}" height="{H}" fill="{t["bg"][1]}"/>')
        body.append(milky_way(rng, t["sky"], 500, 280, -24, 1300, "wBand", n_stars=260, n_faint=200, intensity=.5, clusters=2))
        body.append(starfield(rng, 170, t["sky"]["stars"], box=(0, 0, W, H), o=(.1, .6), twinkle=.12))
    else:
        body.append(f'<rect width="{W}" height="{H}" fill="{t["bg"][0]}"/>')
        body.append(f'<ellipse cx="500" cy="280" rx="620" ry="80" fill="{t["lav"]}" opacity=".07" transform="rotate(-24 500 280)" {B(40)}/>')
        body.append(starfield(rng, 170, t["ink_stars"], box=(0, 0, W, H), o=(.1, .45), r=(.3, 1.2), twinkle=.1))

    px, py, pw, ph = 40, 36, 920, 488
    body.append(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="14" fill="{t["panel"]}" fill-opacity="{.86 if dark else .94}" stroke="{t["panel_edge"]}"/>')
    body.append(f'<path d="M{px} 84H{px + pw}" stroke="{t["panel_edge"]}"/>')
    body.append(text(68, 66, "OBSERVATORY // LPAM NODE", 15, t["ink"], ls=3.4, weight="600"))
    # telemetry indicator
    bars = ""
    for i in range(6):
        hgt = [6, 10, 14, 9, 12, 7][i]
        bars += (f'<rect x="{708 + i * 7}" y="{68 - hgt}" width="4" height="{hgt}" fill="{t["cyan"]}" opacity=".8">'
                 f'<animate attributeName="height" values="{hgt};{3 + (i * 5) % 12};{hgt}" dur="{1.4 + i * .23:.2f}s" repeatCount="indefinite"/>'
                 f'<animate attributeName="y" values="{68 - hgt};{68 - 3 - (i * 5) % 12};{68 - hgt}" dur="{1.4 + i * .23:.2f}s" repeatCount="indefinite"/></rect>')
    body.append(text(668, 66, "TLM", 12, t["dim"], ls=2.4) + bars)
    body.append(f'<circle cx="868" cy="61" r="4.2" fill="#ff8fab"><animate attributeName="opacity" values="1;.2;1" dur="2s" repeatCount="indefinite"/></circle>'
                f'<circle cx="868" cy="61" r="4" fill="none" stroke="#ff8fab"><animate attributeName="r" values="4;11" dur="2s" repeatCount="indefinite"/>'
                f'<animate attributeName="opacity" values=".8;0" dur="2s" repeatCount="indefinite"/></circle>')
    body.append(text(932, 66, "LIVE", 15, t["ink"], anchor="end", ls=3.4, weight="600"))

    # Identity
    rows = [("observer:", "LAURA PAMELA ARANDA MEDRANO", 132), ("origin:", "EARTH", 170), ("field:", "INTERDISCIPLINARY RESEARCH", 208)]
    for k, v, y in rows:
        body.append(text(72, y, k, 16, t["dim"]))
        body.append(text(196, y, v, 16, t["ink"], weight="600" if k == "observer:" else None, ls=.6))
    body.append(f'<circle cx="262" cy="164.5" r="5.5" fill="url(#ocw)"/><circle cx="262" cy="164.5" r="7.5" fill="none" stroke="{t["cyan"]}" stroke-opacity=".5"/>')
    defs.append(f'<radialGradient id="ocw" cx=".35" cy=".35"><stop offset="0" stop-color="{t["ocean"][0]}"/><stop offset="1" stop-color="{t["ocean"][2]}"/></radialGradient>')

    body.append(text(72, 252, "signals:", 16, t["dim"]))
    body.append(text(196, 252, "relative focus · conceptual, not measured", 11.5, t["dim"], ls=.8, op=.8))
    signals = [("§", "LAW", 11, t["lav"]), ("◎", "POLITICS", 10, t["pink"]), ("✦", "SPACE", 12, t["cyan"]),
               ("◉", "DATA", 8, t["warm"]), ("⬡", "TECHNOLOGY", 9, t["lav"])]
    for r_, (g, name, segs, col) in enumerate(signals):
        y = 290 + r_ * 34
        body.append(text(84, y, g, 16, col, anchor="middle"))
        body.append(text(106, y, name, 14.5, t["ink"], ls=1.6))
        for i in range(14):
            x = 254 + i * 19
            if i >= segs:
                body.append(f'<rect x="{x}" y="{y - 13}" width="14" height="15" rx="2" fill="{t["faint"]}" opacity=".25"/>')
                continue
            on = (0.25 + r_ * .12 + i * .06) / 3
            breathe = (f'<animate attributeName="opacity" values="1;.35;1" dur="{2.6 + r_ * .4:.1f}s" begin="3s" repeatCount="indefinite"/>'
                       if i == segs - 1 else "")
            body.append(f'<rect x="{x}" y="{y - 13}" width="14" height="15" rx="2" fill="{col}">'
                        f'<animate attributeName="opacity" values="0;0;1" keyTimes="0;{on:.3f};1" dur="3s" fill="freeze"/>{breathe}</rect>')

    # trajectory
    body.append(text(72, 474, "trajectory:", 16, t["dim"]))
    body.append(text(196, 474, "THEORY", 16, t["ink"], ls=.6))
    body.append(f'<path d="M272 469H418" stroke="{t["faint"]}" stroke-dasharray="3 4"/><path d="M414 464l7 5-7 5" fill="none" stroke="{t["cyan"]}"/>')
    body.append(f'<circle cy="469" r="3.2" fill="{t["cyan"]}" filter="url(#glow)"><animate attributeName="cx" values="274;414" dur="3.2s" repeatCount="indefinite"/>'
                f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.15;.85;1" dur="3.2s" repeatCount="indefinite"/></circle>')
    body.append(text(430, 474, "COMPUTATION", 16, t["ink"], ls=.6))
    body.append(text(72, 506, "status:", 16, t["dim"]))
    body.append(text(196, 506, "OBSERVING", 16, t["cyan"], weight="600", ls=1.2))
    body.append(f'<rect x="300" y="491" width="10" height="19" fill="{t["cyan"]}"><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.5;.5;1" dur="1.1s" repeatCount="indefinite"/></rect>')

    # Field view: a small photographic plate of the galactic centre
    pal = DARK_SKY if dark else DAWN_SKY
    fv = [f'<rect x="572" y="112" width="356" height="280" fill="{t["plate"][0]}"/>',
          milky_way(rng, pal, 750, 262, -32, 840, "fBand", n_stars=420, n_faint=380, intensity=1.1, clusters=3, core=10),
          starfield(rng, 90, pal["stars"], box=(572, 112, 356, 280), o=(.2, .8), twinkle=.15)]
    cx, cy = 750, 252
    tick = "".join(f"M{n(cx + 40 * math.cos(math.radians(a)))} {n(cy + 40 * math.sin(math.radians(a)))}L{n(cx + 48 * math.cos(math.radians(a)))} {n(cy + 48 * math.sin(math.radians(a)))}" for a in range(0, 360, 30))
    fv.append(f'<g stroke="#e9f6ff" fill="none" stroke-opacity=".7"><circle cx="{cx}" cy="{cy}" r="40" stroke-width=".8"/>'
              f'<path d="{tick}M{cx - 70} {cy}H{cx - 16}M{cx + 16} {cy}H{cx + 70}M{cx} {cy - 70}V{cy - 16}M{cx} {cy + 16}V{cy + 70}" stroke-width=".8"/></g>'
              f'<g><circle cx="{cx}" cy="{cy}" r="58" fill="none" stroke="#e9f6ff" stroke-opacity=".35" stroke-dasharray="1 5"/>'
              f'<animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" to="-360 {cx} {cy}" dur="60s" repeatCount="indefinite"/></g>')
    fv.append(f'<rect x="572" y="112" width="356" height="46" fill="url(#scan)"><animate attributeName="y" values="66;392" dur="6.5s" repeatCount="indefinite"/></rect>')
    body.append(f'<g clip-path="url(#fv)">{"".join(fv)}</g>')
    body.append(f'<rect x="572" y="112" width="356" height="280" rx="6" fill="none" stroke="{t["panel_edge"]}"/>')
    body.append(text(586, 132, "FIELD VIEW · CH 01", 11, "#e9f6ff", ls=2.4, op=.85))
    body.append(text(572, 420, "TARGET", 12, t["dim"], ls=2) + text(650, 420, "SGR A* · GALACTIC CENTER", 12, t["ink"], ls=1.2))
    body.append(text(572, 442, "RA 17h45m40s   DEC −29°00′28″", 12, t["dim"], ls=1))
    body.append(f'<circle cx="905" cy="416" r="3.5" fill="{t["cyan"]}"><animate attributeName="opacity" values="1;.2;1" dur="1.6s" repeatCount="indefinite"/></circle>')
    body.append(text(898, 420, "TRACK", 11, t["cyan"], anchor="end", ls=2))

    # Console-wide scanline
    body.append(f'<rect x="{px + 1}" y="86" width="{pw - 2}" height="2" fill="{t["cyan"]}" opacity=".18">'
                f'<animate attributeName="y" values="86;520" dur="9s" repeatCount="indefinite"/></rect>')
    body.append(ticks_frame(W, H, t["dim"] if dark else t["faint"], .35))

    desc = ("Observatory console. Observer: Laura Pamela Aranda Medrano. Origin: Earth. Field: interdisciplinary research. "
            "Research signals: law, politics, space, data, technology (relative focus, conceptual). "
            "Trajectory: theory to computation. Status: observing.")
    return open_svg(W, H, "Observatory // LPAM node", desc) + f'<defs>{"".join(defs)}</defs>' + "".join(body) + "</svg>"


# --------------------------------------------------------------------------- #
# ORBITAL RESEARCH MAP
# --------------------------------------------------------------------------- #

def planet_grad(gid, c) -> str:
    return (f'<radialGradient id="{gid}" cx=".35" cy=".32" r=".8"><stop offset="0" stop-color="#ffffff" stop-opacity=".9"/>'
            f'<stop offset=".38" stop-color="{c}"/><stop offset="1" stop-color="{c}" stop-opacity=".35"/></radialGradient>')


def celestial_body(kind, t) -> str:
    c = t
    if kind == "LAW":  # ringed planet
        return (f'<ellipse rx="25" ry="6.5" fill="none" stroke="{c["warm"]}" stroke-opacity=".5" stroke-width="1.6" transform="rotate(-20)"/>'
                f'<circle r="13" fill="url(#gLaw)"/>'
                f'<path d="M-23.5 8.6A25 6.5 -20 0 0 23.5 -8.6" fill="none" stroke="{c["warm"]}" stroke-width="1.6" transform="rotate(0)"/>')
    if kind == "POLITICS":  # planet with two moons
        moons = "".join(
            f'<circle r="{mr}" fill="{c["ink"]}" opacity=".85"><animateMotion path="{circle_path(0, 0, orb)}" dur="{d}s" repeatCount="indefinite"/></circle>'
            for mr, orb, d in ((2.2, 21, 11), (1.6, 27, 17))
        )
        return (f'<circle r="21" fill="none" stroke="{c["pink"]}" stroke-opacity=".25"/><circle r="12" fill="url(#gPol)"/>{moons}')
    if kind == "TECHNOLOGY":  # faceted, slowly turning body
        hexa = " ".join(f"{n(13 * math.cos(math.radians(a)))},{n(13 * math.sin(math.radians(a)))}" for a in range(30, 390, 60))
        return (f'<g><polygon points="{hexa}" fill="{c["panel"]}" stroke="{c["cyan"]}" stroke-width="1.4"/>'
                f'<path d="M0 -13V13M-11.3 -6.5L11.3 6.5M-11.3 6.5L11.3 -6.5" stroke="{c["cyan"]}" stroke-opacity=".35"/>'
                f'<animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="40s" repeatCount="indefinite"/></g>'
                f'<circle r="3" fill="{c["cyan"]}" filter="url(#glow)"/>')
    if kind == "SPACE":  # a star
        return (f'<circle r="18" fill="{c["cyan"]}" opacity=".2" {B(8)}/>'
                + bright_star(0, 0, 2.6, "#ffffff" if c["mode"] == "dark" else "#2a6f9a", (13, -4)))
    if kind == "DATA":  # point cluster
        pts = [(-6, -6), (0, -8), (6, -5), (-8, 1), (-1, 0), (7, 2), (-4, 7), (3, 8)]
        dots = "".join(
            f'<circle cx="{x}" cy="{y}" r="{1.6 + (i % 3) * .5:.1f}" fill="{c["warm"]}"><animate attributeName="opacity" values="1;.35;1" dur="{2 + i * .37:.2f}s" repeatCount="indefinite"/></circle>'
            for i, (x, y) in enumerate(pts)
        )
        return f'<circle r="16" fill="none" stroke="{c["warm"]}" stroke-opacity=".4" stroke-dasharray="2 3"/>{dots}'
    # SOCIETY: binary pair
    return (f'<circle r="15" fill="none" stroke="{c["lav"]}" stroke-opacity=".3"/>'
            f'<g><circle cx="-6" r="5.5" fill="url(#gSoc)"/><circle cx="7" r="4" fill="url(#gPol)"/>'
            f'<animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="14s" repeatCount="indefinite"/></g>')


def orbital(t) -> str:
    W, H = 1000, 640
    dark = t["mode"] == "dark"
    rng = random.Random(7)
    cx, cy = 500, 320
    defs = [blur_filters(3, 5, 8, 12, 14, 22, 26, 40), GLOW, band_gradient(t["sky"] if dark else DAWN_SKY, 700, "oBand"),
            planet_grad("gLaw", t["lav"]), planet_grad("gPol", t["pink"]), planet_grad("gSoc", t["cyan"]),
            '<radialGradient id="vig" cx=".5" cy=".5" r=".7"><stop offset=".65" stop-color="#000" stop-opacity="0"/>'
            '<stop offset="1" stop-color="#000" stop-opacity=".5"/></radialGradient>']
    body = []
    if dark:
        body.append(f'<rect width="{W}" height="{H}" fill="{t["bg"][1]}"/>')
        body.append(milky_way(rng, t["sky"], 500, 320, 28, 1400, "oBand", n_stars=520, n_faint=420, intensity=.6, clusters=3))
        body.append(starfield(rng, 300, t["sky"]["stars"], box=(0, 0, W, H), o=(.1, .75), twinkle=.08))
        body.append(f'<rect width="{W}" height="{H}" fill="url(#vig)"/>')
    else:
        body.append(f'<rect width="{W}" height="{H}" fill="{t["bg"][0]}"/>')
        body.append(f'<ellipse cx="500" cy="320" rx="700" ry="90" fill="{t["lav"]}" opacity=".07" transform="rotate(28 500 320)" {B(40)}/>')
        body.append(starfield(rng, 300, t["ink_stars"], box=(0, 0, W, H), o=(.1, .5), r=(.3, 1.3), twinkle=.08))
    lc = t["dim"] if dark else t["dim"]

    # graduated outer ring (slowly counter-rotating)
    tk = []
    for a in range(0, 360, 5):
        r1 = 289 if a % 30 == 0 else 294
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        tk.append(f"M{n(cx + r1 * ca)} {n(cy + r1 * sa)}L{n(cx + 300 * ca)} {n(cy + 300 * sa)}")
    labels = "".join(
        text(cx + 277 * math.cos(math.radians(a - 90)), cy + 277 * math.sin(math.radians(a - 90)) + 3.5, f"{a}°", 9, lc,
             anchor="middle", op=.7)
        for a in range(0, 360, 30)
    )
    body.append(f'<g><circle cx="{cx}" cy="{cy}" r="300" fill="none" stroke="{lc}" stroke-opacity=".35"/>'
                f'<path d="{"".join(tk)}" stroke="{lc}" stroke-opacity=".5" stroke-width=".8"/>{labels}'
                f'<animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" to="-360 {cx} {cy}" dur="900s" repeatCount="indefinite"/></g>')
    # spokes of a coordinate grid
    spokes = "".join(f"M{cx} {cy}L{n(cx + 285 * math.cos(math.radians(a)))} {n(cy + 285 * math.sin(math.radians(a)))}" for a in range(0, 360, 30))
    body.append(f'<path d="{spokes}" stroke="{lc}" stroke-opacity=".12" stroke-width=".7"/>')

    rings = [(125, "2 10", 120, 1, 38), (195, "1 8", 200, -1, 64), (265, "3 14", 280, 1, 92)]
    for r, dash, dur, sign, ptd in rings:
        body.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{lc}" stroke-opacity=".28"/>')
        body.append(f'<g><circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{t["cyan"]}" stroke-opacity=".55" stroke-dasharray="{dash}"/>'
                    f'<animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" to="{360 * sign} {cx} {cy}" dur="{dur}s" repeatCount="indefinite"/></g>')
        body.append(f'<circle r="2" fill="{t["cyan"]}" filter="url(#glow)"><animateMotion path="{circle_path(cx, cy, r)}" dur="{ptd}s" repeatCount="indefinite"/></circle>')

    # Rigid constellation of domains, rotating as one system; bodies counter-rotate to stay upright.
    T = 360
    dom = {"LAW": (125, 200, "norms · sovereignty"), "DATA": (125, 20, "signals · methods"),
           "POLITICS": (195, 120, "power · institutions"), "TECHNOLOGY": (195, 300, "infrastructure · AI"),
           "SPACE": (265, 250, "orbits · governance"), "SOCIETY": (265, 70, "people · rights")}
    pos = {k: (cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for k, (r, a, _) in dom.items()}
    ring_order = ["SPACE", "TECHNOLOGY", "DATA", "SOCIETY", "POLITICS", "LAW", "SPACE"]
    sys = []
    for a_, b_ in zip(ring_order, ring_order[1:]):
        (x1, y1), (x2, y2) = pos[a_], pos[b_]
        sys.append(f'<line x1="{n(x1)}" y1="{n(y1)}" x2="{n(x2)}" y2="{n(y2)}" stroke="{t["ink"]}" stroke-opacity=".22" stroke-width=".8"/>')
    for i, (k, (x, y)) in enumerate(pos.items()):
        sys.append(f'<line x1="{cx}" y1="{cy}" x2="{n(x)}" y2="{n(y)}" stroke="{t["lav"]}" stroke-opacity=".3" stroke-dasharray="1 5"/>')
        sys.append(traveller(f"M{cx} {cy}L{n(x)} {n(y)}", t["flow"], 5 + i * .6, -i * 1.3, r=1.6))
    path = "M" + "L".join(f"{n(pos[k][0])} {n(pos[k][1])}" for k in ring_order)
    sys.append(traveller(path, t["warm"], 30, 0, r=1.5))
    for k, (x, y) in pos.items():
        sub = dom[k][2]
        sys.append(
            f'<g transform="translate({n(x)} {n(y)})"><g>{celestial_body(k, t)}'
            + text(0, 38, k, 13.5, t["ink"], anchor="middle", ls=3.2, weight="600", halo=t["bg"][1] if dark else t["bg"][0])
            + text(0, 54, sub, 10.5, t["dim"], anchor="middle", ls=1, halo=t["bg"][1] if dark else t["bg"][0])
            + f'<animateTransform attributeName="transform" type="rotate" from="0" to="-360" dur="{T}s" repeatCount="indefinite"/></g></g>'
        )
    body.append(f'<g>{"".join(sys)}<animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" to="360 {cx} {cy}" dur="{T}s" repeatCount="indefinite"/></g>')

    # Centre: open research
    body.append(f'<circle cx="{cx}" cy="{cy}" r="46" fill="{t["warm"]}" opacity="{.22 if dark else .14}" {B(14)}/>')
    body.append(pulse_node(cx, cy, t["warm"] if dark else t["lav"], core="#fff8ec" if dark else "#ffffff", r=7))
    body.append(text(cx, cy + 40, "OPEN RESEARCH", 14, t["ink"], anchor="middle", ls=4, weight="600",
                     halo=t["bg"][1] if dark else t["bg"][0]))

    # Plate annotations
    body.append(text(40, 48, "MILKY WAY RESEARCH MAP", 14, t["ink"], ls=3.6, weight="600"))
    body.append(text(40, 68, "STAR ATLAS · PLATE II", 11, t["dim"], ls=2.4))
    leg = [("✦", "domain · celestial body"), ("◌", "orbit · line of inquiry"), ("·", "particle · idea in transit")]
    for i, (g, s) in enumerate(leg):
        body.append(text(46, 560 + i * 20, g, 13, t["cyan"], anchor="middle") + text(60, 560 + i * 20, s, 11, t["dim"], ls=.6))
    body.append(text(960, 48, "CONCEPTUAL MAP", 12, t["ink"], anchor="end", ls=3))
    body.append(text(960, 66, "NOT EMPIRICAL DATA", 11, t["dim"], anchor="end", ls=2.4))
    body.append(text(960, 600, "orbital periods are illustrative", 11, t["dim"], anchor="end", ls=.6, italic=True, cls="r"))
    body.append(ticks_frame(W, H, t["dim"] if dark else t["faint"], .35))

    desc = ("Star-atlas style research map. Open research sits at the centre; Law, Data, Politics, Technology, Space and "
            "Society orbit it as celestial bodies connected by constellation lines. Conceptual map, not empirical data.")
    return open_svg(W, H, "Milky Way research map", desc) + f'<defs>{"".join(defs)}</defs>' + "".join(body) + "</svg>"


# --------------------------------------------------------------------------- #
# TELEMETRY
# --------------------------------------------------------------------------- #

def telemetry(t) -> str:
    W, H = 1000, 430
    dark = t["mode"] == "dark"
    rng = random.Random(99)
    wx, ww = 290, 560
    defs = [GLOW, blur_filters(3),
            f'<clipPath id="win"><rect x="{wx}" y="80" width="{ww}" height="290"/></clipPath>',
            f'<linearGradient id="sweep" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{t["cyan"]}" stop-opacity="0"/>'
            f'<stop offset="1" stop-color="{t["cyan"]}" stop-opacity=".2"/></linearGradient>']
    body = [f'<rect width="{W}" height="{H}" fill="{t["bg"][1] if dark else t["bg"][0]}"/>']
    body.append(starfield(rng, 140, t["sky"]["stars"] if dark else t["ink_stars"], box=(0, 0, W, H), o=(.08, .5), twinkle=.1))
    body.append(f'<rect x="24" y="22" width="952" height="386" rx="12" fill="{t["panel"]}" fill-opacity="{.85 if dark else .94}" stroke="{t["panel_edge"]}"/>')
    body.append(text(48, 52, "DEEP-SPACE RECEIVER // LPAM ARRAY", 14, t["ink"], ls=3.2, weight="600"))
    body.append(text(952, 52, "RESEARCH SIGNALS · CONCEPTUAL", 12.5, t["warm"], anchor="end", ls=3))
    body.append(f'<path d="M24 68H976" stroke="{t["panel_edge"]}"/>')
    grid = "".join(f"M{x} 80V370" for x in range(wx, wx + ww + 1, 28))
    body.append(f'<path d="{grid}" stroke="{t["faint"]}" stroke-opacity=".22" stroke-width=".6"/>')

    channels = [("RESEARCH SIGNAL", t["lav"], 3, 7, "LOCK"), ("SPACE GOVERNANCE", t["cyan"], 2, 9, "TRACK"),
                ("TECHNOLOGY", t["pink"], 5, 11, "LOCK"), ("LAW", t["warm"], 1, 4, "TRACK"),
                ("POLITICS", t["lav"], 4, 13, "SCAN"), ("DATA", t["cyan"], 6, 10, "LOCK")]
    waves = []
    for i, (name, col, k1, k2, mode) in enumerate(channels):
        y = 104 + i * 48
        body.append(f'<path d="M48 {y + 20}H952" stroke="{t["faint"]}" stroke-opacity=".25" stroke-width=".6"/>')
        body.append(text(48, y + 4.5, f"CH-{i + 1:02d}", 10.5, t["dim"], ls=1.6) + text(102, y + 4.5, name, 12.5, t["ink"], ls=2))
        d = rng.uniform(1.4, 3.6)
        body.append(f'<circle cx="268" cy="{y}" r="3.6" fill="{col}"><animate attributeName="opacity" values="1;.25;1" dur="{d:.1f}s" repeatCount="indefinite"/></circle>'
                    f'<circle cx="268" cy="{y}" r="3.6" fill="none" stroke="{col}" opacity="0"><animate attributeName="r" values="3.6;10" dur="{d * 2:.1f}s" repeatCount="indefinite"/>'
                    f'<animate attributeName="opacity" values=".7;0" dur="{d * 2:.1f}s" repeatCount="indefinite"/></circle>')
        # periodic waveform over 2 * ww, so the scroll loops seamlessly
        ph = rng.uniform(0, 6.28)
        bursts = [rng.uniform(0, ww) for _ in range(2)]
        pts = []
        for x in range(0, 2 * ww + 1, 4):
            u = x % ww
            v = 5.5 * math.sin(2 * math.pi * k1 * u / ww + ph) + 2.5 * math.sin(2 * math.pi * k2 * u / ww)
            for b in bursts:
                dist = min(abs(u - b), ww - abs(u - b))
                v += 9 * math.exp(-(dist / 14) ** 2) * math.sin(u / 2.2)
            pts.append(f"{x} {n(-v)}")
        dpath = "M" + "L".join(pts)
        dur = 14 + i * 2.3
        waves.append(
            f'<g transform="translate({wx} {y})"><path d="{dpath}" fill="none" stroke="{col}" stroke-width="3" opacity=".18"/>'
            f'<path d="{dpath}" fill="none" stroke="{col}" stroke-width="1.2"/>'
            f'<animateTransform attributeName="transform" type="translate" from="{wx} {y}" to="{wx - ww} {y}" dur="{dur:.1f}s" repeatCount="indefinite"/></g>'
        )
        body.append(text(952, y + 4.5, mode, 11, col, anchor="end", ls=2.4))
    body.append(f'<g clip-path="url(#win)">{"".join(waves)}'
                f'<g><rect x="-60" y="80" width="60" height="290" fill="url(#sweep)"/>'
                f'<rect x="-1" y="80" width="1" height="290" fill="{t["cyan"]}" opacity=".6"/>'
                f'<animateTransform attributeName="transform" type="translate" values="{wx} 0;{wx + ww + 60} 0" dur="7s" repeatCount="indefinite"/></g></g>')
    body.append(f'<rect x="{wx}" y="80" width="{ww}" height="290" fill="none" stroke="{t["panel_edge"]}"/>')
    body.append(f'<path d="M24 380H976" stroke="{t["panel_edge"]}"/>')
    body.append(text(48, 399, "generative waveforms · a visual metaphor for attention, not a measurement", 11, t["dim"], ls=.8, italic=True, cls="r"))
    lights = "".join(
        f'<circle cx="{906 + i * 16}" cy="395" r="3.2" fill="{c}"><animate attributeName="opacity" values="1;.2;1" dur="{1.2 + i * .5:.1f}s" begin="-{i * .4:.1f}s" repeatCount="indefinite"/></circle>'
        for i, c in enumerate([t["cyan"], t["warm"], t["pink"]])
    )
    body.append(text(890, 399, "RX", 11, t["dim"], anchor="end", ls=2) + lights)

    desc = ("Deep-space receiver with six conceptual research channels: research signal, space governance, technology, law, "
            "politics and data. Waveforms are generative visual metaphors, not measurements.")
    return open_svg(W, H, "Research signals · conceptual", desc) + f'<defs>{"".join(defs)}</defs>' + "".join(body) + "</svg>"


# --------------------------------------------------------------------------- #
# FOOTER
# --------------------------------------------------------------------------- #

def footer(t) -> str:
    W, H = 1000, 140
    dark = t["mode"] == "dark"
    rng = random.Random(5)
    arc = "M-20 150Q500 70 1020 150"
    defs = [GLOW, blur_filters(5),
            f'<linearGradient id="limb" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{t["cyan"]}" stop-opacity="0"/>'
            f'<stop offset=".5" stop-color="{t["cyan"]}"/><stop offset="1" stop-color="{t["lav"]}" stop-opacity="0"/></linearGradient>']
    body = [starfield(rng, 70, t["sky"]["stars"] if dark else t["ink_stars"], box=(0, 0, W, 105), o=(.15, .7), twinkle=.2)]
    body.append(f'<path d="{arc}" fill="none" stroke="url(#limb)" stroke-width="6" opacity=".35" {B(5)}/>'
                f'<path d="{arc}" fill="none" stroke="url(#limb)" stroke-width="1.2"/>')
    body.append(f'<g>{satellite(t["ink"], t["cyan"])}<animateMotion path="{arc}" dur="40s" rotate="auto" repeatCount="indefinite"/></g>')
    body.append(text(W / 2, 40, "RESEARCH · CODE · SCIENCE · SPACE · SOCIETY", 13.5, t["ink"], anchor="middle", ls=5))
    body.append(text(W / 2, 66, "Built with curiosity from Mexico · Open research over closed boxes", 15, t["dim"],
                     cls="r", anchor="middle", italic=True))
    return (open_svg(W, H, "Research · Code · Science · Space · Society",
                     "Built with curiosity from Mexico. Open research over closed boxes.")
            + f'<defs>{"".join(defs)}</defs>' + "".join(body) + "</svg>")


# --------------------------------------------------------------------------- #

def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    builders = {"hero": hero, "typing": typing, "whoami": whoami,
                "orbital-research": orbital, "telemetry": telemetry, "footer": footer}
    for name, fn in builders.items():
        for mode, theme in THEMES.items():
            out = ASSETS / f"{name}-{mode}.svg"
            out.write_text(fn(theme), encoding="utf-8")
            print(f"{out.relative_to(ROOT)}  {out.stat().st_size / 1024:6.1f} KB")


if __name__ == "__main__":
    main()
