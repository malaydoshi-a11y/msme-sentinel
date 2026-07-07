let DATA = null;
let currentSort = 'risk';

const ragOrder = { RED: 0, AMBER: 1, GREEN: 2 };
const RAG_COLOR = { RED: '#E1503F', AMBER: '#E8A33D', GREEN: '#34B378' };

function fmtPct(x) { return (x * 100).toFixed(1) + '%'; }

async function init() {
  const res = await fetch('data.json');
  DATA = await res.json();
  renderRagTiles();
  renderGovernance();
  renderSpectrum();
  renderTable();
  wireEvents();
}

function renderGovernance() {
  const m = DATA.portfolio.model_metrics;
  document.getElementById('govBalancedAcc').textContent = (m.balanced_accuracy * 100).toFixed(1) + '%';

  const items = [
    { label: 'AUC-ROC', value: m.auc_roc },
    { label: 'KS-Statistic', value: m.ks_statistic },
    { label: 'Gini Coefficient', value: m.gini_coefficient },
    { label: 'Recall @ Early-Warning Threshold (0.30)', value: m['recall_at_0.30_threshold'] },
  ];
  document.getElementById('govMetricsGrid').innerHTML = items.map(i => `
    <div class="gov-metric-card">
      <div class="gov-metric-value">${i.value}</div>
      <div class="gov-metric-label">${i.label}</div>
    </div>
  `).join('');
}

function renderRagTiles() {
  const dist = DATA.portfolio.rag_distribution;
  const total = DATA.portfolio.total_accounts;
  const order = [
    { key: 'RED', label: 'HIGH RISK · RANK 7–10', cls: 'red' },
    { key: 'AMBER', label: 'WATCHLIST · RANK 4–6', cls: 'amber' },
    { key: 'GREEN', label: 'HEALTHY · RANK 1–3', cls: 'green' },
  ];
  const el = document.getElementById('ragTiles');
  el.innerHTML = order.map(o => `
    <div class="rag-tile ${o.cls}">
      <div class="rag-tile-label">${o.label}</div>
      <div class="rag-tile-value">${fmtPct(dist[o.key] || 0)}</div>
      <div class="rag-tile-sub">${Math.round((dist[o.key] || 0) * total).toLocaleString()} accounts</div>
    </div>
  `).join('');
}

function rankColor(rank) {
  if (rank <= 3) return RAG_COLOR.GREEN;
  if (rank <= 6) return RAG_COLOR.AMBER;
  return RAG_COLOR.RED;
}

function renderSpectrum() {
  const hist = DATA.portfolio.rank_histogram;
  const ctx = document.getElementById('spectrumChart').getContext('2d');
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: hist.map(h => `Rank ${h.rank}`),
      datasets: [{
        data: hist.map(h => h.count),
        backgroundColor: hist.map(h => rankColor(h.rank)),
        borderRadius: 4,
        barPercentage: 0.85,
        categoryPercentage: 1.0,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { enabled: false } },
      scales: {
        x: { ticks: { color: '#6E8983', font: { family: 'IBM Plex Mono', size: 10 }, maxRotation: 0 }, grid: { display: false } },
        y: { display: false }
      }
    }
  });
}

function sortedAccounts() {
  const arr = [...DATA.accounts];
  if (currentSort === 'risk') {
    arr.sort((a, b) => ragOrder[a.rag_status] - ragOrder[b.rag_status] || b.latest_rank - a.latest_rank);
  } else {
    arr.sort((a, b) => a.latest_rank - b.latest_rank);
  }
  return arr;
}

function renderTable(filterText = '') {
  const tbody = document.getElementById('accountsTbody');
  const rows = sortedAccounts().filter(a => {
    if (!filterText) return true;
    const hay = `${a.borrower_id} ${a.loan_type} ${a.business_type} ${a.vintage_bucket}`.toLowerCase();
    return hay.includes(filterText.toLowerCase());
  });
  document.getElementById('accountCount').textContent = `(${rows.length})`;

  tbody.innerHTML = rows.map(a => `
    <tr data-id="${a.borrower_id}">
      <td class="borrower-id">${a.borrower_id}</td>
      <td>${a.loan_type}</td>
      <td>${a.business_type}</td>
      <td>${a.vintage_bucket}</td>
      <td>${a.borrower_category}</td>
      <td class="mono">₹${a.loan_amount_lakhs.toFixed(1)}L</td>
      <td class="score-cell">${a.latest_rank}/10</td>
      <td><span class="badge ${a.rag_status.toLowerCase()}"><span class="dot"></span>${a.rag_status}</span></td>
    </tr>
  `).join('');

  tbody.querySelectorAll('tr').forEach(tr => {
    tr.addEventListener('click', () => openDrawer(tr.dataset.id));
  });
}

