"""
Pre-deploy smoke test for the MSME Sentinel dashboard.

Asserts that dashboard/data.json (the account index) and dashboard/details.json
(lazy-loaded per-account trend + reason codes) exist, parse as valid JSON,
cover the same set of accounts, and contain the fields app.js depends on.
Run this before every deploy:

    python scripts/smoke_test.py
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = REPO_ROOT / "dashboard" / "data.json"
DETAILS_PATH = REPO_ROOT / "dashboard" / "details.json"

REQUIRED_ACCOUNT_FIELDS = [
    "borrower_id", "loan_type", "business_type", "vintage_bucket",
    "borrower_category", "loan_amount_lakhs", "latest_rank",
    "latest_pd", "rag_status", "rank_delta", "est_runway_months",
]
REQUIRED_PORTFOLIO_FIELDS = ["total_accounts", "rag_distribution", "rank_histogram", "model_metrics", "trend", "data_sources"]
REQUIRED_DETAIL_FIELDS = ["top_reasons", "trend"]


def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)


def main():
    for path in (DATA_PATH, DETAILS_PATH):
        if not path.exists():
            fail(f"{path} does not exist")

    try:
        data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        fail(f"{DATA_PATH} is not valid JSON: {e}")

    try:
        details = json.loads(DETAILS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        fail(f"{DETAILS_PATH} is not valid JSON: {e}")

    if "accounts" not in data or not isinstance(data["accounts"], list) or len(data["accounts"]) == 0:
        fail('"accounts" array is missing or empty')

    for field in REQUIRED_ACCOUNT_FIELDS:
        if field not in data["accounts"][0]:
            fail(f'account records are missing required field "{field}"')

    if "portfolio" not in data:
        fail('"portfolio" object is missing')

    for field in REQUIRED_PORTFOLIO_FIELDS:
        if field not in data["portfolio"]:
            fail(f'"portfolio" object is missing required field "{field}"')

    sources = data["portfolio"]["data_sources"]
    if not isinstance(sources, list) or len(sources) == 0:
        fail('"data_sources" is missing or empty')
    for ds in sources:
        if not all(k in ds for k in ("key", "label", "phase", "integration")):
            fail(f'data source entry missing required fields: {ds}')

    index_ids = {a["borrower_id"] for a in data["accounts"]}
    detail_ids = set(details.keys())
    if index_ids != detail_ids:
        fail(f"data.json and details.json cover different accounts ({len(index_ids)} vs {len(detail_ids)})")

    sample_id = next(iter(detail_ids))
    for field in REQUIRED_DETAIL_FIELDS:
        if field not in details[sample_id]:
            fail(f'detail records are missing required field "{field}"')

    print(f"OK: {len(data['accounts'])} accounts in data.json, matching detail records in details.json, portfolio fields present")


if __name__ == "__main__":
    main()
