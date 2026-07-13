# Documentation — generated from provenance

Author documentation from the run record, not from memory (ADR-0006). Cite
evidence files and commit-pinned links. Everything English on disk / code / paths;
wiki prose in the team's wiki language; third person; no authoring-tool leak;
geoscience uses risk-pattern framing (ADR-0007).

## Contents

- What to produce
- The experiment page set
- PR change-control and methodology history
- The gap table
- Publishing recipe and the two-phase gate

## What to produce

- An **experiment page set** for each experiment.
- A **PR change-control page** for each merged PR.
- A **methodology-history** entry only for architectural milestones (contract /
  persistence / strategy / input changes).
- A **gap table** whenever a change makes existing docs stale.

## The experiment page set

Use the templates in `assets/`:

- `experiment_parent_template.md` — the dated parent page: work-item link,
  context, test-environment setup, the ranked hypothesis table, the iteration
  itinerary (one row per `vNN`, status), design-decisions table, non-goals, status
  + PR, references, metadata.
- `experiment_version_template.md` — one per `vNN` step: opens with a "Closes: …"
  line, one probe, tables/SVG, a link to the next.
- `experiment_synthesis_template.md` — the closing synthesis: integrate all
  dimensions, an actionable recommendation, pending items, and the PR. Mark any
  superseded recommendation as superseded — do not delete it.

Folder layout: a dated top page `YYYYMMDD-<slug>.md` plus a sibling folder
`YYYYMMDD-<slug>/` with the same name; sub-pages use clean `vNN-` slugs and never
repeat the date prefix. Each folder needs a sibling cover `.md` and an `.order`
file. `.order` rules: one line per child, no `.md` extension, no path, slug
matching the filename exactly. The experiments index `.order` is
reverse-chronological (prepend new experiments); the `vNN` `.order` inside an
experiment is forward-chronological.

## PR change-control and methodology history

The PR change-control page: `[[_TOC_]]`, a summary, commit-pinned file links
(`?path=...&version=GC<full-sha>` so links survive the merge), metadata, evidence
diffs, impacted contracts, and a validation checklist. Only architectural
milestones go in the methodology history.

## The gap table

Before closing a PR that makes docs stale, produce:

```
| wiki file | says today | should say | action |
|-----------|-----------|-----------|--------|
```

## Publishing recipe and the two-phase gate

- **Diagrams:** SVG preferred (one per finding), PNG only if SVG will not render,
  never plain boxes-and-text. Store binaries under the wiki's attachment root
  (configurable), never beside the `.md`; reference by absolute path from the wiki
  root, URL-encoding spaces/accents, exact casing; size with
  `<img src="..." width="600" />`.
- **Mermaid:** `:::mermaid` … `:::` (not fenced), node labels in double quotes,
  real line breaks.
- **Equations:** `$ x $` inline, `$$ … $$` block, `\begin{aligned} … \\ … \end{aligned}`.
- **Two-phase gate (never skip):** draft into a writable location (not the wiki);
  show the diff (`git diff --no-index`); wait for explicit approval; apply onto the
  wiki; review `git status`/`git diff` again; `git add <specific files>` (never
  `git add .` or `-A`); confirm the commit identity is the expected one; confirm
  the push; then `git commit` + `git push`. Never auto-push a shared wiki — a
  mistake there is visible to every product.

Run `scripts/lang_scan.py` over every page before it is staged.
