"""
MSME Sentinel — Dashboard Data Export
=======================================
Exports the full 6,000-account scored portfolio to the static dashboard, in
two files so the initial page load stays fast:

  - dashboard/data.json    lightweight index for all 6,000 accounts (table,
                            tiles, spectrum, portfolio trend) -- small enough
                            to load instantly.
  - dashboard/details.json per-account trajectory + quantified reason codes,
                            fetched once and cached client-side the first
                            time any account is opened, not on initial load.

Also computes, per account:
  - rank_delta: change vs. last month, so the table can surface what's NEW
    rather than just current state.
  - est_runway_months: a disclosed, linear-extrapolation estimate of how many
    months remain at the current trend before the account crosses into the
    next-worse rank tier -- not a model prediction, a transparent heuristic
    on top of the model's own scored trajectory.
  - quantified reason codes: each SHAP-selected driver now carries the
    account's actual current value alongside its business-type segment
    average, not just a qualitative label.
"""

import json
import re
import numpy as np
import pandas as pd
import xgboost as xgb
import shap
from pathlib import Path

from features import build_feature_matrix
from ingestion import get_manifest as get_data_source_manifest, COLUMN_SOURCE, DATA_SOURCES

SOURCE_PHASE = {ds.key: ds.phase for ds in DATA_SOURCES}

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
DASHBOARD_DIR = REPO_ROOT / "dashboard"

TREND_SUFFIX_PATTERN = re.compile(r"_(slope|vol|avg|min|max|accel)_\d+m$")


def base_signal_name(feature_name):
    return TREND_SUFFIX_PATTERN.sub("", feature_name)


RISK_LABELS = {
    "gst_turnover_consistency_ratio": "GSTR-1 vs GSTR-3B turnover gap widening",
    "gst_compliance_score": "Deteriorating GST filing compliance",
    "upi_cashflow_volatility": "Volatile UPI/cash-flow pattern",
    "utility_payment_ontime_pct": "Utility payment delays",
    "epfo_contribution_regularity_pct": "Irregular EPFO contributions",
    "avg_monthly_inflow_lakhs": "Declining account inflows",
    "overdraft_utilization_pct": "High overdraft utilization",
    "bounce_rate_pct": "Rising cheque/NACH bounce rate",
    "bureau_score": "Weak bureau/credit history",
    "gst_stress_compound": "Compounding GST inconsistency and non-compliance",
    "liquidity_stress_compound": "Compounding overdraft and bounce-rate stress",
}
PROTECTIVE_LABELS = {
    "gst_turnover_consistency_ratio": "Consistent GSTR-1 / GSTR-3B turnover",
    "gst_compliance_score": "Strong GST filing compliance",
    "upi_cashflow_volatility": "Stable UPI/cash-flow pattern",
    "utility_payment_ontime_pct": "Strong utility payment discipline",
    "epfo_contribution_regularity_pct": "Regular EPFO contributions",
    "avg_monthly_inflow_lakhs": "Healthy, steady account inflows",
    "overdraft_utilization_pct": "Low overdraft utilization",
    "bounce_rate_pct": "Negligible cheque/NACH bounces",
    "bureau_score": "Strong bureau/credit history",
    "gst_stress_compound": "No compounding GST risk",
    "liquidity_stress_compound": "No compounding liquidity stress",
}

