/**
 * careers.js — Career paths list and career detail pages.
 */
'use strict';

async function initCareersPage() {
  if (!auth.requireAuth()) return;
  utils.initTheme();
  utils.initSidebar();
  utils.setActiveNav('careers');
  utils.updateSidebarUser(auth.getUser());

  const loadingEl  = document.getElementById('careers-loading');
  const containerEl = document.getElementById('careers-grid');

  if (loadingEl) loadingEl.classList.remove('hidden');

  try {
    const careers = await api.apiGet('/analysis/careers');
    renderCareers(careers, containerEl);
  } catch (err) {
    if (containerEl) containerEl.innerHTML = `<div class="alert alert-danger">${utils.escHtml(err.message)}</div>`;
  } finally {
    if (loadingEl) loadingEl.classList.add('hidden');
  }

  // Search filter
  const searchInput = document.getElementById('career-search');
  if (searchInput) {
    let debounceTimer;
    searchInput.addEventListener('input', () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => filterCareers(searchInput.value), 250);
    });
  }
}

let _allCareers = [];

function renderCareers(careers, container) {
  if (!container) return;
  _allCareers = careers;

  if (careers.length === 0) {
    container.innerHTML = `<div class="empty-state"><div class="empty-icon">🎯</div><div class="empty-title">No careers found</div></div>`;
    return;
  }

  container.innerHTML = careers.map(c => careerCardHTML(c)).join('');
}

function careerCardHTML(c) {
  const skills = (c.skills || []).slice(0, 4).map(s => `<span class="skill-chip">${utils.escHtml(s)}</span>`).join('');
  return `
    <div class="career-card fade-in" onclick="window.location.href='/career-details.html?id=${c.id}'" tabindex="0" role="button" aria-label="View ${utils.escHtml(c.title)}">
      <div class="career-card-title">${utils.escHtml(c.title)}</div>
      <div class="career-card-desc">${utils.escHtml(c.description)}</div>
      <div class="career-card-skills">${skills}</div>
      <div class="career-card-footer">
        <span class="career-card-salary">💰 ${utils.escHtml(c.salary_range || 'Varies')}</span>
        <span class="btn btn-primary btn-sm">View →</span>
      </div>
    </div>`;
}

function filterCareers(query) {
  const q = query.toLowerCase();
  const filtered = _allCareers.filter(c =>
    c.title.toLowerCase().includes(q) ||
    c.description.toLowerCase().includes(q) ||
    (c.skills || []).some(s => s.toLowerCase().includes(q))
  );
  const container = document.getElementById('careers-grid');
  renderCareers(filtered, container);
}

// ── Career Detail Page ─────────────────────────────────
async function initCareerDetailPage() {
  if (!auth.requireAuth()) return;
  utils.initTheme();
  utils.initSidebar();
  utils.setActiveNav('careers');
  utils.updateSidebarUser(auth.getUser());

  const params  = new URLSearchParams(window.location.search);
  const careerId = params.get('id');
  if (!careerId) { window.location.href = '/careers.html'; return; }

  const loadingEl = document.getElementById('detail-loading');
  const contentEl = document.getElementById('detail-content');

  if (loadingEl) loadingEl.classList.remove('hidden');

  try {
    // Get career + user's last resume for skill gap
    const [career, history] = await Promise.all([
      api.apiGet(`/analysis/careers/${careerId}`),
      api.apiGet('/analysis/history').catch(() => []),
    ]);

    let userSkills = [];
    if (history.length > 0) {
      const lastResult = await api.apiGet(`/analysis/history/${history[0].id}`).catch(() => null);
      userSkills = lastResult?.skills || [];
    }

    renderCareerDetail(career, userSkills, contentEl);
    // Update page title
    document.title = `${career.title} | CareerAI`;
  } catch (err) {
    if (contentEl) contentEl.innerHTML = `<div class="alert alert-danger">${utils.escHtml(err.message)}</div>`;
  } finally {
    if (loadingEl) loadingEl.classList.add('hidden');
    if (contentEl) contentEl.classList.remove('hidden');
  }
}

