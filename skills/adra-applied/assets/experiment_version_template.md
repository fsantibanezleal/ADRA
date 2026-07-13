<!-- Experiment version (probe) page. File name: vNN-<step>.md inside the experiment
     folder. One probe per page. English on disk; translate prose on publish. -->

# vNN — <step title>

> Closes: <what this iteration settles>

## Probe

```sql
-- 0N_<name>.sql — run on the shared warehouse (profile <dev|prod>, warehouse <id>)
<the exact SQL>
```

## Result

<table of the returned rows; cite the persisted run file runs/<NN>_<env>_<timestamp>.json>

| <col> | <col> |
|---|---|
| <...> | <...> |

## Reading

<what the rows show — only what they support; "unknown" where they do not>

## Secondary findings

| # | Finding | Severity | Type |
|---|---|---|---|
| 1 | <...> | <BLOCKER/MAJOR/MINOR> | <...> |

Next: [vNN+1 — <next step>](vNN+1-<next-step>.md)
