# Data Feasibility Tiering — What's Actually Adoptable, and When

This exists to answer a direct question honestly: is this solution something a
bank can actually operationalize, or does it read as an impressive-looking pile
of every alternative-data signal we could think of? The honest answer is that
not all seven signal families are equally ready to plug in on day one — and
pretending otherwise would be the thing that makes an evaluator distrust the
whole pitch. So we tiered them.

## Tier 1 — Available today, no new infrastructure required

These can be wired into a production pilot as soon as sandbox access is granted,
because the data-access channel already exists and is mature:

- **Bureau data / CIBIL MSME Rank** — IDBI already subscribes to TransUnion
  CIBIL; this is a live feed today.
- **Bank transaction / cash-flow data** — via the RBI-backed Account Aggregator
  (AA) framework, already operational across major Indian banks.
- **GST returns (GSTR-1, GSTR-3B)** — accessible via GSP (GST Suvidha Provider)
  integration or AA-based consent flows; IDBI's own AMA referenced KYC/Aadhaar-
  grade tooling already in scope, and GST-based underwriting is now mainstream
  among NBFCs.
- **Cheque / NACH mandate bounce data** — already inside every bank's core
  banking system; this is existing internal data, not a new integration.

**Recommendation: this is the Phase 1 / MVP data scope.** A pilot built on
just these four sources is realistic to stand up quickly, and — per our SHAP
importance analysis — several of these (bureau score, GST consistency, bounce
rate) are already among the model's highest-impact features on their own.

## Tier 2 — Real and available, but consent/coverage still maturing

- **UPI transaction patterns** — genuinely available via Account Aggregator
  consent, and increasingly standard in NBFC underwriting, but AA coverage and
  borrower onboarding to consent flows is not yet universal, particularly for
  older or less digitally-active accounts. Treat as an **enrichment layer**
  added once a borrower has completed AA consent, not a blocking requirement
  for scoring every account from day one.

## Tier 3 — Directionally right, weakest infrastructure today

- **EPFO contribution regularity** — real and relevant, but **structurally
  unavailable for a large share of MSMEs**, not just thin: a sole
  proprietorship with no registered employees has no EPFO account at all.
  Our own synthetic data reflects this honestly (~55% of simulated borrowers
  have no EPFO exposure, weighted by business type), and the model is built
  to handle it as a genuine missing-data case (a dedicated flag, not a
  fabricated bad number) rather than assuming universal coverage.
- **Utility/electricity payment history** — unlike GST, Bank, Bureau, and
  NACH, there is no mature, interoperable aggregator for utility payment data
  in India today. This would need a bespoke tie-up with state electricity
  boards or a utility-data aggregator, and should be treated as a **future
  enrichment source**, not a Phase 1 dependency.

## What this means for rollout

**Phase 1 (immediate, on sandbox access):** Bureau/CMR + Bank transactions +
GST + NACH bounce data. This alone lets the model run and already carries
most of its discriminative power per our feature-importance analysis.

**Phase 2 (as AA consent coverage grows):** Add UPI transaction behavior for
borrowers who've completed AA consent.

**Phase 3 (opportunistic enrichment, not a blocker):** EPFO and utility data
where and when a tie-up becomes available — genuinely useful additive signal
for the subset of borrowers it applies to, but never assumed as a baseline
requirement.

This tiering is also why our synthetic data generator explicitly models EPFO
as **structurally absent** for a majority of borrowers rather than universally
present with a "delay" number — the demo shows the model handling real-world
partial data availability, not a fantasy where every signal is always there.
