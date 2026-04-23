/* ===== Main Application Module ===== */

/* ---- Navigation ---- */

function showPage(pageName) {
  // Hide all page sections
  document.querySelectorAll('.page-section').forEach(sec => {
    sec.classList.remove('active');
  });

  // Show target
  const target = document.getElementById(`page-${pageName}`);
  if (target) target.classList.add('active');

  // Update sidebar nav active state
  document.querySelectorAll('.nav-item').forEach(item => {
    item.classList.toggle('active', item.dataset.page === pageName);
  });

  // Initialize page-specific JS
  switch (pageName) {
    case 'dashboard':
      loadDashboardStats();
      startDashboardRefresh();
      break;
    case 'detection':
      initDetectionPage();
      loadCameraDropdown();
      break;
    case 'alerts':
      loadAlerts();
      loadAlertStats();
      startAlertPolling();
      break;
    case 'cameras':
      loadCamerasPage();
      break;
    case 'map':
      setTimeout(() => {
        initMap();
        refreshMap();
        startMapRefresh();
      }, 150);
      break;
    case 'analytics':
      loadAnalyticsPage();
      break;
  }

  // Stop refreshes for inactive pages
  if (pageName !== 'dashboard') stopDashboardRefresh();
  if (pageName !== 'alerts') stopAlertPolling();
  if (pageName !== 'map') stopMapRefresh();

  // Close mobile sidebar
  document.querySelector('.sidebar')?.classList.remove('open');
}

/* ---- Toast Notification System ---- */

function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
  const toast = document.createElement('div');
  toast.className = `toast toast-${type} toast-enter`;
  toast.innerHTML = `
    <span class="toast-icon">${icons[type] || 'ℹ️'}</span>
    <span class="toast-message">${message}</span>
  `;
  container.appendChild(toast);

  setTimeout(() => {
    toast.classList.remove('toast-enter');
    toast.classList.add('toast-exit');
    toast.addEventListener('animationend', () => toast.remove());
  }, 4000);
}

/* ---- Live Clock ---- */

function startClock() {
  function tick() {
    const el = document.getElementById('live-clock');
    if (el) {
      const now = new Date();
      el.textContent = now.toLocaleDateString('en-US', {
        weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
      }) + '  •  ' + now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    }
  }
  tick();
  setInterval(tick, 1000);
}

/* ---- Time Ago Utility ---- */

function timeAgo(isoString) {
  if (!isoString) return 'Unknown';
  const date = new Date(isoString);
  const now = new Date();
  const seconds = Math.floor((now - date) / 1000);

  if (seconds < 60) return 'Just now';
  if (seconds < 3600) return `${Math.floor(seconds / 60)} min ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`;
  if (seconds < 172800) {
    return `Yesterday at ${date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}`;
  }
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });
}

/* ---- Camera Management Page ---- */

async function loadCamerasPage() {
  try {
    const json = await getCameras();
    renderCameraGrid(json.data || []);
  } catch (err) {
    showToast('Failed to load cameras', 'error');
  }
}

