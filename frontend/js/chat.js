/**
 * chat.js — AI Career Assistant chat with streaming responses.
 */
'use strict';

let _chatHistory = [];
let _isStreaming = false;

async function initChatPage() {
  if (!auth.requireAuth()) return;
  utils.initTheme();
  utils.initSidebar();
  utils.setActiveNav('chat');
  utils.updateSidebarUser(auth.getUser());
  setupChat();
}

function setupChat() {
  const sendBtn  = document.getElementById('send-btn');
  const textarea = document.getElementById('chat-input');
  const clearBtn = document.getElementById('clear-btn');

  sendBtn?.addEventListener('click', sendMessage);

  textarea?.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  // Auto-resize textarea
  textarea?.addEventListener('input', () => {
    textarea.style.height = '44px';
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
  });

  clearBtn?.addEventListener('click', clearChat);

  // Suggested chips
  document.querySelectorAll('.chat-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      if (textarea) textarea.value = chip.textContent;
      textarea?.focus();
    });
  });
}

async function sendMessage() {
  if (_isStreaming) return;

  const textarea = document.getElementById('chat-input');
  const message  = textarea?.value.trim();
  if (!message) return;

  textarea.value = '';
  textarea.style.height = '44px';

  // Hide welcome screen
  document.getElementById('chat-welcome')?.classList.add('hidden');

  appendMessage('user', message);

  _chatHistory.push({ role: 'user', content: message });

  const placeholder = appendAssistantPlaceholder();
  _isStreaming = true;
  updateSendBtn(true);

  let fullContent = '';

  try {
    const token = auth.getToken();
    const res = await fetch('/analysis/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        message,
        history: _chatHistory.slice(-10),
      }),
    });

    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || 'Chat request failed.');
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const raw = line.slice(6).trim();
        if (raw === '[DONE]') break;
        try {
          const parsed = JSON.parse(raw);
          const content = parsed.content || '';
          if (content) {
            fullContent += content;
            updatePlaceholder(placeholder, fullContent);
          }
        } catch (_) {}
      }
    }

    _chatHistory.push({ role: 'assistant', content: fullContent });
    // Trim history to last 20 messages (10 pairs)
    if (_chatHistory.length > 20) _chatHistory = _chatHistory.slice(-20);

  } catch (err) {
    updatePlaceholder(placeholder, '⚠️ ' + err.message);
    utils.showToast('Chat error: ' + err.message, 'error');
  } finally {
    _isStreaming = false;
    updateSendBtn(false);
    scrollToBottom();
  }
}

function appendMessage(role, content) {
  const list = document.getElementById('chat-messages');
  const initials = auth.getUser()?.full_name?.charAt(0)?.toUpperCase() || 'U';
  const time = utils.formatTime(new Date());

  const div = document.createElement('div');
  div.className = `message message-${role} fade-in`;
  div.innerHTML = `
    <div class="message-avatar">${role === 'user' ? initials : '🤖'}</div>
    <div class="message-content">
      <div class="message-bubble">${role === 'user' ? utils.escHtml(content) : `<p>${utils.formatAiText(content)}</p>`}</div>
      <div class="message-time">${time}</div>
    </div>`;
  list.appendChild(div);
  scrollToBottom();
  return div;
}

function appendAssistantPlaceholder() {
  const list = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = 'message message-assistant fade-in';
  div.innerHTML = `
    <div class="message-avatar">🤖</div>
    <div class="message-content">
      <div class="message-bubble">
        <div class="typing-indicator">
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
        </div>
      </div>
    </div>`;
  list.appendChild(div);
  scrollToBottom();
  return div;
}

function updatePlaceholder(placeholder, content) {
  const bubble = placeholder.querySelector('.message-bubble');
  if (bubble) bubble.innerHTML = `<p>${utils.formatAiText(content)}</p>`;
  scrollToBottom();
}

function scrollToBottom() {
  const list = document.getElementById('chat-messages');
  if (list) list.scrollTop = list.scrollHeight;
}

function updateSendBtn(isSending) {
  const btn = document.getElementById('send-btn');
  if (!btn) return;
  btn.disabled = isSending;
  btn.innerHTML = isSending
    ? `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`
    : `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>`;
}

function clearChat() {
  _chatHistory = [];
  const list = document.getElementById('chat-messages');
  if (list) list.innerHTML = '';
  document.getElementById('chat-welcome')?.classList.remove('hidden');
}

document.addEventListener('DOMContentLoaded', initChatPage);
