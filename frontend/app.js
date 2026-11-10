/**
 * HR Routine Requests Resolver - Interactive Frontend Application
 */

// Application State
const state = {
  activeTab: 'tab-dashboard',
  isBackendConnected: false,
  metrics: null,
  ticketsData: {
    total: 5000,
    page: 1,
    limit: 20,
    total_pages: 250,
    tickets: []
  },
  filters: {
    search: '',
    category: '',
    decision: '',
    sla_status: '',
    sensitive: ''
  },
  policies: [],
  charts: {}
};

// Quick Test Presets
const PRESETS = {
  benefits: {
    desc: "Can I add my newborn child to my health insurance coverage?",
    confidentiality: "Internal",
    priority: "Medium",
    audience: "Employee"
  },
  harassment: {
    desc: "I need to file a confidential complaint regarding discrimination and harassment by my manager.",
    confidentiality: "Restricted",
    priority: "Critical",
    audience: "Employee"
  },
  ambiguous: {
    desc: "Please help me with my issue, I need assistance.",
    confidentiality: "Internal",
    priority: "Low",
    audience: "Employee"
  },
  payroll: {
    desc: "When is the cut-off date for payroll tax submissions and where can I view my payslip?",
    confidentiality: "Internal",
    priority: "High",
    audience: "Employee"
  },
  leave: {
    desc: "How do I check my annual leave balance and request vacation time off?",
    confidentiality: "Internal",
    priority: "Medium",
    audience: "Employee"
  }
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
  setupNavigation();
  setupPresets();
  setupResolverForm();
  setupTicketFilters();
  setupModal();
  
  // Test connection to backend
  checkBackendConnection().then(() => {
    loadDashboardMetrics();
    loadTickets();
    loadPolicies();
  });
});

/**
 * Navigation tabs setup
 */
function setupNavigation() {
  const tabs = document.querySelectorAll('.tab-btn');
  tabs.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-tab');
      switchTab(targetId);
    });
  });
}

function switchTab(targetId) {
  state.activeTab = targetId;

  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-tab') === targetId);
  });

  document.querySelectorAll('.tab-content').forEach(section => {
    section.classList.toggle('active', section.id === targetId);
  });

  if (targetId === 'tab-dashboard') {
    renderCharts();
  }
}

/**
 * Backend connectivity check
 */
async function checkBackendConnection() {
  const pill = document.getElementById('backend-status-pill');
  const text = document.getElementById('backend-status-text');

  try {
    const res = await fetch('/api/metrics');
    if (res.ok) {
      state.isBackendConnected = true;
      state.metrics = await res.json();
      pill.style.background = 'rgba(16, 185, 129, 0.15)';
      pill.style.color = '#34d399';
      text.textContent = 'Connected: Local Engine API';
      return;
    }
  } catch (err) {
    console.warn('Backend API not reachable directly. Using local simulation fallback.', err);
  }

  // Fallback to offline mode
  state.isBackendConnected = false;
  pill.style.background = 'rgba(245, 158, 11, 0.15)';
  pill.style.color = '#fbbf24';
  text.textContent = 'Client Preview Mode';
  state.metrics = getFallbackMetrics();
}

/**
 * Load and display Dashboard KPIs and Charts
 */
function loadDashboardMetrics() {
  const m = state.metrics.summary || state.metrics;

  document.getElementById('kpi-total-tickets').textContent = Number(m.total_tickets || 5000).toLocaleString();
  document.getElementById('kpi-classification-rate').textContent = (m.classification_rate || 94.08) + '%';
  document.getElementById('kpi-sla-compliance').textContent = (m.sla_compliance_rate || 92.6) + '%';
  document.getElementById('kpi-policy-answers').textContent = Number(m.policy_answers || 3758).toLocaleString();
  document.getElementById('kpi-sensitive-tickets').textContent = Number(m.sensitive_tickets || 946).toLocaleString();
  document.getElementById('kpi-mismatch-rate').textContent = (m.routing_mismatch_rate || 21.78) + '%';

  renderCharts();
}

/**
 * Render visual charts via Chart.js
 */
