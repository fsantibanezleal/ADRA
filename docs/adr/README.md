# ADRA engine — Architecture Decision Records

These ADRs record the **engine's** architecture decisions (distinct from a *client's*
governance ADRs under `adra/clients/synthetic/<client>/adr/`). Each is grounded in the
deep-research dossier produced before the build.

| ADR | Decision |
|---|---|
| [ADR-0001](ADR-0001-deterministic-first-grounding.md) | Deterministic-first grounding — tools are ground truth |
| [ADR-0002](ADR-0002-hand-rolled-orchestrator.md) | Hand-rolled orchestrator, not an agent-framework runtime |
| [ADR-0003](ADR-0003-owned-chatmodel-seam.md) | ADRA-owned `ChatModel` seam + native-SDK providers (no LangChain) |
| [ADR-0004](ADR-0004-shared-typed-rubric.md) | One shared, typed rubric for all adversarial criteria |
| [ADR-0005](ADR-0005-blocking-critic-and-escalation.md) | Blocking critic + human escalation (never silent approval) |
| [ADR-0006](ADR-0006-immutable-provenance.md) | Immutable provenance run record |
| [ADR-0007](ADR-0007-client-agnostic-grounding.md) | Client-agnostic grounding; no client/domain in the engine |
| [ADR-0008](ADR-0008-connector-protocol-and-emulator.md) | Connector `Protocol` + offline emulator as a real backend |
| [ADR-0009](ADR-0009-two-repo-split-and-secrets.md) | Two-repo split + BYOK/vault secrets model |
