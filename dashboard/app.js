let DATA = null;
let DETAILS = null;
let detailsPromise = null;

let currentSort = 'risk';
let currentPage = 1;
let currentFilters = { rag: 'ALL', loanType: 'ALL' };
let currentSearch = '';
const PAGE_SIZE = 50;

const ragOrder = { RED: 0, AMBER: 1, GREEN: 2 };
const RAG_COLOR = { RED: '#C0392B', AMBER: '#B4790E', GREEN: '#1E8E5A' };
const ACCENT_TEAL = '#00836C';
const TICK_COLOR = '#6C7E77';
const GRID_COLOR = 'rgba(20, 35, 30, 0.06)';

function fmtPct(x) { return (x * 100).toFixed(1) + '%'; }

function fmtMetric(v, kind) {
  if (kind === 'pct') return v.toFixed(1) + '%';
  if (kind === 'ratio') return v.toFixed(3);
  if (kind === 'lakhs') return '₹' + v.toFixed(2) + 'L';
  if (kind === 'score') return Math.round(v);
  return v;
}

window.onerror = function (message, source, lineno, colno, error) {
  console.error('Unhandled error:', message, 'at', (source || '') + ':' + lineno, error || '');
};

async function init() {
  try {
    const res = await fetch('data.json');
    if (!res.ok) throw new Error('HTTP ' + res.status + ' fetching data.json');
    DATA = await res.json();
    renderRagTiles();
    renderGovernance();
    renderAccuracyCallout();
    renderDataSources();
    renderSpectrum();
    renderPortfolioTrend();
    renderTable();
    wireEvents();
    hideStatusOverlay();
  } catch (err) {
    console.error('Failed to load dashboard data:', err);
    showErrorState();
  }
}

function loadDetails() {
  if (DETAILS) return Promise.resolve(DETAILS);
  if (detailsPromise) return detailsPromise;
  detailsPromise = fetch('details.json')
    .then(res => { if (!res.ok) throw new Error('HTTP ' + res.status + ' fetching details.json'); return res.json(); })
    .then(json => { DETAILS = json; return DETAILS; });
  return detailsPromise;
}

function hideStatusOverlay() {
  const el = document.getElementById('statusOverlay');
  if (el) el.remove();
}

function showErrorState() {
  const el = document.getElementById('statusOverlay');
  if (!el) return;
  el.classList.add('is-error');
  el.innerHTML = `
    <div class="status-icon">!</div>
    <div class="status-text">Couldn't load portfolio data &mdash; please refresh.</div>
  `;
}

function renderAccuracyCallout() {
  const el = document.getElementById('portfolioAccuracyNote');
  if (!el) return;
  const pct = (DATA.portfolio.model_metrics.balanced_accuracy * 100).toFixed(1);
  el.innerHTML = `Model validated &middot; <strong>${pct}% balanced accuracy</strong> &middot; <a data-goto-tab="governance">see Model Governance</a>`;
}

function renderDataSources() {
  const el = document.getElementById('dataSourcesRow');
  const sources = DATA.portfolio.data_sources;
  if (!el || !sources) return;
  el.innerHTML = sources.map(ds => `
    <div class="datasource-chip" title="${ds.integration}">
      <span class="datasource-phase p${ds.phase}">P${ds.phase}</span>
      <span class="datasource-label">${ds.label}</span>
    </div>
  `).join('');
}

function switchTab(tabName) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === tabName));
  document.getElementById('tabPortfolio').classList.toggle('hidden', tabName !== 'portfolio');
  document.getElementById('tabGovernance').classList.toggle('hidden', tabName !== 'governance');
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
      plugins: { legend: { display: false }, tooltip: { enabled: true } },
      scales: {
        x: { ticks: { color: TICK_COLOR, font: { family: 'IBM Plex Mono', size: 10 }, maxRotation: 0 }, grid: { display: false } },
        y: { display: false }
      }
    }
  });
}

function renderPortfolioTrend() {
  const trend = DATA.portfolio.trend;
  const ctx = document.getElementById('portfolioTrendChart').getContext('2d');
  const mk = (key, color, fillColor) => ({
    label: key,
    data: trend.map(t => Math.round(t[key.toLowerCase() + '_pct'] * 1000) / 10),
    borderColor: color,
    backgroundColor: fillColor,
    fill: true,
    stack: 'rag',
    pointRadius: 0,
    borderWidth: 1,
    tension: 0.25,
  });
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: trend.map(t => `M${t.month}`),
      datasets: [
        mk('Red', RAG_COLOR.RED, 'rgba(192,57,43,0.65)'),
        mk('Amber', RAG_COLOR.AMBER, 'rgba(180,121,14,0.65)'),
        mk('Green', RAG_COLOR.GREEN, 'rgba(30,142,90,0.65)'),
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { display: true, position: 'bottom', labels: { color: '#44564F', font: { size: 10 }, boxWidth: 10, padding: 12 } },
        tooltip: { mode: 'index', intersect: false, callbacks: { label: (c) => `${c.dataset.label}: ${c.parsed.y}%` } },
      },
      scales: {
        x: { ticks: { color: TICK_COLOR, font: { size: 9 }, maxTicksLimit: 8 }, grid: { display: false } },
        y: { stacked: true, min: 0, max: 100, ticks: { color: TICK_COLOR, font: { family: 'IBM Plex Mono', size: 9 }, callback: v => v + '%' }, grid: { color: GRID_COLOR } }
      }
    }
  });
}

