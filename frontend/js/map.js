/* ===== Map Module (Leaflet.js) ===== */

let map = null;
let markersLayer = null;
let mapRefreshInterval = null;

const SEVERITY_MARKER_COLORS = {
  critical: '#D50000',
  high: '#FF6D00',
  medium: '#FFD600',
  low: '#00C853',
};

function initMap() {
  if (map) return; // already initialised

  map = L.map('city-map', {
    center: [13.0827, 80.2707], // Chennai, India
    zoom: 12,
    zoomControl: true,
  });

  // Dark tile layer
  L.tileLayer('https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://stadiamaps.com/">Stadia</a> &copy; <a href="https://openmaptiles.org/">OpenMapTiles</a>',
  }).addTo(map);

  markersLayer = L.layerGroup().addTo(map);

  // Legend
  const legend = L.control({ position: 'bottomright' });
  legend.onAdd = function () {
    const div = L.DomUtil.create('div', 'map-legend');
    div.innerHTML = `
      <div style="background:#1F2937;padding:12px 16px;border-radius:8px;border:1px solid rgba(255,255,255,0.08);font-size:12px;color:#F9FAFB;">
        <div style="font-weight:700;margin-bottom:8px;">Severity</div>
        <div style="display:flex;align-items:center;gap:6px;margin-bottom:4px;"><span style="width:10px;height:10px;border-radius:50%;background:#D50000;display:inline-block;"></span> Critical</div>
        <div style="display:flex;align-items:center;gap:6px;margin-bottom:4px;"><span style="width:10px;height:10px;border-radius:50%;background:#FF6D00;display:inline-block;"></span> High</div>
        <div style="display:flex;align-items:center;gap:6px;margin-bottom:4px;"><span style="width:10px;height:10px;border-radius:50%;background:#FFD600;display:inline-block;"></span> Medium</div>
        <div style="display:flex;align-items:center;gap:6px;"><span style="width:10px;height:10px;border-radius:50%;background:#00C853;display:inline-block;"></span> Low</div>
      </div>`;
    return div;
  };
  legend.addTo(map);

  loadMapMarkers();
}

async function loadMapMarkers() {
  try {
    const json = await getMapData();
    const markers = json.data || [];
    if (!markersLayer) return;
    markersLayer.clearLayers();
    markers.forEach(m => createMarker(m));
  } catch (err) {
    console.error('Failed to load map markers:', err);
  }
}

function createMarker(detection) {
  if (!detection.latitude || !detection.longitude) return;

  const color = SEVERITY_MARKER_COLORS[detection.severity] || '#00C853';
  const isCritical = detection.severity === 'critical';

  const icon = L.divIcon({
    className: 'custom-marker',
    html: `<div style="
      width:${isCritical ? 18 : 14}px;
      height:${isCritical ? 18 : 14}px;
      background:${color};
      border-radius:50%;
      border:2px solid #fff;
      box-shadow:0 0 ${isCritical ? 12 : 6}px ${color};
      ${isCritical ? 'animation:pulse 1.5s ease-in-out infinite;' : ''}
    "></div>`,
    iconSize: [isCritical ? 18 : 14, isCritical ? 18 : 14],
    iconAnchor: [isCritical ? 9 : 7, isCritical ? 9 : 7],
  });

  const marker = L.marker([detection.latitude, detection.longitude], { icon });
  marker.bindPopup(createPopup(detection), {
    className: 'dark-popup',
    maxWidth: 280,
  });
  markersLayer.addLayer(marker);
}

function createPopup(detection) {
  const color = SEVERITY_MARKER_COLORS[detection.severity] || '#00C853';
  return `
    <div style="font-family:'Inter',sans-serif;color:#F9FAFB;min-width:200px;">
      <div style="font-weight:700;font-size:14px;margin-bottom:6px;">${detection.location_name || 'Unknown'}</div>
      <div style="display:flex;gap:6px;margin-bottom:8px;">
        <span style="display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:700;background:${color}33;color:${color};border:1px solid ${color}55;">${(detection.severity || '').toUpperCase()}</span>
        <span style="font-size:11px;color:#9CA3AF;">${detection.detection_count || 0} items</span>
      </div>
      <div style="font-size:11px;color:#9CA3AF;margin-bottom:4px;">Bin: ${(detection.bin_fill_level || 'N/A').toUpperCase()}</div>
      <div style="font-size:11px;color:#6B7280;">${timeAgo(detection.timestamp)}</div>
    </div>
  `;
}

function refreshMap() {
  loadMapMarkers();
  if (map) setTimeout(() => map.invalidateSize(), 200);
}

function startMapRefresh() {
  if (mapRefreshInterval) clearInterval(mapRefreshInterval);
  mapRefreshInterval = setInterval(refreshMap, 60000);
}

function stopMapRefresh() {
  if (mapRefreshInterval) {
    clearInterval(mapRefreshInterval);
    mapRefreshInterval = null;
  }
}

function filterMarkersBySeverity(severity) {
  // Re-load with filter (simple approach — re-fetch and filter client-side)
  loadMapMarkers().then(() => {
    if (severity === 'all' || !severity) return;
    if (!markersLayer) return;
    markersLayer.eachLayer(layer => {
      // We'd need stored data per marker; simpler to re-fetch filtered
    });
  });
}
