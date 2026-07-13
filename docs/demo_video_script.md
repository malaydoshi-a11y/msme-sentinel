# MSME Sentinel — 3-Minute Demo Video Script

**Goal:** In 3 minutes, a banker who has never seen this should understand (1) what problem it solves, (2) why it's different from a generic default-classifier, (3) that it actually works, on screen, live, at real scale — and walk away having seen every major differentiator this build actually has, not just the ones from the first draft.

Record screen + voiceover. Suggested pacing below (timestamps are targets, not rigid). Total spoken content is timed to land at ~2:50, leaving a few seconds of buffer for screen transitions.

---

**[0:00–0:15] Hook — the problem, in their own words**

*(Show the dashboard's main portfolio view as you talk)*

> "IDBI's current MSME default model runs at 16 to 22 percent accuracy, and sees about 3 months ahead. IDBI asked for 90%+ accuracy and a 12-month early warning. This is MSME Sentinel — not another point-in-time classifier. It's built on trend, not a snapshot."

---

**[0:15–0:40] Portfolio view — RAG mix, the trend chart, and data feasibility**

*(Point at the RAG tiles, then the Portfolio Trend chart just below them, then the Data Sources panel)*

> "Every account gets one common risk rank, 1 to 10, matching CIBIL's own MSME Rank convention. Green, Amber, Red map directly onto RBI's SMA categories. Right now: 51% healthy, 29% watchlist, 19% high-risk. This trend chart is the actual proof of early warning, not a one-time claim. And right here — every data source is tagged by how ready it is today. Phase 1 sources are live channels IDBI already has; Phase 2 and 3 are staged honestly, not oversold."

---

**[0:40–1:00] Model Governance tab**

*(Click the "Model Governance" tab)*

> "Performance metrics live in their own tab, on purpose — a loan officer's daily screen shouldn't show AUC-ROC. Balanced accuracy: 82.75%, correctly measured for imbalanced data — the metric IDBI actually asked for, done right. AUC-ROC 0.90 and KS-statistic 0.66 back it up as real discriminative power, not a lucky train/test split."

---

**[1:00–1:20] Back to Portfolio — full scale, filters, and what's NEW**

*(Click back to Portfolio View, point at the account count, then the filter dropdowns, then click "Sort: Recently worsened")*

> "This isn't a curated sample of 40 accounts — it's the full 6,000-account monitored book, filterable by status and loan type. Early warning means catching what's *new*. Sort by 'recently worsened,' and the accounts that just deteriorated rise straight to the top."

---

**[1:20–1:55] Click into a flagged account — trajectory, runway, and quantified reasons**

*(Search for or scroll to account MSME102011 — rank 8, a clean example — click it and let the drawer slide open)*

> "Here's an account at rank 8, one step into RBI's SMA-2 territory. This chart is a 24-month trajectory — it actually recovered to healthy mid-panel, then relapsed, jumping four ranks worse this month. Here's the runway: an estimated 3 months before it crosses further, a number an officer can actually plan around. Every reason is quantified too, not just labeled — GST turnover consistency, 0.70 now versus 0.88 six months ago, tagged Phase 1. No black box — the underwriter sees the evidence and makes the final call."

---

**[1:55–2:10] Click a GREEN account — not just alarmist**

*(Click a healthy account)*

> "Click a healthy account and it explains itself the same way — consistent GST filings, stable cash flow. Confidence, not noise."

---

**[2:10–2:25] New-to-Credit handling (quick mention)**

> "For thin-file, new-to-credit borrowers — a gap IDBI flagged directly — the model falls back on alternative signals instead of auto-rejecting a blank slate."

---

**[2:25–2:50] Close — honesty about scope, integration, and what's next**

> "Built on our own synthetic data, generated causally so the signal is real — staged by actual data maturity, not everything at once. This runs alongside your existing core banking system, not in place of it — IDBI's real sandbox data plugs in directly once shortlisted. This is MSME Sentinel — not a coin flip on default, an early-warning radar a loan officer can actually use. Thank you."

---

## Recording notes
- Keep the browser window clean — close other tabs, use the dashboard at a normal 1300px+ width.
- **Use account `MSME102011` for the [1:20–1:55] drill-down beat** — verified against the live data: rank 8, a genuine +4 rank jump last month, a populated runway estimate (~3.3 months, not "already at highest tier" or "stable"), and clean quantified reason codes across two different data-source phases (GST = Phase 1, utility = Phase 3). Search its ID directly rather than hunting through the table live.
- The 0.70 vs 0.88 GST figure in the script is this account's real, current exported value — don't paraphrase it into a round number, and don't reuse it if you re-export the data before recording (re-run `python scripts/smoke_test.py` and re-check the account's numbers in `dashboard/details.json` if you regenerate data first).
- The dashboard's light, IDBI-teal theme and the Data Sources panel are themselves part of the pitch — don't scroll past them too fast during [0:15–0:40].
- Use a quiet room / decent mic — judges will be reviewing many videos back to back; clear audio buys attention.
- If using Loom/OBS: record at 1080p, keep it under 3:00 sharp — many hackathon rubrics cut off or penalize overage. This script's spoken content lands around 2:50; the remaining ~10s is buffer for clicks/transitions, not more talking.
