# NDP CI standards

The `ndp-ci` shared templates are the source of truth for "green". The agent must
reproduce the **exact** commands, never an approximation (see `adr/ADR-0001`).

## Unit tests + coverage (the exact command)

```bash
python -m coverage run -m unittest discover -s databricks -p "test*.py"
python -m coverage report --fail-under=80
```

- **Discovery pattern is `test*.py`** (prefix). A file named `*_test.py` (suffix) is
  **never collected** and is dead code (see `adr/ADR-0004`, `cases/CASE-2024-047`).
- A package without `__init__.py` is **not** recursed into by `unittest discover`.
- Product logic must be **importable, non-notebook** code (a plain `.py` outside
  `tests/`); notebooks are excluded from coverage and cannot be imported (they call
  `dbutils` / `spark` at module load).
- `Ran 0 tests` → coverage reports **"No data was collected"** → non-zero exit. This
  is a CI failure, not a warning.

## Bundle validation

```bash
databricks bundle validate -t <env>
```

Must print `Validation OK!`. Run it before any PR that touches `resources/` or the
bundle (see `adr/ADR-0003`).

## Experiments / ad-hoc data access

Experiments run against the **shared SQL warehouse**, never a fresh interactive
cluster (see `adr/ADR-0005`):

```bash
databricks api post /api/2.0/sql/statements --profile <prod|dev> --json '{...}'
```

Before concluding "no access" to a catalog, exhaust the 8-point preflight in
`adr/ADR-0005`.
