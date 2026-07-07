<p align="center">
  <img src="dashboard/assets/idbi-bank-logo.svg" alt="IDBI Bank" height="56" />
  &nbsp;&nbsp;&nbsp;
  <img src="dashboard/assets/guardinger-logo.svg" alt="Guardinger Advanced Technologies" height="48" />
</p>

# MSME Sentinel
### An Early-Warning System for MSME Credit Stress
**IDBI Innovate 2026 — Track 04: MSME Credit Predictive AI Risk Management**
**A prototype for IDBI Bank, developed by Guardinger Advanced Technologies**

---

## The problem, as IDBI framed it

IDBI Bank's current MSME default-prediction capability sits at **16–22% accuracy**, relies solely on **structured data**, and uses fragmented methods across loan types and borrower segments. The bank wants a solution that flags potential stress **12 months in advance**, using both structured and unstructured/alternative data, with a consistent scoring framework across all MSME loans.

## Why we didn't just build "another classifier"

Every team in this track will submit a gradient-boosted binary classifier trained to predict default. That's necessary, but on its own it overclaims what a single-shot, point-in-time model can honestly deliver a full year out — MSME cash flows are volatile, and a naive high-accuracy claim on an imbalanced dataset is a well-known statistical trap (a model that always predicts "no default" can look >90% "accurate" while being useless — a risk explicitly raised, and acknowledged, in IDBI's own AMA session for this track).

**MSME Sentinel reframes the deliverable**: instead of a single binary prophecy, it is a continuously-updating **Early Warning System** that tracks each borrower's financial-health trajectory month over month, and flags *deteriorating trends* early enough for a loan officer to act — which is what "12 months in advance" is actually useful for.

## What it does

1. **Ingests** structured (bureau, financials, transactions) and alternative data (GST filing regularity, UPI/cash-flow volatility, utility payment consistency, EPFO contributions) — explicitly covering IDBI's New-to-Credit (thin-file) borrower case.
2. **Engineers trend features**, not just snapshots — 3- and 6-month rolling slopes and volatility per signal, because a deteriorating trend is the real early-warning signal, not a single bad month.
3. **Scores** each account with a segment-aware XGBoost ensemble, properly corrected for class imbalance (not optimized for a misleading raw-accuracy number).
4. **Calibrates** the raw probability into one common, comparable **CMR-style MSME Risk Rank (1–10)** — deliberately matching the real **CIBIL MSME Rank (CMR)** convention already used across Indian MSME lending for this exact exposure band and 12-month horizon, not the 300–900 scale used for personal/individual credit. A single scale across every loan type and borrower segment, resolving IDBI's "unified vs. segmented" ask with a concrete hybrid answer.
5. **Maps RAG status onto RBI's real SMA-0/SMA-1/SMA-2 early-warning classification** — not an invented 3-tier scheme. Green = Standard asset, Amber = SMA-0/SMA-1 territory, Red = SMA-2 (one step from NPA).
6. **Explains** every score with SHAP-derived, plain-English reason codes grounded in real underwriting signals (GSTR-1 vs GSTR-3B turnover consistency, GST filing compliance, EPFO regularity, cheque/NACH bounce rate) — risk drivers for stressed accounts, protective factors for healthy ones.
7. **Presents** it all in a RAG (Red/Amber/Green) loan-officer dashboard with per-account trajectory charts — a decision-support tool. **The AI advises; the underwriter decides** — human-in-the-loop by design, exactly as IDBI's DGMs stated on record ("we are not going to remove human intervention").

See [`docs/domain_research.md`](docs/domain_research.md) for the full sourcing behind every feature and design choice above.

## Results (on our synthetic evaluation panel — see Data note below)

