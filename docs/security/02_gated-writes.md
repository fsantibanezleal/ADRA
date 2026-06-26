# 02 · Gated writes & human gates

Every **write** ADRA can perform is gated twice: it needs `allow_external=True` (the engine gate)
**and** is meant to sit behind an **explicit human confirmation** in interactive use. ADRA prepares
evidence and a recommendation; a person commits the action (ADR-0005, ADR-0007).

Landing: [security.md](./security.md).

## The connector write gate

Both REST connectors guard writes with `_require_write()`:

```python
def _require_write(self):
    if not self.allow_external:
        raise PermissionError("write blocked: set allow_external=True (and confirm) to ...")
```

| Write | Connector | Endpoint |
|---|---|---|
| `create_issue(title, body)` | GitHub / Azure DevOps | `POST …/issues` / `POST …/wit/workitems/$Issue` |
| `comment_on_pull_request(number, body)` | GitHub / Azure DevOps | `POST …/issues/{n}/comments` / `POST …/pullrequests/{id}/threads` |

The emulator's writes are no-op stubs (returning `emulator://…`), so the offline path never touches
a real platform.

## The CLI's double gate

`adra github-review owner/repo PR# --post` writes a PR comment **only** when `--external` is also
passed. Without it, the CLI prints:

```
(--post needs --external to write to GitHub; skipped)
```

So the deliberate sequence to write is: review read-only → inspect the verdict → re-run with
`--external --post` (the human confirmation is the operator choosing to add those flags).

## What stays human-owned (the human gates)

| Action | Gate |
|---|---|
| Create / merge a PR, push | `allow_external` + explicit confirmation; never autonomous (ADR-0005) |
| Run the engine against a live repo/warehouse | `--external` (else dry-run) |
| Any decision-support **risk claim** | framed as likelihood/risk, never "detect/predict/guarantee" (`overclaim_language`, ADR-0007) |
| Choosing a route | `decide` produces options + a recommendation; `decision_owner` = **human** |
| An unresolved blocker | **escalates** to a human with evidence (never silent approval) |

This is the security face of [human escalation](../methodologies/05_human-escalation.md): the
agent's job is to surface a defensible recommendation; the consequential commit is a person's.

## Why (NIST AI RMF *manage*)

Keeping high-consequence actions human-owned and gating high-impact agent actions is exactly the
*manage/govern* posture of the NIST AI RMF GenAI Profile and the ToolEmu finding. The point of an
adversarial reviewer is to *refuse to act* when it can't prove safety — and to ask.

## What this IS and is NOT

- **IS** writes gated by an engine flag plus an operator confirmation, with high-consequence actions
  reserved for humans.
- **IS NOT** a system that opens PRs/pushes on its own. There is no autonomous write path.

## See also

- [01_read-only-default.md](./01_read-only-default.md) · [03_untrusted-content.md](./03_untrusted-content.md)
- [../frameworks/02_httpx/01_github.md](../frameworks/02_httpx/01_github.md) — the gated GitHub
  writes.
- [../adr/ADR-0005-blocking-critic-and-escalation.md](../adr/ADR-0005-blocking-critic-and-escalation.md)
