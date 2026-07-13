# Integration Architecture — How This Actually Connects to IDBI's Systems

`docs/data_feasibility_tiering.md` answers *which* data sources are realistic
and when. This answers the question that matters more to a bank evaluator:
*how does this actually plug into what IDBI already runs*, technically —
because a good model that requires a two-year IT project to connect is not
an adoptable solution.

## The integration pattern: a scoring service, not a replacement

MSME Sentinel is designed to run as a **modular scoring service alongside
the existing core banking system** (e.g. Finacle) — not a system that
replaces or sits in front of it. It reads data in, scores, and exposes
results via API. Nothing about a bank's existing loan origination, core
banking, or credit committee workflow needs to change to adopt it; those
systems keep doing what they do, and this adds an early-warning signal on
top.

```
Core Banking (Finacle etc.) ─┐
Bureau (CIBIL, live feed)    ─┼──►  Ingestion layer  ──►  Feature store  ──►  Scoring service  ──►  RAG API  ──►  Loan Officer Dashboard
GSP / GST API                ─┤        (batch or API)      (monthly re-score)   (XGBoost, <1MB)      (this UI)
Account Aggregator (AA)      ─┘
```

Every box on the right already exists in this repo in a form that maps
directly to production: **`src/ingestion.py` is the ingestion layer** — a
manifest of every data source, its phase (1/2/3), and the specific real
integration a production implementation would call, with each raw feature
column explicitly owned by one source (`COLUMN_SOURCE`). This isn't a
separate claim from the model — `dashboard_export.py` imports this same
manifest to populate the dashboard's "Data Sources" panel *and* to tag
every SHAP reason code with which data source (and phase) it came from, so
"is this signal production-ready" is answered inline, per reason, not just
asserted in a doc. `src/features.py` is the feature store logic,
`src/train_model.py` is the scoring service's model artifact producer
(`data/xgb_model.json`, ~700KB — small enough to serve from a lightweight
container, no GPU, no exotic infra), and `dashboard/` is the RAG API's
reference UI. Nothing here needs a rebuild to go to production; it needs
its **inputs** switched from the synthetic generator to real feeds — that
swap happens inside `src/ingestion.py`'s source definitions, not scattered
across the pipeline.

## Ingestion: how data actually gets in

Two realistic ingestion paths, not one — because not every source is
API-ready today, and pretending otherwise is exactly the kind of thing an
evaluator with real banking-systems experience will catch:

**API/consent-based (preferred, where already mature):**
- Bureau/CIBIL MSME Rank — pulled via IDBI's existing bureau subscription,
  already a live feed.
- Bank transactions — via the RBI-backed Account Aggregator consent flow,
  standard OAuth-style consent artefact, no new rails to build.
- GST returns — via GSP API or AA-based GST consent, same pattern.

**Batch fallback (realistic for anything not API-ready yet):**
- NACH/cheque bounce data — lives inside the core banking system's own
  database; a nightly batch export (CSV/SFTP or a direct read-replica
  query) is the pragmatic Phase 1 path rather than requiring a new
  real-time hook into core banking on day one.

This mirrors how most Indian banking-system integrations actually get
built: start with a batch nightly job (low risk, no core-system changes),
move specific feeds to real-time API only where the volume/latency need
actually justifies it (e.g. bureau pulls at loan origination). A monthly
batch re-score is enough for a 12-month-horizon early-warning tool — this
is not a fraud-detection system that needs millisecond latency, and
over-engineering it to look like one would be the wrong call, not a
stronger one.

## Deployment: where this actually runs

**Important distinction the current public demo link should not obscure:**
the deployed `msme-sentinel.vercel.app` link is a public static demo built
for judging — it does not, and should not, reflect how this would actually
be hosted in production. RBI data-residency expectations for financial
data mean a real deployment runs inside IDBI's own network boundary, not a
public URL:

- **On-prem or a private VPC within an India region** (IDBI's own AMA
  referenced AWS-aligned sandbox infrastructure — AWS Mumbai/Hyderabad
  regions satisfy data-residency requirements for this).
- The scoring service itself is a small, stateless container (single model
  file + a Python inference process) — this is one of the cheapest parts
  of a bank's infrastructure to stand up, not a heavy system.
- The dashboard becomes a UI **inside IDBI's existing internal portal**
  (embedded view or reskinned to IDBI's internal design system — see the
  UI redesign in this same commit for the visual starting point), not a
  separately-hosted public site.

## What changes between this prototype and a production pilot

| | Prototype (this submission) | Production pilot |
|---|---|---|
| Data | Synthetic, generated by `src/data_generator.py` | Real feeds per the ingestion paths above |
| Hosting | Public static site (for judge access) | Private VPC / on-prem, inside IDBI's network |
| Scoring | Batch export to a JSON file, read by a static dashboard | Same model, served via a small API (or the same batch pattern, just against real data) |
| Accounts shown | All 6,000 synthetic borrowers | The bank's actual monitored loan book |
| Auth | None (public demo) | RBAC tied to IDBI's existing identity/access system |
| Refresh cadence | One-off export | Monthly batch re-score (or more frequent, if a specific feed justifies it) |

The architecture doesn't change shape going from left column to right —
only the inputs, hosting boundary, and auth layer do. That's the point:
the modeling and UI work already done here isn't throwaway hackathon code
that gets rebuilt for production, it's the same pipeline pointed at real
data behind a private network.

## Effort estimate

Consistent with the phased cost estimate already in the submission deck:
Phase 1 integration (bureau + AA bank data + GST + NACH bounce, all
existing mature channels) is realistically a **3-4 week integration
effort**, not a multi-quarter project, specifically because none of these
four sources require building new data infrastructure — they require
connecting to infrastructure IDBI already has.