# label -> [(raw_col, format), ...] -- two entries for compound reasons, whose
# own numeric value isn't something a loan officer reads directly.
FMT_RATIO, FMT_PCT, FMT_LAKHS, FMT_SCORE = "ratio", "pct", "lakhs", "score"
REASON_METRICS = {
    "GSTR-1 vs GSTR-3B turnover gap widening": [("gst_turnover_consistency_ratio", FMT_RATIO)],
    "Consistent GSTR-1 / GSTR-3B turnover": [("gst_turnover_consistency_ratio", FMT_RATIO)],
    "Deteriorating GST filing compliance": [("gst_compliance_score", FMT_PCT)],
    "Strong GST filing compliance": [("gst_compliance_score", FMT_PCT)],
    "Volatile UPI/cash-flow pattern": [("upi_cashflow_volatility", FMT_RATIO)],
    "Stable UPI/cash-flow pattern": [("upi_cashflow_volatility", FMT_RATIO)],
    "Utility payment delays": [("utility_payment_ontime_pct", FMT_PCT)],
    "Strong utility payment discipline": [("utility_payment_ontime_pct", FMT_PCT)],
    "Irregular EPFO contributions": [("epfo_contribution_regularity_pct", FMT_PCT)],
    "Regular EPFO contributions": [("epfo_contribution_regularity_pct", FMT_PCT)],
    "Declining account inflows": [("avg_monthly_inflow_lakhs", FMT_LAKHS)],
    "Healthy, steady account inflows": [("avg_monthly_inflow_lakhs", FMT_LAKHS)],
    "High overdraft utilization": [("overdraft_utilization_pct", FMT_PCT)],
    "Low overdraft utilization": [("overdraft_utilization_pct", FMT_PCT)],
    "Rising cheque/NACH bounce rate": [("bounce_rate_pct", FMT_PCT)],
    "Negligible cheque/NACH bounces": [("bounce_rate_pct", FMT_PCT)],
    "Weak bureau/credit history": [("bureau_score", FMT_SCORE)],
    "Strong bureau/credit history": [("bureau_score", FMT_SCORE)],
    "Compounding GST inconsistency and non-compliance": [
        ("gst_turnover_consistency_ratio", FMT_RATIO), ("gst_compliance_score", FMT_PCT),
    ],
    "No compounding GST risk": [
        ("gst_turnover_consistency_ratio", FMT_RATIO), ("gst_compliance_score", FMT_PCT),
    ],
    "Compounding overdraft and bounce-rate stress": [
        ("overdraft_utilization_pct", FMT_PCT), ("bounce_rate_pct", FMT_PCT),
    ],
    "No compounding liquidity stress": [
        ("overdraft_utilization_pct", FMT_PCT), ("bounce_rate_pct", FMT_PCT),
    ],
}


def fmt_value(val, kind):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None
    if kind == FMT_RATIO:
        return round(float(val), 3)
    if kind == FMT_PCT:
        return round(float(val), 1)
    if kind == FMT_LAKHS:
        return round(float(val), 2)
    if kind == FMT_SCORE:
        return round(float(val))
    return round(float(val), 3)


def top_reasons(row_shap, feature_cols, rag_status, epfo_missing_flag, k=3):
    pairs = sorted(zip(feature_cols, row_shap), key=lambda x: -abs(x[1]))
    want_positive = rag_status in ("RED", "AMBER")
    labels_map = RISK_LABELS if want_positive else PROTECTIVE_LABELS
    reasons = []
    for name, val in pairs:
        base = base_signal_name(name)
        if epfo_missing_flag and base.startswith("epfo_contribution_regularity_pct"):
            continue
        if want_positive and val <= 0:
            continue
        if (not want_positive) and val >= 0:
            continue
        label = labels_map.get(base)
        if label and label not in reasons:
            reasons.append(label)
        if len(reasons) == k:
            break
    if reasons:
        return reasons
    return ["Mixed signals -- no single dominant driver"] if want_positive else ["Broadly stable across monitored indicators"]


# Signals whose own value 6-months-ago is available (present in
# scored_full.parquet's monthly panel), so the reason code can be compared
# against the account's OWN trajectory rather than a cross-sectional average.
TREND_COMPARABLE_COLS = {
    "gst_turnover_consistency_ratio", "gst_compliance_score", "upi_cashflow_volatility",
    "utility_payment_ontime_pct", "epfo_contribution_regularity_pct",
    "overdraft_utilization_pct", "bounce_rate_pct",
}

# True if a HIGHER raw value means healthier for that signal.
HIGHER_IS_BETTER = {
    "gst_turnover_consistency_ratio": True,
    "gst_compliance_score": True,
    "upi_cashflow_volatility": False,
    "utility_payment_ontime_pct": True,
    "epfo_contribution_regularity_pct": True,
    "avg_monthly_inflow_lakhs": True,
    "overdraft_utilization_pct": False,
    "bounce_rate_pct": False,
    "bureau_score": True,
}


