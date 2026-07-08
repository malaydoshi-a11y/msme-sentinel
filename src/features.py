"""
MSME Sentinel — Feature Engineering
====================================

Three feature families:
  1. SNAPSHOT — current-month value of each alt-data + structured signal.
  2. TREND — 3/6/9-month rolling slope, volatility, min, and max of each
     signal, plus an acceleration term (change in slope vs. the prior
     window) so the model can tell a slowing decline from a worsening one,
     not just "up or down".
  3. INTERACTION — a small set of cross-signal terms for compounding stress
     patterns that don't show up in any single signal on its own (e.g. a
     GST inconsistency combined with rising overdraft use is a stronger
     signal than either alone).
"""

import numpy as np
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

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


def add_trend_features(df, signal_cols=SIGNAL_COLS, windows=(3, 6, 9)):
    df = df.sort_values(["borrower_id", "month"]).copy()
    g = df.groupby("borrower_id", sort=False)

    for col in signal_cols:
        slopes = {}
        for w in windows:
            roll = g[col].rolling(window=w, min_periods=max(2, w // 2))
            # slope proxy: (current - value w-months-ago) / w -> rate of change
            slope = g[col].transform(lambda s, w=w: (s - s.shift(w)) / w)
            slopes[w] = slope
            df[f"{col}_slope_{w}m"] = slope
            df[f"{col}_vol_{w}m"] = roll.std().reset_index(level=0, drop=True)
            df[f"{col}_avg_{w}m"] = roll.mean().reset_index(level=0, drop=True)
            df[f"{col}_min_{w}m"] = roll.min().reset_index(level=0, drop=True)
            df[f"{col}_max_{w}m"] = roll.max().reset_index(level=0, drop=True)

        # Acceleration: how much the slope itself has changed vs. the prior,
        # non-overlapping window of the same length -- distinguishes a decline
        # that's leveling off from one that's getting worse, which a slope
        # value alone can't tell apart.
        for w in windows:
            df[f"{col}_accel_{w}m"] = slopes[w] - slopes[w].groupby(df["borrower_id"]).shift(w)

    return df


def add_interaction_features(df):
    """
    Cross-signal terms for compounding stress patterns that a single signal
    won't capture on its own: GST inconsistency alongside rising overdraft
    use, or GST inconsistency alongside late filings, are each a stronger
    signal together than either is individually.
    """
    df["gst_stress_compound"] = (1 - df["gst_turnover_consistency_ratio"]) * (100 - df["gst_compliance_score"])
    df["liquidity_stress_compound"] = df["overdraft_utilization_pct"] * df["bounce_rate_pct"]
    return df


TREND_SUFFIXES = ("_slope", "_vol", "_avg", "_min", "_max", "_accel")
INTERACTION_COLS = ["gst_stress_compound", "liquidity_stress_compound"]


def build_feature_matrix(full_df):
    df = add_trend_features(full_df)
    df = add_interaction_features(df)

    # segment encodings (kept as categorical codes; tree models handle natively)
    for cat_col in ["loan_type", "business_type", "vintage_bucket", "borrower_category"]:
        df[f"{cat_col}_code"] = df[cat_col].astype("category").cat.codes

    feature_cols = (
        SIGNAL_COLS
        + [c for c in df.columns if any(c.startswith(s + suf) for s in SIGNAL_COLS for suf in TREND_SUFFIXES)]
        + INTERACTION_COLS
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
    full = pd.read_csv(DATA_DIR / "full_dataset.csv")
    df, feature_cols = build_feature_matrix(full)
    print(f"Total features: {len(feature_cols)}")
    print(feature_cols)
    df.to_parquet(DATA_DIR / "feature_matrix.parquet", index=False)
    print("Saved feature_matrix.parquet, shape:", df.shape)
