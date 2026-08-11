/**
 * resume.js — Resume upload, analysis, and result display.
 */
'use strict';

let _uploadedFile = null;
let _lastResult   = null;

async function initResumePage() {
  if (!auth.requireAuth()) return;
  utils.initTheme();
  utils.initSidebar();
  utils.setActiveNav('resume');
  utils.updateSidebarUser(auth.getUser());
  setupDropZone();
}

// ── Drop Zone ──────────────────────────────────────────
function setupDropZone() {
  const dz       = document.getElementById('drop-zone');
  const fileInput = document.getElementById('file-input');
  const analyzeBtn = document.getElementById('analyze-btn');

  if (!dz) return;

  // Click to browse
  dz.addEventListener('click', () => fileInput.click());
  dz.addEventListener('keydown', e => {
    if (e.key === 'Enter' || e.key === ' ') fileInput.click();
  });

  // Drag events
  dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('drag-over'); });
  dz.addEventListener('dragleave', () => dz.classList.remove('drag-over'));
  dz.addEventListener('drop', e => {
    e.preventDefault();
    dz.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files[0]) handleFile(fileInput.files[0]);
  });

  // Analyze button
  analyzeBtn?.addEventListener('click', runAnalysis);

  // Target role enter key
  document.getElementById('target-role')?.addEventListener('keydown', e => {
    if (e.key === 'Enter') runAnalysis();
  });
}

function handleFile(file) {
  const ext = file.name.split('.').pop().toLowerCase();
  if (!['pdf', 'docx'].includes(ext)) {
    showFileError('Only PDF and DOCX files are supported.');
    return;
  }
  if (file.size > 10 * 1024 * 1024) {
    showFileError('File exceeds 10 MB limit.');
    return;
  }

  _uploadedFile = file;
  clearFileError();

  // Show selected file indicator
  const sel = document.getElementById('file-selected');
  if (sel) {
    sel.innerHTML = `<span>✓</span> ${utils.escHtml(file.name)} (${formatSize(file.size)})`;
    sel.classList.remove('hidden');
  }

  document.getElementById('analyze-btn').disabled = false;
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + 'B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + 'KB';
  return (bytes / (1024 * 1024)).toFixed(1) + 'MB';
}

function showFileError(msg) {
  const el = document.getElementById('file-error');
  if (el) { el.textContent = msg; el.classList.remove('hidden'); }
}
function clearFileError() {
  const el = document.getElementById('file-error');
  if (el) el.classList.add('hidden');
}

// ── Run Analysis ───────────────────────────────────────
async function runAnalysis() {
  if (!_uploadedFile) return;

  const targetRole = document.getElementById('target-role')?.value.trim();
  const analyzeBtn = document.getElementById('analyze-btn');
  const resultsEl  = document.getElementById('results-section');
  const loadingEl  = document.getElementById('loading-panel');

  clearFileError();
  analyzeBtn.disabled = true;
  analyzeBtn.innerHTML = '<span class="spinner spinner-sm"></span> Analyzing…';
  if (resultsEl) resultsEl.classList.add('hidden');
  if (loadingEl) loadingEl.classList.remove('hidden');

  utils.startLoadingSteps('loading-panel');

  const formData = new FormData();
  formData.append('file', _uploadedFile);
  if (targetRole) formData.append('target_role', targetRole);

  try {
    const result = await api.apiForm('/analysis/upload', formData);
    _lastResult = result;
    renderResults(result);
    if (resultsEl) resultsEl.classList.remove('hidden');
    utils.showToast('Resume analyzed successfully!', 'success');
  } catch (err) {
    showFileError(err.message);
    utils.showToast('Analysis failed: ' + err.message, 'error');
  } finally {
    if (loadingEl) loadingEl.classList.add('hidden');
    analyzeBtn.disabled = false;
    analyzeBtn.innerHTML = '✨ Analyze Resume';
    utils.stopLoadingSteps();
  }
}

// ── Render Results ─────────────────────────────────────
function renderResults(data) {
  renderAtsScore(data.ats_score, data.ats_summary);
  renderSkills(data.skills);
  renderList('strengths-list', data.strengths, 'list-strengths');
  renderList('gaps-list', data.gaps, 'list-gaps');
  renderList('suggestions-list', data.suggestions, 'list-suggestions');
  renderCareerMatches(data.career_matches);
}

function renderAtsScore(score, summary) {
  score = Math.round(score || 0);
  const color = utils.getScoreColor(score);
  const label = utils.getScoreLabelText(score);

  // Number
  const numEl = document.getElementById('ats-num');
  if (numEl) { numEl.textContent = score; numEl.style.color = color; }

  // SVG ring (circumference = 2π*54 ≈ 339)
  const fill = document.getElementById('ats-ring-fill');
  if (fill) {
    const circ = 339;
    const offset = circ - (score / 100) * circ;
    fill.style.stroke = color;
    setTimeout(() => fill.style.strokeDashoffset = offset, 100);
  }

  // Label + summary
  const labelEl = document.getElementById('ats-label');
  if (labelEl) { labelEl.textContent = label; labelEl.style.color = color; }
  const summaryEl = document.getElementById('ats-summary');
  if (summaryEl) summaryEl.textContent = summary || '';
}

function renderSkills(skills) {
  const container = document.getElementById('skills-container');
  if (!container) return;
  if (!skills || skills.length === 0) {
    container.innerHTML = '<span class="text-muted fs-sm">No skills detected</span>';
    return;
  }
  container.innerHTML = skills
    .map(s => `<span class="skill-chip">${utils.escHtml(s)}</span>`)
    .join('');
}

function renderList(id, items, cls) {
  const ul = document.getElementById(id);
  if (!ul) return;
  if (!items || items.length === 0) {
    ul.innerHTML = '<li>No data available.</li>';
    return;
  }
  ul.className = `result-list ${cls}`;
  ul.innerHTML = items.map(i => `<li>${utils.escHtml(i)}</li>`).join('');
}

function renderCareerMatches(matches) {
  const container = document.getElementById('career-matches');
  if (!container) return;
  if (!matches || matches.length === 0) {
    container.innerHTML = '<div class="empty-state"><div class="empty-icon">🎯</div><div class="empty-title">No career matches found</div></div>';
    return;
  }
  container.innerHTML = matches.map(c => {
    const pct = c.match_percentage || 0;
    const color = utils.getScoreColor(pct);
    const skills = (c.matched_skills || []).slice(0, 4).map(s =>
      `<span class="skill-chip">${utils.escHtml(s)}</span>`).join('');
    return `
      <div class="career-match-card" onclick="window.location.href='/career-details.html?id=${c.id}'">
        <div class="career-match-header">
          <div class="career-match-title">${utils.escHtml(c.title)}</div>
          <div class="career-match-pct" style="color:${color}">${pct}%</div>
        </div>
        <div class="career-match-skills">${skills}</div>
        ${c.salary_range ? `<div class="career-match-salary">💰 ${utils.escHtml(c.salary_range)}</div>` : ''}
        <div class="flex gap-2">
          <button class="btn btn-primary btn-sm" onclick="event.stopPropagation();window.location.href='/career-details.html?id=${c.id}'">View Career</button>
        </div>
      </div>`;
  }).join('');
}

document.addEventListener('DOMContentLoaded', initResumePage);
