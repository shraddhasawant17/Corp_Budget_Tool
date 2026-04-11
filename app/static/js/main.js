// ═══════════════════════════════════════════════════════════
// main.js — Global JS: Theme, Toast, Sidebar, Helpers
// ═══════════════════════════════════════════════════════════

// ── THEME (Dark / Light) ──────────────────────────────────
// localStorage se saved theme lo — page refresh pe bhi yaad rahe
const savedTheme = localStorage.getItem('rbl-theme') || 'dark';
document.documentElement.setAttribute('data-theme', savedTheme);
updateThemeBtn(savedTheme);

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme');
  const next    = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('rbl-theme', next);
  updateThemeBtn(next);
}

function updateThemeBtn(theme) {
  const btn = document.getElementById('themeBtn');
  if (btn) btn.textContent = theme === 'dark' ? '🌙' : '☀️';
}

// ── SIDEBAR TOGGLE ────────────────────────────────────────
function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  const main    = document.querySelector('.main-wrapper');
  if (window.innerWidth <= 768) {
    sidebar.classList.toggle('open');
  } else {
    sidebar.classList.toggle('collapsed');
    main.classList.toggle('full');
  }
}

// ── TOAST ─────────────────────────────────────────────────
let toastTimer;
function showToast(msg, type = 'success') {
  const t    = document.getElementById('toast');
  const icon = document.getElementById('toastIcon');
  const text = document.getElementById('toastText');
  const icons = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' };
  icon.textContent = icons[type] || 'ℹ️';
  text.textContent = msg;
  t.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove('show'), 3200);
}

// ── FORM STEPPER ──────────────────────────────────────────
let currentStep = 1;
const totalSteps = 5;

function goStep(n) {
  if (n < 1 || n > totalSteps) return;
  // Validate current step before going forward
  if (n > currentStep && !validateStep(currentStep)) return;
  if (n === totalSteps) populateReview();
  currentStep = n;
  renderStepper();
}

function renderStepper() {
  for (let i = 1; i <= totalSteps; i++) {
    const stepEl = document.getElementById('step-' + i);
    const cardEl = document.getElementById('form-step-' + i);
    if (!stepEl || !cardEl) continue;
    stepEl.className = 'step' + (i < currentStep ? ' done' : i === currentStep ? ' active' : '');
    cardEl.classList.toggle('hidden', i !== currentStep);
  }
}

function validateStep(n) {
  // Basic required field check per step
  const stepCard = document.getElementById('form-step-' + n);
  if (!stepCard) return true;
  const required = stepCard.querySelectorAll('[required]');
  let valid = true;
  required.forEach(el => {
    if (!el.value.trim()) {
      el.style.borderColor = 'var(--rbl-red)';
      el.addEventListener('input', () => el.style.borderColor = '', { once: true });
      valid = false;
    }
  });
  if (!valid) showToast('Please fill all required fields', 'error');
  return valid;
}

// ── CALCULATIONS (Budget Form Step 3) ────────────────────
function calcDiffs() {
  const a = parseFloat(document.getElementById('budgetA')?.value) || 0;
  const b = parseFloat(document.getElementById('budgetB')?.value) || 0;
  const c = parseFloat(document.getElementById('budgetC')?.value) || 0;
  const hasInput = document.getElementById('budgetA')?.value !== '';
  setCalcBox('calcAB', a - b, hasInput);
  setCalcBox('calcCB', c - b, hasInput);
  setCalcBox('calcCA', c - a, hasInput);
}

function setCalcBox(id, val, hasInput) {
  const el = document.getElementById(id);
  if (!el) return;
  if (!hasInput) { el.textContent = '—'; el.style.color = 'var(--text-muted)'; return; }
  const fmt = '₹' + Math.abs(val).toLocaleString('en-IN', { maximumFractionDigits: 2 });
  el.textContent  = (val >= 0 ? '+ ' : '− ') + fmt;
  el.style.color  = val >= 0 ? 'var(--success)' : 'var(--rbl-light-red)';
}