def quantify_reasons(labels, borrower_row, segment_avgs, business_type, own_history, want_positive):
    """
    SHAP selects a reason by the model's joint, nonlinear marginal
    contribution -- not by whether a signal's raw value "looks good" in
    isolation. Attaching a comparison number that visibly contradicts the
    label (e.g. a "strong" reading that actually declined) would undermine
    trust rather than build it, so a baseline is only attached when its
    direction actually agrees with the label; otherwise the current value is
    shown on its own, with no unsupported comparison claim.
    """
    out = []
    seg_row = segment_avgs.loc[business_type] if business_type in segment_avgs.index else None
    for label in labels:
        metrics = REASON_METRICS.get(label, [])
        entry = {"label": label, "metrics": []}
        for raw_col, kind in metrics:
            val = borrower_row.get(raw_col)
            fval = fmt_value(val, kind)
            if fval is None:
                continue
            baseline, baseline_label = None, None
            if raw_col in TREND_COMPARABLE_COLS and own_history.get(raw_col) is not None:
                candidate, candidate_label = own_history[raw_col], "6 months ago"
            elif seg_row is not None and raw_col in seg_row.index:
                candidate, candidate_label = seg_row[raw_col], "segment avg"
            else:
                candidate, candidate_label = None, None

            if candidate is not None:
                higher_better = HIGHER_IS_BETTER.get(raw_col, True)
                improved = (val >= candidate) if higher_better else (val <= candidate)
                # want_positive=True means this is a RISK driver (expect val
                # to look worse than baseline); False means PROTECTIVE
                # (expect val to look at least as good as baseline)
                consistent = (not improved) if want_positive else improved
                if consistent:
                    baseline = fmt_value(candidate, kind)
                    baseline_label = candidate_label

            source_key = COLUMN_SOURCE.get(raw_col)
            entry["metrics"].append({
                "col": raw_col, "value": fval, "baseline": baseline,
                "baseline_label": baseline_label, "format": kind,
                "source_phase": SOURCE_PHASE.get(source_key),
            })
        out.append(entry)
    return out


def estimate_runway_months(pd_now, pd_6mo_ago, rank_now, cutpoints, window=6):
    """
    Linear extrapolation of the trailing PD slope to estimate how many months
    remain, at the current trend, before this account's probability of
    default would cross into the next-worse rank tier. A transparent
    heuristic on top of the model's own scored trajectory -- not a second
    model, not a guarantee. Returns None when the account is already at the
    worst rank, or when the trend isn't currently worsening.
    """
    if rank_now >= 10:
        return None
    if pd.isna(pd_now) or pd.isna(pd_6mo_ago):
        return None
    slope = (pd_now - pd_6mo_ago) / window
    if slope <= 1e-6:
        return None
    target = cutpoints[rank_now]  # boundary between current rank and rank+1
    if pd_now >= target:
        return 0.0
    months = (target - pd_now) / slope
    return months if np.isfinite(months) else None


