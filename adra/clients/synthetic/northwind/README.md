# Northwind Data Platform — engineering standards (fictional client suite)

> **Fictional.** Northwind Trading and everything below are invented for this
> reference agent. They model a realistic governance baseline so ADRA has a concrete
> client to reason against, without referencing any real organization. Point the
> agent at a different client by replacing this `standards/` folder.

## Client profile

**Northwind Trading** — a fictional B2B commerce company. The **Northwind Data Platform
(NDP)** runs the analytics and decision-support products for four operating domains.

| Item | Value |
|---|---|
| Cloud / compute | Azure Databricks |
| Catalog / governance | Unity Catalog (UC) |
| Deploy unit | Databricks Asset Bundles (DAB) |
| Pipelines | Delta Live Tables (DLT) |
| Source control / CI | Azure DevOps — org `NorthwindNDP`, project `Data Platform`, shared CI templates `ndp-ci` |
| Integration branch | `main` |
| Work branches | `task/<NDP-ticket>/<slug>` |
| Tickets | `NDP-####` |
| Catalog naming | `<env>_<domain>_<subdomain>` (env ∈ `dev` / `preprod` / `prod`) |

### Domains

| Domain | Scope | Example catalog |
|---|---|---|
| `catalog` | Product catalog & merchandising | `prod_catalog_items` |
| `orders` | Order management & fulfilment | `prod_orders_fulfilment` |
| `payments` | Payments, billing & reconciliation | `prod_payments_ledger` |
| `analytics` | Demand/risk forecasting & decision support | `prod_analytics_forecast` |

## Index

- `conventions.md` — language, naming, branching, PR body, labels.
- `ci-standards.md` — the exact CI command, coverage, test discovery, bundle validate.
- `glossary.md` — domain and platform terms.
- `adr/` — Architecture Decision Records (`ADR-0001` … `ADR-0008`).
- `cases/` — anonymized post-incident notes the rubric is learned from (`CASE-*`).

These documents are the source of truth the ADRA agent grounds on. The adversarial
rubric (`adra/rubric.py`) references them by id, and the skill/critic prompts cite
them, so "what we check" lives in one place.
