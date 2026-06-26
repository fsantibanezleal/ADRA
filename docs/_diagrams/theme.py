"""Shared theme: palette + geometry for the ADRA deck.

Single source of truth for both renderers (svg_lib.py and pptx_native.py) so the
SVG deliverables and the native PowerPoint shapes never diverge. Palette matches
the Capacidades_AA / Workshop deck (white page, dark cards, purple/cyan).

Design space is 1280x720 (16:9); renderers map it onto a 10 x 5.62 in slide.
"""

# ---- palette -------------------------------------------------------------
PAGE = "#FFFFFF"     # slide background
INK = "#1B1430"      # near-black title on white
CARD = "#19152A"     # dark card fill
CARD2 = "#221C38"    # dark card fill (nodes)
STROKE = "#5B3D9E"   # purple card border
HAIR = "#352B53"     # inner hairline on dark cards
PURPLE = "#A100FF"
CYAN = "#00C2E8"
BLUE = "#2FA8D9"
DPURPLE = "#7A38D6"
GREEN = "#22C36B"
AMBER = "#FF9F2E"
RED = "#FF5C72"
WHITE = "#FFFFFF"
BODY = "#CBD0D9"     # body text on dark cards
MUTE = "#9AA0AC"     # muted text on dark cards
MUTE2 = "#6B7280"    # muted text on white page
FONT = "Segoe UI, Calibri, Arial, sans-serif"

W, H = 1280, 720

# Accent rotation used by multi-card components.
ACCENTS = [CYAN, BLUE, PURPLE, AMBER, GREEN]

# Legibility: bump small body/label text (titles >= FS_TITLE_MIN are left alone),
# applied uniformly by both renderers so the two deck versions stay in sync.
FS_BOOST = 1.20
FS_TITLE_MIN = 16.0


def fs(size):
    """Boost small text for on-screen legibility; leave large titles unchanged."""
    return round(size * FS_BOOST, 1) if size < FS_TITLE_MIN else size
