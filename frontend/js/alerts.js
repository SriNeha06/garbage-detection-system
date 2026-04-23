/* ===== Alerts Module ===== */

let alertPollInterval = null;
let lastAlertCount = 0;

async function loadAlerts(filters = {}) {
  try {
    const json = await getAlerts(filters);
    const data = json.data;
    renderAlertList(data.items || []);
    lastAlertCount = data.total || 0;
  } catch (err) {
    console.error('Failed to load alerts:', err);
    const container = document.getElementById('alerts-list');
    if (container) container.innerHTML = `<div class="empty-state"><div class="empty-icon">⚠️</div><p>Failed to load alerts</p></div>`;
  }
}

function renderAlertList(alerts) {
  const container = document.getElementById('alerts-list');
  if (!container) return;

  if (alerts.length === 0) {
    container.innerHTML = `<div class="empty-state"><div class="empty-icon">🔔</div><p>No alerts found</p></div>`;
    return;
  }

  container.innerHTML = alerts.map(a => renderAlertCard(a)).join('');
}

function renderAlertCard(alert) {
  const iconMap = { email: '📧', sms: '📱', system: '🔔' };
  const icon = iconMap[alert.alert_type] || '🔔';
  const isPending = alert.status === 'pending';

  return `
    <div class="alert-card ${isPending ? 'is-pending' : ''}" id="alert-${alert.id}">
      <div class="alert-border ${alert.severity}"></div>
      <div class="alert-body">
        <div class="alert-icon">${icon}</div>
        <div class="alert-content">
          <div class="alert-location">${alert.location_name || 'Unknown Location'}</div>
          <div class="alert-message">${alert.message || 'No details available.'}</div>
          <div class="alert-time">${timeAgo(alert.created_at)}</div>
        </div>
      </div>
      <div class="alert-right">
        <div class="alert-status">
          <span class="badge badge-${alert.status}">${alert.status}</span>
          <span class="badge badge-${alert.severity}" style="margin-left:4px;">${alert.severity}</span>
        </div>
        <div class="alert-actions">
          ${alert.status === 'pending' ? `<button class="btn btn-sm btn-secondary" onclick="handleAcknowledge('${alert.id}')">Acknowledge</button>` : ''}
          ${alert.status !== 'resolved' ? `<button class="btn btn-sm btn-primary" onclick="handleResolve('${alert.id}')">Resolve</button>` : ''}
        </div>
      </div>
    </div>
  `;
}

async function handleAcknowledge(id) {
  try {
    await acknowledgeAlert(id);
    showToast('Alert acknowledged', 'success');
    loadAlerts(getCurrentAlertFilters());
    loadAlertStats();
  } catch (err) {
    showToast(`Failed: ${err.message}`, 'error');
  }
}

async function handleResolve(id) {
  try {
    await resolveAlert(id);
    showToast('Alert resolved', 'success');
    loadAlerts(getCurrentAlertFilters());
    loadAlertStats();
  } catch (err) {
    showToast(`Failed: ${err.message}`, 'error');
  }
}

function getCurrentAlertFilters() {
  const activeStatus = document.querySelector('.alert-filters .filter-btn.active');
  const activeSeverity = document.querySelector('.severity-filters .filter-btn.active');
  const filters = {};
  if (activeStatus && activeStatus.dataset.status !== 'all') filters.status = activeStatus.dataset.status;
  if (activeSeverity && activeSeverity.dataset.severity !== 'all') filters.severity = activeSeverity.dataset.severity;
  return filters;
}

function filterAlertsByStatus(btn) {
  document.querySelectorAll('.alert-filters .filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  loadAlerts(getCurrentAlertFilters());
}

function filterAlertsBySeverity(btn) {
  document.querySelectorAll('.severity-filters .filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  loadAlerts(getCurrentAlertFilters());
}

async function loadAlertStats() {
  try {
    const json = await getAlertStats();
    const d = json.data;
    const pendingEl = document.getElementById('alert-stat-pending');
    const avgEl = document.getElementById('alert-stat-avg');
    const critEl = document.getElementById('alert-stat-critical');
    if (pendingEl) pendingEl.textContent = d.pending || 0;
    if (avgEl) avgEl.textContent = `${d.avg_resolution_minutes || 0} min`;
    if (critEl) critEl.textContent = d.by_severity?.critical || 0;
  } catch {
    // silent
  }
}

async function handleSendTestAlert() {
  if (!confirm('Send a test alert to verify email configuration?')) return;
  try {
    const json = await sendTestAlert();
    showToast(json.message || 'Test alert processed', 'info');
  } catch (err) {
    showToast(`Failed: ${err.message}`, 'error');
  }
}

function startAlertPolling() {
  if (alertPollInterval) clearInterval(alertPollInterval);
  alertPollInterval = setInterval(async () => {
    try {
      const json = await getAlerts({ limit: 1 });
      const newTotal = json.data?.total || 0;
      if (newTotal > lastAlertCount && lastAlertCount > 0) {
        showToast(`${newTotal - lastAlertCount} new alert(s)!`, 'warning');
      }
      lastAlertCount = newTotal;
    } catch { /* silent */ }
  }, 30000);
}

function stopAlertPolling() {
  if (alertPollInterval) {
    clearInterval(alertPollInterval);
    alertPollInterval = null;
  }
}
