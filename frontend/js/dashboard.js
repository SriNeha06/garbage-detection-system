/* ===== Dashboard Module ===== */

let trendChart = null;
let severityChart = null;
let zoneChart = null;
let hourlyChart = null;
let dashboardInterval = null;

async function loadDashboardStats() {
  try {
    const json = await getDashboardStats();
    const d = json.data;

    // Stat cards
    animateCounter('stat-detections-today', d.total_detections_today);
    animateCounter('stat-critical-alerts', d.critical_alerts_today);
    animateCounter('stat-bins-overflow', d.bins_overflow);

    // Cleanliness ring
    updateCleanlinessRing(d.cleanliness_score);

    // Glow effects
    const critCard = document.getElementById('card-critical');
    if (critCard) critCard.classList.toggle('glow', d.critical_alerts_today > 0);
    const binCard = document.getElementById('card-overflow');
    if (binCard) binCard.classList.toggle('glow', d.bins_overflow > 0);

    // Trend chart
    renderDetectionTrend(d.detection_trend);

    // Severity doughnut
    renderSeverityChart(d.severity_breakdown);

    // Zone chart
    renderZoneChart(d.zone_breakdown);

    // Hourly chart
    renderHourlyChart(d.hourly_distribution);

    // Recent detections
    renderRecentDetections(d.recent_detections);

  } catch (err) {
    console.error('Dashboard load failed:', err);
    showToast('Failed to load dashboard data', 'error');
  }
}

/* ---- Charts ---- */

function renderDetectionTrend(trend) {
  if (!trend || !trend.length) return;
  const labels = trend.map(t => t.label);
  const data = trend.map(t => t.count);
  destroyChart(trendChart);
  trendChart = createLineChart('trendChart', labels, data, { label: 'Detections', color: '#00C853' });
}

function renderSeverityChart(breakdown) {
  if (!breakdown) return;
  const labels = ['Low', 'Medium', 'High', 'Critical'];
  const data = [breakdown.low || 0, breakdown.medium || 0, breakdown.high || 0, breakdown.critical || 0];
  destroyChart(severityChart);
  severityChart = createDoughnutChart('severityChart', labels, data);
}

function renderZoneChart(zones) {
  if (!zones || !zones.length) return;
  const labels = zones.map(z => z.zone.charAt(0).toUpperCase() + z.zone.slice(1));
  const data = zones.map(z => z.count);
  const colors = zones.map(() => '#42A5F5');
  destroyChart(zoneChart);
  zoneChart = createBarChart('zoneChart', labels, data, { horizontal: true, colors, label: 'Detections' });
}

function renderHourlyChart(hourly) {
  if (!hourly) return;
  const labels = Array.from({ length: 24 }, (_, i) => `${i}:00`);
  const colors = hourly.map(v => v >= 4 ? '#D50000' : v >= 2 ? '#FF6D00' : '#00C853');
  destroyChart(hourlyChart);
  hourlyChart = createBarChart('hourlyChart', labels, hourly, { colors, label: 'Detections', maxBarThickness: 20 });
}

/* ---- Recent Detections ---- */

function renderRecentDetections(detections) {
  const container = document.getElementById('recent-detections-list');
  if (!container) return;

  if (!detections || detections.length === 0) {
    container.innerHTML = `<div class="empty-state"><div class="empty-icon">📋</div><p>No recent detections</p></div>`;
    return;
  }

  container.innerHTML = detections.map(d => `
    <div class="recent-item" onclick="showPage('detection')">
      <div class="ri-severity ${d.severity}"></div>
      <div class="ri-info">
        <div class="ri-location">${d.location_name || 'Unknown'}</div>
        <div class="ri-meta">${d.detection_count} items · ${timeAgo(d.timestamp)}</div>
      </div>
      <div class="ri-badge">
        <span class="badge badge-${d.severity}">${d.severity}</span>
      </div>
    </div>
  `).join('');
}

/* ---- Cleanliness Ring ---- */

function updateCleanlinessRing(score) {
  const ring = document.getElementById('cleanliness-ring');
  const value = document.getElementById('cleanliness-value');
  if (ring) ring.style.setProperty('--score', score);
  if (value) value.textContent = Math.round(score);
}

/* ---- Animated Counter ---- */

function animateCounter(elementId, target) {
  const el = document.getElementById(elementId);
  if (!el) return;
  const start = parseInt(el.textContent) || 0;
  const duration = 600;
  const startTime = performance.now();

  function tick(now) {
    const elapsed = now - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(start + (target - start) * eased);
    if (progress < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

/* ---- Auto Refresh ---- */

function startDashboardRefresh() {
  if (dashboardInterval) clearInterval(dashboardInterval);
  dashboardInterval = setInterval(loadDashboardStats, 60000);
}

function stopDashboardRefresh() {
  if (dashboardInterval) {
    clearInterval(dashboardInterval);
    dashboardInterval = null;
  }
}
