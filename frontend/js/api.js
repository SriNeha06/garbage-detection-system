/* ===== API Module ===== */

const API_BASE = `${window.GREENCITY_API_BASE || ''}/api`;

/**
 * Generic fetch wrapper with error handling.
 */
async function apiFetch(endpoint, options = {}) {
  try {
    const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;
    const res = await fetch(url, {
      headers: { 'Content-Type': 'application/json', ...options.headers },
      ...options,
    });
    const json = await res.json();
    if (!res.ok || json.success === false) {
      throw new Error(json.message || `HTTP ${res.status}`);
    }
    return json;
  } catch (err) {
    console.error(`API error [${endpoint}]:`, err);
    throw err;
  }
}

/* ---- Detection ---- */

async function detectImage(formData) {
  const res = await fetch(`${API_BASE}/detect`, {
    method: 'POST',
    body: formData, // multipart — no Content-Type header
  });
  const json = await res.json();
  if (!res.ok || json.success === false) throw new Error(json.message || 'Detection failed');
  return json;
}

async function getDetections(params = {}) {
  const qs = new URLSearchParams(params).toString();
  return apiFetch(`/detections?${qs}`);
}

async function getDetection(id) {
  return apiFetch(`/detections/${id}`);
}

async function deleteDetection(id) {
  return apiFetch(`/detections/${id}`, { method: 'DELETE' });
}

/* ---- Alerts ---- */

async function getAlerts(params = {}) {
  const qs = new URLSearchParams(params).toString();
  return apiFetch(`/alerts?${qs}`);
}

async function acknowledgeAlert(alertId) {
  return apiFetch(`/alerts/${alertId}/acknowledge`, { method: 'POST' });
}

async function resolveAlert(alertId) {
  return apiFetch(`/alerts/${alertId}/resolve`, { method: 'POST' });
}

async function sendTestAlert() {
  return apiFetch('/alerts/send-test', { method: 'POST' });
}

async function getAlertStats() {
  return apiFetch('/alerts/stats');
}

/* ---- Dashboard ---- */

async function getDashboardStats() {
  return apiFetch('/dashboard/stats');
}

async function getMapData() {
  return apiFetch('/dashboard/map-data');
}

/* ---- Cameras ---- */

async function getCameras() {
  return apiFetch('/cameras');
}

async function addCamera(data) {
  return apiFetch('/cameras', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

async function updateCamera(id, data) {
  return apiFetch(`/cameras/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

async function deleteCamera(id) {
  return apiFetch(`/cameras/${id}`, { method: 'DELETE' });
}

async function captureFromCamera(id) {
  return apiFetch(`/cameras/${id}/capture`, { method: 'POST' });
}

/* ---- Health ---- */

async function checkBackendConnection() {
  try {
    const json = await apiFetch('/health');
    updateConnectionStatus(true);
    return json;
  } catch {
    updateConnectionStatus(false);
    return null;
  }
}

function updateConnectionStatus(connected) {
  const dot = document.getElementById('connection-dot');
  const label = document.getElementById('connection-label');
  if (dot) {
    dot.classList.toggle('connected', connected);
  }
  if (label) {
    label.textContent = connected ? 'Backend Connected' : 'Offline';
  }
}

// Poll every 30 seconds
setInterval(checkBackendConnection, 30000);