function filteredSortedAccounts() {
  let arr = DATA.accounts;
  if (currentFilters.rag !== 'ALL') arr = arr.filter(a => a.rag_status === currentFilters.rag);
  if (currentFilters.loanType !== 'ALL') arr = arr.filter(a => a.loan_type === currentFilters.loanType);
  if (currentSearch) {
    const q = currentSearch.toLowerCase();
    arr = arr.filter(a => `${a.borrower_id} ${a.loan_type} ${a.business_type} ${a.vintage_bucket}`.toLowerCase().includes(q));
  }
  arr = [...arr];
  if (currentSort === 'risk') {
    arr.sort((a, b) => ragOrder[a.rag_status] - ragOrder[b.rag_status] || b.latest_rank - a.latest_rank);
  } else if (currentSort === 'worsened') {
    arr.sort((a, b) => b.rank_delta - a.rank_delta || ragOrder[a.rag_status] - ragOrder[b.rag_status]);
  } else {
    arr.sort((a, b) => a.latest_rank - b.latest_rank);
  }
  return arr;
}

function renderDelta(delta) {
  if (!delta) return '';
  if (delta > 0) return ` <span class="rank-delta worse">&#9650;${delta}</span>`;
  return ` <span class="rank-delta better">&#9660;${Math.abs(delta)}</span>`;
}

function renderTable() {
  const all = filteredSortedAccounts();
  const totalPages = Math.max(1, Math.ceil(all.length / PAGE_SIZE));
  if (currentPage > totalPages) currentPage = totalPages;
  const start = (currentPage - 1) * PAGE_SIZE;
  const rows = all.slice(start, start + PAGE_SIZE);

  document.getElementById('accountCount').textContent = `(${all.length.toLocaleString()})`;

  const tbody = document.getElementById('accountsTbody');
  tbody.innerHTML = rows.map(a => `
    <tr data-id="${a.borrower_id}">
      <td class="borrower-id">${a.borrower_id}</td>
      <td>${a.loan_type}</td>
      <td>${a.business_type}</td>
      <td>${a.vintage_bucket}</td>
      <td>${a.borrower_category}</td>
      <td class="mono">₹${a.loan_amount_lakhs.toFixed(1)}L</td>
      <td class="score-cell">${a.latest_rank}/10${renderDelta(a.rank_delta)}</td>
      <td><span class="badge ${a.rag_status.toLowerCase()}"><span class="dot"></span>${a.rag_status}</span></td>
    </tr>
  `).join('');

  tbody.querySelectorAll('tr').forEach(tr => {
    tr.addEventListener('click', () => openDrawer(tr.dataset.id));
  });

  document.getElementById('pageInfo').textContent = `Page ${currentPage} of ${totalPages}`;
  document.getElementById('pagePrev').disabled = currentPage <= 1;
  document.getElementById('pageNext').disabled = currentPage >= totalPages;
}

function wireEvents() {
  document.getElementById('searchInput').addEventListener('input', (e) => {
    currentSearch = e.target.value;
    currentPage = 1;
    renderTable();
  });
  document.getElementById('filterRag').addEventListener('change', (e) => {
    currentFilters.rag = e.target.value;
    currentPage = 1;
    renderTable();
  });
  document.getElementById('filterLoanType').addEventListener('change', (e) => {
    currentFilters.loanType = e.target.value;
    currentPage = 1;
    renderTable();
  });
  document.querySelectorAll('.sort-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.sort-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentSort = btn.dataset.sort;
      currentPage = 1;
      renderTable();
    });
  });
  document.getElementById('pagePrev').addEventListener('click', () => {
    if (currentPage > 1) { currentPage--; renderTable(); window.scrollTo({ top: 0, behavior: 'smooth' }); }
  });
  document.getElementById('pageNext').addEventListener('click', () => {
    currentPage++; renderTable(); window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  document.getElementById('drawerClose').addEventListener('click', closeDrawer);
  document.getElementById('scrim').addEventListener('click', closeDrawer);

  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => switchTab(btn.dataset.tab));
  });

  const accuracyLink = document.querySelector('#portfolioAccuracyNote [data-goto-tab]');
  if (accuracyLink) {
    accuracyLink.addEventListener('click', (e) => {
      e.preventDefault();
      switchTab(accuracyLink.dataset.gotoTab);
    });
  }
}