**Primary metric (per IDBI's literal ask — "accuracy improving to 90%"):**

| Metric | Value |
|---|---|
| **Balanced Accuracy** | **81.4%** (at optimal threshold 0.41) |

**Supporting rigor metrics — why this number can be trusted:**

| Metric | Value | Why this metric matters |
|---|---|---|
| AUC-ROC | **0.885** | Standard discrimination metric for imbalanced credit risk problems |
| KS-Statistic | **0.629** | Classic credit-scoring separation metric; >0.4 is considered strong, this is very strong |
| Gini Coefficient | **0.770** | Industry-standard scorecard quality metric (2×AUC−1) |
| Recall @ Early-Warning Threshold (0.30) | **0.895** | A deliberately different, more sensitive threshold for the early-warning use case, where missing a defaulter is costlier than a false alarm |

We report **balanced accuracy** as primary because IDBI's problem statement literally asks for "accuracy" — we answer that directly, just measured correctly for imbalanced data instead of using the naive version that a participant in IDBI's own AMA correctly flagged as misleading. See [`docs/metrics_note.md`](docs/metrics_note.md) for the full reasoning.

In the dashboard itself, these metrics live in a separate **Model Governance** view, deliberately kept apart from the Portfolio view a loan officer uses daily — model validation is a technical/audit concern, not something that belongs cluttering the operational screen.

## Data note — important

IDBI's real synthetic sandbox datasets and APIs are only released to shortlisted teams (per the orientation session Q&A). For this first-stage prototype, all data is a **self-generated synthetic MSME panel** (6,000 borrowers × 24 months) built with a causal generative model — defaults emerge from deteriorating alternative-data signals rather than being randomly assigned, so the model has genuine signal to learn and the SHAP explanations are meaningful, not noise. See [`src/data_generator.py`](src/data_generator.py) for the full generation logic. The pipeline is designed to swap in IDBI's real sandbox datasets with no architecture changes once shortlisted.

We deliberately did **not** substitute a real but domain-mismatched public dataset (e.g. personal/consumer credit datasets like Home Credit Default Risk) just to claim "real data" — that's a different lending domain (individual consumer credit vs. MSME business credit) and would be a worse choice than transparent, well-calibrated synthetic data, not a better one. Instead, we anchored our synthetic panel's overall stress rate to **real, published RBI/Finance Ministry MSME-sector Gross NPA figures** (9.87% in March 2021, down to 3.27% in September 2025) — see [`docs/data_calibration_note.md`](docs/data_calibration_note.md) for the full sourcing and reasoning. The individual borrower records are synthetic (necessarily — no public dataset pairs Indian MSME defaults with GST/UPI/EPFO signals), but the *rate* they're calibrated to is real and cited, not invented.

## Architecture

![Architecture Diagram](docs/diagrams/architecture.png)

## Process Flow

![Process Flow Diagram](docs/diagrams/process_flow.png)

## Repository structure

```
msme-sentinel/
├── src/
│   ├── data_generator.py     # Synthetic MSME data engine (causal default generation)
│   ├── features.py           # Snapshot + trend/slope feature engineering
│   ├── train_model.py        # Model training, calibration, SHAP, metrics
│   └── dashboard_export.py   # Curated dataset export for the dashboard
├── dashboard/
│   ├── index.html            # RAG loan-officer dashboard
│   ├── style.css
│   ├── app.js
│   ├── data.json             # Exported dashboard dataset
│   └── vendor/chart.umd.js   # Vendored Chart.js (no external CDN dependency)
├── data/                      # Generated datasets + trained model + metrics (gitignored bulk files)
├── docs/
│   ├── diagrams/              # Architecture & process-flow diagrams
│   └── metrics_note.md        # Why we report AUC/KS/Gini instead of raw accuracy
└── requirements.txt
```

## Running it locally

```bash
pip install -r requirements.txt
cd src
python data_generator.py      # generates the synthetic 24-month MSME panel
python features.py            # builds the feature matrix
python train_model.py         # trains the model, calibrates scores, computes metrics
python dashboard_export.py    # exports the curated dataset for the dashboard
cd ../dashboard
python -m http.server 8080    # serve the dashboard locally
# open http://localhost:8080
```

The dashboard is a static site (HTML/CSS/JS + a JSON data file, no backend) — deployable as-is to GitHub Pages, Netlify, or Vercel.

## Team

- **Team name:** Guardinger Advanced Technologies
- **Team leader:** Malay Doshi
- **Problem statement:** Track 04 — MSME Credit Default Prediction (Predictive AI Risk Management)

## Feasibility: what's adoptable now vs. later

Not every alternative-data signal in this model is equally ready to plug into a
live bank system tomorrow, and we think saying so explicitly is what makes this
credible rather than what undermines it.

- **Phase 1 (available today, no new infrastructure):** Bureau/CIBIL MSME
  Rank, bank transactions (via Account Aggregator), GST returns (via GSP/AA),
  cheque/NACH bounce data (already inside core banking). A pilot on just these
  four is realistic to stand up immediately, and per our SHAP feature-importance
  analysis, several of them are already among the model's highest-impact
  signals on their own.
- **Phase 2 (real, but consent/coverage still maturing):** UPI transaction
  behavior, added as borrowers complete Account Aggregator consent.
- **Phase 3 (genuinely useful, not a blocker):** EPFO contribution regularity
  and utility payment history — both directionally right (and both raised by
  IDBI's own team in the AMA), but the weakest infrastructure today. EPFO in
  particular is **structurally absent**, not just thin, for the large share of
  MSMEs with no registered employees — our synthetic data models this honestly
  (~55% of simulated borrowers have no EPFO exposure at all, handled via a
  dedicated missing-data flag rather than a fabricated number).

Full reasoning and sourcing: [`docs/data_feasibility_tiering.md`](docs/data_feasibility_tiering.md).

## Roadmap (post-shortlisting)

- Swap synthetic data for IDBI's real sandbox datasets/APIs — architecture requires no changes.
- Add account-level restructuring recommendations (not just flags).
- Extend segment-aware calibration with more granular industry/cluster benchmarks (as raised for the MSME rapid-growth identification use case in Track 3/4 discussions).
- Add a model monitoring layer (population stability index / drift detection) for production readiness.
