# NDP glossary

| Term | Meaning |
|---|---|
| NDP | Northwind Data Platform |
| Domain | A product area: `catalog`, `orders`, `payments`, `analytics` |
| UC | Unity Catalog (governance over catalogs / schemas / tables / volumes) |
| DAB | Databricks Asset Bundle (the deploy unit) |
| DLT | Delta Live Tables (declarative pipelines) |
| Medallion | `landing` → `trusted` → `refined` schema split |
| Warehouse | Shared serverless SQL warehouse for ad-hoc queries / experiments |
| SKU | Stock-keeping unit — a `catalog` product identifier |
| Threshold | A configurable decision target in `analytics` (e.g. a fraud-score cutoff) |
| Conversion | Order conversion rate (%) tracked in `analytics` |
| Forecast/risk output | `analytics` decision-support output — a likelihood/recommendation, not a guarantee |
| Data contract | The documented schema + semantics of a published UC table |
| Provenance run record | The immutable JSON ADRA writes per run (evidence + decisions) |
| Preflight | The 8-point access checklist before declaring "no access" (`adr/ADR-0005`) |
| Blast radius | The reach of a change (shared templates, cross-domain libs, prod data) |
