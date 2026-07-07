# Domain Research Note — What Real Indian MSME Credit Underwriting Actually Uses

This document exists because we were asked a fair question: if the alternative-data
signals are synthetic, how do we know they reflect what's *actually* used in Indian
MSME credit risk assessment, rather than plausible-sounding invented features? This
is the homework behind every field in `src/data_generator.py`. Every feature below
is grounded in a cited, real practice — nothing was included just because it sounded
technical.

---

## 1. The regulatory early-warning framework already in use (RBI SMA classification)

Before we invented anything, we checked: does an "early warning system" for loan
stress already exist in Indian banking? It does, and it's mandatory.

RBI introduced **Special Mention Account (SMA)** classification in 2014, refined
since, as the official precursor-to-NPA framework every scheduled commercial bank
must run:
- **SMA-0**: principal/interest overdue 1–30 days (early stress, no overdue penalty yet)
- **SMA-1**: overdue 31–60 days
- **SMA-2**: overdue 61–90 days (the last stage before NPA classification at 90+ days)
- **SMA-NF**: non-financial early warning signals (e.g., delayed stock statement
  submission) even when the account isn't technically overdue

RBI's PSB Reforms Agenda already mandates **~80 automated EWS triggers** per account
in public sector banks, and 2025 guidelines added a "Risk Escalation Matrix" and
daily (not monthly) SMA stamping for large exposures.

**What we did with this:** our RAG (Red/Amber/Green) bucketing is not an arbitrary
3-tier scheme we invented — it is deliberately mapped onto this real framework:
- **GREEN** = Standard asset, no SMA flag
- **AMBER** = SMA-0 / SMA-1 territory (early stress, still recoverable with intervention)
- **RED** = SMA-2 territory (one step from NPA — urgent underwriter action needed)

This means a loan officer looking at our dashboard is seeing the same conceptual
categories their own bank's core banking system already tracks, not a new taxonomy
they have to learn.

Sources: RBI Master Direction on SMA/NPA classification (2014, amended); PIB release
on PSB Reforms Agenda EWS triggers (Dec 2025); multiple secondary summaries (ixambee,
getzype, muthootfinance) cross-checked for consistency.

## 2. RBI's actual fraud/stress Early Warning Signal categories

RBI's Master Directions on Frauds (July 2016, updated July 2024) list **42 specific
Early Warning Signals**, grouped into 7 categories: operations of account,
concealment/falsification of documents, diversion of funds, issues in primary/
collateral security, inter-group/concentration of transactions, regulatory concerns,
and other signals. Signal #1 on the official list is **bouncing of high-value
cheques**; others include delayed stock-statement submission, fund routing through
group companies, and deteriorating financial ratios.

**What we did with this:** our `bounce_rate_pct` feature isn't a generic "payment
failures" stand-in — it's modeled specifically on RBI's actual Signal #1
(cheque/payment bounces), because that's the literal, named, regulatory-grade
signal banks are required to monitor for exactly this purpose.

## 3. GST-based underwriting — what's actually checked, not just "filing delay"

We initially modeled GST behavior as a generic "filing delay in days." That was too
vague. Real GST-based MSME underwriting (used by NBFCs and increasingly banks, per
multiple 2025-2026 industry sources) checks specific, named things:

- **GSTR-1** (outward supplies / sales, invoice-level) vs **GSTR-3B** (self-declared
  tax liability + Input Tax Credit summary) — a **gap between these two returns is
  the single most common real-world fraud/risk pattern** in MSME lending (e.g., a
  business declaring ₹90L in GSTR-1 but only ₹50L in GSTR-3B). This is flagged
  automatically by the GST portal itself.
- **GSTR-2B** — auto-populated from supplier filings, the formal ITC reference since
  FY2020-21; a claimed ITC that doesn't appear here is a red flag.
- **GST-declared turnover vs. actual bank account credits** — real lenders reconcile
  these directly; validated GST turnover typically anchors loan sizing (lenders
  commonly offer 10–30% of annual turnover as the credit line).
- **Filing timeliness/consistency** as a compliance rating — industry tools (e.g.
  Precisa) generate a 0–100 compliance score based on on-time filing across a
  rolling 24-month window, not a single "days late" number.
- As of Q3 FY25, **GSTR filing compliance nationally was 92.77%** — meaning
  persistent non-filers or erratic filers are a genuine minority signal, not noise.

