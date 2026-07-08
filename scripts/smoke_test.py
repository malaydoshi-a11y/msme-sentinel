"""
Pre-deploy smoke test for the MSME Sentinel dashboard.

Asserts that dashboard/data.json exists, parses as valid JSON, and contains
a non-empty "accounts" array with the fields app.js depends on. Run this
before every deploy:

    python scripts/smoke_test.py
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = REPO_ROOT / "dashboard" / "data.json"

REQUIRED_ACCOUNT_FIELDS = [
    "borrower_id", "loan_type", "business_type", "vintage_bucket",
    "borrower_category", "loan_amount_lakhs", "latest_rank",
    "latest_pd", "rag_status", "top_reasons", "trend",
]
REQUIRED_PORTFOLIO_FIELDS = ["total_accounts", "rag_distribution", "rank_histogram", "model_metrics"]


def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)


def main():
    if not DATA_PATH.exists():
        fail(f"{DATA_PATH} does not exist")

    try:
        data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        fail(f"{DATA_PATH} is not valid JSON: {e}")

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

    print(f"OK: {DATA_PATH} valid, {len(data['accounts'])} accounts, portfolio fields present")


if __name__ == "__main__":
    main()
