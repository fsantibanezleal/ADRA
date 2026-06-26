"""High-quality SVG figures for the ADRA docs.

Each builder draws one figure on an SvgBackend; build.py writes them to ../images/.
Reuses the shared primitives (svg_lib), icons and components — same visual language
as the deck (white page, dark gradient cards, iconography, soft shadows). No mermaid.
"""

from __future__ import annotations

import components as C
import icons
import theme as T
from svg_lib import SvgBackend


def _bg(bk, w, h):
    bk.rect(0, 0, w, h, fill=T.PAGE)
    g = bk.radialgrad(T.PURPLE, T.PURPLE, op0="0.07", op1="0")
    bk.oval(w - 10, 6, 180, grad=g)


def _caption(bk, x, y, text, accent=T.PURPLE):
    bk.rect(x, y, 6, 20, fill=accent, radius=3)
    bk.text(x + 16, y - 2, 900, 24, [(text, T.INK, True, False)], size=16, valign="middle")


def _chip(bk, x, y, w, h, label, accent, name=None):
    bk.rect(x, y, w, h, fill=T.CARD, line=accent, line_w=1.3, radius=10, shadow=True)
    tx = x + 14
    if name:
        C.icon_disc(bk, x + h / 2 + 2, y + h / 2, h / 2 - 7, name, accent)
        tx = x + h + 2
    bk.text(tx, y, w - (tx - x) - 10, h, [(label, T.WHITE, True, False)], size=12, valign="middle")


# =========================================================================
def loop(bk, W, H):
    _bg(bk, W, H)
    _caption(bk, 40, 40, "Adversarial loop — plan · ground · generate · critic · revise · decide")
    cy = 200
    stages = [("terminal", "Intake", T.MUTE), ("loop", "Plan", T.CYAN),
              ("gear", "Ground", T.BLUE), ("spark", "Generate", T.DPURPLE),
              ("shield", "Critic", T.RED)]
    xs = [120, 360, 600, 840, 1080]
    r = 44
    bk.line(120, cy, 1080, cy, color=T.STROKE, w=2, opacity=0.4)
    for i, (ic, t, acc) in enumerate(stages):
        C.icon_badge(bk, xs[i], cy, r, ic, acc)
        bk.text(xs[i] - 80, cy + 56, 160, 18, [(t, T.INK, True, False)], size=13.5,
                align="center", valign="middle")
        if i < 4:
            bk.arrow(xs[i] + r + 4, cy, xs[i + 1] - r - 4, cy, color=T.PURPLE, w=2.4)
    bk.arrow(xs[4], cy - r - 4, xs[3], cy - r - 4, color=T.AMBER, w=2.2, curve=0.34)
    bk.text(xs[3] - 30, cy - 112, xs[4] - xs[3] + 60, 16,
            [("revise ≤ max_rounds", T.AMBER, True, False)], size=11.5, align="center", valign="middle")
    oy = cy + 96
    C.pill(bk, 760, oy, 196, 46, "Accepted → artifacts", T.GREEN, name="check")
    C.pill(bk, 984, oy, 196, 46, "Escalate → human", T.RED, name="warning")
    bk.arrow(xs[4] - 16, cy + r, 858, oy - 3, color=T.GREEN, w=2.0)
    bk.arrow(xs[4] + 6, cy + r, 1082, oy - 3, color=T.RED, w=2.0)
    # grounding + provenance strip
    py = oy + 86
    g = bk.lineargrad(T.CARD2, T.CARD, vertical=True)
    bk.rect(40, py, 1200, 64, grad=g, line=T.STROKE, line_w=1.2, radius=12, shadow=True)
    bk.rect(40, py, 6, 64, fill=T.PURPLE, radius=3)
    C.icon_disc(bk, 86, py + 32, 18, "target", T.PURPLE)
    bk.text(118, py + 8, 1100, 22, [("Grounded on the shared rubric + client standards/ADRs", T.WHITE, True, False)],
            size=12.5, valign="middle")
    bk.text(118, py + 32, 1100, 22, [("deterministic tools are ground truth · every step logged to the immutable run record", T.MUTE, False, False)],
            size=11, valign="middle")


