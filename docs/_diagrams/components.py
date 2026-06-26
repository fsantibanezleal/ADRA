"""Reusable, high-quality slide components.

Gradient fills, soft shadows and real icon badges — so slides read as designed
infographics, not boxes with bullet lists. All draw on the SvgBackend.
"""

from __future__ import annotations

import icons
import theme as T


# -- backdrop / chrome -----------------------------------------------------
def decor(bk):
    """White page + soft purple corner glow + dot-grid motif (top-right)."""
    bk.rect(0, 0, T.W, T.H, fill=T.PAGE)
    g = bk.radialgrad(T.PURPLE, T.PURPLE, op0="0.10", op1="0")
    bk.oval(1230, 20, 230, grad=g)
    g2 = bk.radialgrad(T.CYAN, T.CYAN, op0="0.06", op1="0")
    bk.oval(60, 700, 200, grad=g2)
    for r in range(4):
        for c in range(7):
            bk.oval(1052 + c * 28, 30 + r * 26, 2.6, line=T.PURPLE, line_w=1.0, opacity=0.5)


def header(bk, tag, title, right="", icon=None, accent=T.PURPLE):
    tw = max(176, len(tag) * 8.6 + 34)
    g = bk.lineargrad(T.PURPLE, T.DPURPLE)
    bk.rect(56, 34, tw, 27, grad=g, radius=13.5, shadow=True)
    bk.text(56, 34, tw, 27, [(tag, T.WHITE, True, False)], size=11.5, align="center",
            valign="middle", spacing="1.2")
    bk.text(54, 66, 1000, 46, [(title, T.INK, True, False)], size=30, valign="middle")
    gu = bk.lineargrad(T.PURPLE, T.CYAN)
    bk.rect(56, 114, 64, 4, grad=gu, radius=2)
    if icon:
        icon_badge(bk, 1168, 64, 30, icon, accent)
    if right:
        bk.text(640, 700, 584, 18, [(right, T.MUTE2, True, False)], size=11, align="right",
                valign="middle", spacing="0.4")


def cover(bk, title, subtitle, tagline, footer):
    bk.rect(0, 0, T.W, T.H, fill=T.PAGE)
    g = bk.radialgrad(T.PURPLE, T.PURPLE, op0="0.13", op1="0")
    bk.oval(1140, 120, 360, grad=g)
    g2 = bk.radialgrad(T.CYAN, T.CYAN, op0="0.10", op1="0")
    bk.oval(120, 660, 280, grad=g2)
    for r in range(6):
        for c in range(6):
            bk.oval(64 + c * 26, 60 + r * 26, 2.6, line=T.PURPLE, line_w=1.0, opacity=0.45)
    gp = bk.lineargrad(T.PURPLE, T.DPURPLE)
    bk.rect(110, 250, 250, 30, grad=gp, radius=15, shadow=True)
    bk.text(110, 250, 250, 30, [("AA CAPABILITIES · 2026", T.WHITE, True, False)],
            size=12, align="center", valign="middle", spacing="1.6")
    for i, ln in enumerate(str(title).split("\n")):
        bk.text(108, 292 + i * 60, 1080, 66, [(ln, T.INK, True, False)], size=53, valign="top")
    gu = bk.lineargrad(T.PURPLE, T.CYAN)
    bk.rect(112, 424, 92, 6, grad=gu, radius=3)
    bk.text(110, 444, 1040, 40, [(subtitle, T.DPURPLE, True, False)], size=20, valign="top")
    bk.text(110, 494, 1040, 60, [(tagline, T.MUTE2, False, True)], size=15, valign="top")
    # small icon row, hinting the five capabilities
    for i, ic in enumerate(["magnifier", "git_merge", "flask", "wrench", "doc"]):
        icon_badge(bk, 132 + i * 70, 600, 24, ic, T.ACCENTS[i % 5])
    bk.text(110, 690, 1080, 20, [(footer, T.MUTE2, True, False)], size=12, valign="middle")


def section_divider(bk, number, title, subtitle="", icon="loop"):
    bk.rect(0, 0, T.W, T.H, fill=T.INK)
    g = bk.radialgrad(T.PURPLE, T.PURPLE, op0="0.22", op1="0")
    bk.oval(1080, 130, 420, grad=g)
    g2 = bk.radialgrad(T.CYAN, T.CYAN, op0="0.12", op1="0")
    bk.oval(160, 640, 300, grad=g2)
    for r in range(5):
        for c in range(7):
            bk.oval(70 + c * 28, 70 + r * 28, 2.6, line=T.PURPLE, line_w=1.0, opacity=0.5)
    gp = bk.lineargrad(T.PURPLE, T.CYAN)
    bk.text(118, 300, 240, 120, [(number, "#FFFFFF", True, False)], size=120, valign="middle")
    bk.rect(124, 432, 78, 6, grad=gp, radius=3)
    bk.text(320, 300, 760, 90, [(title, T.WHITE, True, False)], size=43, valign="middle")
    if subtitle:
        bk.text(322, 412, 740, 50, [(subtitle, T.MUTE, False, True)], size=18, valign="top")
    icon_badge(bk, 1120, 360, 60, icon, T.PURPLE)


