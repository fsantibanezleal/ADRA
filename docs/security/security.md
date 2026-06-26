# Security

ADRA's security model, grounded in the engine code and the relevant standards (NIST AI RMF, OWASP
LLM/Agentic Top-10, ToolEmu, the CaMeL dual-LLM pattern). The posture in one line: **deterministic
floor as ground truth · read-only by default · gated, human-confirmed writes · untrusted repo/PR
content handled as an attack surface · BYOK secrets never persisted or logged.**

## Read in order

1. [01_read-only-default.md](./01_read-only-default.md) — dry-run / read-only by default; the
   `allow_external` gate; why the LLM cannot overturn a deterministic blocker.
2. [02_gated-writes.md](./02_gated-writes.md) — every write (PR create/comment, issue, push, live
   CI / SQL) requires `allow_external` **and** explicit human confirmation; the human gates.
3. [03_untrusted-content.md](./03_untrusted-content.md) — the agent reads untrusted repo/PR/issue
   content; today the deterministic floor + read-only-by-default contain it, and a dual-LLM /
   capability split (CaMeL) + sandboxing + egress filtering are planned for the connector phase
   (not yet implemented; OWASP LLM/Agentic Top-10).
4. [04_secret-handling.md](./04_secret-handling.md) — BYOK, never stored/logged; the two-repo split
   (public engine vs private console); English-only + AI-authorship-leak scan on anything written.

## At a glance

| Control | Where | Default |
|---|---|---|
| Deterministic floor is ground truth (LLM can't overturn a blocker) | `critic.py`, `tools/*`, ADR-0001 | always on |
| Read-only / dry-run | `config.Settings.allow_external_calls`, every tool & connector | `False` |
| Writes gated | `_require_write()` (connectors), `allow_external` (tools) | blocked |
| Human gates on PR create/push/merge + risk claims | `decide` skill, escalation, ADR-0005/0007 | human-owned |
| English-only + AI-leak scan on disk-bound text | `lang_tools.scan_language`, rubric `language_leak` (BLOCKER) | always on |
| Immutable provenance per run | `provenance.py`, ADR-0006 | always on |
| Secrets BYOK, never persisted/logged | `config.py`, connectors, ADR-0009 | env only |

## What ADRA IS and is NOT (security)

- **IS** a tool whose verdicts have a hard, evidence-backed floor; whose default is to *read, not
  act*; and whose high-consequence actions are human-gated.
- **IS NOT** an autonomous agent with standing write access. There is no path from "the model
  decided" to a real PR/push/merge without `--external` + a human in the loop. The connected,
  key-holding instance is the **separate private console** (ADR-0009), never this public engine.

## References

NIST AI RMF — GenAI Profile (`AI 600-1`) · ToolEmu (`arXiv:2309.15817`) · Indirect Prompt
Injection (Greshake 2023, `arXiv:2302.12173`) · OWASP Top 10 for LLM Apps (2025) + Agentic Apps.
See [../../refs/README.md](../../refs/README.md) §5.

## See also

- [../methodologies/05_human-escalation.md](../methodologies/05_human-escalation.md) — what stays
  human-owned and why.
- [../adr/ADR-0009-two-repo-split-and-secrets.md](../adr/ADR-0009-two-repo-split-and-secrets.md)
- [../data-contract/04_missing-and-outlier-data.md](../data-contract/04_missing-and-outlier-data.md)
