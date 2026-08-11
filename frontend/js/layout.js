/**
 * layout.js — Injects shared sidebar + topbar HTML dynamically.
 * Call layout.init(pageId, pageTitle, pageSubtitle) at the top of each protected page.
 */
'use strict';

const SIDEBAR_HTML = `
<aside id="sidebar" class="sidebar" role="navigation" aria-label="Main navigation">
  <a href="/dashboard.html" class="sidebar-brand">
    <div class="sidebar-logo">🚀</div>
    <div>
      <div class="sidebar-name">CareerAI</div>
      <div class="sidebar-tagline">Career Platform</div>
    </div>
  </a>
  <nav class="sidebar-nav">
    <div class="nav-section-label">Main</div>
    <a href="/dashboard.html" class="nav-item" data-page="dashboard">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
      Dashboard
    </a>
    <a href="/resume.html" class="nav-item" data-page="resume">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
      Resume Analyzer
    </a>
    <a href="/careers.html" class="nav-item" data-page="careers">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>
      Career Paths
    </a>
    <a href="/chat.html" class="nav-item" data-page="chat">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
      AI Assistant
    </a>
    <div class="nav-section-label" style="margin-top:8px">Records</div>
    <a href="/history.html" class="nav-item" data-page="history">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="12 8 12 12 14 14"/><path d="M3.05 11a9 9 0 1 0 .5-4.5"/><polyline points="3 3 3 7 7 7"/></svg>
      History
    </a>
    <div class="nav-section-label" style="margin-top:8px">Account</div>
    <a href="/profile.html" class="nav-item" data-page="profile">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
      Profile
    </a>
    <a href="/settings.html" class="nav-item" data-page="settings">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
      Settings
    </a>
  </nav>
  <div class="sidebar-footer">
    <div class="sidebar-user" id="sidebar-logout" role="button" tabindex="0" aria-label="Logout">
      <div class="user-avatar" id="sidebar-user-initial">U</div>
      <div class="user-info">
        <div class="user-name" id="sidebar-user-name">Loading…</div>
        <div class="user-role">Click to logout</div>
      </div>
    </div>
  </div>
</aside>`;

const layout = {
  init(pageId, pageTitle, pageSubtitle = '') {
    // Auth gate
    if (!auth.requireAuth()) return false;

    // Theme
    utils.initTheme();

    // Inject sidebar if not already present
    if (!document.getElementById('sidebar')) {
      const overlay = document.createElement('div');
      overlay.id = 'sidebar-overlay';
      overlay.className = 'sidebar-overlay';
      document.body.insertAdjacentHTML('afterbegin', SIDEBAR_HTML);
      document.body.insertAdjacentElement('afterbegin', overlay);
    }

    // Inject topbar if not already present
    if (!document.getElementById('topbar')) {
      const topbarHTML = `
        <header id="topbar" class="topbar">
          <div class="topbar-left">
            <button id="menu-toggle" class="menu-toggle" aria-label="Toggle menu">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
            </button>
            <div>
              <div class="topbar-title">${pageTitle}</div>
              ${pageSubtitle ? `<div class="topbar-subtitle">${pageSubtitle}</div>` : ''}
            </div>
          </div>
          <div class="topbar-right">
            <button class="theme-toggle" id="theme-toggle-btn" aria-label="Toggle theme" title="Toggle dark mode">
              <span id="theme-icon">🌙</span>
            </button>
          </div>
        </header>`;
      document.body.insertAdjacentHTML('afterbegin', topbarHTML);
    }

    // Sidebar logic
    utils.initSidebar();
    utils.setActiveNav(pageId);

    // User info
    const user = auth.getUser();
    utils.updateSidebarUser(user);

    // Logout handler
    document.getElementById('sidebar-logout')?.addEventListener('click', () => {
      auth.logout();
      window.location.href = '/login.html';
    });

    // Theme toggle
    document.getElementById('theme-toggle-btn')?.addEventListener('click', () => utils.toggleTheme());

    // Mobile sidebar
    const menuBtn = document.getElementById('menu-toggle');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    if (window.innerWidth <= 768) {
      menuBtn.style.display = 'flex';
    } else {
      menuBtn.style.display = 'none';
    }
    window.addEventListener('resize', () => {
      menuBtn.style.display = window.innerWidth <= 768 ? 'flex' : 'none';
    });
    menuBtn?.addEventListener('click', () => { sidebar?.classList.toggle('open'); overlay?.classList.toggle('show'); });
    overlay?.addEventListener('click', () => { sidebar?.classList.remove('open'); overlay?.classList.remove('show'); });

    return true;
  }
};

window.layout = layout;
