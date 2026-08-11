/**
 * api.js — Centralized API utility for all backend requests.
 * All calls go to relative URLs (same origin, no CORS needed).
 */
'use strict';

const API_BASE = '';  // same origin

/**
 * Core fetch wrapper with auth header injection and error handling.
 */
async function apiRequest(url, options = {}) {
  const token = auth.getToken();
  const headers = { ...options.headers };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Don't set Content-Type for FormData (browser sets multipart boundary)
  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    if (options.body) headers['Content-Type'] = 'application/json';
  }

  const res = await fetch(API_BASE + url, { ...options, headers });

  if (res.status === 401) {
    auth.logout();
    window.location.href = '/login.html';
    throw new Error('Session expired. Please log in again.');
  }

  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    try {
      const data = await res.json();
      message = data.detail || data.message || data.error || message;
    } catch (_) {}
    throw new Error(message);
  }

  // Return null for 204 No Content
  if (res.status === 204) return null;

  const ct = res.headers.get('content-type') || '';
  if (ct.includes('application/json')) return res.json();
  return res;
}

async function apiGet(url)           { return apiRequest(url, { method: 'GET' }); }
async function apiPost(url, body)    { return apiRequest(url, { method: 'POST', body: JSON.stringify(body) }); }
async function apiDelete(url)        { return apiRequest(url, { method: 'DELETE' }); }
async function apiForm(url, formData){ return apiRequest(url, { method: 'POST', body: formData }); }

// Named exports as global object
window.api = { apiRequest, apiGet, apiPost, apiDelete, apiForm };
