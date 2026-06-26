"""The emulator — a real, self-contained platform so the full ADRA flow runs offline
(no external dependency, not a toy): multi-industry synthetic pull requests (with planted,
deterministically-catchable flaws) and a seeded SQLite warehouse for experiments.

It implements the same connector Protocol as the real adapters, so skills/the console run
against it transparently. Add industries by appending to ``SYNTHETIC_PRS`` / ``SEED_SQL``.
"""

from __future__ import annotations

import sqlite3

from adra.connectors.base import Issue, PullRequest

# Synthetic PRs across industries. The fixtures (git_state / ci) reproduce real failure
# modes the deterministic floor catches even offline; the diffs are industry-flavored.
SYNTHETIC_PRS: dict[int, PullRequest] = {
    101: PullRequest(
        number=101, title="[fintech] payments: retry wrapper for settlement calls",
        source_branch="task/PAY-441/retry", target_branch="main",
        author="dev-fintech", url="emulator://fintech/pull/101",
        diff=(
            "+++ b/payments/settlement/py_retry_test.py\n"
            "+ # Co-Authored-By: Claude\n"
            "+ def settle(tx):\n"
            "+     try:\n"
            "+         return gateway.charge(tx)\n"
            "+     except Exception:\n"
            "+         pass  # swallow and continue\n"
        ),
        ci={"command": 'python -m coverage run -m unittest discover -s payments -p "test*.py"',
            "fixture": {"stdout": "Ran 0 tests in 0.000s\nNo data was collected", "returncode": 1}},
    ),
    102: PullRequest(
        number=102, title="[ecommerce] catalog: split current-state table build",
        source_branch="task/CAT-220/split", target_branch="main",
        author="dev-ecom", url="emulator://ecommerce/pull/102",
        diff="(stale-base diff — see git_state)",
        git_state={"behind": 8, "deletions": ["catalog/refined/nb-merch-scoring.py"],
                   "renames": ["R100\tcatalog/resources/bundle.resources.schemas.yml\t"
                               "catalog/resources/bundle.resources.schemas.yml.t"]},
        ci={"bundle_fixture": {"stdout": "Error: schema resource not found", "returncode": 1}},
    ),
    103: PullRequest(
        number=103, title="[healthtech] consent: add export endpoint",
        source_branch="task/CON-77/export", target_branch="main",
        author="dev-health", url="emulator://healthtech/pull/103",
        diff=(
            "+++ b/consent/api/export.py\n"
            "+ # esta funcion exporta sin validar el consentimiento\n"
            "+ def export(patient_id):\n"
            "+     return db.dump(patient_id)  # TODO: check consent flag\n"
        ),
        ci={"command": 'python -m coverage run -m unittest discover -s consent -p "test*.py"',
            "fixture": {"stdout": "Ran 3 tests in 0.10s\nOK\nTOTAL 81%", "returncode": 0}},
    ),
    104: PullRequest(
        number=104, title="[logistics] telemetry: widen route table schema",
        source_branch="task/TEL-310/widen", target_branch="main",
        author="dev-logistics", url="emulator://logistics/pull/104",
        diff=(
            "+++ b/telemetry/models/route.py\n"
            "+ # add a column consumed downstream\n"
            "+ route.add_column('eta_seconds', Integer)  # contract change\n"
        ),
        ci={"command": 'python -m coverage run -m unittest discover -s telemetry -p "test*.py"',
            "fixture": {"stdout": "Ran 6 tests in 0.20s\nOK\nTOTAL 92%", "returncode": 0}},
    ),
}

# Seeded warehouse: one small table per industry, queried by the experiment skill.
SEED_SQL = [
    "CREATE TABLE payments_settlement (id INTEGER, amount REAL, status TEXT)",
    "INSERT INTO payments_settlement VALUES (1,120.5,'ok'),(2,90.0,'ok'),(3,5.0,'failed')",
    "CREATE TABLE catalog_items (sku TEXT, price REAL, active INTEGER)",
    "INSERT INTO catalog_items VALUES ('A1',9.9,1),('A2',19.0,1),('A3',4.5,0)",
    "CREATE TABLE telemetry_routes (route_id INTEGER, eta_seconds INTEGER)",
    "INSERT INTO telemetry_routes VALUES (1,1800),(2,3600),(3,900)",
]


class EmulatorRepo:
    """A synthetic source-control surface implementing ``RepoProvider``."""

    name = "emulator"

    def list_pull_requests(self, state: str = "open") -> list[PullRequest]:
        return list(SYNTHETIC_PRS.values())

    def get_pull_request(self, number: int) -> PullRequest:
        if number not in SYNTHETIC_PRS:
            raise KeyError(f"emulator PR {number} not found; available: {sorted(SYNTHETIC_PRS)}")
        return SYNTHETIC_PRS[number]

    def create_issue(self, title: str, body: str) -> Issue:
        return Issue(number=9001, title=title, url="emulator://issues/9001")

    def comment_on_pull_request(self, number: int, body: str) -> str:
        return f"emulator://pull/{number}#comment"


class EmulatorData:
    """A real, seeded SQLite warehouse implementing ``DataProvider`` (read-only probes)."""

    name = "emulator"

    def __init__(self) -> None:
        self._conn = sqlite3.connect(":memory:")
        for stmt in SEED_SQL:
            self._conn.execute(stmt)
        self._conn.commit()

    def run_sql(self, sql: str) -> dict:
        cur = self._conn.execute(sql)
        rows = [list(r) for r in cur.fetchall()]
        cols = [d[0] for d in (cur.description or [])]
        return {"columns": cols, "rows": rows}
