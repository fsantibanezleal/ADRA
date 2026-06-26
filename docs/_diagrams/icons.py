"""Line-art icon library (24x24 grid, scalable).

Each icon draws within the box [x, x+s] x [y, y+s] using the SvgBackend
primitives. Stroke-based, rounded — modern and legible at any size. These give the
diagrams real iconography instead of plain boxes.

Use via ``draw(bk, name, x, y, s, color)`` or the ICONS registry.
"""

from __future__ import annotations

import theme as T


def _sw(s):
    return max(1.4, s * 0.082)


def _xy(x, y, s, gx, gy):
    return x + gx * s / 24.0, y + gy * s / 24.0


def _poly(x, y, s, pts, close=False):
    d = "M" + " L".join(f"{x + a * s / 24:.2f},{y + b * s / 24:.2f}" for a, b in pts)
    return d + (" Z" if close else "")


# -- individual icons (col = stroke color) --------------------------------
def magnifier(bk, x, y, s, col):  # code review
    bk.oval(*_xy(x, y, s, 10, 10), 6 * s / 24, line=col, line_w=_sw(s))
    bk.line(*_xy(x, y, s, 14.5, 14.5), *_xy(x, y, s, 20, 20), color=col, w=_sw(s))


def git_merge(bk, x, y, s, col):  # pr eval
    w = _sw(s)
    bk.oval(*_xy(x, y, s, 6, 6), 2.6 * s / 24, line=col, line_w=w)
    bk.oval(*_xy(x, y, s, 6, 18), 2.6 * s / 24, line=col, line_w=w)
    bk.oval(*_xy(x, y, s, 18, 9), 2.6 * s / 24, line=col, line_w=w)
    bk.line(*_xy(x, y, s, 6, 8.6), *_xy(x, y, s, 6, 15.4), color=col, w=w)
    bk.path(_poly(x, y, s, [(6, 15), (6, 12), (15.4, 9.5)]), stroke=col, sw=w)


def flask(bk, x, y, s, col):  # experiment
    w = _sw(s)
    bk.path(_poly(x, y, s, [(9, 3), (9, 9), (4.5, 19), (19.5, 19), (15, 9), (15, 3)], True),
            stroke=col, sw=w)
    bk.line(*_xy(x, y, s, 8, 3), *_xy(x, y, s, 16, 3), color=col, w=w)
    bk.line(*_xy(x, y, s, 7, 14), *_xy(x, y, s, 17, 14), color=col, w=w)
    bk.oval(*_xy(x, y, s, 10.5, 16.5), 0.9 * s / 24, fill=col)
    bk.oval(*_xy(x, y, s, 13.5, 17.5), 0.7 * s / 24, fill=col)


def wrench(bk, x, y, s, col):  # improve (tune / sliders)
    w = _sw(s)
    for gy, knob in ((7, 16), (12, 8), (17, 14)):
        bk.line(*_xy(x, y, s, 4, gy), *_xy(x, y, s, 20, gy), color=col, w=w)
        bk.oval(*_xy(x, y, s, knob, gy), 2.3 * s / 24, fill=T.CARD, line=col, line_w=w)


def doc(bk, x, y, s, col):  # document
    w = _sw(s)
    bk.path(_poly(x, y, s, [(6, 3), (15, 3), (19, 7), (19, 21), (6, 21)], True), stroke=col, sw=w)
    bk.path(_poly(x, y, s, [(15, 3), (15, 7), (19, 7)]), stroke=col, sw=w)
    for gy in (11, 14, 17):
        bk.line(*_xy(x, y, s, 9, gy), *_xy(x, y, s, 16, gy), color=col, w=w * 0.8)


def shield(bk, x, y, s, col, fill=None):  # critic / guardrails
    w = _sw(s)
    bk.path(_poly(x, y, s, [(12, 2.5), (20, 6), (20, 12), (12, 21.5), (4, 12), (4, 6)], True),
            stroke=col, sw=w, fill=fill)


