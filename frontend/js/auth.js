/**
 * auth.js — Authentication state management.
 * Stores JWT token + user profile in localStorage.
 * All pages that require auth call auth.requireAuth() on load.
 */
'use strict';

const TOKEN_KEY = 'career_ai_token';
const USER_KEY  = 'career_ai_user';

const auth = {
  getToken() { return localStorage.getItem(TOKEN_KEY); },
  getUser()  { return JSON.parse(localStorage.getItem(USER_KEY) || 'null'); },
  isLoggedIn() { return !!this.getToken(); },

  saveSession(token, user) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  },

  logout() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },

  /** Redirect to login if not authenticated. Call at top of every protected page. */
  requireAuth() {
    if (!this.isLoggedIn()) {
      window.location.replace('/login.html');
      return false;
    }
    return true;
  },

  /** Redirect dashboard if already logged in (for login/register pages). */
  redirectIfLoggedIn() {
    if (this.isLoggedIn()) {
      window.location.replace('/dashboard.html');
      return true;
    }
    return false;
  },

  /** Verify token with server and refresh user data. */
  async verifyAndRefresh() {
    try {
      const user = await api.apiGet('/auth/verify');
      this.saveSession(this.getToken(), user);
      return user;
    } catch (_) {
      this.logout();
      window.location.replace('/login.html');
      return null;
    }
  },
};

window.auth = auth;

// ── Login form ─────────────────────────────────────────
function initLoginPage() {
  auth.redirectIfLoggedIn();

  const form     = document.getElementById('login-form');
  const errEl    = document.getElementById('login-error');
  const submitBtn = document.getElementById('login-btn');

  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email    = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value;

    errEl.classList.add('hidden');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner spinner-sm"></span> Signing in…';

    try {
      // OAuth2 form expects username + password as form data
      const formData = new URLSearchParams();
      formData.set('username', email);
      formData.set('password', password);

      const res = await fetch('/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData,
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || 'Invalid email or password.');
      }

      const data = await res.json();
      auth.saveSession(data.access_token, data.user);

      if (document.getElementById('remember-me')?.checked) {
        // Token already persisted in localStorage — nothing extra needed
      }

      window.location.href = '/dashboard.html';
    } catch (err) {
      errEl.textContent = err.message;
      errEl.classList.remove('hidden');
      submitBtn.disabled = false;
      submitBtn.innerHTML = 'Sign In';
    }
  });
}

// ── Register form ──────────────────────────────────────
function initRegisterPage() {
  auth.redirectIfLoggedIn();

  const form      = document.getElementById('register-form');
  const errEl     = document.getElementById('register-error');
  const submitBtn = document.getElementById('register-btn');
  const passInput = document.getElementById('reg-password');

  if (!form) return;

  // Password strength indicator
  passInput?.addEventListener('input', () => {
    const pass = passInput.value;
    const bars = document.querySelectorAll('.strength-bar');
    const label = document.getElementById('strength-label');
    let strength = 0;
    if (pass.length >= 8)  strength++;
    if (/[A-Z]/.test(pass)) strength++;
    if (/[0-9]/.test(pass)) strength++;
    if (/[^A-Za-z0-9]/.test(pass)) strength++;

    bars.forEach((bar, i) => {
      bar.className = 'strength-bar';
      if (i < strength) {
        bar.classList.add(strength <= 1 ? 'filled-weak' : strength <= 2 ? 'filled-medium' : 'filled-strong');
      }
    });
    if (label) {
      label.textContent = ['', 'Weak', 'Fair', 'Good', 'Strong'][strength] || '';
      label.style.color = ['', 'var(--danger)', 'var(--warning)', 'var(--success)', 'var(--success)'][strength];
    }
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name     = document.getElementById('reg-name').value.trim();
    const email    = document.getElementById('reg-email').value.trim();
    const password = document.getElementById('reg-password').value;
    const confirm  = document.getElementById('reg-confirm').value;

    errEl.classList.add('hidden');

    if (password !== confirm) {
      errEl.textContent = 'Passwords do not match.';
      errEl.classList.remove('hidden');
      return;
    }
    if (password.length < 8) {
      errEl.textContent = 'Password must be at least 8 characters.';
      errEl.classList.remove('hidden');
      return;
    }

    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner spinner-sm"></span> Creating account…';

    try {
      const data = await api.apiPost('/auth/register', { email, full_name: name, password });
      auth.saveSession(data.access_token, data.user);
      window.location.href = '/dashboard.html';
    } catch (err) {
      errEl.textContent = err.message;
      errEl.classList.remove('hidden');
      submitBtn.disabled = false;
      submitBtn.innerHTML = 'Create Account';
    }
  });
}