function wireEvents() {
  document.getElementById('searchInput').addEventListener('input', (e) => renderTable(e.target.value));
  document.querySelectorAll('.sort-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.sort-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentSort = btn.dataset.sort;
      renderTable(document.getElementById('searchInput').value);
    });
  });
  document.getElementById('drawerClose').addEventListener('click', closeDrawer);
  document.getElementById('scrim').addEventListener('click', closeDrawer);

  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById('tabPortfolio').classList.toggle('hidden', btn.dataset.tab !== 'portfolio');
      document.getElementById('tabGovernance').classList.toggle('hidden', btn.dataset.tab !== 'governance');
    });
  });
}

let trajectoryChartInstance = null;

function openDrawer(borrowerId) {
  const acc = DATA.accounts.find(a => a.borrower_id === borrowerId);
  if (!acc) return;

  const ragCls = acc.rag_status.toLowerCase();
  const smaLabel = { GREEN: 'Standard asset', AMBER: 'SMA-0 / SMA-1 territory', RED: 'SMA-2 territory' }[acc.rag_status];

  const reasonColor = RAG_COLOR[acc.rag_status];
  const reasonsHtml = acc.top_reasons.map(r => `
    <li><span class="rdot" style="background:${reasonColor}"></span>${r}</li>
  `).join('');

  document.getElementById('drawerContent').innerHTML = `
    <div class="dw-id">${acc.borrower_id}</div>
    <div class="dw-meta">${acc.loan_type} &middot; ${acc.business_type} &middot; ${acc.vintage_bucket} vintage &middot; ${acc.borrower_category}</div>

    <div class="dw-score-row">
      <div class="dw-score ${ragCls}">${acc.latest_rank}<span style="font-size:22px;opacity:0.55">/10</span></div>
      <div class="dw-pd">Probability of Default (12mo)<br/><strong style="color:#EDF4F1">${fmtPct(acc.latest_pd)}</strong></div>
    </div>
    <span class="badge ${ragCls}"><span class="dot"></span>${acc.rag_status} &middot; ${smaLabel}</span>

    <div class="dw-section-label">Risk Trajectory &middot; 24-Month Panel</div>
    <div class="dw-chart-wrap"><canvas id="trajectoryChart"></canvas></div>

    <div class="dw-section-label">${acc.rag_status === 'GREEN' ? 'Why this account is healthy' : 'Why this account is flagged'}</div>
    <ul class="reason-list">${reasonsHtml}</ul>

    <div class="dw-section-label">Account Details</div>
    <div class="meta-grid">
      <div class="meta-item"><div class="meta-item-label">Loan Amount</div><div class="meta-item-value mono">₹${acc.loan_amount_lakhs.toFixed(1)} Lakhs</div></div>
      <div class="meta-item"><div class="meta-item-label">Loan Type</div><div class="meta-item-value">${acc.loan_type}</div></div>
      <div class="meta-item"><div class="meta-item-label">Business Segment</div><div class="meta-item-value">${acc.business_type}</div></div>
      <div class="meta-item"><div class="meta-item-label">Borrower Category</div><div class="meta-item-value">${acc.borrower_category}</div></div>
    </div>
  `;

  document.getElementById('drawer').classList.add('open');
  document.getElementById('scrim').classList.add('open');

  if (trajectoryChartInstance) trajectoryChartInstance.destroy();
  const ctx = document.getElementById('trajectoryChart').getContext('2d');
  trajectoryChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: acc.trend.map(t => `M${t.month}`),
      datasets: [{
        data: acc.trend.map(t => t.risk_index),
        borderColor: '#E8672C',
        backgroundColor: 'rgba(232,103,44,0.08)',
        fill: true,
        tension: 0.3,
        pointRadius: 0,
        borderWidth: 2,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: '#6E8983', font: { size: 9 }, maxTicksLimit: 8 }, grid: { display: false } },
        y: {
          min: 0, max: 100,
          title: { display: true, text: 'Risk Index (100 = healthiest)', color: '#6E8983', font: { size: 9 } },
          ticks: { color: '#6E8983', font: { family: 'IBM Plex Mono', size: 9 } },
          grid: { color: 'rgba(237,244,241,0.05)' }
        }
      }
    }
  });
}

function closeDrawer() {
  document.getElementById('drawer').classList.remove('open');
  document.getElementById('scrim').classList.remove('open');
}

init();