def scale(bk, x, y, s, col):  # judge (balance)
    w = _sw(s)
    bk.line(*_xy(x, y, s, 12, 4), *_xy(x, y, s, 12, 20), color=col, w=w)
    bk.line(*_xy(x, y, s, 5, 6.5), *_xy(x, y, s, 19, 6.5), color=col, w=w)
    bk.line(*_xy(x, y, s, 8, 20), *_xy(x, y, s, 16, 20), color=col, w=w)
    bk.oval(*_xy(x, y, s, 12, 5), 1.3 * s / 24, fill=col)
    for cxg in (5, 19):
        bk.path(f"M{x+(cxg-3)*s/24:.1f},{y+6.5*s/24:.1f} "
                f"A3,3 0 0 0 {x+(cxg+3)*s/24:.1f},{y+6.5*s/24:.1f}", stroke=col, sw=w)
        bk.line(*_xy(x, y, s, cxg, 6.5), *_xy(x, y, s, cxg - 3, 6.5), color=col, w=w * 0.7)
        bk.line(*_xy(x, y, s, cxg, 6.5), *_xy(x, y, s, cxg + 3, 6.5), color=col, w=w * 0.7)


def clock(bk, x, y, s, col):  # history / provenance
    w = _sw(s)
    bk.oval(*_xy(x, y, s, 12, 12), 8.5 * s / 24, line=col, line_w=w)
    bk.line(*_xy(x, y, s, 12, 12), *_xy(x, y, s, 12, 7), color=col, w=w)
    bk.line(*_xy(x, y, s, 12, 12), *_xy(x, y, s, 16, 13.5), color=col, w=w)


def gauge(bk, x, y, s, col):  # CI / exact command
    w = _sw(s)
    bk.path(f"M{x+4*s/24:.1f},{y+17*s/24:.1f} A8.5,8.5 0 0 1 {x+20*s/24:.1f},{y+17*s/24:.1f}",
            stroke=col, sw=w)
    bk.line(*_xy(x, y, s, 12, 17), *_xy(x, y, s, 16, 10.5), color=col, w=w)
    bk.oval(*_xy(x, y, s, 12, 17), 1.4 * s / 24, fill=col)


def cube(bk, x, y, s, col):  # bundle
    w = _sw(s)
    bk.path(_poly(x, y, s, [(12, 3), (20, 7.5), (20, 16.5), (12, 21), (4, 16.5), (4, 7.5)], True),
            stroke=col, sw=w)
    bk.path(_poly(x, y, s, [(4, 7.5), (12, 12), (20, 7.5)]), stroke=col, sw=w)
    bk.line(*_xy(x, y, s, 12, 12), *_xy(x, y, s, 12, 21), color=col, w=w)


def globe(bk, x, y, s, col):  # language
    w = _sw(s)
    bk.oval(*_xy(x, y, s, 12, 12), 8.5 * s / 24, line=col, line_w=w)
    bk.line(*_xy(x, y, s, 3.5, 12), *_xy(x, y, s, 20.5, 12), color=col, w=w * 0.8)
    bk.path(f"M{x+12*s/24:.1f},{y+3.5*s/24:.1f} A6,11 0 0 0 {x+12*s/24:.1f},{y+20.5*s/24:.1f}",
            stroke=col, sw=w * 0.8)
    bk.path(f"M{x+12*s/24:.1f},{y+3.5*s/24:.1f} A6,11 0 0 1 {x+12*s/24:.1f},{y+20.5*s/24:.1f}",
            stroke=col, sw=w * 0.8)


def database(bk, x, y, s, col):  # data / SQL probe
    w = _sw(s)
    bk.path(f"M{x+5*s/24:.1f},{y+6*s/24:.1f} A7,2.6 0 0 0 {x+19*s/24:.1f},{y+6*s/24:.1f}",
            stroke=col, sw=w)
    bk.path(f"M{x+5*s/24:.1f},{y+6*s/24:.1f} A7,2.6 0 0 1 {x+19*s/24:.1f},{y+6*s/24:.1f}",
            stroke=col, sw=w)
    for gy in (6, 12, 18):
        bk.path(f"M{x+5*s/24:.1f},{y+gy*s/24:.1f} A7,2.6 0 0 0 {x+19*s/24:.1f},{y+gy*s/24:.1f}",
                stroke=col, sw=w)
    bk.line(*_xy(x, y, s, 5, 6), *_xy(x, y, s, 5, 18), color=col, w=w)
    bk.line(*_xy(x, y, s, 19, 6), *_xy(x, y, s, 19, 18), color=col, w=w)