// ── REVIEW POPULATE (Step 5) ──────────────────────────────
function populateReview() {
  const getVal = id => document.getElementById(id)?.value || '—';
  const getText = id => {
    const el = document.getElementById(id);
    return el?.options?.[el.selectedIndex]?.text || el?.value || '—';
  };
  const fmt = v => v ? '₹' + parseFloat(v).toLocaleString('en-IN') : '—';

  setReview('rev-oldnew',   getText('oldNew'));
  setReview('rev-business', getText('businessSelect'));
  setReview('rev-costcode', document.getElementById('costCodeDisplay')?.textContent || '—');
  setReview('rev-ithead',   document.getElementById('itHeadDisplay')?.textContent || '—');
  setReview('rev-type',     getText('expenseSubType'));
  setReview('rev-app',      getVal('applicationPlatform'));
  setReview('rev-vendor',   getVal('vendorName'));
  setReview('rev-desc',     getVal('shortDescription'));
  setReview('rev-a',        fmt(getVal('budgetA')));
  setReview('rev-b',        fmt(getVal('budgetB')));
  setReview('rev-c',        fmt(getVal('budgetC')));

  const a = parseFloat(getVal('budgetA')) || 0;
  const b = parseFloat(getVal('budgetB')) || 0;
  const diff = a - b;
  const diffEl = document.getElementById('rev-ab');
  if (diffEl) {
    diffEl.textContent = (diff >= 0 ? '+ ' : '− ') + '₹' + Math.abs(diff).toLocaleString('en-IN');
    diffEl.style.color = diff >= 0 ? 'var(--success)' : 'var(--rbl-light-red)';
  }
}

function setReview(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

// ── CONDITIONAL FIELDS ────────────────────────────────────
function togglePrevKey() {
  const v  = document.getElementById('oldNew')?.value;
  const el = document.getElementById('prevKeyField');
  if (!el) return;
  el.classList.toggle('hidden', v !== 'old');
  const input = el.querySelector('input');
  if (input) input.required = v === 'old';
}

// Cost code map — business → cost code
const COST_CODES = {
  retail   : 'RBL-RB-CC-001',
  corporate: 'RBL-CB-CC-002',
  digital  : 'RBL-DB-CC-003',
  risk     : 'RBL-RM-CC-004',
  ops      : 'RBL-OP-CC-005',
  treasury : 'RBL-TR-CC-006',
};

function autoFillCostCode() {
  const v  = document.getElementById('businessSelect')?.value;
  const el = document.getElementById('costCodeDisplay');
  if (el) el.textContent = COST_CODES[v] || 'Select a Business Name first';
  // Hidden input update
  const hidden = document.getElementById('costCodeHidden');
  if (hidden) hidden.value = COST_CODES[v] || '';
}

// ── CONFIRM DIALOGS ───────────────────────────────────────
function confirmAction(msg, formId) {
  if (confirm(msg)) {
    document.getElementById(formId)?.submit();
  }
}

// ── FORMAT NUMBERS ────────────────────────────────────────
function formatINR(num) {
  return '₹' + parseFloat(num).toLocaleString('en-IN', { maximumFractionDigits: 2 });
}

// ── CHART INIT (Dashboard) ───────────────────────────────
// Charts are initialized inline in dashboard template
// This is a placeholder for any shared chart config
const CHART_DEFAULTS = {
  gridColor : 'rgba(128,128,160,0.1)',
  textColor : getComputedStyle(document.documentElement).getPropertyValue('--text-muted').trim() || '#8888A0',
  fontFamily: "'Plus Jakarta Sans', sans-serif",
};

// Re-render charts on theme toggle
const _origToggleTheme = toggleTheme;
window.toggleTheme = function () {
  _origToggleTheme();
  // Small delay to let CSS vars update then reload
  setTimeout(() => location.reload(), 150);
};
