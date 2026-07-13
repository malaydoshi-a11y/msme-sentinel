# MSME Sentinel — 3-Minute Demo Video Script

**Goal:** In 3 minutes, a banker who's never seen this should understand what problem it solves, why it's different from a generic default-classifier, and that it actually works, on screen, live, at real scale.

Record screen + voiceover. Talk through it like you're actually walking a colleague through your own screen, not reciting slides — the pauses and small asides in the lines below are intentional, not filler. Timestamps are targets, not rigid. Every number below was checked directly against the live data before writing this — see the recording notes for exactly what to click and why.

---

**[0:00–0:15] Hook**

*(Show the dashboard's main portfolio view as you talk)*

> "IDBI's current MSME default model runs at just 16 to 22 percent accuracy, and reportedly only sees about three months ahead. IDBI asked for ninety percent-plus accuracy and a full year of warning instead. So we built MSME Sentinel around trend, not a single snapshot."

---

**[0:15–0:50] Portfolio view — rank, RAG mix, the trend chart, data sources**

*(Point at the RAG tiles, then the Portfolio Trend chart, then the Data Sources panel)*

> "Every account here gets one common rank, one to ten — CIBIL's own MSME Rank convention. Green, amber, red map straight onto RBI's own SMA categories. Right now the book reads fifty-one percent healthy, twenty-nine watchlist, nineteen high-risk. This chart is the actual evidence for early warning — the whole portfolio's mix over twenty-four months. And down here, every data source is tagged by how ready it is — bureau, bank transactions, GST, NACH bounce are live channels IDBI already has; the rest are staged honestly, not oversold."

---

**[0:50–1:10] Model Governance tab**

*(Click the "Model Governance" tab)*

> "Flip to Model Governance — kept separate on purpose. A loan officer doesn't need to know what AUC-ROC means. Balanced accuracy comes out to eighty-two point seven five percent, measured the way that actually accounts for how rare defaults are. AUC-ROC point nine oh, KS-statistic point six six, back that up as real separation, not a fluke split."

---

**[1:10–1:30] Back to Portfolio — full scale and what's new**

*(Click back to Portfolio View, point at the account count, then click "Sort: Recently worsened")*

> "Back on Portfolio — this isn't a small curated sample, it's the full six-thousand-account book, filterable by status or loan type. Early warning means catching what's new — sort by recently worsened, and whatever just deteriorated jumps straight to the top."

---

**[1:30–2:10] Click into a flagged account — trajectory, runway, quantified reasons**

*(Search for account MSME102011, click it, let the drawer slide open)*

> "Let's open one. Rank eight, inside RBI's SMA-2 band. The trajectory shows it improved to watchlist territory mid-panel, then relapsed, jumping four ranks worse just last month. Here's the part that matters: an estimated three-point-three months before it slides further — a number an officer can plan around. Every reason is quantified, not just named — GST turnover consistency at point seven-oh-two now, down from point eight-seven-five six months ago, tagged Phase 1, a channel IDBI can pull today. This account's also New-to-Credit, thin bureau file — caught anyway, without leaning on bureau history."

---

**[2:10–2:20] Click a healthy account**

*(Click a GREEN account)*

> "Click a healthy one, and it explains itself the same way, just in reverse — steady GST filings, stable cash flow. Not just there to raise alarms."

---

**[2:20–2:50] Close — honesty about scope and integration**

> "This runs on synthetic data we generated ourselves, with a causal model so the signal is real — staged by real data-infrastructure maturity, not everything at once. In production it sits alongside your existing core banking system, not instead of it, and IDBI's real sandbox data drops in without a rebuild once shortlisted. This is MSME Sentinel. Thanks for watching."

---

## Recording notes

- Keep the browser window clean — close other tabs, dashboard at 1300px+ width.
- **Account `MSME102011` for the [1:30–2:10] beat** — verified directly against `dashboard/details.json`: rank 8, RAG Red, a genuine +4 rank jump last month (month 23 → month 24), a real trajectory arc (dipped to rank 4 — watchlist, *not* healthy — around months 15–19, then relapsed to rank 8), a populated runway estimate (3.3 months), and its top reason (GST turnover consistency) is `0.702` now vs `0.875` six months ago — both shown on screen to 3 decimal places, so say "point seven-oh-two" / "point eight-seven-five," not rounded figures. It's also genuinely `borrower_category: NTC`, visible twice in the drawer (the meta line under the account ID, and the Account Details grid), which is what makes the New-to-Credit line honest rather than a generic claim.
- If you regenerate `dashboard/data.json` / `details.json` before recording (e.g. by re-running `python src/dashboard_export.py`), **re-check this account's numbers first** — the synthetic panel is seeded/deterministic so they should match, but confirm rather than assume, and re-run `python scripts/smoke_test.py` either way.
- The RAG split (51% / 29% / 19%) and metrics (82.75% / 0.90 / 0.66) were checked directly against `dashboard/data.json` at time of writing. If either file changes, update this script before recording — don't let the video go stale the way the first draft of this script did.
- The dashboard's light, IDBI-teal theme and the Data Sources panel are themselves part of the pitch — don't scroll past them too fast during [0:15–0:50].
- Use a quiet room / decent mic — judges review many videos back to back; clear audio buys attention.
- Spoken content is ~413 words, landing at ~2:45–2:55 even at a deliberate, unhurried pace (140–150 words/minute). Don't speed-read to fit more in — if you're consistently going over 3:00, cut a sentence rather than talk faster.
