/**
 * dashboard.js — Dashboard page: stats, recent activity, quick actions.
 */
'use strict';

async function initDashboard() {
  if (!auth.requireAuth()) return;
  utils.initTheme();
  utils.initSidebar();
  utils.setActiveNav('dashboard');

  const user = auth.getUser();
  utils.updateSidebarUser(user);

  // Greeting
  const greetEl = document.getElementById('greeting');
  const nameEl  = document.getElementById('greeting-name');
  if (greetEl) greetEl.textContent = utils.getGreeting() + ',';
  if (nameEl && user) nameEl.textContent = (user.full_name || user.email).split(' ')[0];

  // Load history for stats
  try {
    const history = await api.apiGet('/analysis/history');
    renderStats(history);
    renderActivity(history);
  } catch (err) {
    console.error('Dashboard load error:', err);
  }
}

function renderStats(history) {
  const analyses = history.length;
  const lastResult = history[0];
  const avgScore = analyses > 0
    ? Math.round(history.reduce((s, r) => s + r.ats_score, 0) / analyses)
    : 0;

  document.getElementById('stat-analyses').textContent = analyses;
  document.getElementById('stat-score').textContent = lastResult?.ats_score
    ? Math.round(lastResult.ats_score) + '/100'
    : 'N/A';
  document.getElementById('stat-careers').textContent = lastResult?.career_matches?.length || 0;
  document.getElementById('stat-avg').textContent = analyses > 0 ? avgScore + '/100' : 'N/A';
}

function renderActivity(history) {
  const container = document.getElementById('activity-list');
  if (!container) return;

  if (history.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">📄</div>
        <div class="empty-title">No analyses yet</div>
        <div class="empty-text">Upload your first resume to get started.</div>
        <a href="/resume.html" class="btn btn-primary btn-sm mt-2">Analyze Resume</a>
      </div>`;
    return;
  }

  container.innerHTML = history.slice(0, 5).map(r => {
    const scoreColor = utils.getScoreColor(r.ats_score);
    const careers = (r.career_matches || []).slice(0, 1).join('') || 'Career analysis';
    return `
      <div class="activity-item fade-in">
        <div class="activity-icon primary" style="background:var(--primary-glow)">📄</div>
        <div class="activity-content">
          <div class="activity-title">${utils.escHtml(r.filename)}</div>
          <div class="activity-time">${careers} • ${utils.timeAgo(r.created_at)}</div>
        </div>
        <div class="activity-score" style="color:${scoreColor}">${Math.round(r.ats_score)}</div>
        <a href="/history.html?id=${r.id}" class="btn btn-ghost btn-sm btn-icon">→</a>
      </div>`;
  }).join('');
}

document.addEventListener('DOMContentLoaded', initDashboard);
