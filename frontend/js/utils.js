/**
 * utils.js — Shared utilities: toasts, theme, sidebar, DOM helpers, time.
 */
'use strict';

// ── Toast notifications ────────────────────────────────
function showToast(message, type = 'info', duration = 4000) {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const icons = { success: '✓', error: '✕', info: 'ℹ', warning: '⚠' };
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span>${icons[type] || 'ℹ'}</span><span>${escHtml(message)}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(20px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// ── Escape HTML ────────────────────────────────────────
function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// ── Format markdown-ish AI text → safe HTML ────────────
function formatAiText(text) {
  return escHtml(text)
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>');
}

// ── Theme toggle ───────────────────────────────────────
function initTheme() {
  const saved = localStorage.getItem('theme') || 'light';
  applyTheme(saved);
}

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('theme', theme);

  // Update toggle icon if present
  const icon = document.getElementById('theme-icon');
  if (icon) icon.textContent = theme === 'dark' ? '☀️' : '🌙';
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme') || 'light';
  applyTheme(current === 'dark' ? 'light' : 'dark');
}

// ── Sidebar ────────────────────────────────────────────
function initSidebar() {
  const sidebar  = document.getElementById('sidebar');
  const overlay  = document.getElementById('sidebar-overlay');
  const menuBtn  = document.getElementById('menu-toggle');

  if (!sidebar) return;

  menuBtn?.addEventListener('click', () => {
    sidebar.classList.toggle('open');
    overlay?.classList.toggle('show');
  });

  overlay?.addEventListener('click', () => {
    sidebar.classList.remove('open');
    overlay.classList.remove('show');
  });
}

// Mark active nav item
function setActiveNav(pageId) {
  document.querySelectorAll('.nav-item').forEach(item => {
    item.classList.toggle('active', item.dataset.page === pageId);
  });
}

// ── Date/time helpers ──────────────────────────────────
function formatDate(isoString) {
  if (!isoString) return '—';
  const d = new Date(isoString);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function formatTime(date) {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function timeAgo(isoString) {
  if (!isoString) return '';
  const diff = Date.now() - new Date(isoString).getTime();
  const mins  = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days  = Math.floor(diff / 86400000);
  if (mins < 1)   return 'just now';
  if (mins < 60)  return `${mins}m ago`;
  if (hours < 24) return `${hours}h ago`;
  if (days < 7)   return `${days}d ago`;
  return formatDate(isoString);
}

// ── Greeting ───────────────────────────────────────────
function getGreeting() {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 17) return 'Good afternoon';
  return 'Good evening';
}

// ── ATS score color ────────────────────────────────────
function getScoreColor(score) {
  if (score >= 80) return '#10b981';
  if (score >= 60) return '#f59e0b';
  if (score >= 40) return '#f97316';
  return '#ef4444';
}

function getScoreLabelText(score) {
  if (score >= 80) return 'Excellent';
  if (score >= 60) return 'Good';
  if (score >= 40) return 'Needs Work';
  return 'Poor';
}

// ── Loading steps animator ──────────────────────────────
let _stepTimer = null;

function startLoadingSteps(containerId) {
  const steps = document.querySelectorAll(`#${containerId} .loading-step`);
  let i = 0;
  steps.forEach(s => s.classList.remove('active', 'done'));
  if (steps[0]) steps[0].classList.add('active');
  _stepTimer = setInterval(() => {
    if (i < steps.length) {
      if (i > 0) steps[i - 1].classList.replace('active', 'done');
      if (steps[i]) steps[i].classList.add('active');
      i++;
    }
  }, 2000);
}

function stopLoadingSteps() {
  if (_stepTimer) { clearInterval(_stepTimer); _stepTimer = null; }
}

// ── User sidebar display ───────────────────────────────
function updateSidebarUser(user) {
  const nameEl = document.getElementById('sidebar-user-name');
  const initEl = document.getElementById('sidebar-user-initial');
  if (nameEl && user) nameEl.textContent = user.full_name || user.email;
  if (initEl && user) initEl.textContent = (user.full_name || user.email || 'U')[0].toUpperCase();
}

// Expose globally
window.utils = {
  showToast, escHtml, formatAiText,
  initTheme, applyTheme, toggleTheme,
  initSidebar, setActiveNav,
  formatDate, formatTime, timeAgo,
  getGreeting, getScoreColor, getScoreLabelText,
  startLoadingSteps, stopLoadingSteps,
  updateSidebarUser,
};
