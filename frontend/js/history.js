/**
 * history.js — Resume analysis history page.
 */
'use strict';

async function initHistoryPage() {
  if (!auth.requireAuth()) return;
  utils.initTheme();
  utils.initSidebar();
  utils.setActiveNav('history');
  utils.updateSidebarUser(auth.getUser());

  const params = new URLSearchParams(window.location.search);
  const detailId = params.get('id');

  if (detailId) {
    await loadHistoryDetail(detailId);
  } else {
    await loadHistoryList();
  }
}

async function loadHistoryList() {
  const tableBody = document.getElementById('history-tbody');
  const emptyEl   = document.getElementById('history-empty');
  const loadingEl = document.getElementById('history-loading');

  if (loadingEl) loadingEl.classList.remove('hidden');

  try {
    const history = await api.apiGet('/analysis/history');
    if (loadingEl) loadingEl.classList.add('hidden');

    if (history.length === 0) {
      if (emptyEl) emptyEl.classList.remove('hidden');
      return;
    }

    if (tableBody) {
      tableBody.innerHTML = history.map(r => {
        const scoreColor = utils.getScoreColor(r.ats_score);
        const scoreLbl   = utils.getScoreLabelText(r.ats_score);
        const careers    = (r.career_matches || []).slice(0, 2).join(', ') || '—';
        return `
          <tr>
            <td><div class="filename-cell" title="${utils.escHtml(r.filename)}">${utils.escHtml(r.filename)}</div></td>
            <td>
              <span class="fw-700" style="color:${scoreColor}">${Math.round(r.ats_score)}</span>
              <span class="text-muted fs-sm">&nbsp;${scoreLbl}</span>
            </td>
            <td class="text-secondary">${utils.escHtml(careers)}</td>
            <td class="text-muted fs-sm">${utils.formatDate(r.created_at)}</td>
            <td>
              <div class="flex gap-2">
                <a href="/history.html?id=${r.id}" class="btn btn-secondary btn-sm">View</a>
                <button class="btn btn-danger btn-sm" onclick="deleteResult(${r.id}, this)">Delete</button>
              </div>
            </td>
          </tr>`;
      }).join('');
    }
  } catch (err) {
    if (loadingEl) loadingEl.classList.add('hidden');
    utils.showToast('Failed to load history: ' + err.message, 'error');
  }
}

async function deleteResult(id, btn) {
  if (!confirm('Delete this analysis? This cannot be undone.')) return;
  btn.disabled = true;
  try {
    await api.apiDelete(`/analysis/history/${id}`);
    utils.showToast('Analysis deleted.', 'success');
    await loadHistoryList();
  } catch (err) {
    utils.showToast('Delete failed: ' + err.message, 'error');
    btn.disabled = false;
  }
}

async function loadHistoryDetail(id) {
  const detailEl  = document.getElementById('detail-panel');
  const listEl    = document.getElementById('list-panel');
  if (listEl)   listEl.classList.add('hidden');
  if (detailEl) detailEl.classList.remove('hidden');

  const loadingEl = document.getElementById('detail-loading');
  if (loadingEl) loadingEl.classList.remove('hidden');

  try {
    const r = await api.apiGet(`/analysis/history/${id}`);
    if (loadingEl) loadingEl.classList.add('hidden');
    renderDetail(r);
  } catch (err) {
    if (loadingEl) loadingEl.classList.add('hidden');
    utils.showToast('Could not load detail: ' + err.message, 'error');
  }
}

function renderDetail(r) {
  const scoreColor = utils.getScoreColor(r.ats_score);

  document.getElementById('detail-filename').textContent = r.filename || '';
  document.getElementById('detail-date').textContent = utils.formatDate(r.created_at);

  // ATS score
  const numEl = document.getElementById('detail-score-num');
  const fill  = document.getElementById('detail-ring-fill');
  if (numEl) { numEl.textContent = Math.round(r.ats_score); numEl.style.color = scoreColor; }
  if (fill) {
    const circ = 339;
    fill.style.stroke = scoreColor;
    setTimeout(() => fill.style.strokeDashoffset = circ - (r.ats_score / 100) * circ, 100);
  }

  // Summary
  document.getElementById('detail-summary').textContent = r.ats_summary || '';

  // Skills
  const skillsEl = document.getElementById('detail-skills');
  if (skillsEl) {
    skillsEl.innerHTML = (r.skills || []).map(s => `<span class="skill-chip">${utils.escHtml(s)}</span>`).join('') || '<span class="text-muted fs-sm">None detected</span>';
  }

  // Lists
  renderDetailList('detail-strengths', r.strengths, 'list-strengths');
  renderDetailList('detail-gaps', r.gaps, 'list-gaps');
  renderDetailList('detail-suggestions', r.suggestions, 'list-suggestions');
}

function renderDetailList(id, items, cls) {
  const ul = document.getElementById(id);
  if (!ul) return;
  ul.className = `result-list ${cls}`;
  ul.innerHTML = (items || []).map(i => `<li>${utils.escHtml(i)}</li>`).join('') || '<li>None</li>';
}

window.deleteResult = deleteResult;

document.addEventListener('DOMContentLoaded', initHistoryPage);