function renderCameraGrid(cameras) {
  const grid = document.getElementById('cameras-grid');
  if (!grid) return;

  if (cameras.length === 0) {
    grid.innerHTML = `<div class="empty-state" style="grid-column:1/-1;"><div class="empty-icon">📷</div><p>No cameras registered</p></div>`;
    return;
  }

  grid.innerHTML = cameras.map(cam => `
    <div class="card" id="cam-${cam.id}" style="position:relative;">
      <div style="display:flex;justify-content:space-between;align-items:start;margin-bottom:12px;">
        <div>
          <div style="font-weight:700;font-size:0.95rem;margin-bottom:4px;">${cam.name}</div>
          <div style="font-size:0.78rem;color:var(--text-muted);">${cam.location_name || ''}</div>
        </div>
        <div style="display:flex;align-items:center;gap:6px;">
          <span class="status-dot ${cam.is_active ? 'connected' : ''}"></span>
          <span class="badge badge-${cam.zone === 'commercial' ? 'high' : cam.zone === 'industrial' ? 'medium' : cam.zone === 'park' ? 'low' : 'acknowledged'}">${cam.zone}</span>
        </div>
      </div>
      <div style="font-size:0.72rem;color:var(--text-muted);margin-bottom:14px;">
        Last checked: ${cam.last_checked ? timeAgo(cam.last_checked) : 'Never'}
      </div>
      <div style="display:flex;gap:8px;">
        <button class="btn btn-sm btn-primary" onclick="handleCameraCapture('${cam.id}')">
          <i class="fas fa-camera"></i> Capture
        </button>
        <button class="btn btn-sm btn-secondary" onclick="openEditCameraModal('${cam.id}', ${JSON.stringify(cam).replace(/"/g, '&quot;')})">
          <i class="fas fa-edit"></i>
        </button>
        <button class="btn btn-sm btn-icon" onclick="handleDeleteCamera('${cam.id}')" style="color:var(--critical);">
          <i class="fas fa-trash"></i>
        </button>
      </div>
    </div>
  `).join('');
}

async function handleCameraCapture(id) {
  showToast('Capturing from camera…', 'info');
  try {
    const json = await captureFromCamera(id);
    showToast('Capture complete! Detection saved.', 'success');
    loadCamerasPage();
  } catch (err) {
    showToast(`Capture failed: ${err.message}`, 'error');
  }
}

async function handleDeleteCamera(id) {
  if (!confirm('Delete this camera?')) return;
  try {
    await deleteCamera(id);
    showToast('Camera deleted', 'success');
    loadCamerasPage();
  } catch (err) {
    showToast(`Delete failed: ${err.message}`, 'error');
  }
}

/* ---- Camera Modal ---- */

let editingCameraId = null;

function openAddCameraModal() {
  editingCameraId = null;
  document.getElementById('modal-title').textContent = 'Add Camera';
  document.getElementById('cam-form').reset();
  document.getElementById('cam-active').checked = true;
  document.getElementById('camera-modal').classList.add('active');
}

function openEditCameraModal(id, cam) {
  editingCameraId = id;
  document.getElementById('modal-title').textContent = 'Edit Camera';
  document.getElementById('cam-name').value = cam.name || '';
  document.getElementById('cam-location').value = cam.location_name || '';
  document.getElementById('cam-lat').value = cam.latitude || '';
  document.getElementById('cam-lng').value = cam.longitude || '';
  document.getElementById('cam-stream').value = cam.stream_url || '';
  document.getElementById('cam-zone').value = cam.zone || 'residential';
  document.getElementById('cam-active').checked = cam.is_active !== false;
  document.getElementById('camera-modal').classList.add('active');
}

function closeCameraModal() {
  document.getElementById('camera-modal').classList.remove('active');
  editingCameraId = null;
}

async function handleCameraFormSubmit(e) {
  e.preventDefault();
  const data = {
    name: document.getElementById('cam-name').value.trim(),
    location_name: document.getElementById('cam-location').value.trim(),
    latitude: parseFloat(document.getElementById('cam-lat').value) || null,
    longitude: parseFloat(document.getElementById('cam-lng').value) || null,
    stream_url: document.getElementById('cam-stream').value.trim(),
    zone: document.getElementById('cam-zone').value,
    is_active: document.getElementById('cam-active').checked,
  };

  if (!data.name) {
    showToast('Camera name is required', 'warning');
    return;
  }

  try {
    if (editingCameraId) {
      await updateCamera(editingCameraId, data);
      showToast('Camera updated', 'success');
    } else {
      await addCamera(data);
      showToast('Camera added', 'success');
    }
    closeCameraModal();
    loadCamerasPage();
  } catch (err) {
    showToast(`Failed: ${err.message}`, 'error');
  }
}

/* ---- Analytics Page ---- */