**What we did with this:** we replaced our vague "GST filing delay" feature with
two features that mirror real practice: (a) a **GSTR-1 vs GSTR-3B turnover
consistency ratio**, and (b) a **GST filing compliance score (0–100)**, matching
industry convention rather than an invented unit.

## 4. UPI and bank-statement behavioral signals

Real alternative-data underwriting (per 2025-2026 NBFC industry sources) uses UPI
data specifically for **payment frequency, merchant category diversity, and income
consistency** — not just a vague "cash-flow volatility" number. A borrower making
80+ UPI transactions/month to diverse merchants is read as a specific positive
signal of real business activity. NACH mandate history (EMI auto-debit success/
failure) is used as a distinct, named signal for repayment discipline, separate from
manual cheque bounces.

**What we did with this:** we kept cash-flow volatility (it's real and used) but
added it as a genuine time-series volatility measure rather than a cosmetic number,
and we treat overdraft/CC utilization and NACH-style bounce behavior as distinct
signals rather than folding everything into one vague "behavior score."

## 5. CIBIL MSME Rank (CMR) — the real scoring convention for this exact use case

This is the most important finding, and it changed our output design. TransUnion
CIBIL already runs **CIBIL MSME Rank (CMR)**, a model that:
- Is specifically built for MSME exposure between ₹10 lakh and ₹50 crore
- **Explicitly predicts probability of default over a 12-month horizon** — the same
  horizon IDBI asked for
- Uses a **1–10 scale (CMR-1 = lowest risk, CMR-10 = highest risk)**, not the 300–900
  scale used for personal/individual CIBIL scores
- Is recalculated roughly every 30–45 days as lenders report fresh data
- Draws on repayment behavior, credit utilization, credit history length, enquiry
  frequency, and firmographics (age, industry, ownership type)

We had originally designed our unified score on a 300–900 scale, matching personal
retail credit convention. **That was a miss** — a banker underwriting an MSME loan
thinks in CMR-1-through-10 terms, not personal-CIBIL terms, and presenting an MSME
score on the wrong bureau's scale would read as not having done the homework.

**What we did with this:** we now present our unified score as a **CMR-style 1–10
MSME Risk Rank** (1 = best, 10 = worst) as the primary output, matching the exact
convention Indian MSME lenders already use daily, alongside the underlying PD
probability. See `src/train_model.py` for the calibration logic.

## 6. The consent/data-access mechanism this would actually run on

None of this data can legally be pulled without consent. The real mechanism is the
RBI-backed **Account Aggregator (AA) framework** — part of what industry sources
call the "India-5 stack" (Account Aggregator, UPI, GST, Bureau, NACH) — through
which a borrower consents, per data category and time window, to share GST returns,
bank statements, and other financial data with a lender via a licensed AA
intermediary, who never stores the data itself. This is already referenced in our
architecture diagram's data-sources layer and is the correct real-world plumbing
this system would sit on top of, not a generic "API integration."

## 7. What we deliberately did NOT add

Not every real signal earns a place in a hackathon prototype. We left out, on
purpose:
- **CGTMSE guarantee-cover flag** — real and relevant (guarantee-backed loans behave
  differently on recovery), but it changes loss-given-default economics, not
  probability of default, which is out of scope for this track's ask.
- **MCA/ROC filing data** — relevant for registered companies specifically, but a
  large share of MSMEs are proprietorships/partnerships with no ROC filings, so it
  would only apply to a subset and add complexity without broad benefit.
- **Full 42-signal RBI fraud checklist** — we deliberately modeled only the signals
  that map to data categories we actually generate (cheque bounces, GST
  consistency, financial ratio deterioration) rather than padding the feature list
  with signals we can't honestly back with a data source, even a synthetic one.

This is the "best of kind, not biggest" principle: every feature in the model
traces to a specific, named, real practice — not a plausible-sounding superset.

---

## Sources

- RBI SMA/NPA classification framework (2014, amended); PIB release on PSB Reforms
  Agenda EWS triggers (Dec 2025).
- RBI Master Directions on Frauds (July 2016; updated July 2024) — 42 Early Warning
  Signals across 7 categories.
- Precisa (GSTR analysis for lenders, 2026 guide); industry coverage of GSTR-1 vs
  GSTR-3B reconciliation practice; GSTN filing compliance statistics (Q3 FY25).
- APPWRK, "AI-Powered Loan Underwriting" (2026) — UPI/GST/AA/NACH/EPFO as India's
  alternative-data stack for credit scoring.
- TransUnion CIBIL — CIBIL MSME Rank (CMR) product documentation and asset sheet.
