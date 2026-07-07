"""
MSME Sentinel — Feature Engineering
====================================

Two feature families, deliberately:
  1. SNAPSHOT features — current-month values of each alt-data + structured signal.
  2. TREND features — 3-month and 6-month rolling slope/volatility of each signal.

The trend features are the whole point of this solution. A single bad month
of GST filing delay means little. A *worsening slope* across 3-6 months is
the actual early-warning signal a 12-month-ahead system should be built on.
This is what separates us from a generic "classify this row" default model.
"""

import numpy as np
import pandas as pd

SIGNAL_COLS = [
    "gst_turnover_consistency_ratio",
    "gst_compliance_score",
    "upi_cashflow_volatility",
    "utility_payment_ontime_pct",
    "epfo_contribution_regularity_pct",
    "avg_monthly_inflow_lakhs",
    "overdraft_utilization_pct",
    "bounce_rate_pct",
]

STRUCTURED_COLS = [
    "loan_amount_lakhs",
    "owner_age",
    "gst_registered",
    "existing_credit_lines",
    "bureau_score",
]


def add_trend_features(df, signal_cols=SIGNAL_COLS, windows=(3, 6)):
    df = df.sort_values(["borrower_id", "month"]).copy()
    g = df.groupby("borrower_id", sort=False)

    for col in signal_cols:
        for w in windows:
            roll = g[col].rolling(window=w, min_periods=max(2, w // 2))
            # slope proxy: (current - value w-months-ago) / w  -> rate of change
            df[f"{col}_slope_{w}m"] = g[col].transform(
                lambda s, w=w: (s - s.shift(w)) / w
            )
            df[f"{col}_vol_{w}m"] = roll.std().reset_index(level=0, drop=True)
            df[f"{col}_avg_{w}m"] = roll.mean().reset_index(level=0, drop=True)

    return df


def build_feature_matrix(full_df):
    df = add_trend_features(full_df)

    # segment encodings (kept as categorical codes; tree models handle natively)
    for cat_col in ["loan_type", "business_type", "vintage_bucket", "borrower_category"]:
        df[f"{cat_col}_code"] = df[cat_col].astype("category").cat.codes

    feature_cols = (
        SIGNAL_COLS
        + [c for c in df.columns if any(c.startswith(s + "_slope") or c.startswith(s + "_vol") or c.startswith(s + "_avg") for s in SIGNAL_COLS)]
        + STRUCTURED_COLS
        + [f"{c}_code" for c in ["loan_type", "business_type", "vintage_bucket", "borrower_category"]]
    )

    # NTC borrowers have NaN bureau_score by design -> fill with a flag + median
    df["bureau_score_missing"] = df["bureau_score"].isna().astype(int)
    df["bureau_score"] = df["bureau_score"].fillna(df["bureau_score"].median())
    if "bureau_score_missing" not in feature_cols:
        feature_cols.append("bureau_score_missing")

    # Borrowers with no EPFO exposure (no registered employees) have NaN
    # across every epfo_* column, including the derived trend features.
    # Filling with 0 would wrongly read as "0% contribution regularity" --
    # maximum apparent risk -- which unfairly penalizes sole proprietorships
    # that simply have no EPFO account at all. Fill with the NEUTRAL median
    # of borrowers who DO have exposure instead, and let a missing-flag
    # carry the "no EPFO data" signal explicitly so the model can learn to
    # discount it rather than being misled by a fabricated bad number.
    epfo_cols = [c for c in feature_cols if c.startswith("epfo_contribution_regularity_pct")]
    df["epfo_missing"] = df["epfo_contribution_regularity_pct"].isna().astype(int)
    for col in epfo_cols:
        df[col] = df[col].fillna(df[col].median())
    if "epfo_missing" not in feature_cols:
        feature_cols.append("epfo_missing")

    return df, feature_cols


if __name__ == "__main__":
    full = pd.read_csv("/home/claude/msme-sentinel/data/full_dataset.csv")
    df, feature_cols = build_feature_matrix(full)
    print(f"Total features: {len(feature_cols)}")
    print(feature_cols)
    df.to_parquet("/home/claude/msme-sentinel/data/feature_matrix.parquet", index=False)
    print("Saved feature_matrix.parquet, shape:", df.shape)
