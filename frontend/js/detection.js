/* ===== Detection Upload Module ===== */

let selectedFile = null;

function initDetectionPage() {
  const dropZone = document.getElementById('drop-zone');
  const fileInput = document.getElementById('file-input');

  if (!dropZone || !fileInput) return;

  // Drag and drop
  dropZone.addEventListener('dragover', e => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
  });

  dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('drag-over');
  });

  dropZone.addEventListener('drop', e => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    const files = e.dataTransfer.files;
    if (files.length > 0) handleFileSelect(files[0]);
  });

  // Click to browse
  dropZone.addEventListener('click', () => fileInput.click());

  fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) handleFileSelect(fileInput.files[0]);
  });
}

function handleFileSelect(file) {
  const allowed = ['image/jpeg', 'image/png', 'image/webp'];
  if (!allowed.includes(file.type)) {
    showToast('Invalid file type. Please upload JPG, PNG or WebP.', 'error');
    return;
  }
  selectedFile = file;
  previewImage(file);
}

function previewImage(file) {
  const preview = document.getElementById('upload-preview');
  const placeholder = document.getElementById('drop-placeholder');
  if (!preview) return;

  const reader = new FileReader();
  reader.onload = e => {
    preview.src = e.target.result;
    preview.style.display = 'block';
    if (placeholder) placeholder.style.display = 'none';
  };
  reader.readAsDataURL(file);
}

async function submitDetection() {
  if (!selectedFile) {
    showToast('Please select an image first.', 'warning');
    return;
  }

  const location = document.getElementById('det-location')?.value || 'Unknown Location';
  const lat = document.getElementById('det-latitude')?.value || '';
  const lng = document.getElementById('det-longitude')?.value || '';
  const cameraId = document.getElementById('det-camera')?.value || '';

  const formData = new FormData();
  formData.append('image', selectedFile);
  formData.append('location', location);
  if (lat) formData.append('latitude', lat);
  if (lng) formData.append('longitude', lng);
  if (cameraId) formData.append('camera_id', cameraId);

  showLoadingState();

  try {
    const json = await detectImage(formData);
    hideLoadingState();
    renderDetectionResults(json.data);
    showToast('Detection completed successfully!', 'success');
  } catch (err) {
    hideLoadingState();
    showToast(`Detection failed: ${err.message}`, 'error');
  }
}

function renderDetectionResults(data) {
  const panel = document.getElementById('detection-results');
  if (!panel) return;
  panel.style.display = 'block';
  panel.classList.add('anim-fade-in-up');

  // Annotated image
  const img = document.getElementById('result-image');
  if (img && data.annotated_image_base64) {
    img.src = `data:image/jpeg;base64,${data.annotated_image_base64}`;
    img.style.display = 'block';
  }

  // Severity badge
  const sevEl = document.getElementById('result-severity');
  if (sevEl) {
    sevEl.className = `badge badge-${data.severity}`;
    sevEl.textContent = data.severity.toUpperCase();
  }

  // Detection count
  const countEl = document.getElementById('result-count');
  if (countEl) countEl.textContent = data.detection_count || 0;

  // Bin fill gauge
  renderBinGauge(data.bin_fill_level);

  // Detected class tags
  renderDetectionTags(data.detected_classes || []);

  // Confidence bars
  renderConfidenceBars(data.confidence_scores || {});

  // Alert status
  const alertEl = document.getElementById('result-alert');
  if (alertEl) {
    alertEl.innerHTML = data.alert_sent
      ? '<span style="color:var(--primary)">✓ Alert Sent</span>'
      : '<span style="color:var(--text-muted)">No Alert Required</span>';
  }
}

function renderBinGauge(level) {
  const el = document.getElementById('bin-gauge');
  if (!el) return;
  const levels = { empty: 0, half: 50, full: 85, overflow: 100 };
  const pct = levels[level] || 0;
  const color = pct >= 100 ? 'var(--critical)' : pct >= 80 ? 'var(--accent)' : pct >= 50 ? 'var(--medium)' : 'var(--primary)';
  el.innerHTML = `
    <div style="display:flex;align-items:center;gap:10px;">
      <div style="flex:1;height:10px;background:rgba(255,255,255,0.08);border-radius:5px;overflow:hidden;">
        <div style="width:${pct}%;height:100%;background:${color};border-radius:5px;transition:width 0.6s ease;"></div>
      </div>
      <span style="font-size:0.8rem;font-weight:700;color:${color};min-width:60px;">${level.toUpperCase()}</span>
    </div>
  `;
}

function renderDetectionTags(classes) {
  const el = document.getElementById('result-tags');
  if (!el) return;
  const tagColors = {
    garbage_pile: 'var(--critical)', bin_overflow: 'var(--critical)', litter_heavy: 'var(--critical)',
    bin_full: 'var(--accent)', bin_half: 'var(--medium)', litter_light: 'var(--medium)',
    bin_empty: 'var(--primary)', plastic_waste: '#42A5F5',
  };
  el.innerHTML = classes.map(c => {
    const color = tagColors[c] || 'var(--text-muted)';
    return `<span style="display:inline-block;padding:3px 10px;border-radius:12px;font-size:0.72rem;font-weight:600;
      background:${color}22;color:${color};border:1px solid ${color}44;margin:3px 4px 3px 0;">${c.replace(/_/g, ' ')}</span>`;
  }).join('');
}

function renderConfidenceBars(scores) {
  const el = document.getElementById('result-confidence');
  if (!el) return;
  if (!Object.keys(scores).length) {
    el.innerHTML = '<span style="color:var(--text-muted)">No scores</span>';
    return;
  }
  el.innerHTML = Object.entries(scores).map(([cls, conf]) => {
    const pct = Math.round(conf * 100);
    return `
      <div style="margin-bottom:8px;">
        <div style="display:flex;justify-content:space-between;font-size:0.75rem;margin-bottom:3px;">
          <span style="color:var(--text-secondary)">${cls.replace(/_/g, ' ')}</span>
          <span style="color:var(--text-primary);font-weight:700">${pct}%</span>
        </div>
        <div style="height:6px;background:rgba(255,255,255,0.08);border-radius:3px;overflow:hidden;">
          <div style="width:${pct}%;height:100%;background:var(--primary);border-radius:3px;transition:width 0.5s ease;"></div>
        </div>
      </div>`;
  }).join('');
}

function showLoadingState() {
  const btn = document.getElementById('detect-btn');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Analyzing…';
  }
}

function hideLoadingState() {
  const btn = document.getElementById('detect-btn');
  if (btn) {
    btn.disabled = false;
    btn.innerHTML = '<i class="fas fa-search"></i> Run Detection';
  }
}

function downloadReport() {
  const sev = document.getElementById('result-severity')?.textContent || '';
  const count = document.getElementById('result-count')?.textContent || '';
  const text = [
    '===== GreenCity Garbage Detection Report =====',
    `Date: ${new Date().toLocaleString()}`,
    `Severity: ${sev}`,
    `Objects Detected: ${count}`,
    '',
    'Generated by GreenCity Waste Intelligence System v1.0.0',
  ].join('\n');

  const blob = new Blob([text], { type: 'text/plain' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `detection_report_${Date.now()}.txt`;
  a.click();
  URL.revokeObjectURL(a.href);
}

async function loadCameraDropdown() {
  try {
    const json = await getCameras();
    const select = document.getElementById('det-camera');
    if (!select || !json.data) return;
    json.data.forEach(cam => {
      const opt = document.createElement('option');
      opt.value = cam.id;
      opt.textContent = cam.name;
      select.appendChild(opt);
    });
  } catch {
    // silent
  }
}
