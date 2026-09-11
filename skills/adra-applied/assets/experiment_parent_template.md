<!-- Experiment parent page. File name: YYYYMMDD-<slug>.md with a sibling folder
     YYYYMMDD-<slug>/ of the same name. English on disk; translate prose + headings to
     the wiki's language on publish (Spanish for this org's wiki). Keep dead-ends visible. -->

# <WI-id> · <problem in one line>

> <one-line statement of what this experiment sets out to confirm or refute>

- Start: <YYYY-MM-DD>
- Work item: <AB#NNNNN / full link>
- File under analysis: <repo/path/to/file.py>
- Output affected: <table / dashboard / job>
- Background: <cross-links to related experiments, if any>

## 1. Context and problem

<the central operational question, in bold>

## 2. Test-environment setup

- Profile: <dev | prod>   Warehouse: <id>
- Window: <date range>    Tables: <catalog.schema.table, ...>

## 3. Hypotheses

| # | Hypothesis | Probability | Impact if true | Probe | Verdict |
|---|-----------|-------------|----------------|-------|---------|
| H1 | <...> | High/Med/Low | <...> | `01_<name>.sql` | <confirmed / partial / discarded> |

## 4. Iteration itinerary

| Version | Focus | Status |
|---|---|---|
| v00 | context / plan | closed |
| v01 | <probe> | closed |
| v0X | synthesis | closed |

## 5. Design decisions

| Decision | Reason |
|---|---|
| <...> | <...> |

## 6. Non-goals

- <what this experiment explicitly does not address>

## 7. Status and next steps

- Decision: <draft / in progress / completed / discarded>
- PR: <full URL> · merged <time> · CD <status>

## References

- <official docs URLs, system tables, job ids, ADR ids, the wiki path>
