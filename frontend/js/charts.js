/* ===== Chart.js Helpers — dark theme ===== */

// Global Chart.js defaults
Chart.defaults.color = '#9CA3AF';
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.font.size = 12;
Chart.defaults.plugins.legend.labels.usePointStyle = true;
Chart.defaults.plugins.legend.labels.padding = 16;
Chart.defaults.plugins.tooltip.backgroundColor = '#1F2937';
Chart.defaults.plugins.tooltip.borderColor = 'rgba(255,255,255,0.08)';
Chart.defaults.plugins.tooltip.borderWidth = 1;
Chart.defaults.plugins.tooltip.cornerRadius = 8;
Chart.defaults.plugins.tooltip.padding = 10;
Chart.defaults.plugins.tooltip.titleFont = { weight: '600' };
Chart.defaults.scale.grid = { color: 'rgba(255,255,255,0.05)' };

/* Colour palette matching design system */
const CHART_COLORS = {
  primary: '#00C853',
  primaryFade: 'rgba(0, 200, 83, 0.15)',
  critical: '#D50000',
  criticalFade: 'rgba(213, 0, 0, 0.15)',
  high: '#FF6D00',
  highFade: 'rgba(255, 109, 0, 0.15)',
  medium: '#FFD600',
  mediumFade: 'rgba(255, 214, 0, 0.15)',
  blue: '#42A5F5',
  blueFade: 'rgba(66, 165, 245, 0.15)',
  purple: '#AB47BC',
  purpleFade: 'rgba(171, 71, 188, 0.15)',
  teal: '#26A69A',
  tealFade: 'rgba(38, 166, 154, 0.15)',
  white08: 'rgba(255,255,255,0.08)',
};

const SEVERITY_CHART_COLORS = [CHART_COLORS.primary, CHART_COLORS.medium, CHART_COLORS.high, CHART_COLORS.critical];

/**
 * Create a gradient fill for line/area charts.
 */
function createGradient(ctx, color, alpha1 = 0.35, alpha2 = 0.0) {
  const gradient = ctx.createLinearGradient(0, 0, 0, 300);
  gradient.addColorStop(0, color.replace(')', `, ${alpha1})`).replace('rgb', 'rgba'));
  gradient.addColorStop(1, color.replace(')', `, ${alpha2})`).replace('rgb', 'rgba'));
  return gradient;
}

function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}

function makeGradient(ctx, hex, a1 = 0.35, a2 = 0.0) {
  const gradient = ctx.createLinearGradient(0, 0, 0, 300);
  gradient.addColorStop(0, hexToRgba(hex, a1));
  gradient.addColorStop(1, hexToRgba(hex, a2));
  return gradient;
}

/* ---- Factory functions ---- */

function createLineChart(canvasId, labels, data, options = {}) {
  const ctx = document.getElementById(canvasId)?.getContext('2d');
  if (!ctx) return null;
  const color = options.color || CHART_COLORS.primary;
  return new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: options.label || 'Detections',
        data,
        borderColor: color,
        backgroundColor: makeGradient(ctx, color),
        fill: true,
        tension: 0.4,
        borderWidth: 2.5,
        pointRadius: 4,
        pointBackgroundColor: color,
        pointBorderColor: '#111827',
        pointBorderWidth: 2,
        pointHoverRadius: 6,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: !!options.showLegend } },
      scales: {
        x: { grid: { display: false } },
        y: { beginAtZero: true, ticks: { stepSize: options.stepSize || undefined } },
      },
      interaction: { mode: 'index', intersect: false },
    },
  });
}

function createDoughnutChart(canvasId, labels, data, colors) {
  const ctx = document.getElementById(canvasId)?.getContext('2d');
  if (!ctx) return null;
  colors = colors || SEVERITY_CHART_COLORS;
  return new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data,
        backgroundColor: colors,
        borderColor: '#111827',
        borderWidth: 3,
        hoverOffset: 6,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '68%',
      plugins: {
        legend: { position: 'bottom' },
      },
    },
  });
}

function createBarChart(canvasId, labels, data, options = {}) {
  const ctx = document.getElementById(canvasId)?.getContext('2d');
  if (!ctx) return null;
  const horizontal = !!options.horizontal;
  const colors = options.colors || labels.map(() => CHART_COLORS.primary);
  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: options.label || 'Count',
        data,
        backgroundColor: colors.map(c => hexToRgba(c, 0.7)),
        borderColor: colors,
        borderWidth: 1,
        borderRadius: 6,
        maxBarThickness: options.maxBarThickness || 40,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: horizontal ? 'y' : 'x',
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: horizontal }, beginAtZero: true },
        y: { grid: { display: !horizontal }, beginAtZero: true },
      },
    },
  });
}

function createAreaChart(canvasId, labels, data, options = {}) {
  return createLineChart(canvasId, labels, data, { ...options, fill: true });
}

/* ---- Update / Destroy helpers ---- */

function updateChart(chart, newLabels, newData) {
  if (!chart) return;
  chart.data.labels = newLabels;
  chart.data.datasets[0].data = newData;
  chart.update('none');
}

function destroyChart(chart) {
  if (chart) {
    chart.destroy();
  }
}
