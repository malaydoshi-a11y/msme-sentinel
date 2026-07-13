"""
Data Ingestion Manifest
========================
The single source of truth for "where does each signal come from, and how
mature is that channel" -- referenced by both the feature pipeline and the
dashboard export, so the Data Sources panel a judge sees in the product is
derived from the same metadata the model itself is built on, not a
separately-maintained decorative label that can drift out of sync.

Every source is tagged with its real-world adoption phase (see
docs/data_feasibility_tiering.md for the full reasoning) and the specific
integration a Phase-N implementation would call in production (see
docs/integration_architecture.md). Today every source is backed by the
synthetic panel; swapping to IDBI's real sandbox means replacing what each
source's raw columns are populated FROM, not restructuring the pipeline --
the phase tags and column ownership below are already the real seam.
"""

from dataclasses import dataclass, field


@dataclass
class DataSource:
    key: str
    label: str
    phase: int  # 1 = ready today, 2 = maturing, 3 = opportunistic
    integration: str  # what a real Phase-N implementation would call
    columns: list = field(default_factory=list)  # raw columns this source owns


DATA_SOURCES = [
    DataSource(
        "bureau", "Bureau / CIBIL MSME Rank", 1,
        "IDBI's existing bureau subscription (live pull, already operational)",
        ["bureau_score"],
    ),
    DataSource(
        "bank_txn", "Bank transactions (Account Aggregator)", 1,
        "RBI Account Aggregator consent flow",
        ["avg_monthly_inflow_lakhs", "overdraft_utilization_pct"],
    ),
    DataSource(
        "gst", "GST returns (GSTR-1/3B via GSP/AA)", 1,
        "GSP API or AA-based GST consent",
        ["gst_turnover_consistency_ratio", "gst_compliance_score", "gst_registered"],
    ),
    DataSource(
        "nach_bounce", "NACH / cheque bounce (core banking)", 1,
        "Core banking's own database -- nightly batch (read-replica or CSV/SFTP export)",
        ["bounce_rate_pct"],
    ),
    DataSource(
        "upi", "UPI transaction behaviour", 2,
        "AA consent, added once a borrower completes onboarding -- coverage still maturing",
        ["upi_cashflow_volatility"],
    ),
    DataSource(
        "epfo", "EPFO contributions", 3,
        "EPFO employer portal API -- bespoke tie-up; structurally absent (not just thin) for MSMEs with no registered employees",
        ["epfo_contribution_regularity_pct"],
    ),
    DataSource(
        "utility", "Utility payment history", 3,
        "No mature, interoperable aggregator in India today -- would need a bespoke state electricity board tie-up",
        ["utility_payment_ontime_pct"],
    ),
]

# raw column -> source key, built once from the manifest above so the
# mapping can never drift from the sources it's describing
COLUMN_SOURCE = {col: ds.key for ds in DATA_SOURCES for col in ds.columns}


def get_manifest():
    """JSON-serializable manifest for the dashboard export."""
    return [
        {"key": ds.key, "label": ds.label, "phase": ds.phase, "integration": ds.integration}
        for ds in DATA_SOURCES
    ]