def brain(bk, x, y, s, col):  # agent core / reasoning (CPU chip)
    w = _sw(s)
    bk.rect(x + 6.5 * s / 24, y + 6.5 * s / 24, 11 * s / 24, 11 * s / 24, line=col, line_w=w,
            radius=2 * s / 24)
    bk.rect(x + 9.5 * s / 24, y + 9.5 * s / 24, 5 * s / 24, 5 * s / 24, line=col, line_w=w * 0.8,
            radius=1 * s / 24)
    for g in (9.5, 12, 14.5):  # pins
        bk.line(*_xy(x, y, s, g, 3.5), *_xy(x, y, s, g, 6.5), color=col, w=w)
        bk.line(*_xy(x, y, s, g, 17.5), *_xy(x, y, s, g, 20.5), color=col, w=w)
        bk.line(*_xy(x, y, s, 3.5, g), *_xy(x, y, s, 6.5, g), color=col, w=w)
        bk.line(*_xy(x, y, s, 17.5, g), *_xy(x, y, s, 20.5, g), color=col, w=w)


def funnel(bk, x, y, s, col):  # adversarial filter
    w = _sw(s)
    bk.path(_poly(x, y, s, [(4, 4), (20, 4), (14, 12), (14, 20), (10, 17.5), (10, 12)], True),
            stroke=col, sw=w)


def warning(bk, x, y, s, col, fill=None):  # warning / escalate
    w = _sw(s)
    bk.path(_poly(x, y, s, [(12, 3.5), (21, 19.5), (3, 19.5)], True), stroke=col, sw=w, fill=fill)
    bk.line(*_xy(x, y, s, 12, 9), *_xy(x, y, s, 12, 14.5), color=col, w=w)
    bk.oval(*_xy(x, y, s, 12, 17), 0.9 * s / 24, fill=col)


def check(bk, x, y, s, col):  # accepted
    bk.path(_poly(x, y, s, [(5, 12.5), (10, 18), (19, 6)]), stroke=col, sw=_sw(s) * 1.2)


def cross(bk, x, y, s, col):  # reject / escalate
    w = _sw(s) * 1.1
    bk.line(*_xy(x, y, s, 6, 6), *_xy(x, y, s, 18, 18), color=col, w=w)
    bk.line(*_xy(x, y, s, 18, 6), *_xy(x, y, s, 6, 18), color=col, w=w)


def gear(bk, x, y, s, col):  # tools / orchestration
    import math
    w = _sw(s)
    cx, cy = x + 12 * s / 24, y + 12 * s / 24
    rO, rI = 8 * s / 24, 5.2 * s / 24
    pts = []
    for k in range(8):
        a = math.radians(k * 45)
        a2 = math.radians(k * 45 + 22)
        pts.append((cx + rO * math.cos(a), cy + rO * math.sin(a)))
        pts.append((cx + rI * math.cos(a2), cy + rI * math.sin(a2)))
    d = "M" + " L".join(f"{px:.2f},{py:.2f}" for px, py in pts) + " Z"
    bk.path(d, stroke=col, sw=w)
    bk.oval(cx, cy, 2.4 * s / 24, line=col, line_w=w)


def layers(bk, x, y, s, col):  # stack
    w = _sw(s)
    for gy in (6, 11, 16):
        bk.path(_poly(x, y, s, [(12, gy - 3), (20, gy), (12, gy + 3), (4, gy)], True),
                stroke=col, sw=w)


def terminal(bk, x, y, s, col):  # surfaces / CLI
    w = _sw(s)
    bk.rect(x + 3.5 * s / 24, y + 5 * s / 24, 17 * s / 24, 14 * s / 24, line=col, line_w=w,
            radius=2 * s / 24)
    bk.path(_poly(x, y, s, [(7, 10), (10, 12.5), (7, 15)]), stroke=col, sw=w)
    bk.line(*_xy(x, y, s, 12, 15.5), *_xy(x, y, s, 16, 15.5), color=col, w=w)


def branch(bk, x, y, s, col):  # git branch
    w = _sw(s)
    bk.oval(*_xy(x, y, s, 7, 5.5), 2.4 * s / 24, line=col, line_w=w)
    bk.oval(*_xy(x, y, s, 7, 18.5), 2.4 * s / 24, line=col, line_w=w)
    bk.oval(*_xy(x, y, s, 17, 8), 2.4 * s / 24, line=col, line_w=w)
    bk.line(*_xy(x, y, s, 7, 8), *_xy(x, y, s, 7, 16), color=col, w=w)
    bk.path(f"M{x+7*s/24:.1f},{y+16*s/24:.1f} q0,-6 {10*s/24:.1f},-6.5", stroke=col, sw=w)


