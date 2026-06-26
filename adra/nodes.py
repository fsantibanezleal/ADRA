"""Graph node identifiers.

Every LLM call is tagged with the node it serves. This makes the offline mock
deterministic (it answers per node) and keeps the generation/critic/judge call
sites explicit instead of passing around magic strings.
"""

from __future__ import annotations

from enum import Enum


class Node(str, Enum):
    PLAN = "plan"
    CODE_REVIEW = "code_review"
    PR_EVAL = "pr_eval"
    EXPERIMENT = "experiment"
    IMPROVE = "improve"
    DOCUMENT = "document"
    DECIDE = "decide"
    CRITIC = "critic"
    JUDGE = "judge"