let analyticsTrendChart = null;
let analyticsTypeChart = null;
let analyticsZoneChart = null;
let analyticsHourlyChart = null;

async function loadAnalyticsPage() {
  try {
    const json = await getDashboardStats();
    const d = json.data;

    // Trend chart
    if (d.detection_trend) {
      const labels = d.detection_trend.map(t => t.label);
      const data = d.detection_trend.map(t => t.count);
      destroyChart(analyticsTrendChart);
      analyticsTrendChart = createLineChart('analyticsTrendChart', labels, data, { label: 'Detections', color: '#42A5F5' });
    }

    // Type distribution (severity as proxy)
    if (d.severity_breakdown) {
      const labels = ['Low', 'Medium', 'High', 'Critical'];
      const data = [d.severity_breakdown.low, d.severity_breakdown.medium, d.severity_breakdown.high, d.severity_breakdown.critical];
      destroyChart(analyticsTypeChart);
      analyticsTypeChart = createDoughnutChart('analyticsTypeChart', labels, data);
    }

    // Zone chart
    if (d.zone_breakdown) {
      const labels = d.zone_breakdown.map(z => z.zone.charAt(0).toUpperCase() + z.zone.slice(1));
      const data = d.zone_breakdown.map(z => z.count);
      const colors = ['#00C853', '#42A5F5', '#FF6D00', '#AB47BC', '#26A69A'];
      destroyChart(analyticsZoneChart);
      analyticsZoneChart = createBarChart('analyticsZoneChart', labels, data, { horizontal: true, colors });
    }

    // Peak hours
    if (d.hourly_distribution) {
      const labels = Array.from({ length: 24 }, (_, i) => `${i}h`);
      const colors = d.hourly_distribution.map(v => v >= 4 ? '#D50000' : v >= 2 ? '#FF6D00' : '#00C853');
      destroyChart(analyticsHourlyChart);
      analyticsHourlyChart = createBarChart('analyticsHourlyChart', labels, d.hourly_distribution, { colors, maxBarThickness: 16 });
    }

    // Summary stats
    const totalDet = document.getElementById('analytics-total');
    const bestZone = document.getElementById('analytics-best');
    const worstZone = document.getElementById('analytics-worst');
    const score = document.getElementById('analytics-score');

    if (totalDet) totalDet.textContent = d.total_detections_week || 0;
    if (score) score.textContent = `${d.cleanliness_score || 0}%`;
    if (worstZone) worstZone.textContent = d.most_polluted_zone || 'N/A';
    if (bestZone) {
      const zones = d.zone_breakdown || [];
      const best = zones.length ? zones.reduce((a, b) => a.count < b.count ? a : b) : null;
      bestZone.textContent = best ? best.zone.charAt(0).toUpperCase() + best.zone.slice(1) : 'N/A';
    }

  } catch (err) {
    console.error('Analytics load failed:', err);
    showToast('Failed to load analytics', 'error');
  }
}

/* ---- Mobile Sidebar Toggle ---- */

function toggleSidebar() {
  document.querySelector('.sidebar')?.classList.toggle('open');
}

/* ---- Greeting ---- */

function setGreeting() {
  const el = document.getElementById('greeting-text');
  if (!el) return;
  const hour = new Date().getHours();
  let greeting = 'Good Evening';
  if (hour < 12) greeting = 'Good Morning';
  else if (hour < 17) greeting = 'Good Afternoon';
  el.textContent = `${greeting}, Officer 👋`;
}

/* ---- Initialisation ---- */

document.addEventListener('DOMContentLoaded', () => {
  // Set greeting
  setGreeting();

  // Start clock
  startClock();

  // Check backend connection
  checkBackendConnection();

  // Sidebar nav clicks
  document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => showPage(item.dataset.page));
  });

  // Camera form
  const camForm = document.getElementById('cam-form');
  if (camForm) camForm.addEventListener('submit', handleCameraFormSubmit);

  // Load default page (dashboard)
  showPage('dashboard');
});