function renderCharts() {
  if (typeof Chart === 'undefined') return;

  const m = state.metrics;
  const categories = m.categories || {
    benefits: 1350,
    leave: 1280,
    payroll: 1120,
    onboarding: 954,
    employee_relations: 296
  };

  const queues = m.queues || {
    HR_BENEFITS: 1250,
    HR_LEAVE: 1180,
    HR_PAYROLL: 1040,
    HR_ONBOARDING: 880,
    HR_EMPLOYEE_RELATIONS: 946,
    HR_GENERAL: 296
  };

  const decisions = m.decisions || {
    ANSWER_WITH_POLICY: 3758,
    ESCALATE_TO_HR: 956,
    REQUEST_CLARIFICATION: 286
  };

  const prioritySla = m.priority_sla || {
    Critical: { met: 380, breached: 42 },
    High: { met: 1150, breached: 98 },
    Medium: { met: 1850, breached: 134 },
    Low: { met: 1250, breached: 96 }
  };

  // 1. Categories Doughnut Chart
  renderChart('categoryChart', 'doughnut', {
    labels: Object.keys(categories).map(c => c.replace('_', ' ').toUpperCase()),
    datasets: [{
      data: Object.values(categories),
      backgroundColor: ['#6366f1', '#10b981', '#f59e0b', '#3b82f6', '#ec4899', '#8b5cf6'],
      borderWidth: 2,
      borderColor: '#ffffff'
    }]
  }, { cutout: '65%' });

  // 2. SLA Performance Stacked Bar Chart
  const prioLabels = Object.keys(prioritySla);
  renderChart('slaChart', 'bar', {
    labels: prioLabels,
    datasets: [
      {
        label: 'SLA Met',
        data: prioLabels.map(p => prioritySla[p].met),
        backgroundColor: '#10b981',
        borderRadius: 6
      },
      {
        label: 'SLA Breached',
        data: prioLabels.map(p => prioritySla[p].breached),
        backgroundColor: '#f43f5e',
        borderRadius: 6
      }
    ]
  }, {
    scales: {
      x: { stacked: true },
      y: { stacked: true }
    }
  });

  // 3. Resolution Decisions Pie
  renderChart('decisionChart', 'pie', {
    labels: ['Answer with Policy', 'Escalate to Specialist HR', 'Request Clarification'],
    datasets: [{
      data: [
        decisions.ANSWER_WITH_POLICY || 3758,
        decisions.ESCALATE_TO_HR || 956,
        decisions.REQUEST_CLARIFICATION || 286
      ],
      backgroundColor: ['#10b981', '#f43f5e', '#0ea5e9'],
      borderWidth: 2,
      borderColor: '#ffffff'
    }]
  });

  // 4. Queues Bar Chart
  renderChart('queueChart', 'bar', {
    labels: Object.keys(queues).map(q => q.replace('HR_', '')),
    datasets: [{
      label: 'Assigned Requests',
      data: Object.values(queues),
      backgroundColor: '#4f46e5',
      borderRadius: 6
    }]
  }, {
    plugins: { legend: { display: false } }
  });
}

function renderChart(canvasId, type, data, extraOptions = {}) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  if (state.charts[canvasId]) {
    state.charts[canvasId].destroy();
  }

  const defaultOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
        labels: { boxWidth: 12, font: { family: 'Inter', size: 11 } }
      }
    }
  };

  state.charts[canvasId] = new Chart(canvas, {
    type,
    data,
    options: { ...defaultOptions, ...extraOptions }
  });
}

/**
 * Setup Quick Presets
 */
function setupPresets() {
  document.querySelectorAll('.preset-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const key = chip.getAttribute('data-preset');
      const preset = PRESETS[key];
      if (!preset) return;

      document.getElementById('sim-description').value = preset.desc;
      document.getElementById('sim-confidentiality').value = preset.confidentiality;
      document.getElementById('sim-priority').value = preset.priority;
      document.getElementById('sim-audience').value = preset.audience;

      // Auto trigger resolution
      runResolution();
    });
  });
}

/**
 * Setup Resolver Form
 */
function setupResolverForm() {
  const form = document.getElementById('resolver-form');
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    runResolution();
  });
}

/**
 * Execute Resolution Engine Simulation
 */