def main():
    scored_full = pd.read_parquet(DATA_DIR / "scored_full.parquet")
    full_raw = pd.read_csv(DATA_DIR / "full_dataset.csv")
    with open(DATA_DIR / "metrics.json") as f:
        metrics = json.load(f)
    with open(DATA_DIR / "rank_cutpoints.json") as f:
        rank_cutpoints = json.load(f)

    model = xgb.XGBClassifier()
    model.load_model(DATA_DIR / "xgb_model.json")

    df_feat, feature_cols = build_feature_matrix(full_raw)
    df_feat = df_feat.dropna(subset=[c for c in feature_cols if "_9m" in c], how="all").fillna(0)

    latest_month = int(scored_full["month"].max())
    prev_month = latest_month - 6

    latest_rows = df_feat.sort_values("month").groupby("borrower_id").tail(1).reset_index(drop=True)
    score_cols = scored_full[["borrower_id", "month", "rag_status", "msme_rank", "risk_index", "pd_probability"]]
    latest_rows = latest_rows.merge(score_cols, on=["borrower_id", "month"], how="left")

    # previous-month rank (for "what changed") and 6-months-ago PD (for runway)
    prev_rank = scored_full[scored_full["month"] == latest_month - 1][["borrower_id", "msme_rank"]].rename(
        columns={"msme_rank": "prev_rank"})
    pd_6mo_ago = scored_full[scored_full["month"] == prev_month][["borrower_id", "pd_probability"]].rename(
        columns={"pd_probability": "pd_6mo_ago"})
    latest_rows = latest_rows.merge(prev_rank, on="borrower_id", how="left")
    latest_rows = latest_rows.merge(pd_6mo_ago, on="borrower_id", how="left")

    X_latest = latest_rows[feature_cols]
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_latest)

    latest_rows["top_reason_labels"] = [
        top_reasons(shap_values[i], feature_cols, latest_rows.loc[i, "rag_status"], bool(latest_rows.loc[i, "epfo_missing"]))
        for i in range(len(latest_rows))
    ]

    # business-type segment averages of each raw signal, at the latest month --
    # fallback comparison for signals with no own-history baseline available
    # (bureau_score, avg_monthly_inflow_lakhs)
    raw_latest = full_raw[full_raw["month"] == latest_month]
    segment_avgs = raw_latest.groupby("business_type")[
        ["gst_turnover_consistency_ratio", "gst_compliance_score", "upi_cashflow_volatility",
         "utility_payment_ontime_pct", "epfo_contribution_regularity_pct", "avg_monthly_inflow_lakhs",
         "overdraft_utilization_pct", "bounce_rate_pct", "bureau_score"]
    ].mean()

    # each account's own signal values 6 months ago, for the primary
    # "vs your own trajectory" comparison
    own_history_cols = [
        "gst_turnover_consistency_ratio", "gst_compliance_score", "upi_cashflow_volatility",
        "utility_payment_ontime_pct", "epfo_contribution_regularity_pct",
        "overdraft_utilization_pct", "bounce_rate_pct",
    ]
    own_history_df = scored_full[scored_full["month"] == prev_month].set_index("borrower_id")[own_history_cols]

    latest_rows["rank_delta"] = (latest_rows["msme_rank"] - latest_rows["prev_rank"]).fillna(0).astype(int)
    latest_rows["est_runway_months"] = [
        estimate_runway_months(
            latest_rows.loc[i, "pd_probability"], latest_rows.loc[i, "pd_6mo_ago"],
            int(latest_rows.loc[i, "msme_rank"]), rank_cutpoints,
        )
        for i in range(len(latest_rows))
    ]

    index_rows = []
    details = {}
    for i in range(len(latest_rows)):
        row = latest_rows.loc[i]
        bid = row["borrower_id"]
        runway = row["est_runway_months"]

        index_rows.append({
            "borrower_id": bid,
            "loan_type": row["loan_type"],
            "business_type": row["business_type"],
            "vintage_bucket": row["vintage_bucket"],
            "borrower_category": row["borrower_category"],
            "loan_amount_lakhs": round(float(row["loan_amount_lakhs"]), 1),
            "latest_rank": int(row["msme_rank"]),
            "latest_pd": round(float(row["pd_probability"]), 4),
            "rag_status": row["rag_status"],
            "rank_delta": int(row["rank_delta"]),
            "est_runway_months": round(float(runway), 1) if runway is not None and np.isfinite(runway) else None,
        })

        own_hist = own_history_df.loc[bid].to_dict() if bid in own_history_df.index else {}
        trend = scored_full[scored_full["borrower_id"] == bid].sort_values("month")
        details[bid] = {
            "top_reasons": quantify_reasons(
                row["top_reason_labels"], row, segment_avgs, row["business_type"], own_hist,
                want_positive=(row["rag_status"] in ("RED", "AMBER")),
            ),
            "trend": [
                {
                    "month": int(r["month"]),
                    "rank": int(r["msme_rank"]),
                    "risk_index": round(float(r["risk_index"]), 1),
                    "pd": round(float(r["pd_probability"]), 4),
                    "rag": r["rag_status"],
                }
                for _, r in trend.iterrows()
            ],
        }

    # portfolio-level RAG mix over time (all 6,000 accounts, every month) --
    # the visual evidence for "early warning system", not just a claim
    portfolio_trend = []
    for m in range(1, latest_month + 1):
        month_slice = scored_full[scored_full["month"] == m]
        dist = month_slice["rag_status"].value_counts(normalize=True)
        portfolio_trend.append({
            "month": m,
            "green_pct": round(float(dist.get("GREEN", 0.0)), 4),
            "amber_pct": round(float(dist.get("AMBER", 0.0)), 4),
            "red_pct": round(float(dist.get("RED", 0.0)), 4),
        })

    latest_all = scored_full.sort_values("month").groupby("borrower_id").tail(1)
    rank_counts = latest_all["msme_rank"].value_counts().reindex(range(1, 11), fill_value=0)
    rank_histogram = [{"rank": int(r), "count": int(rank_counts[r])} for r in range(1, 11)]
    # RAG mix as of the latest month only -- the same population every other
    # portfolio-level stat in this export uses. Averaging across the whole
    # 24-month panel (as an earlier version of this pipeline did) mixes in
    # much older, less representative months and visibly disagrees with the
    # rank histogram and account table, which are always "as of now".
    rag_dist = (latest_all["rag_status"].value_counts(normalize=True)).round(4).to_dict()

    bundle = {
        "portfolio": {
            "total_accounts": int(latest_all.shape[0]),
            "rag_distribution": rag_dist,
            "rank_histogram": rank_histogram,
            "model_metrics": metrics,
            "trend": portfolio_trend,
            "data_sources": get_data_source_manifest(),
        },
        "accounts": index_rows,
    }

    with open(DASHBOARD_DIR / "data.json", "w") as f:
        json.dump(bundle, f, separators=(",", ":"), allow_nan=False)
    with open(DASHBOARD_DIR / "details.json", "w") as f:
        json.dump(details, f, separators=(",", ":"), allow_nan=False)

    print(f"Exported {len(index_rows)} accounts to dashboard/data.json (index) and dashboard/details.json (lazy detail)")
    print(f"Portfolio total_accounts: {bundle['portfolio']['total_accounts']}")


if __name__ == "__main__":
    main()
