"""
MSME Sentinel — Dashboard Data Export
=======================================
Selects a diverse, representative slice of borrowers (across RAG status,
loan type, and business type) and bundles portfolio summary + per-account
24-month trajectories + SHAP reason codes into a single dashboard_data.json
consumed by the static dashboard (no backend required).
"""

import json
import numpy as np
import pandas as pd
import xgboost as xgb
import shap

from features import build_feature_matrix

DATA_DIR = "/home/claude/msme-sentinel/data"

N_PER_BUCKET = {"RED": 16, "AMBER": 14, "GREEN": 12}  # latest-month status


def select_representative_borrowers(scored_full):
    latest = scored_full.sort_values("month").groupby("borrower_id").tail(1)
    picks = []
    for rag, n in N_PER_BUCKET.items():
        pool = latest[latest["rag_status"] == rag]
        pool = pool.sample(frac=1, random_state=7)
        picks.append(pool.head(n))
    chosen = pd.concat(picks)["borrower_id"].tolist()
    return chosen


def main():
    scored_full = pd.read_parquet(f"{DATA_DIR}/scored_full.parquet")
    full_raw = pd.read_csv(f"{DATA_DIR}/full_dataset.csv")
    with open(f"{DATA_DIR}/metrics.json") as f:
        metrics = json.load(f)
    with open(f"{DATA_DIR}/rag_distribution.json") as f:
        rag_dist = json.load(f)

    borrower_ids = select_representative_borrowers(scored_full)

    model = xgb.XGBClassifier()
    model.load_model(f"{DATA_DIR}/xgb_model.json")

    df_feat, feature_cols = build_feature_matrix(full_raw)
    df_feat = df_feat.dropna(subset=[c for c in feature_cols if "_6m" in c], how="all").fillna(0)

    latest_rows = df_feat[df_feat["borrower_id"].isin(borrower_ids)].sort_values("month").groupby("borrower_id").tail(1)
    score_cols = scored_full[["borrower_id", "month", "rag_status", "msme_rank", "risk_index", "pd_probability"]]
    latest_rows = latest_rows.merge(score_cols, on=["borrower_id", "month"], how="left")
    X_latest = latest_rows[feature_cols]

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_latest)

    risk_labels = {
        "gst_turnover_consistency_ratio": "GSTR-1 vs GSTR-3B turnover gap widening",
        "gst_compliance_score": "Deteriorating GST filing compliance",
        "upi_cashflow_volatility": "Volatile UPI/cash-flow pattern",
        "utility_payment_ontime_pct": "Utility payment delays",
        "epfo_contribution_regularity_pct": "Irregular EPFO contributions",
        "avg_monthly_inflow_lakhs": "Declining account inflows",
        "overdraft_utilization_pct": "High overdraft utilization",
        "bounce_rate_pct": "Rising cheque/NACH bounce rate",
        "bureau_score": "Weak bureau/credit history",
    }
    protective_labels = {
        "gst_turnover_consistency_ratio": "Consistent GSTR-1 / GSTR-3B turnover",
        "gst_compliance_score": "Strong GST filing compliance",
        "upi_cashflow_volatility": "Stable UPI/cash-flow pattern",
        "utility_payment_ontime_pct": "Strong utility payment discipline",
        "epfo_contribution_regularity_pct": "Regular EPFO contributions",
        "avg_monthly_inflow_lakhs": "Healthy, steady account inflows",
        "overdraft_utilization_pct": "Low overdraft utilization",
        "bounce_rate_pct": "Negligible cheque/NACH bounces",
        "bureau_score": "Strong bureau/credit history",
    }

    def top_reasons(row_shap, rag_status, epfo_missing_flag, k=3):
        pairs = sorted(zip(feature_cols, row_shap), key=lambda x: -abs(x[1]))
        want_positive = rag_status in ("RED", "AMBER")
        labels_map = risk_labels if want_positive else protective_labels
        reasons = []
        for name, val in pairs:
            if epfo_missing_flag and name.startswith("epfo_contribution_regularity_pct"):
                continue
            if want_positive and val <= 0:
                continue
            if (not want_positive) and val >= 0:
                continue
            base = name.split("_slope_")[0].split("_vol_")[0].split("_avg_")[0]
            label = labels_map.get(base)
            if label and label not in reasons:
                reasons.append(label)
            if len(reasons) == k:
                break
        if reasons:
            return reasons
        return ["Mixed signals -- no single dominant driver"] if want_positive else ["Broadly stable across monitored indicators"]

    latest_rows = latest_rows.reset_index(drop=True)
    latest_rows["top_reasons"] = [
        top_reasons(shap_values[i], latest_rows.loc[i, "rag_status"], bool(latest_rows.loc[i, "epfo_missing"]))
        for i in range(len(latest_rows))
    ]

    accounts = []
    for bid in borrower_ids:
        meta = latest_rows[latest_rows["borrower_id"] == bid].iloc[0]
        trend = scored_full[scored_full["borrower_id"] == bid].sort_values("month")
        accounts.append({
            "borrower_id": bid,
            "loan_type": meta["loan_type"],
            "business_type": meta["business_type"],
            "vintage_bucket": meta["vintage_bucket"],
            "borrower_category": meta["borrower_category"],
            "loan_amount_lakhs": float(meta["loan_amount_lakhs"]),
            "latest_rank": int(meta["msme_rank"]),
            "latest_risk_index": round(float(meta["risk_index"]), 1),
            "latest_pd": round(float(meta["pd_probability"]), 4),
            "rag_status": meta["rag_status"],
            "top_reasons": meta["top_reasons"],
            "will_default_in_horizon": int(meta["will_default_in_horizon"]),
            "trend": [
                {
                    "month": int(r["month"]),
                    "rank": int(r["msme_rank"]),
                    "risk_index": round(float(r["risk_index"]), 1),
                    "pd": round(float(r["pd_probability"]), 4),
                    "rag": r["rag_status"],
                    "gst_consistency": round(float(r["gst_turnover_consistency_ratio"]), 3),
                    "gst_compliance": round(float(r["gst_compliance_score"]), 1),
                    "upi_volatility": round(float(r["upi_cashflow_volatility"]), 3),
                    "utility_ontime": round(float(r["utility_payment_ontime_pct"]), 1),
                    "overdraft_util": round(float(r["overdraft_utilization_pct"]), 1),
                }
                for _, r in trend.iterrows()
            ],
        })

    latest_all = scored_full.sort_values("month").groupby("borrower_id").tail(1)
    rank_counts = latest_all["msme_rank"].value_counts().reindex(range(1, 11), fill_value=0)
    rank_histogram = [{"rank": int(r), "count": int(rank_counts[r])} for r in range(1, 11)]

    bundle = {
        "portfolio": {
            "total_accounts": int(latest_all.shape[0]),
            "rag_distribution": rag_dist,
            "rank_histogram": rank_histogram,
            "model_metrics": metrics,
        },
        "accounts": accounts,
    }

    with open("/home/claude/msme-sentinel/dashboard/data.json", "w") as f:
        json.dump(bundle, f, indent=2)

    print(f"Exported {len(accounts)} accounts to dashboard/data.json")
    print(f"Portfolio total_accounts: {bundle['portfolio']['total_accounts']}")


if __name__ == "__main__":
    main()
