# MSME Sentinel — Slide Content for Official IDBI Innovate PPT Template

**Important:** Download the real, editable `.pptx` template from Hack2skill (Submission tab → Prototype Submission). Do not alter its structure/slide count. Paste the content below into the corresponding sections. Image files referenced are in `docs/diagrams/` and dashboard screenshots.

---

## Slide: Team Details
- **a. Team name:** Guardinger Advanced Technologies
- **b. Team leader name:** Malay Doshi
- **c. Problem Statement:** Track 04 — MSME Credit (Predictive AI, Risk Management)

---

## Slide: Brief about the idea

MSME Sentinel is an AI-powered **Early Warning System (EWS)** for MSME credit risk — not a single point-in-time "will they default" classifier. It continuously monitors each MSME loan account's financial-health trajectory using structured bank data (bureau score, turnover, transactions) alongside alternative data (GST filing regularity, UPI/cash-flow patterns, utility payment consistency, EPFO contributions).

Every account receives one common, comparable **CMR-style MSME Risk Rank (1–10)** — deliberately matching the real CIBIL MSME Rank convention already used across Indian MSME lending, not an invented scale — calibrated consistently across all loan types and borrower segments, and mapped onto RBI's own **SMA-0 / SMA-1 / SMA-2** early-warning categories as a **Red / Amber / Green** status. When a rank starts deteriorating, the system flags it up to **12 months ahead** of potential stress — with a plain-English explanation of *why* — giving loan officers real runway to intervene before an account becomes an NPA.

The AI advises; the underwriter always makes the final call.

---

## Slide: Opportunities

**How different is it from other existing ideas?**
Most default-prediction approaches — and likely most other submissions — build a single binary classifier that outputs "default / no default" as of today, using invented or generic feature names. MSME Sentinel differs in four concrete ways:
1. Built on **trend/slope features** across rolling 3- and 6-month windows, not just current-month snapshots — this is what makes a genuine 12-month lead time possible.
2. Produces a **CMR-style 1–10 rank**, matching the real CIBIL MSME Rank convention already used industry-wide for this exact exposure band and horizon — not an invented scale.
3. **RAG status maps directly onto RBI's own SMA-0/SMA-1/SMA-2 early-warning classification** — a loan officer sees the same categories their core banking system already tracks, not a new taxonomy to learn.
4. Every score ships with **SHAP-based, human-readable reasoning grounded in real underwriting signals** — GSTR-1 vs GSTR-3B turnover consistency (the actual primary GST fraud/risk signal used by NBFCs today), not a generic "GST filing delay."