async function runResolution() {
  const desc = document.getElementById('sim-description').value.trim();
  const conf = document.getElementById('sim-confidentiality').value;
  const prio = document.getElementById('sim-priority').value;
  const audience = document.getElementById('sim-audience').value;
  const asOf = document.getElementById('sim-date').value;

  if (!desc) return;

  const btn = document.getElementById('btn-run-simulation');
  btn.disabled = true;
  btn.innerHTML = `<span class="status-pulse"></span> Evaluating Rules &amp; Policies...`;

  try {
    let result;
    if (state.isBackendConnected) {
      const res = await fetch('/api/resolve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          description: desc,
          confidentiality: conf,
          priority: prio,
          audience: audience,
          as_of_date: asOf
        })
      });
      result = await res.json();
    } else {
      // Local client fallback evaluation
      result = simulateResolutionClient(desc, conf, prio, audience, asOf);
    }

    displayResolutionResult(result);
  } catch (err) {
    console.error('Resolution failed:', err);
    alert('Failed to evaluate request: ' + err.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
      Execute Resolution Engine
    `;
  }
}

/**
 * Display Pipeline Resolution Outcome
 */
function displayResolutionResult(data) {
  const p = data.pipeline;
  const banner = document.getElementById('sim-decision-card');
  const badge = document.getElementById('sim-decision-badge');
  const heading = document.getElementById('sim-decision-heading');
  const summary = document.getElementById('sim-decision-summary');

  // Decision Banner
  banner.className = 'decision-card';
  badge.textContent = p.resolution.decision;

  if (p.resolution.decision === 'ANSWER_WITH_POLICY') {
    banner.classList.add('answer');
    heading.textContent = 'Auto-Answer Prepared with Verified Policy';
    const policyTitle = p.resolution.policy_doc ? p.resolution.policy_doc.policy_title : 'Policy Document';
    const versionId = p.resolution.policy_reference || 'VER-POL-HR-2026-001-03';
    summary.innerHTML = `
      Applicable policy verified: <strong>${policyTitle} (${versionId})</strong>.<br/>
      <div style="margin-top: 0.5rem; padding: 0.5rem; background: rgba(255,255,255,0.7); border-radius: 6px; font-family: monospace; font-size: 0.8rem;">
        "${p.resolution.policy_version?.policy_text || 'Synthetic policy content for ' + versionId}"
      </div>
    `;
  } else if (p.resolution.decision === 'ESCALATE_TO_HR') {
    banner.classList.add('escalate');
    heading.textContent = 'Escalated to Specialist HR Queue';
    summary.textContent = `
      This request requires specialist human intervention (Reason: ${p.resolution.reason}). Routed immediately to ${p.routing.recommended_queue}.
    `;
  } else {
    banner.classList.add('clarify');
    heading.textContent = 'Clarification Required From Employee';
    summary.textContent = `
      The inquiry is ambiguous or missing essential details. An automated prompt will be sent to the employee to specify their request.
    `;
  }

  // Step 1: Classification
  document.getElementById('step-class-conf').textContent = `Confidence: ${Math.round(p.classification.confidence * 100)}%`;
  document.getElementById('step-class-reason').textContent = `Reason: ${p.classification.reason}`;
  document.getElementById('step-class-category').textContent = `Category: ${p.classification.category}`;
  const sensTag = document.getElementById('step-class-sensitive');
  if (p.classification.sensitive) {
    sensTag.style.display = 'inline-flex';
    sensTag.textContent = 'Restricted / Sensitive: TRUE';
  } else {
    sensTag.style.display = 'none';
  }

  // Step 2: Ambiguity
  const ambTag = document.getElementById('step-ambiguity-status');
  if (p.ambiguity.is_ambiguous) {
    ambTag.className = 'kpi-badge badge-amber';
    ambTag.textContent = 'Ambiguous Request';
    document.getElementById('step-ambiguity-desc').textContent = 'Flagged missing actionable context (e.g. vague assistance phrasing).';
  } else {
    ambTag.className = 'kpi-badge badge-green';
    ambTag.textContent = 'Clear Context';
    document.getElementById('step-ambiguity-desc').textContent = 'Contains specific context suitable for deterministic resolution.';
  }

  // Step 3: Routing
  document.getElementById('step-routing-queue').textContent = `Queue: ${p.routing.recommended_queue}`;
  document.getElementById('step-routing-reason').textContent = `Reason: ${p.routing.routing_reason || 'Departmental match'} ${p.routing.priority_route ? '(Priority Route)' : ''}`;

  // Step 4: Policy & Citation
  const polTag = document.getElementById('step-policy-status');
  if (p.resolution.citation_valid) {
    polTag.className = 'kpi-badge badge-green';
    polTag.textContent = 'Citation Valid';
    document.getElementById('step-policy-text').innerHTML = `Referenced: <strong>${p.resolution.policy_reference}</strong>. Active status and audience constraints matched.`;
  } else {
    polTag.className = 'kpi-badge badge-rose';
    polTag.textContent = p.resolution.policy_reference ? 'Citation Invalid/Expired' : 'No Citation';
    document.getElementById('step-policy-text').textContent = 'No active and effective published policy version was verified for this query.';
  }

  // Step 5: SLA Prediction
  document.getElementById('step-sla-hours').textContent = `Target SLA: ${p.sla.target_hours}.0h`;
  document.getElementById('step-sla-desc').textContent = `${p.sla.business_hours_summary}`;
}

/**
 * Setup Ticket Filters and Pagination
 */
function setupTicketFilters() {
  const searchInput = document.getElementById('table-search');
  let debounceTimeout;
  searchInput.addEventListener('input', () => {
    clearTimeout(debounceTimeout);
    debounceTimeout = setTimeout(() => {
      state.filters.search = searchInput.value;
      state.ticketsData.page = 1;
      loadTickets();
    }, 250);
  });

  const catSelect = document.getElementById('filter-category');
  catSelect.addEventListener('change', () => {
    state.filters.category = catSelect.value;
    state.ticketsData.page = 1;
    loadTickets();
  });

  const decSelect = document.getElementById('filter-decision');
  decSelect.addEventListener('change', () => {
    state.filters.decision = decSelect.value;
    state.ticketsData.page = 1;
    loadTickets();
  });

  const slaSelect = document.getElementById('filter-sla');
  slaSelect.addEventListener('change', () => {
    state.filters.sla_status = slaSelect.value;
    state.ticketsData.page = 1;
    loadTickets();
  });

  const sensSelect = document.getElementById('filter-sensitive');
  sensSelect.addEventListener('change', () => {
    state.filters.sensitive = sensSelect.value;
    state.ticketsData.page = 1;
    loadTickets();
  });

  document.getElementById('btn-prev-page').addEventListener('click', () => {
    if (state.ticketsData.page > 1) {
      state.ticketsData.page--;
      loadTickets();
    }
  });

  document.getElementById('btn-next-page').addEventListener('click', () => {
    if (state.ticketsData.page < state.ticketsData.total_pages) {
      state.ticketsData.page++;
      loadTickets();
    }
  });
}

/**
 * Load Tickets List
 */
async function loadTickets() {
  const tbody = document.getElementById('tickets-table-body');
  tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; padding: 2rem;">Loading tickets...</td></tr>`;

  if (state.isBackendConnected) {
    try {
      const q = new URLSearchParams({
        page: state.ticketsData.page,
        limit: state.ticketsData.limit,
        search: state.filters.search,
        category: state.filters.category,
        decision: state.filters.decision,
        sla_status: state.filters.sla_status,
        sensitive: state.filters.sensitive
      });

      const res = await fetch(`/api/tickets?${q.toString()}`);
      state.ticketsData = await res.json();
    } catch (err) {
      console.warn('Failed to load tickets from API, using fallback:', err);
      state.ticketsData = getFallbackTickets(state.ticketsData.page, state.ticketsData.limit, state.filters);
    }
  } else {
    state.ticketsData = getFallbackTickets(state.ticketsData.page, state.ticketsData.limit, state.filters);
  }

  renderTicketsTable();
}

/**
 * Render Tickets Table Rows
 */
function renderTicketsTable() {
  const tbody = document.getElementById('tickets-table-body');
  const d = state.ticketsData;

  document.getElementById('page-total').textContent = Number(d.total).toLocaleString();
  document.getElementById('tab-ticket-count').textContent = Number(d.total).toLocaleString();
  const start = d.total === 0 ? 0 : (d.page - 1) * d.limit + 1;
  const end = Math.min(d.total, d.page * d.limit);
  document.getElementById('page-start').textContent = start;
  document.getElementById('page-end').textContent = end;
  document.getElementById('page-current-display').textContent = `Page ${d.page} / ${d.total_pages}`;

  document.getElementById('btn-prev-page').disabled = d.page <= 1;
  document.getElementById('btn-next-page').disabled = d.page >= d.total_pages;

  if (!d.tickets || d.tickets.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; padding: 2rem; color: #64748b;">No matching tickets found.</td></tr>`;
    return;
  }

  tbody.innerHTML = d.tickets.map(t => {
    const isSensitive = String(t.sensitive).toLowerCase() === 'true';
    const isSlaMet = t.sla_status === 'MET';

    let decisionTag = `<span class="tag tag-policy">POLICY</span>`;
    if (t.decision === 'ESCALATE_TO_HR') {
      decisionTag = `<span class="tag tag-escalate">ESCALATE</span>`;
    } else if (t.decision === 'REQUEST_CLARIFICATION') {
      decisionTag = `<span class="tag tag-clarify">CLARIFY</span>`;
    }

    const slaTag = isSlaMet
      ? `<span class="tag tag-sla-met">MET</span>`
      : `<span class="tag tag-sla-breach">BREACHED</span>`;

    const sensitivePill = isSensitive
      ? `<span class="tag tag-sensitive" style="margin-left: 4px;">RESTRICTED</span>`
      : ``;

    return `
      <tr onclick="openTicketDetail('${t.ticket_id}')">
        <td style="font-family: monospace; font-weight: 600; color: #4338ca;">
          ${t.ticket_id}
          ${sensitivePill}
        </td>
        <td>
          <div style="font-weight: 600;">${t.employee_id}</div>
          <div style="font-size: 0.72rem; color: #64748b;">${t.department_name || t.department_id || 'DEPT'}</div>
        </td>
        <td>
          <span class="tag" style="background:#f1f5f9; color:#334155;">${t.predicted_category || t.source_category}</span>
        </td>
        <td style="max-width: 280px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${t.description || ''}">
          ${t.description || 'Routine employee request'}
        </td>
        <td>
          <span style="font-family: monospace; font-size: 0.76rem; font-weight: 600;">${t.recommended_queue || 'HR_GENERAL'}</span>
        </td>
        <td>${decisionTag}</td>
        <td style="font-family: monospace; font-size: 0.75rem; color: #64748b;">
          ${t.policy_version_id || '—'}
        </td>
        <td>${slaTag}</td>
        <td style="font-size: 0.78rem;">
          <strong>${t.sla_actual_hours ?? 0}h</strong> / ${t.sla_target_hours || 40}h
        </td>
      </tr>
    `;
  }).join('');
}

/**
 * Open Ticket Detail Modal
 */
async function openTicketDetail(ticketId) {
  const modal = document.getElementById('ticket-modal');

  document.getElementById('modal-ticket-id').textContent = ticketId;
  document.getElementById('modal-description').textContent = 'Loading ticket details...';
  modal.classList.add('active');

  let data;
  if (state.isBackendConnected) {
    try {
      const res = await fetch(`/api/tickets/${ticketId}`);
      data = await res.json();
    } catch (err) {
      console.warn('API error, using local ticket fallback', err);
      data = getFallbackTicketDetail(ticketId);
    }
  } else {
    data = getFallbackTicketDetail(ticketId);
  }

  const t = data.ticket;
  document.getElementById('modal-ticket-meta').textContent = `Created: ${t.created_at || '2026-01-02'} • Priority: ${t.priority || 'Medium'} • Confidentiality: ${t.confidentiality || 'Internal'}`;
  document.getElementById('modal-description').textContent = t.description || 'No description provided';
  document.getElementById('modal-employee-id').textContent = t.employee_id || 'EMP-UNKNOWN';
  document.getElementById('modal-employee-dept').textContent = `${t.department_name || t.department_id || 'HR'} • ${t.employee_location || 'Global'} (${t.employee_type || 'Full-time'})`;
  document.getElementById('modal-decision').textContent = t.decision;
  document.getElementById('modal-queue').textContent = `Queue: ${t.recommended_queue || 'HR_GENERAL'}`;

  const slaBox = document.getElementById('modal-sla-badge');
  const isSlaMet = t.sla_status === 'MET';
  slaBox.innerHTML = isSlaMet
    ? `<span class="tag tag-sla-met">SLA MET</span>`
    : `<span class="tag tag-sla-breach">SLA BREACHED</span>`;
  document.getElementById('modal-sla-hours').textContent = `Actual: ${t.sla_actual_hours || 0}h / Target: ${t.sla_target_hours || 40}h`;

  // Policy Citation
  const policyBox = document.getElementById('modal-policy-box');
  if (data.policy) {
    policyBox.style.display = 'block';
    document.getElementById('modal-policy-title').textContent = `${data.policy.title} (${data.policy.version_id})`;
    document.getElementById('modal-policy-text').textContent = data.policy.policy_text || 'Active policy verified.';
  } else if (t.policy_version_id) {
    policyBox.style.display = 'block';
    document.getElementById('modal-policy-title').textContent = `Policy Citation: ${t.policy_version_id}`;
    document.getElementById('modal-policy-text').textContent = 'Valid citation identified and confirmed effective for date of request.';
  } else {
    policyBox.style.display = 'none';
  }

  // Messages Timeline
  const timeline = document.getElementById('modal-timeline');
  const msgs = data.messages || [];
  if (msgs.length === 0) {
    timeline.innerHTML = `<div style="color: #64748b; font-size: 0.82rem;">No message history recorded.</div>`;
  } else {
    timeline.innerHTML = msgs.map(m => `
      <div class="timeline-item">
        <div class="timeline-dot"></div>
        <div class="timeline-header">
          <strong>${m.sender_type} (${m.message_type})</strong>
          <span>${m.created_at || ''}</span>
        </div>
        <div class="timeline-bubble">${m.message_text}</div>
      </div>
    `).join('');
  }
}

/**
 * Setup Modal Close Button & Backdrop
 */
function setupModal() {
  const modal = document.getElementById('ticket-modal');
  const closeBtn = document.getElementById('modal-close-btn');

  closeBtn.addEventListener('click', () => modal.classList.remove('active'));
  modal.addEventListener('click', (e) => {
    if (e.target === modal) modal.classList.remove('active');
  });
}

/**
 * Load Policy Knowledge Base
 */
async function loadPolicies() {
  const container = document.getElementById('policies-container');

  let list = [];
  if (state.isBackendConnected) {
    try {
      const res = await fetch('/api/policies');
      list = await res.json();
    } catch (e) {
      list = getFallbackPolicies();
    }
  } else {
    list = getFallbackPolicies();
  }

  container.innerHTML = list.map(p => `
    <div class="policy-card" onclick="this.classList.toggle('open')">
      <div class="policy-header">
        <div>
          <span style="font-family: monospace; font-weight: 700; color: #4338ca; margin-right: 0.5rem;">${p.policy_id}</span>
          <strong style="font-size: 0.95rem;">${p.policy_title}</strong>
          <span class="tag tag-policy" style="margin-left: 0.5rem;">${p.lifecycle_state || 'Published'}</span>
        </div>
        <div style="font-size: 0.78rem; color: #64748b;">
          Audience: <strong>${p.audience || 'All'}</strong> • ${(p.versions || []).length} Versions ▾
        </div>
      </div>
      <div class="policy-content">
        <div style="font-size: 0.78rem; font-weight: 700; color: #475569; margin-bottom: 0.5rem; text-transform: uppercase;">
          Policy Versions History
        </div>
        ${(p.versions || []).map(v => `
          <div style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 0.75rem; margin-bottom: 0.5rem;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
              <strong style="font-family: monospace; font-size: 0.82rem; color: #1e1b4b;">${v.version_id} (v${v.version_number})</strong>
              <span class="tag ${v.status === 'Active' ? 'tag-sla-met' : 'tag-clarify'}">${v.status}</span>
            </div>
            <div style="font-size: 0.78rem; color: #64748b; margin-bottom: 0.4rem;">
              Effective: ${v.effective_from || '—'} to ${v.effective_to || 'Indefinite'}
            </div>
            <div style="font-size: 0.82rem; color: #334155; font-style: italic;">
              "${v.policy_text || 'Synthetic policy content'}"
            </div>
          </div>
        `).join('')}
      </div>
    </div>
  `).join('');
}

/**
 * CLIENT-SIDE SIMULATION LOGIC (Fallback when API is not running)
 */
function simulateResolutionClient(desc, conf, priority, audience, asOf) {
  const norm = desc.toLowerCase();

  // 1. Classification
  let cat = 'benefits';
  let confScore = 0.8;
  let sensitive = false;
  let reason = 'KEYWORD_MATCH';

  if (norm.includes('harassment') || norm.includes('misconduct') || norm.includes('discrimination') || norm.includes('retaliation')) {
    cat = 'employee_relations';
    confScore = 1.0;
    sensitive = true;
    reason = 'SENSITIVE_KEYWORD';
  } else if (norm.includes('salary') || norm.includes('payroll') || norm.includes('payslip') || norm.includes('tax')) {
    cat = 'payroll';
    confScore = 0.85;
  } else if (norm.includes('leave') || norm.includes('vacation') || norm.includes('holiday')) {
    cat = 'leave';
    confScore = 0.8;
  } else if (norm.includes('onboarding') || norm.includes('joining') || norm.includes('new hire')) {
    cat = 'onboarding';
    confScore = 0.75;
  }

  // 2. Ambiguity
  const isAmbiguous = norm.includes('help me') || norm.includes('need assistance') || norm.includes('my problem') || norm.length < 15;

  // 3. Routing
  let queue = 'HR_GENERAL';
  if (conf === 'Restricted' || sensitive || cat === 'employee_relations') {
    queue = 'HR_EMPLOYEE_RELATIONS';
  } else {
    queue = {
      benefits: 'HR_BENEFITS',
      leave: 'HR_LEAVE',
      payroll: 'HR_PAYROLL',
      onboarding: 'HR_ONBOARDING'
    }[cat] || 'HR_GENERAL';
  }

  // 4. Decision
  let decision = 'ANSWER_WITH_POLICY';
  let decReason = 'VALID_POLICY_FOUND';
  let citationId = 'VER-POL-HR-2026-001-03';
  let citationValid = true;

  if (conf === 'Restricted' || sensitive) {
    decision = 'ESCALATE_TO_HR';
    decReason = 'SENSITIVE_CASE';
    citationId = null;
    citationValid = false;
  } else if (isAmbiguous) {
    decision = 'REQUEST_CLARIFICATION';
    decReason = 'MISSING_CONTEXT';
    citationId = null;
    citationValid = false;
  }

  const targets = { Critical: 8, High: 24, Medium: 40, Low: 80 };
  const targetHours = targets[priority] || 40;

  return {
    pipeline: {
      classification: {
        category: cat,
        confidence: confScore,
        sensitive: sensitive,
        reason: reason
      },
      ambiguity: {
        is_ambiguous: isAmbiguous,
        missing_context: isAmbiguous,
        missing_fields: []
      },
      routing: {
        recommended_queue: queue,
        priority_route: conf === 'Restricted' || sensitive,
        routing_reason: sensitive ? 'SENSITIVE_CASE' : 'CATEGORY_MATCH'
      },
      resolution: {
        decision: decision,
        reason: decReason,
        policy_reference: citationId,
        citation_valid: citationValid,
        policy_doc: {
          policy_id: 'POL-HR-2026-001',
          policy_title: 'HR General Benefits & Policies',
          audience: 'All'
        },
        policy_version: {
          version_id: 'VER-POL-HR-2026-001-03',
          version_number: 3,
          status: 'Active',
          policy_text: 'Synthetic policy content for POL-HR-2026-001, version 3'
        }
      },
      sla: {
        priority: priority,
        target_hours: targetHours,
        business_hours_summary: `Target completion within ${targetHours} business hours (9am - 5pm, Mon-Fri).`
      }
    }
  };
}

/**
 * Fallback Datasets (Used if server is offline or opened via file://)
 */
function getFallbackMetrics() {
  return {
    summary: {
      total_tickets: 5000,
      classified_tickets: 4704,
      sensitive_tickets: 946,
      ambiguous_tickets: 296,
      policy_citations_valid: 3758,
      routing_mismatches: 1089,
      clarification_requests: 286,
      escalations: 956,
      policy_answers: 3758,
      sla_met: 4630,
      sla_breached: 370,
      classification_rate: 94.08,
      routing_mismatch_rate: 21.78,
      sla_compliance_rate: 92.6
    },
    categories: {
      benefits: 1350,
      leave: 1280,
      payroll: 1120,
      onboarding: 954,
      employee_relations: 296
    },
    queues: {
      HR_BENEFITS: 1250,
      HR_LEAVE: 1180,
      HR_PAYROLL: 1040,
      HR_ONBOARDING: 880,
      HR_EMPLOYEE_RELATIONS: 946,
      HR_GENERAL: 296
    },
    decisions: {
      ANSWER_WITH_POLICY: 3758,
      ESCALATE_TO_HR: 956,
      REQUEST_CLARIFICATION: 286
    },
    priority_sla: {
      Critical: { met: 380, breached: 42 },
      High: { met: 1150, breached: 98 },
      Medium: { met: 1850, breached: 134 },
      Low: { met: 1250, breached: 96 }
    }
  };
}

function getFallbackTickets(page = 1, limit = 20, filters = {}) {
  const sampleDescriptions = [
    { cat: 'leave', desc: 'I need to apply for annual leave.', prio: 'High' },
    { cat: 'payroll', desc: 'How can I check my salary payslip and deduction details?', prio: 'Medium' },
    { cat: 'leave', desc: 'I need clarification regarding my carry-over leave balance.', prio: 'Low' },
    { cat: 'onboarding', desc: 'What documents are required for new hire joining verification?', prio: 'Critical' },
    { cat: 'benefits', desc: 'Where do I find details about medical and health insurance coverage?', prio: 'Medium' },
    { cat: 'employee_relations', desc: 'Reporting confidential harassment and workplace discrimination.', prio: 'Critical', sens: true },
    { cat: 'benefits', desc: 'Can I claim dental reimbursement under our current benefits policy?', prio: 'Low' },
    { cat: 'payroll', desc: 'When will the annual tax declaration form be accessible in the portal?', prio: 'High' }
  ];

  const queues = {
    benefits: 'HR_BENEFITS',
    leave: 'HR_LEAVE',
    payroll: 'HR_PAYROLL',
    onboarding: 'HR_ONBOARDING',
    employee_relations: 'HR_EMPLOYEE_RELATIONS'
  };

  const list = [];
  for (let i = 1; i <= 50; i++) {
    const sample = sampleDescriptions[(i - 1) % sampleDescriptions.length];
    const isSensitive = sample.sens || false;
    const isSlaBreached = i % 13 === 0;
    const tid = `TKT-2026-${String(i).padStart(6, '0')}`;
    const eid = `EMP-${String(100 + (i % 300)).padStart(6, '0')}`;
    const targetHours = sample.prio === 'Critical' ? 8 : (sample.prio === 'High' ? 24 : (sample.prio === 'Medium' ? 40 : 80));
    const actualHours = isSlaBreached ? targetHours + 4.5 : Math.max(0, targetHours - 6.0);

    let decision = 'ANSWER_WITH_POLICY';
    if (isSensitive) decision = 'ESCALATE_TO_HR';
    else if (i % 17 === 0) decision = 'REQUEST_CLARIFICATION';

    list.push({
      ticket_id: tid,
      employee_id: eid,
      department_id: `DEPT-${String((i % 12) + 1).padStart(3, '0')}`,
      department_name: ['Engineering', 'Finance', 'HR', 'Marketing', 'Sales', 'Operations'][(i % 6)],
      source_category: sample.cat,
      predicted_category: sample.cat,
      description: sample.desc,
      priority: sample.prio,
      confidentiality: isSensitive ? 'Restricted' : 'Internal',
      sensitive: isSensitive,
      decision: decision,
      recommended_queue: queues[sample.cat] || 'HR_GENERAL',
      policy_version_id: isSensitive ? '' : 'VER-POL-HR-2026-001-03',
      sla_status: isSlaBreached ? 'BREACHED' : 'MET',
      sla_target_hours: targetHours,
      sla_actual_hours: actualHours
    });
  }

  // Filter
  let filtered = list;
  if (filters.search) {
    const s = filters.search.toLowerCase();
    filtered = filtered.filter(t => t.ticket_id.toLowerCase().includes(s) || t.description.toLowerCase().includes(s));
  }
  if (filters.category) {
    filtered = filtered.filter(t => t.predicted_category === filters.category);
  }
  if (filters.decision) {
    filtered = filtered.filter(t => t.decision === filters.decision);
  }
  if (filters.sla_status) {
    filtered = filtered.filter(t => t.sla_status === filters.sla_status);
  }
  if (filters.sensitive) {
    filtered = filtered.filter(t => String(t.sensitive) === filters.sensitive);
  }

  const total = filtered.length;
  const start = (page - 1) * limit;
  const pageItems = filtered.slice(start, start + limit);

  return {
    total,
    page,
    limit,
    total_pages: Math.max(1, Math.ceil(total / limit)),
    tickets: pageItems
  };
}

function getFallbackTicketDetail(ticketId) {
  return {
    ticket: {
      ticket_id: ticketId,
      employee_id: 'EMP-000151',
      department_name: 'Engineering',
      department_id: 'DEPT-003',
      employee_location: 'India',
      employee_type: 'Full-time',
      created_at: '2026-01-02T10:00:00',
      priority: 'High',
      confidentiality: 'Internal',
      description: 'I need to apply for annual leave.',
      decision: 'ANSWER_WITH_POLICY',
      recommended_queue: 'HR_LEAVE',
      policy_version_id: 'VER-POL-HR-2026-001-03',
      sla_status: 'MET',
      sla_target_hours: 24,
      sla_actual_hours: 4.0
    },
    policy: {
      policy_id: 'POL-HR-2026-001',
      version_id: 'VER-POL-HR-2026-001-03',
      title: 'HR Leave & Time-Off Policy 001',
      policy_text: 'Synthetic policy content for POL-HR-2026-001, version 3. All full-time employees are entitled to standard paid time off with prior managerial authorization.'
    },
    messages: [
      { sender_type: 'Employee', message_type: 'Request', message_text: 'I need to apply for annual leave.', created_at: '2026-01-02T10:00:00' },
      { sender_type: 'HR', message_type: 'Response', message_text: 'Referenced HR Policy POL-HR-2026-001: Leave balance confirmed.', created_at: '2026-01-02T14:00:00' }
    ]
  };
}

function getFallbackPolicies() {
  const p = [];
  for (let i = 1; i <= 8; i++) {
    const pid = `POL-HR-2026-${String(i).padStart(3, '0')}`;
    p.push({
      policy_id: pid,
      policy_title: `HR Policy ${String(i).padStart(3, '0')}`,
      audience: ['Employee', 'Manager', 'All'][(i % 3)],
      lifecycle_state: 'Published',
      versions: [
        { version_id: `VER-${pid}-01`, version_number: 1, status: 'Superseded', effective_from: '2025-01-01', effective_to: '2025-02-01', policy_text: `Initial policy document for ${pid}` },
        { version_id: `VER-${pid}-02`, version_number: 2, status: 'Superseded', effective_from: '2025-02-01', effective_to: '2025-03-01', policy_text: `Revision 2 for ${pid}` },
        { version_id: `VER-${pid}-03`, version_number: 3, status: 'Active', effective_from: '2025-03-01', effective_to: '', policy_text: `Current active and legally verified HR policy content for ${pid}` }
      ]
    });
  }
  return p;
}

