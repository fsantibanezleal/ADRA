"""Skill registry.

Maps skill name -> instance. The orchestrator dispatches on this registry, so
adding a capability is just adding a :class:`~adra.skills.base.Skill` here.
"""

from adra.skills.code_review import CodeReviewSkill
from adra.skills.decide import DecideSkill
from adra.skills.document import DocumentSkill
from adra.skills.experiment import ExperimentSkill
from adra.skills.improve import ImproveSkill
from adra.skills.pr_eval import PrEvalSkill

SKILLS = {
    s.name: s
    for s in (
        CodeReviewSkill(),
        PrEvalSkill(),
        ExperimentSkill(),
        ImproveSkill(),
        DocumentSkill(),
        DecideSkill(),
    )
}

__all__ = ["SKILLS"]