function runwayText(acc) {
  const r = acc.est_runway_months;
  if (r === null || r === undefined) {
    if (acc.latest_rank >= 10) return 'Already at the highest risk tier.';
    return 'Currently stable &mdash; not on a worsening trend.';
  }
  if (r < 1) return `Est. <strong>&lt;1 month</strong> to next risk tier at the current trend.`;
  if (r > 12) return `Est. <strong>12+ months</strong> to next risk tier at the current trend.`;
  const m = Math.round(r);
  return `Est. <strong>~${m} month${m === 1 ? '' : 's'}</strong> to next risk tier at the current trend.`;
}

function renderReasonsList(reasons, reasonColor) {
  return reasons.map(r => {
    const metricsHtml = r.metrics.map(m => {
      const valStr = fmtMetric(m.value, m.format);
      const phaseTag = m.source_phase ? `<span class="datasource-phase p${m.source_phase} reason-phase">P${m.source_phase}</span>` : '';
      const text = (m.baseline !== null && m.baseline !== undefined)
        ? `${valStr} (${m.baseline_label}: ${fmtMetric(m.baseline, m.format)})`
        : valStr;
      return `<div class="reason-metric">${phaseTag}${text}</div>`;
    }).join('');
    return `<li><span class="rdot" style="background:${reasonColor}"></span><div class="rtext"><div>${r.label}</div>${metricsHtml}</div></li>`;
  }).join('');
}

let trajectoryChartInstance = null;

async function openDrawer(borrowerId) {
  const acc = DATA.accounts.find(a => a.borrower_id === borrowerId);
  if (!acc) return;

  const ragCls = acc.rag_status.toLowerCase();
  const smaLabel = { GREEN: 'Standard asset', AMBER: 'SMA-0 / SMA-1 territory', RED: 'SMA-2 territory' }[acc.rag_status];

  document.getElementById('drawerContent').innerHTML = `
    <div class="dw-id">${acc.borrower_id}</div>
    <div class="dw-meta">${acc.loan_type} &middot; ${acc.business_type} &middot; ${acc.vintage_bucket} vintage &middot; ${acc.borrower_category}</div>

    <div class="dw-score-row">
      <div class="dw-score ${ragCls}">${acc.latest_rank}<span style="font-size:22px;opacity:0.55">/10</span></div>
      <div class="dw-pd">Probability of Default (12mo)<br/><strong style="color:#14231E">${fmtPct(acc.latest_pd)}</strong></div>
    </div>
    <span class="badge ${ragCls}"><span class="dot"></span>${acc.rag_status} &middot; ${smaLabel}</span>
    <div class="dw-runway">${runwayText(acc)}</div>

    <div class="dw-section-label">Risk Trajectory &middot; 24-Month Panel</div>
    <div class="dw-chart-wrap"><canvas id="trajectoryChart"></canvas></div>

    <div class="dw-section-label">${acc.rag_status === 'GREEN' ? 'Why this account is healthy' : 'Why this account is flagged'}</div>
    <ul class="reason-list" id="reasonList"><li><span class="rdot" style="background:#6C7E77"></span><div class="rtext"><div>Loading&hellip;</div></div></li></ul>

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

  try {
    const details = await loadDetails();
    const detail = details[borrowerId];
    if (!detail) return;

    const reasonColor = RAG_COLOR[acc.rag_status];
    const reasonListEl = document.getElementById('reasonList');
    if (reasonListEl) reasonListEl.innerHTML = renderReasonsList(detail.top_reasons, reasonColor);

    if (trajectoryChartInstance) trajectoryChartInstance.destroy();
    const canvas = document.getElementById('trajectoryChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    trajectoryChartInstance = new Chart(ctx, {
      type: 'line',
      data: {
        labels: detail.trend.map(t => `M${t.month}`),
        datasets: [{
          data: detail.trend.map(t => t.risk_index),
          borderColor: ACCENT_TEAL,
          backgroundColor: 'rgba(0,131,108,0.08)',
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
          x: { ticks: { color: TICK_COLOR, font: { size: 9 }, maxTicksLimit: 8 }, grid: { display: false } },
          y: {
            min: 0, max: 100,
            title: { display: true, text: 'Risk Index (100 = healthiest)', color: TICK_COLOR, font: { size: 9 } },
            ticks: { color: TICK_COLOR, font: { family: 'IBM Plex Mono', size: 9 } },
            grid: { color: GRID_COLOR }
          }
        }
      }
    });
  } catch (err) {
    console.error('Failed to load account detail:', err);
    const reasonListEl = document.getElementById('reasonList');
    if (reasonListEl) reasonListEl.innerHTML = '<li><span class="rdot" style="background:#C0392B"></span><div class="rtext"><div>Couldn\'t load detail &mdash; please try again.</div></div></li>';
  }
}

function closeDrawer() {
  document.getElementById('drawer').classList.remove('open');
  document.getElementById('scrim').classList.remove('open');
}

init();