**How will it solve the problem?**
It directly targets both gaps IDBI named: accuracy (16–22% today → we demonstrate AUC-ROC 0.885 / KS-statistic 0.629, correctly measured for imbalanced default data) and lead time (IDBI's own internal model reportedly predicts only ~3 months ahead; our trend-based design targets the full 12-month window). It also solves New-to-Credit thin-file scoring through alternative-data fallback features, and gives underwriters an explainable, actionable interface instead of a raw score they have to trust blindly.

**USP:** *Early warning, not a coin flip.* A trajectory-based system that tells a loan officer not just "is this account risky" but "is it getting worse, why, and how much runway is left" — which is the actual decision a bank needs to make.

---

## Slide: List of features offered by the solution

- Segment-aware, class-imbalance-corrected ML scoring engine (XGBoost ensemble)
- **CMR-style MSME Risk Rank (1–10)** across all loan types/segments — matches the real CIBIL MSME Rank convention used industry-wide for this exact exposure band and horizon, not an invented scale
- **RAG status mapped onto RBI's real SMA-0/SMA-1/SMA-2 early-warning framework** — the same categories a bank's core banking system already tracks
- 12-month early-warning trajectory monitoring — not point-in-time classification
- SHAP-based explainability with plain-English reason codes grounded in real underwriting signals (GSTR-1 vs GSTR-3B turnover consistency, GST compliance, EPFO regularity, NACH/cheque bounce rate)
- RAG portfolio dashboard built for loan officers, **with model performance metrics deliberately separated into their own "Model Governance" view** — a loan officer's daily screen shows accounts at risk, not AUC-ROC; model validation is a distinct audience with its own tab
- Per-account drill-down: 24-month trend chart, rank, PD probability, top risk/protective drivers
- New-to-Credit (thin-file) borrower handling via alternative data signals
- Human-in-the-loop by design — decision support, not autonomous approval/rejection
- Fully documented, reproducible ML pipeline, with every feature traced to a cited real practice (see `docs/domain_research.md`)
- Architecture designed for drop-in replacement of synthetic data with IDBI's real sandbox datasets, no rebuild required

---

## Slide: Process flow diagram or Use-case diagram

*Insert image:* `docs/diagrams/process_flow.png`

(Shows the loan-officer journey: monthly data refresh → score & trend update → RAG classification → officer review for Amber/Red accounts → human decision & action → outcome logged → feedback loop into model retraining.)

---

## Slide: Wireframes/Mock diagrams of the proposed solution (optional)

Skip or replace with a note: *"A working, interactive prototype was built directly rather than static wireframes — see Snapshots of the Prototype section."*

---

## Slide: Architecture diagram of the proposed solution

*Insert image:* `docs/diagrams/architecture.png`

(Shows the 8-layer pipeline: Data Sources → Feature Engineering → Segment-Aware Ensemble Model → Score Calibration → Early-Warning Trajectory Engine → Explainability Layer → Loan Officer RAG Dashboard → Human-in-the-Loop Decision, with a feedback loop back into retraining.)

---

## Slide: Technologies to be used in the solution

- **Python** — data generation, feature engineering, modeling
- **XGBoost** — segment-aware gradient boosting ensemble
- **SHAP** — model explainability (reason codes)
- **scikit-learn** — evaluation, train/test splitting (group-aware, leak-free)
- **Pandas / NumPy / PyArrow** — data pipeline
- **HTML5 / CSS3 / vanilla JavaScript** — RAG dashboard (framework-free, fast, easy to audit)
- **Chart.js** — score spectrum & account trajectory visualizations
- **AWS-compatible static hosting** (S3 + CloudFront, or Amplify) — aligned with IDBI's AWS-based sandbox
- **GitHub** — version control, CI-ready repo structure

---

## Slide: Estimated implementation cost (optional)

Phased, matching the rollout tiers above rather than one lump estimate:
- **Phase 1** (Bureau/CMR + Bank via AA + GST + NACH bounce — mature channels): cloud hosting **~₹15,000–20,000/month** at pilot scale; integration effort **~3–4 weeks**, small team, since these are existing data channels, not new infrastructure.
- **Phase 2** (add UPI via AA consent): incremental **~₹3,000–5,000/month**; **~1–2 weeks** additional integration.
- **Phase 3** (EPFO/utility enrichment, opportunistic): cost depends on the specific tie-up secured; treated as a future line item, not a Phase 1 dependency.
- Ongoing model monitoring & periodic retraining: **~1 FTE-equivalent, part-time**, post go-live, across all phases.

---

## Slide: Snapshots of the prototype

*Insert screenshots:* dashboard main view (portfolio + RAG tiles + score spectrum + account table) and the account drill-down drawer (score, trajectory chart, reason codes).

---

## Slide: Prototype Performance report/Benchmarking

**Primary metric (per problem statement's literal ask):**

| Metric | Value |
|---|---|
| **Balanced Accuracy** | **81.4%** |

*Balanced accuracy — the average of sensitivity and specificity — correctly accounts for class imbalance in default data, unlike raw accuracy. It is still honestly "accuracy," just measured the way a credit-risk team actually measures it.*

**Supporting rigor metrics (why the number above can be trusted):**

| Metric | Value | Note |
|---|---|---|
| AUC-ROC | 0.885 | Standard discrimination metric for imbalanced credit risk problems |
| KS-Statistic | 0.629 | >0.4 is considered strong in credit scoring — this is very strong |
| Gini Coefficient | 0.770 | Industry-standard scorecard quality metric (2×AUC−1) |
| Recall @ Early-Warning Threshold (0.30) | 0.895 | A separate, more sensitive operating point used specifically for early-warning sensitivity — deliberately different from the balanced-accuracy threshold, since missing a future defaulter is costlier than a false alarm |

*Note (include this — it shows rigor, not evasion):* Raw accuracy on this imbalanced dataset is a well-known misleading metric — a model that always predicts "no default" can exceed 90% raw accuracy while being useless. This exact concern was raised in IDBI's own AMA for this track. We report balanced accuracy instead, which answers their literal ask correctly rather than avoiding it. Full reasoning in `docs/metrics_note.md`.

**Product note:** in the actual dashboard, these performance metrics live in a separate "Model Governance" view, deliberately kept out of the daily loan-officer screen — a loan officer needs to see which accounts are at risk, not AUC-ROC. Model performance is for the technical/audit reviewer, not the end user, and the product is built to reflect that separation.

---

## Slide: Additional Details/Future Development (if any)

**Phased rollout — built for real adoption, not a one-shot data dump:**
- **Phase 1 (immediate, on sandbox access):** Bureau/CIBIL MSME Rank + bank transactions (Account Aggregator) + GST returns (GSP/AA) + cheque/NACH bounce data — all available today via mature, existing channels. Per our feature-importance analysis, this alone carries most of the model's discriminative power.
- **Phase 2 (as AA consent coverage grows):** UPI transaction behavior, added once a borrower completes Account Aggregator consent.
- **Phase 3 (opportunistic enrichment, never a blocker):** EPFO contribution regularity and utility payment history — directionally valuable (and both raised by IDBI's own team), but the weakest data-infrastructure maturity today. EPFO in particular is structurally unavailable for MSMEs with no registered employees, not just thin — our model handles this as an explicit missing-data case, not a fabricated number, and the same design would apply to real deployment.

Other future development:
- Swap synthetic data for IDBI's real sandbox datasets/APIs once shortlisted — architecture requires no changes.
- Add a restructuring/intervention recommendation engine (not just a risk flag, a suggested next action).
- Add a Population Stability Index (PSI) drift-monitoring layer for production readiness.
- Extend to portfolio/cluster-level early warning (e.g., flagging an entire MSME industry cluster showing correlated stress).
- Multi-language reason-code generation, reusable across IDBI's other hackathon tracks (e.g., Track 1's multilingual requirement).

---

## Slide: Provide links to your

- **GitHub Public Repository:** _[push the repo and paste the URL]_
- **Demo Video Link (3 Minutes):** _[record per docs/demo_video_script.md and paste the URL]_
- **Final Product Link:** _[deploy per docs/deployment_guide.md and paste the URL]_
