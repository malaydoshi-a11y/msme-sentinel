# MSME Sentinel — 3-Minute Demo Video Script

**Goal:** In 3 minutes, a banker who has never seen this should understand (1) what problem it solves, (2) why it's different from a generic default-classifier, (3) that it actually works, on screen, live.

Record screen + voiceover. Suggested pacing below (timestamps are targets, not rigid).

---

**[0:00–0:20] Hook — the problem, in their own words**

*(Show the dashboard's main portfolio view as you talk)*

> "IDBI's current MSME default model runs at 16 to 22 percent accuracy, and only sees about 3 months ahead. IDBI asked for 90%+ accuracy and a 12-month early warning. But raw accuracy on an imbalanced default dataset is misleading — a model that predicts 'no one defaults' can score 90% and be useless. So instead of another black-box classifier, we built MSME Sentinel: an early-warning system that tracks how an account's financial health is *trending*, not just what it looks like today."

---

**[0:20–0:55] Portfolio view walkthrough**

*(Point at RAG tiles, then the score spectrum)*

> "Every MSME account gets a common risk rank, 1 to 10 — matching CIBIL's own MSME Rank convention, not a scale we invented. Green, Amber, Red map directly onto RBI's SMA-0, SMA-1, SMA-2 categories, so a loan officer isn't learning new vocabulary. Right now: 51% healthy, 29% watchlist, 19% high-risk. And notice — no model internals cluttering this view. This is the daily-use screen."

*(Click the "Model Governance" tab)*

> "Performance metrics live in their own tab, on purpose. Balanced accuracy: 82.75%, correctly measured for imbalanced data — the metric IDBI actually asked for, done right. AUC-ROC 0.90, KS-statistic 0.66 back it up as real discriminative power."

---

**[0:55–1:20] Click into a RED account — the core differentiator**

*(Click a red account, let the drawer slide open, point at the trajectory chart)*

> "Here's an account currently flagged red — rank 10 out of 10, one step from RBI's SMA-2 category. But look at this chart — this isn't a single prediction, it's a 24-month trajectory. You can see the account was actually stable, even in the watch zone, several months ago, and has been steadily deteriorating since. That trend — not a one-off snapshot — is what gives a loan officer real runway to act, months before a default would actually happen."

---

**[1:20–1:45] Explainability — the human-in-the-loop piece**

*(Point at the reason codes list)*

> "AI shouldn't replace the underwriter, it should give reasons. Every rank ships with plain-English drivers — irregular EPFO contributions, a widening GSTR-1 vs GSTR-3B gap, rising bounce rate. No black box. The underwriter sees why, and makes the final call."

---

**[1:45–2:05] Click a GREEN account — showing it's not just alarmist**

*(Click a healthy account)*

> "It's not just flagging risk — a healthy account shows *why* it's healthy: consistent GST filings, strong utility payment discipline. Confidence, not noise."

---

**[2:05–2:25] New-to-Credit handling (quick mention)**

> "For new-to-credit borrowers with thin GST or bureau history — a gap IDBI flagged directly — the model falls back on alternative signals instead of auto-rejecting blank-slate applicants."

---

**[2:25–3:00] Close — honesty about scope + what's next**

> "Built on our own synthetic data, generated with a causal model so the signal is real, not random — and staged by real data-infrastructure maturity, not everything at once. This runs alongside your existing core banking system, not in place of it — IDBI's actual sandbox data plugs in directly once shortlisted, no rebuild needed. This is MSME Sentinel — not a coin flip on default, an early warning radar. Thank you."

---

## Recording notes
- Keep the browser window clean — close other tabs, use the dashboard at a normal 1300px+ width.
- The dashboard's light, IDBI-teal theme and the "Data Sources" panel (visible right below the RAG tiles) are themselves part of the pitch — no extra narration needed, just don't scroll past them too fast during the [0:20–0:55] portfolio walkthrough.
- Zoom in slightly on the trajectory chart moment (1:00–1:20) — it's the single most important visual in the whole video.
- Use a quiet room / decent mic — judges will be reviewing many videos back to back; clear audio buys attention.
- If using Loom/OBS: record at 1080p, keep it under 3:00 sharp — many hackathon rubrics cut off or penalize overage.