def loop(bk, x, y, s, col):  # circular arrow (revise / shared loop)
    w = _sw(s)
    r = 7.5
    # ~270 deg arc as three quarter arcs: top -> right -> bottom -> left
    pts = [(12, 12 - r), (12 + r, 12), (12, 12 + r), (12 - r, 12)]
    abs_pts = [(_xy(x, y, s, a, b)) for a, b in pts]
    rr = r * s / 24
    d = (f"M{abs_pts[0][0]:.1f},{abs_pts[0][1]:.1f} "
         f"A{rr:.1f},{rr:.1f} 0 0 1 {abs_pts[1][0]:.1f},{abs_pts[1][1]:.1f} "
         f"A{rr:.1f},{rr:.1f} 0 0 1 {abs_pts[2][0]:.1f},{abs_pts[2][1]:.1f} "
         f"A{rr:.1f},{rr:.1f} 0 0 1 {abs_pts[3][0]:.1f},{abs_pts[3][1]:.1f}")
    bk.path(d, stroke=col, sw=w)
    bk.path(_poly(x, y, s, [(9, 2.5), (12, 4.5), (9.5, 7.5)]), stroke=col, sw=w)  # arrowhead at top


def lock(bk, x, y, s, col):  # secrets / access
    w = _sw(s)
    bk.rect(x + 5 * s / 24, y + 10 * s / 24, 14 * s / 24, 10 * s / 24, line=col, line_w=w,
            radius=2 * s / 24)
    bk.path(f"M{x+8*s/24:.1f},{y+10*s/24:.1f} v-2 a4,4 0 0 1 8,0 v2", stroke=col, sw=w)
    bk.oval(*_xy(x, y, s, 12, 15), 1.2 * s / 24, fill=col)


def trash(bk, x, y, s, col):  # deletions
    w = _sw(s)
    bk.line(*_xy(x, y, s, 5, 7), *_xy(x, y, s, 19, 7), color=col, w=w)
    bk.path(_poly(x, y, s, [(6.5, 7), (7.5, 20), (16.5, 20), (17.5, 7)]), stroke=col, sw=w)
    bk.path(_poly(x, y, s, [(9.5, 7), (9.5, 4.5), (14.5, 4.5), (14.5, 7)]), stroke=col, sw=w)


def target(bk, x, y, s, col):  # goal / standardize
    w = _sw(s)
    bk.oval(*_xy(x, y, s, 12, 12), 8.5 * s / 24, line=col, line_w=w)
    bk.oval(*_xy(x, y, s, 12, 12), 4.8 * s / 24, line=col, line_w=w)
    bk.oval(*_xy(x, y, s, 12, 12), 1.4 * s / 24, fill=col)


def quote(bk, x, y, s, col):  # unverified claim (speech bubble + !)
    w = _sw(s)
    bk.rect(x + 3.5 * s / 24, y + 4.5 * s / 24, 17 * s / 24, 12 * s / 24, line=col, line_w=w,
            radius=3 * s / 24)
    bk.path(_poly(x, y, s, [(8, 16.5), (8, 20.5), (12.5, 16.5)]), stroke=col, sw=w)
    bk.line(*_xy(x, y, s, 12, 7.5), *_xy(x, y, s, 12, 11.5), color=col, w=w)
    bk.oval(*_xy(x, y, s, 12, 13.7), 0.9 * s / 24, fill=col)


def spark(bk, x, y, s, col):  # spark / improvement
    w = _sw(s)
    bk.path(_poly(x, y, s, [(12, 3), (14, 10), (21, 12), (14, 14), (12, 21), (10, 14),
                            (3, 12), (10, 10)], True), stroke=col, sw=w)


ICONS = {
    "magnifier": magnifier, "git_merge": git_merge, "flask": flask, "wrench": wrench,
    "doc": doc, "shield": shield, "scale": scale, "clock": clock, "gauge": gauge,
    "cube": cube, "globe": globe, "database": database, "brain": brain, "funnel": funnel,
    "warning": warning, "check": check, "cross": cross, "gear": gear, "layers": layers,
    "terminal": terminal, "branch": branch, "loop": loop, "lock": lock, "trash": trash,
    "target": target, "quote": quote, "spark": spark,
}


def draw(bk, name, x, y, s, col=T.WHITE):
    ICONS[name](bk, x, y, s, col)
