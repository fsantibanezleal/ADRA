"""The rubric gained generic, hard-won review items distilled from real practice;
verify they are present and wired into the skill views and the prompt block."""

from __future__ import annotations

from adra import rubric

NEW_IDS = {
    "fixed_by_deletion", "over_deletion_regression", "feature_self_activates",
    "validated_config_mismatch", "premise_vs_prod", "aggressive_threshold_no_fallback",
    "driver_collect_oom", "temporary_exception_not_fix", "warm_cache_not_evidence",
    "conflicting_reference_values",
}


def test_new_items_present():
    for item_id in NEW_IDS:
        assert rubric.get(item_id).id == item_id


def test_pr_eval_includes_new_items():
    ids = {it.id for it in rubric.for_skill("pr_eval")}
    assert {"fixed_by_deletion", "over_deletion_regression", "feature_self_activates"} <= ids


def test_over_deletion_is_deterministic():
    det = {it.id for it in rubric.for_skill("pr_eval", "deterministic")}
    assert "over_deletion_regression" in det


def test_prompt_block_renders_a_new_item():
    assert "Over-deletion regression" in rubric.prompt_block("pr_eval")


def test_every_item_has_incident_and_method():
    for it in rubric.RUBRIC:
        assert it.incident and it.method  # each criterion is grounded and actionable
