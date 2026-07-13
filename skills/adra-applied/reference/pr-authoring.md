# PR authoring — propose or comment

Comment on an existing PR, or open a new improvement PR. Discipline is ADR-0008
(minimum-functional, smallest reversible change) and the conventions (fixed PR
body, full-URL references, commit-pinned links, team labels).

## Contents

- Minimum-functional first
- Choosing the route (human-owned)
- The PR body
- Hygiene rules
- Commenting on an existing PR

## Minimum-functional first

- Include **only what advances the result**; prune filler even if copied from a
  team standard or template.
- Removing code requires **proof it is dead** (not collected by CI discovery,
  unreferenced) — show it, do not assert it.
- Prefer the **smallest reversible** diff and **name the rollback**.

## Choosing the route (human-owned)

When more than one route exists, present 2–4 candidates scored on effort, blast
radius, reversibility, risk, and precedent. Prefer the smallest-scope, reversible
route justified against a precedent or a measured gap. Record discarded routes with
their trade-off. Mark the decision **human-owned** — do not auto-decide a
high-consequence choice.

Assess **blast radius** explicitly: a change to a shared CI template or a
cross-domain library or prod data reaches every consumer — prefer the local route
unless the shared one is justified.

## The PR body

Use `assets/pr_body_template.md`. Fixed section order:

1. **Objective** — what the PR achieves, and the work item.
2. **Changes** — what changed, concretely.
3. **What is NOT touched** — the explicit non-scope.
4. **Validation** — the exact CI command output, and `bundle validate` = OK if
   `resources/` changed.
5. **Risks / mitigations.**
6. **Test plan.**
7. **Work Item** — the ticket id/link.

## Hygiene rules

- Reference another PR by its **full URL**, never a bare `#NNNN`.
- Use **commit-pinned** file links (`?version=GC<full-sha>`) so they survive the
  merge.
- Apply the owning team's **labels** before completing.
- A PR with any deterministic blocker is **not ready** — changes requested,
  regardless of opinion.
- Follow the repo's own PR template if it has one
  (`.azuredevops/pull_request_template*.md` or `.github/PULL_REQUEST_TEMPLATE*`);
  the section list above is the baseline, the repo template wins where it differs.

## Commenting on an existing PR

Ground first (run the Review phase), then post findings as a comment. The write is
gated: only with `--allow-external` and after the operator confirms. Draft the
comment body to a file, scan it with `lang_scan.py`, then:

```bash
gh pr comment <number|url> --repo <owner/repo> --body-file <file>      # GitHub
# Azure DevOps: az devops invoke (PR comment thread) — see connections.md
```

Never create, complete, or vote on a PR without an explicit human go-ahead.