# =========================================================================
def module_map(bk, W, H):
    _bg(bk, W, H)
    _caption(bk, 40, 40, "Module interrelations")
    # surfaces
    bk.text(40, 86, 240, 18, [("SURFACES", T.MUTE2, True, False)], size=11, valign="middle", spacing="0.6")
    for i, (ic, lab, acc) in enumerate([("terminal", "CLIs / demo", T.GREEN)]):
        _chip(bk, 40, 112, 232, 56, lab, acc, ic)
    bk.arrow(160, 168, 160, 206, color=T.STROKE, w=2)
    # engine
    ex, ey, ew, eh = 40, 210, 760, 330
    bk.rect(ex, ey, ew, eh, fill="#F7F4FC", line=T.STROKE, line_w=1.4, radius=16)
    bk.text(ex + 18, ey + 14, 400, 20, [("ENGINE", T.DPURPLE, True, False)], size=12, valign="middle", spacing="0.6")
    eng = [("loop", "orchestrator", T.PURPLE), ("spark", "skills (6)", T.GREEN),
           ("shield", "critic", T.RED), ("scale", "judge", T.AMBER),
           ("target", "rubric", T.CYAN), ("brain", "llm + mock", T.DPURPLE),
           ("clock", "provenance", T.BLUE), ("doc", "state (model)", T.MUTE)]
    for i, (ic, lab, acc) in enumerate(eng):
        x = ex + 22 + (i % 4) * 184
        y = ey + 44 + (i // 4) * 130
        _chip(bk, x, y, 172, 56, lab, acc, ic)
    # tools
    bk.text(840, 86, 240, 18, [("DETERMINISTIC TOOLS", T.MUTE2, True, False)], size=11, valign="middle", spacing="0.6")
    tools = [("branch", "git_tools", T.BLUE), ("gauge", "ci_tools", T.CYAN), ("cube", "bundle_tools", T.PURPLE),
             ("globe", "lang_tools", T.AMBER), ("doc", "discovery_tools", T.RED), ("database", "sql_tools", T.GREEN)]
    for i, (ic, lab, acc) in enumerate(tools):
        _chip(bk, 840, 112 + i * 70, 400, 56, lab, acc, ic)
    bk.arrow(800, 300, 836, 300, color=T.STROKE, w=2)
    # client knowledge
    bk.rect(40, 560, 760, 132, fill=T.INK, line=T.STROKE, line_w=1.2, radius=14, shadow=True)
    C.icon_disc(bk, 80, 596, 17, "target", T.PURPLE)
    bk.text(108, 572, 660, 22, [("CLIENT KNOWLEDGE", T.WHITE, True, False)], size=12.5, valign="middle", spacing="0.5")
    bk.text(108, 600, 680, 22, [("standards/ (ADRs · conventions · cases)  ·  prompts/*.md", T.MUTE, False, False)], size=11.5, valign="middle")
    bk.text(108, 628, 680, 40, [("the rubric references standards by id; critic & skills load their prompts", T.BODY, False, False)], size=11, valign="top")
    bk.arrow(420, 558, 420, 542, color=T.STROKE, w=2)


# =========================================================================
def data_flow(bk, W, H):
    _bg(bk, W, H)
    _caption(bk, 40, 36, "Data flow — what crosses each boundary")
    steps = [("Intake", "dict", T.MUTE), ("ground", "ToolResult[]", T.BLUE),
             ("generate", "draft", T.DPURPLE), ("critic", "CriticVerdict", T.RED),
             ("decide", "artifacts", T.GREEN)]
    xs = [60, 300, 540, 780, 1020]
    y, w, h = 120, 200, 92
    for i, (t, payload, acc) in enumerate(steps):
        C.node(bk, xs[i], y, w, h, {"Intake": "terminal", "ground": "gear", "generate": "spark",
               "critic": "shield", "decide": "check"}[t], t, [payload], acc)
        if i < 4:
            bk.arrow(xs[i] + w + 2, y + h / 2, xs[i + 1] - 3, y + h / 2, color=T.PURPLE, w=2.4)
            bk.text(xs[i] + w - 20, y + h / 2 - 26, 80, 16,
                    [("→", T.MUTE2, False, False)], size=12, align="center", valign="middle")
    # provenance sink
    py = 290
    bk.rect(60, py, 1160, 60, fill=T.CARD2, line=T.STROKE, line_w=1.2, radius=12, shadow=True)
    C.icon_disc(bk, 100, py + 30, 17, "clock", T.PURPLE)
    bk.text(128, py + 6, 1080, 22, [("RunRecord (provenance)", T.WHITE, True, False)], size=12.5, valign="middle")
    bk.text(128, py + 30, 1080, 22, [("grounding evidence · critic verdicts · decision · artifacts — appended at every step", T.MUTE, False, False)], size=11, valign="middle")
    for x in xs:
        bk.line(x + w / 2, y + h, x + w / 2, py, color=T.STROKE, w=1.0, opacity=0.5)


# =========================================================================
def run_sequence(bk, W, H):
    _bg(bk, W, H)
    _caption(bk, 40, 36, "A run, step by step (pr_eval)")
    steps = [
        ("terminal", "Caller", "run(\"pr_eval\", intake)", T.MUTE),
        ("loop", "Orchestrator", "plan → select tools", T.PURPLE),
        ("gear", "Tools", "merge-base health · bundle validate · lang scan → ToolResult[]", T.BLUE),
        ("spark", "Skill", "generate verdict + PR body (a blocker forces changes-requested)", T.DPURPLE),
        ("shield", "Critic", "deterministic rubric + LLM attacks → CriticVerdict", T.RED),
        ("loop", "Loop", "revise → critic, until clean or max_rounds (else escalate)", T.AMBER),
        ("doc", "Finalize", "pr_verdict.md · pr_body.md", T.GREEN),
        ("clock", "Provenance", "write runs/<id>.json", T.CYAN),
    ]
    x, y, w, h, gap = 80, 96, 1120, 64, 14
    for i, (ic, who, what, acc) in enumerate(steps):
        yy = y + i * (h + gap)
        bk.rect(x, yy, w, h, fill=T.CARD, line=T.STROKE, line_w=1.1, radius=12, shadow=True)
        bk.rect(x, yy, 5, h, fill=acc, radius=2)
        bk.oval(x + 34, yy + h / 2, 13, fill=acc)
        bk.text(x + 34 - 13, yy, 26, h, [(str(i + 1), T.CARD, True, False)], size=12, align="center", valign="middle")
        C.icon_disc(bk, x + 80, yy + h / 2, 14, ic, acc)
        bk.text(x + 104, yy + 10, 180, 22, [(who, T.WHITE, True, False)], size=12.5, valign="middle")
        bk.text(x + 300, yy, w - 320, h, [(what, T.BODY, False, False)], size=11.5, valign="middle")
        if i < len(steps) - 1:
            bk.arrow(x + 34, yy + h, x + 34, yy + h + gap, color=T.STROKE, w=1.8)


# =========================================================================
def _class_box(bk, x, y, w, title, fields, accent):
    h = 40 + len(fields) * 20 + 10
    g = bk.lineargrad(T.CARD2, T.CARD, vertical=True)
    bk.rect(x, y, w, h, grad=g, line=accent, line_w=1.5, radius=12, shadow=True)
    bk.rect(x, y, w, 34, fill=accent, radius=12)
    bk.rect(x, y + 18, w, 16, fill=T.CARD)
    bk.text(x + 14, y + 6, w - 20, 24, [(title, T.WHITE, True, False)], size=12.5, valign="middle")
    for i, f in enumerate(fields):
        bk.text(x + 14, y + 40 + i * 20, w - 24, 18, [(f, T.BODY, False, False)], size=10.6, valign="middle")
    return h


def domain_model(bk, W, H):
    _bg(bk, W, H)
    _caption(bk, 40, 36, "Domain model — one typed contract")
    _class_box(bk, 60, 100, 210, "Severity «enum»", ["BLOCKER / MAJOR", "MINOR / NIT", "+ is_blocking"], T.AMBER)
    _class_box(bk, 60, 250, 250, "Finding", ["severity: Severity", "category · message", "location · evidence", "suggested_fix · source"], T.RED)
    _class_box(bk, 400, 110, 270, "ToolResult", ["tool · ran · reason", "findings: Finding[]", "data: dict", "+ blocking() · clean()"], T.BLUE)
    _class_box(bk, 400, 320, 270, "CriticVerdict", ["clean: bool", "blocking: Finding[]", "attacks_tried · notes", "+ messages()"], T.PURPLE)
    _class_box(bk, 760, 150, 290, "RunState", ["skill · intake · plan", "grounding: ToolResult[]", "draft · rounds · decision", "critic_history · artifacts"], T.DPURPLE)
    _class_box(bk, 760, 380, 290, "RunRecord", ["run_id · skill · steps[]", "final_decision", "artifacts (append-only JSON)"], T.CYAN)
    bk.arrow(310, 300, 398, 230, color=T.STROKE, w=1.6)   # Finding -> ToolResult
    bk.arrow(310, 330, 398, 380, color=T.STROKE, w=1.6)   # Finding -> CriticVerdict
    bk.arrow(672, 220, 758, 250, color=T.STROKE, w=1.6)   # ToolResult -> RunState
    bk.arrow(672, 380, 758, 320, color=T.STROKE, w=1.6)   # CriticVerdict -> RunState
    bk.arrow(900, 300, 900, 378, color=T.STROKE, w=1.6)   # RunState -> RunRecord
    bk.text(905, 330, 180, 18, [("mirrors", T.MUTE2, False, True)], size=10.5, valign="middle")


# =========================================================================
def capability_grounding(bk, W, H):
    _bg(bk, W, H)
    _caption(bk, 40, 36, "How a skill enforces criteria (code_review)")
    C.node(bk, 50, 150, 150, 90, "doc", "diff", ["the change set"], T.MUTE)
    tools = [("globe", "lang scan", T.AMBER), ("doc", "test discovery", T.RED), ("gauge", "exact CI cmd", T.CYAN)]
    for i, (ic, lab, acc) in enumerate(tools):
        _chip(bk, 280, 110 + i * 70, 250, 56, lab, acc, ic)
        bk.arrow(204, 195, 276, 138 + i * 70, color=T.STROKE, w=1.6)
    # grounding
    C.node(bk, 580, 150, 190, 90, "gear", "grounding", ["ToolResult[]", "findings + evidence"], T.BLUE)
    for i in range(3):
        bk.arrow(534, 138 + i * 70, 576, 195, color=T.STROKE, w=1.6)
    # generate + critic
    C.node(bk, 840, 108, 190, 84, "spark", "generate", ["semantic findings"], T.DPURPLE)
    C.node(bk, 840, 214, 190, 84, "shield", "critic", ["blocking gate"], T.RED)
    bk.arrow(774, 180, 836, 150, color=T.PURPLE, w=2)
    bk.arrow(774, 210, 836, 256, color=T.PURPLE, w=2)
    # output (inside canvas)
    C.pill(bk, 1086, 168, 168, 48, "review.md", T.GREEN, name="check")
    bk.arrow(1034, 150, 1082, 186, color=T.GREEN, w=2)
    bk.arrow(1034, 256, 1082, 198, color=T.GREEN, w=2)
    C.callout(bk, 50, 360, 1204, "Deterministic findings are tool-grounded truth; the model adds only what they cannot settle.",
              accent=T.PURPLE, name="target")


# =========================================================================
def rubric_sources(bk, W, H):
    _bg(bk, W, H)
    _caption(bk, 40, 36, "One shared rubric — single source for checks and prompts")
    C.icon_badge(bk, W / 2, 150, 40, "target", T.CYAN)
    bk.text(W / 2 - 180, 200, 360, 20, [("rubric.py — 17 criteria as data", T.INK, True, False)], size=14, align="center", valign="middle")
    bk.text(W / 2 - 220, 220, 440, 18, [("severity · category · kind · applies_to · method · incident", T.MUTE2, False, False)], size=10.5, align="center", valign="middle")
    C.node(bk, 120, 300, 460, 110, "gear", "Deterministic enforcement", ["critic.deterministic_attacks", "mechanical, blocking (kind = deterministic)"], T.BLUE)
    C.node(bk, 700, 300, 460, 110, "shield", "Prompt enforcement", ["rubric.prompt_block(skill) → critic prompt", "semantic attacks (kind = semantic)"], T.RED)
    bk.arrow(W / 2 - 60, 196, 350, 296, color=T.PURPLE, w=2.2)
    bk.arrow(W / 2 + 60, 196, 930, 296, color=T.PURPLE, w=2.2)
    bk.rect(360, 470, 560, 60, fill=T.INK, line=T.STROKE, line_w=1.2, radius=12, shadow=True)
    C.icon_disc(bk, 398, 500, 16, "doc", T.AMBER)
    bk.text(424, 478, 480, 22, [("client standards / ADRs · cases", T.WHITE, True, False)], size=12, valign="middle")
    bk.text(424, 502, 480, 22, [("each criterion references an ADR-xxxx / CASE-xxxx by id", T.MUTE, False, False)], size=10.5, valign="middle")
    bk.line(W / 2, 198, W / 2, 466, color=T.STROKE, w=1.4, opacity=0.6)


# =========================================================================
def history_layers(bk, W, H):
    _bg(bk, W, H)
    _caption(bk, 40, 36, "One run record → five layers of history")
    C.node(bk, 60, 150, 230, 120, "clock", "RunRecord", ["immutable JSON", "evidence · verdicts", "decision · artifacts"], T.PURPLE)
    layers = [("doc", "Functional", "what it does, per role", T.CYAN),
              ("gear", "Operational", "how it runs, state", T.BLUE),
              ("git_merge", "Change", "one per merged PR", T.GREEN),
              ("layers", "Architectural", "milestones / ADRs", T.AMBER),
              ("database", "Evidence", "raw, reproducible", T.RED)]
    for i, (ic, t, sub, acc) in enumerate(layers):
        y = 110 + i * 64
        _chip(bk, 520, y, 540, 52, f"{t} — {sub}", acc, ic)
        bk.arrow(296, 210, 514, y + 26, color=T.STROKE, w=1.5)


# =========================================================================
def extension_points(bk, W, H):
    _bg(bk, W, H)
    _caption(bk, 40, 36, "Extension points")
    rows = [("target", "New criterion", "add a RubricItem → semantic auto-injected; deterministic wires a check", T.CYAN),
            ("spark", "New capability", "Skill subclass + prompts/<skill>.md + register + Node", T.GREEN),
            ("gear", "New tool", "a function returning ToolResult, called from a skill's ground()", T.BLUE),
            ("doc", "New client", "replace standards/ + rubric incident refs — no code change", T.AMBER)]
    for i, (ic, t, d, acc) in enumerate(rows):
        y = 110 + i * 84
        bk.rect(60, y, 1140, 68, fill=T.CARD, line=acc, line_w=1.3, radius=12, shadow=True)
        C.icon_disc(bk, 98, y + 34, 16, ic, acc)
        bk.text(126, y + 10, 300, 24, [(t, T.WHITE, True, False)], size=13, valign="middle")
        bk.text(126, y + 36, 1040, 22, [(d, T.MUTE, False, False)], size=11.5, valign="middle")


FIGURES = {
    "loop": (loop, 1280, 540),
    "module_map": (module_map, 1280, 712),
    "data_flow": (data_flow, 1280, 380),
    "run_sequence": (run_sequence, 1280, 720),
    "domain_model": (domain_model, 1110, 560),
    "capability_grounding": (capability_grounding, 1280, 440),
    "rubric_sources": (rubric_sources, 1280, 560),
    "history_layers": (history_layers, 1100, 470),
    "extension_points": (extension_points, 1260, 460),
}


def render(name):
    fn, w, h = FIGURES[name]
    bk = SvgBackend()
    fn(bk, w, h)
    return bk.svg(w, h)
