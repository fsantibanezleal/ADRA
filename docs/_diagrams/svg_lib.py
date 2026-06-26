"""High-quality SVG drawing backend for the ADRA deck.

Rich primitives: gradients, soft drop-shadows, vector paths, arcs — so diagrams
are real visual compositions (iconography + depth), not boxes with bullet lists.
The PPTX deck embeds the rendered SVGs, so this backend is the single visual source
of truth; it can use the full SVG feature set.

Coordinate space is the 1280x720 design space from theme.py.
"""

from __future__ import annotations

from html import escape

import theme as T


def esc(s) -> str:
    return escape(str(s), quote=True)


def wrap_text(text: str, maxchars: int) -> list[str]:
    out, cur = [], ""
    for word in str(text).split():
        if len(cur) + len(word) + 1 <= maxchars or not cur:
            cur = (cur + " " + word).strip()
        else:
            out.append(cur)
            cur = word
    if cur:
        out.append(cur)
    return out or [""]


class SvgBackend:
    """Accumulates SVG markup with gradients, shadows and paths."""

    def __init__(self):
        self.parts: list[str] = []
        self._defs: dict[str, str] = {}
        self._n = 0
        self._shadow()

    def _uid(self, prefix="d"):
        self._n += 1
        return f"{prefix}{self._n}"

    # -- defs -------------------------------------------------------------
    def _shadow(self):
        self._defs["softshadow"] = (
            '<filter id="softshadow" x="-30%" y="-30%" width="160%" height="160%">'
            '<feDropShadow dx="0" dy="4" stdDeviation="7" flood-color="#140C28" '
            'flood-opacity="0.30"/></filter>'
        )
        self._defs["glow"] = (
            '<filter id="glow" x="-50%" y="-50%" width="200%" height="200%">'
            '<feGaussianBlur stdDeviation="5" result="b"/>'
            '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>'
            '</filter>'
        )

    def lineargrad(self, c0, c1, vertical=False, name=None):
        gid = name or self._uid("lg")
        if gid in self._defs:
            return gid
        coords = 'x1="0" y1="0" x2="0" y2="1"' if vertical else 'x1="0" y1="0" x2="1" y2="0"'
        self._defs[gid] = (
            f'<linearGradient id="{gid}" {coords}>'
            f'<stop offset="0" stop-color="{c0}"/><stop offset="1" stop-color="{c1}"/>'
            f'</linearGradient>'
        )
        return gid

    def radialgrad(self, c0, c1, name=None, op0="1", op1="0"):
        gid = name or self._uid("rg")
        if gid in self._defs:
            return gid
        self._defs[gid] = (
            f'<radialGradient id="{gid}" cx="0.5" cy="0.4" r="0.7">'
            f'<stop offset="0" stop-color="{c0}" stop-opacity="{op0}"/>'
            f'<stop offset="1" stop-color="{c1}" stop-opacity="{op1}"/></radialGradient>'
        )
        return gid

    # -- primitives -------------------------------------------------------
    def _fill(self, fill, grad):
        if grad:
            return f'url(#{grad})'
        return fill if fill else "none"

    def rect(self, x, y, w, h, fill=None, line=None, line_w=1.0, radius=0.0,
             opacity=None, grad=None, shadow=False):
        st = f' stroke="{line}" stroke-width="{line_w}"' if line else ""
        op = f' opacity="{opacity}"' if opacity is not None else ""
        fl = ' filter="url(#softshadow)"' if shadow else ""
        self.parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
            f'rx="{radius:.1f}" ry="{radius:.1f}" fill="{self._fill(fill, grad)}"{st}{op}{fl}/>'
        )

    def oval(self, cx, cy, r, fill=None, line=None, line_w=1.0, grad=None, shadow=False,
             opacity=None):
        st = f' stroke="{line}" stroke-width="{line_w}"' if line else ""
        fl = ' filter="url(#softshadow)"' if shadow else ""
        op = f' opacity="{opacity}"' if opacity is not None else ""
        self.parts.append(
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" '
            f'fill="{self._fill(fill, grad)}"{st}{op}{fl}/>'
        )

    def line(self, x1, y1, x2, y2, color=T.HAIR, w=1.0, dash=None, cap="round", opacity=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        op = f' opacity="{opacity}"' if opacity is not None else ""
        self.parts.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{color}" stroke-width="{w}" stroke-linecap="{cap}"{d}{op}/>'
        )

    def path(self, d, fill=None, stroke=None, sw=1.0, grad=None, cap="round", join="round",
             opacity=None, shadow=False):
        st = f' stroke="{stroke}" stroke-width="{sw}" stroke-linecap="{cap}" stroke-linejoin="{join}"' if stroke else ""
        op = f' opacity="{opacity}"' if opacity is not None else ""
        fl = ' filter="url(#softshadow)"' if shadow else ""
        self.parts.append(f'<path d="{d}" fill="{self._fill(fill, grad)}"{st}{op}{fl}/>')

    def arrow(self, x1, y1, x2, y2, color=T.PURPLE, w=2.2, curve=0.0):
        """Straight (curve=0) or quadratic-curved arrow with a triangular head."""
        mk = self._uid("ar")
        self._defs[mk] = (
            f'<marker id="{mk}" markerWidth="9" markerHeight="9" refX="6" refY="3" '
            f'orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="{color}"/></marker>'
        )
        if curve:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            dx, dy = x2 - x1, y2 - y1
            cx, cy = mx - dy * curve, my + dx * curve
            self.parts.append(
                f'<path d="M{x1:.1f},{y1:.1f} Q{cx:.1f},{cy:.1f} {x2:.1f},{y2:.1f}" '
                f'fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="round" '
                f'marker-end="url(#{mk})"/>'
            )
        else:
            self.parts.append(
                f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                f'stroke="{color}" stroke-width="{w}" stroke-linecap="round" '
                f'marker-end="url(#{mk})"/>'
            )

    def _anchor(self, align):
        return {"left": "start", "center": "middle", "right": "end"}[align]

    def text(self, x, y, w, h, runs, size=14, align="left", valign="middle",
             spacing=None, italic=False):
        size = T.fs(size)
        anchor = self._anchor(align)
        tx = x if align == "left" else (x + w / 2 if align == "center" else x + w)
        ty = {"top": y + size, "middle": y + h / 2 + size * 0.34,
              "bottom": y + h - 2}[valign]
        ls = f' letter-spacing="{spacing}"' if spacing is not None else ""
        spans = []
        for (txt, col, bold, ital) in runs:
            fw = "700" if bold else "400"
            it = ' font-style="italic"' if (ital or italic) else ""
            spans.append(f'<tspan fill="{col}" font-weight="{fw}"{it}>{esc(txt)}</tspan>')
        self.parts.append(
            f'<text x="{tx:.1f}" y="{ty:.1f}" font-family="{T.FONT}" font-size="{size}" '
            f'text-anchor="{anchor}"{ls}>' + "".join(spans) + '</text>'
        )

    def paragraph(self, x, y, w, h, text, size=12, color=T.BODY, align="left",
                  valign="top", bold=False, line_spacing=1.34):
        size = T.fs(size)
        anchor = self._anchor(align)
        tx = x if align == "left" else (x + w / 2 if align == "center" else x + w)
        maxchars = max(6, int(w / (size * 0.55)))  # conservative: avoid Chromium overflow
        lines = wrap_text(text, maxchars)
        lh = size * line_spacing
        total = len(lines) * lh
        if valign == "middle":
            y0 = y + (h - total) / 2 + size * 0.9
        elif valign == "bottom":
            y0 = y + h - total + size * 0.9
        else:
            y0 = y + size
        fw = "700" if bold else "400"
        for i, ln in enumerate(lines):
            self.parts.append(
                f'<text x="{tx:.1f}" y="{y0 + i * lh:.1f}" font-family="{T.FONT}" '
                f'font-size="{size}" fill="{color}" font-weight="{fw}" '
                f'text-anchor="{anchor}">{esc(ln)}</text>'
            )
        return total

    def bullets(self, x, y, w, items, size=11.5, marker=T.CYAN, color=T.BODY, gap=7):
        cy = y
        for it in items:
            mc, txt = (it if isinstance(it, tuple) else (marker, it))
            self.oval(x + 3, cy + size * 0.5, 2.6, fill=mc)
            consumed = self.paragraph(x + 14, cy, w - 16, 100, txt, size=size, color=color)
            cy += consumed + gap
        return cy - y

    def svg(self, w: int = T.W, h: int = T.H) -> str:
        defs = "<defs>" + "".join(self._defs.values()) + "</defs>"
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
                f'width="{w}" height="{h}">' + defs + "".join(self.parts) + '</svg>')