function renderCareerDetail(career, userSkills, container) {
  if (!container) return;

  const userSkillsLower = userSkills.map(s => s.toLowerCase());
  const careerSkills    = career.skills || [];
  const haveSkills      = careerSkills.filter(s => userSkillsLower.includes(s.toLowerCase()));
  const missingSkills   = careerSkills.filter(s => !userSkillsLower.includes(s.toLowerCase()));

  const skillGapHTML = (userSkills.length > 0)
    ? `<div class="card mt-4">
        <h4 class="mb-2">🎯 Skill Gap Analysis</h4>
        <p class="fs-sm text-muted mb-3">Based on your uploaded resume:</p>
        ${haveSkills.map(s => `<div class="skill-gap-row skill-have"><span class="skill-gap-icon">✓</span><span class="skill-gap-name">${utils.escHtml(s)}</span><span class="badge badge-success">Have</span></div>`).join('')}
        ${missingSkills.map(s => `<div class="skill-gap-row skill-missing"><span class="skill-gap-icon">✕</span><span class="skill-gap-name">${utils.escHtml(s)}</span><span class="badge badge-danger">Missing</span></div>`).join('')}
      </div>`
    : `<div class="alert alert-info mt-4">Upload your resume to see a personalized skill gap analysis.</div>`;

  const toolsHTML = (career.tools || []).map(t => `<span class="badge badge-gray">${utils.escHtml(t)}</span>`).join('');
  const respHTML  = (career.responsibilities || []).map(r => `<li>${utils.escHtml(r)}</li>`).join('');

  container.innerHTML = `
    <div class="career-detail-header">
      <div class="career-detail-icon">💼</div>
      <div>
        <div class="career-detail-title">${utils.escHtml(career.title)}</div>
        <div class="career-detail-salary">💰 ${utils.escHtml(career.salary_range || 'Salary varies')}</div>
        <div class="career-detail-desc">${utils.escHtml(career.description)}</div>
      </div>
    </div>

    <div class="two-col-grid">
      <div>
        <div class="card mb-4">
          <h4 class="mb-3">🛠 Required Skills</h4>
          <div class="skills-container">
            ${careerSkills.map(s => `<span class="skill-chip">${utils.escHtml(s)}</span>`).join('')}
          </div>
        </div>

        <div class="card mb-4">
          <h4 class="mb-3">⚙️ Tools & Technologies</h4>
          <div class="flex" style="flex-wrap:wrap;gap:6px">${toolsHTML}</div>
        </div>

        ${skillGapHTML}
      </div>

      <div>
        <div class="card mb-4">
          <h4 class="mb-3">📋 Responsibilities</h4>
          <ul class="resp-list">${respHTML}</ul>
        </div>

        <div class="card mb-4">
          <h4 class="mb-3">🚀 Future Scope</h4>
          <p class="fs-sm">${utils.escHtml(career.future_scope || '')}</p>
        </div>

        <button class="btn btn-primary btn-full" onclick="window.location.href='/chat.html'">
          💬 Ask AI About This Career
        </button>
      </div>
    </div>
  `;
}

// ── Roadmap on career detail ───────────────────────────
async function generateRoadmap(currentRole, targetRole) {
  const container = document.getElementById('roadmap-result');
  if (!container) return;

  container.innerHTML = '<div class="page-loading"><div class="spinner"></div> Generating roadmap…</div>';

  try {
    const data = await api.apiPost('/analysis/roadmap', { current_role: currentRole, target_role: targetRole });
    renderRoadmap(data, container);
  } catch (err) {
    container.innerHTML = `<div class="alert alert-danger">${utils.escHtml(err.message)}</div>`;
  }
}

function renderRoadmap(data, container) {
  const stagesHTML = (data.stages || []).map(stage => `
    <div class="roadmap-stage fade-in">
      <span class="stage-period">${utils.escHtml(stage.period)}</span>
      <div class="stage-goal">${utils.escHtml(stage.goal)}</div>
      <div class="stage-grid">
        <div>
          <div class="stage-list-title actions">⚡ Actions</div>
          <ul class="stage-items actions">
            ${(stage.actions || []).map(a => `<li>${utils.escHtml(a)}</li>`).join('')}
          </ul>
        </div>
        <div>
          <div class="stage-list-title resources">📚 Resources</div>
          <ul class="stage-items resources">
            ${(stage.resources || []).map(r => `<li>${utils.escHtml(r)}</li>`).join('')}
          </ul>
        </div>
      </div>
    </div>`).join('');

  container.innerHTML = `
    <div class="card mb-4">
      <p class="fs-sm text-secondary">${utils.escHtml(data.overview || '')}</p>
    </div>
    ${stagesHTML}`;
}

window.generateRoadmap = generateRoadmap;

document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('careers-grid'))    initCareersPage();
  if (document.getElementById('detail-content'))  initCareerDetailPage();
});