# -- building blocks -------------------------------------------------------
def icon_badge(bk, cx, cy, r, name, accent, ring=True):
    """Filled gradient disc with a centered white icon."""
    g = bk.lineargrad(accent, _mix(accent, T.CARD, 0.45), vertical=True)
    if ring:
        bk.oval(cx, cy, r + 3, fill=_mix(accent, T.PAGE, 0.18))
    bk.oval(cx, cy, r, grad=g, shadow=True)
    s = r * 1.15
    icons.draw(bk, name, cx - s / 2, cy - s / 2, s, col=T.WHITE)


def icon_disc(bk, cx, cy, r, name, accent):
    """Outlined disc (dark fill, accent ring) with accent icon — lighter weight."""
    bk.oval(cx, cy, r, fill=T.CARD2, line=accent, line_w=1.6)
    s = r * 1.1
    icons.draw(bk, name, cx - s / 2, cy - s / 2, s, col=accent)


def node(bk, x, y, w, h, name, title, sublines, accent):
    """Flow node: gradient dark card, icon badge, title + sub-lines."""
    g = bk.lineargrad(T.CARD2, T.CARD, vertical=True)
    bk.rect(x, y, w, h, grad=g, line=T.STROKE, line_w=1.1, radius=14, shadow=True)
    bk.rect(x, y, w, 4, fill=accent, radius=2)
    icon_disc(bk, x + 26, y + 30, 15, name, accent)
    bk.text(x + 48, y + 16, w - 56, 24, [(title, T.WHITE, True, False)], size=13.5, valign="middle")
    cy = y + 46
    for sline in sublines:
        bk.text(x + 16, cy, w - 24, 15, [(sline, T.MUTE, False, False)], size=10.6, valign="middle")
        cy += 15


def icon_card(bk, x, y, w, h, name, title, body, accent, sublines=None):
    """Card with a top icon badge + title + body paragraph (or bullet sublines)."""
    g = bk.lineargrad(T.CARD2, T.CARD, vertical=True)
    bk.rect(x, y, w, h, grad=g, line=T.STROKE, line_w=1.1, radius=16, shadow=True)
    bk.rect(x, y, w, 5, fill=accent, radius=2)
    icon_badge(bk, x + 40, y + 44, 22, name, accent)
    bk.text(x + 74, y + 24, w - 88, 40, [(title, T.WHITE, True, False)], size=15, valign="middle")
    bk.line(x + 22, y + 80, x + w - 22, y + 80, color=T.HAIR, w=1.0)
    if sublines:
        bk.bullets(x + 22, y + 94, w - 40, sublines, size=11.5, marker=accent)
    elif body:
        bk.paragraph(x + 22, y + 92, w - 44, h - 104, body, size=11.5, color=T.BODY)


def pill(bk, x, y, w, h, label, accent, name=None):
    bk.rect(x, y, w, h, fill=T.CARD, line=accent, line_w=1.5, radius=h / 2)
    tx = x + 16
    if name:
        icon_disc(bk, x + h / 2 + 2, y + h / 2, h / 2 - 5, name, accent)
        tx = x + h + 4
    bk.text(tx, y, w - (tx - x) - 12, h, [(label, T.WHITE, True, False)], size=12, valign="middle")


def callout(bk, x, y, w, label, accent=T.PURPLE, name="target", h=38):
    g = bk.lineargrad(_mix(accent, T.CARD, 0.30), T.CARD)
    bk.rect(x, y, w, h, grad=g, line=accent, line_w=1.5, radius=h / 2, shadow=True)
    icon_disc(bk, x + h / 2 + 3, y + h / 2, h / 2 - 6, name, accent)
    bk.text(x + h + 8, y, w - h - 22, h, [(label, T.WHITE, True, False)], size=12.5, valign="middle")


def stat(bk, x, y, w, h, big, small, accent, name=None):
    g = bk.lineargrad(T.CARD2, T.CARD, vertical=True)
    bk.rect(x, y, w, h, grad=g, line=accent, line_w=1.5, radius=14, shadow=True)
    if name:
        icon_disc(bk, x + w / 2, y + 26, 15, name, accent)
        ty = y + h * 0.46
    else:
        ty = y + 8
    bk.text(x, ty, w, h * 0.34, [(big, accent, True, False)], size=20, align="center", valign="middle")
    bk.text(x, y + h * 0.72, w, h * 0.26, [(small, T.BODY, False, False)], size=10.5,
            align="center", valign="middle")


# -- util ------------------------------------------------------------------
def _mix(fg, bg, t):
    fg, bg = fg.lstrip("#"), bg.lstrip("#")
    out = []
    for i in (0, 2, 4):
        out.append(int(round(int(fg[i:i+2], 16) * t + int(bg[i:i+2], 16) * (1 - t))))
    return "#%02X%02X%02X" % tuple(out)
