/* =====================================================
   🚀 Main JavaScript - IndoGovRAG Frontend
   API Integration & Chat Logic
   ===================================================== */

// Configuration
const CONFIG = {
    API_URL: 'http://localhost:8000/query',
    MAX_RETRIES: 3,
    RETRY_DELAY: 1000,
    TIMEOUT: 120000 // 2 minutes
};

// State
let isLoading = false;
let messageHistory = [];

// DOM Elements
const chatForm = document.getElementById('chatForm');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const messagesArea = document.getElementById('messagesArea');
const themeToggle = document.getElementById('themeToggle');
const themeIcon = document.getElementById('themeIcon');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    init();
});

function init() {
    setupEventListeners();
    setupThemeToggle();
    setupInputAutoResize();
    loadTheme();

    // Set welcome time
    updateTime();
}

// Event Listeners
function setupEventListeners() {
    chatForm.addEventListener('submit', handleSubmit);
    messageInput.addEventListener('keydown', handleKeyDown);
    sendButton.addEventListener('click', () => {
        if (!isLoading) {
            window.animationUtils.pulseButton(sendButton);
        }
    });
}

// Handle form submission
async function handleSubmit(e) {
    e.preventDefault();

    const query = messageInput.value.trim();
    if (!query || isLoading) return;

    // Clear input
    messageInput.value = '';
    resizeTextarea();

    // Add user message
    addUserMessage(query);

    // Show typing indicator
    const typingIndicator = window.animationUtils.createTypingIndicator();
    messagesArea.appendChild(typingIndicator);
    window.animationUtils.scrollToBottom(messagesArea);

    // Make API call
    try {
        isLoading = true;
        updateSendButton(true);

        const response = await queryAPI(query);

        // Remove typing indicator
        window.animationUtils.removeTypingIndicator();

        // Add assistant response
        addAssistantMessage(response);

    } catch (error) {
        console.error('Error querying API:', error);
        window.animationUtils.removeTypingIndicator();
        addErrorMessage(error.message);
    } finally {
        isLoading = false;
        updateSendButton(false);
        messageInput.focus();
    }
}

// Query API
async function queryAPI(query) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), CONFIG.TIMEOUT);

    try {
        const response = await fetch(CONFIG.API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query }),
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            throw new Error(`API Error: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        return data;

    } catch (error) {
        clearTimeout(timeoutId);

        if (error.name === 'AbortError') {
            throw new Error('Request timeout - please try again');
        }

        throw error;
    }
}

// Add user message
function addUserMessage(text) {
    const messageEl = createMessageElement('user', text);
    messagesArea.appendChild(messageEl);
    window.animationUtils.animateMessageEntry(messageEl);
    window.animationUtils.scrollToBottom(messagesArea);

    // Store in history
    messageHistory.push({ role: 'user', content: text, timestamp: new Date() });
}

// Add assistant message
function addAssistantMessage(data) {
    const messageEl = createMessageElement('assistant', data.answer, data.sources, data);
    messagesArea.appendChild(messageEl);
    window.animationUtils.animateMessageEntry(messageEl);
    window.animationUtils.scrollToBottom(messagesArea);

    // Store in history
    messageHistory.push({ role: 'assistant', content: data.answer, timestamp: new Date() });
}

// Add error message
function addErrorMessage(errorText) {
    const messageEl = document.createElement('div');
    messageEl.className = 'message assistant fade-in-up';

    const now = new Date();
    const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;

    messageEl.innerHTML = `
        <div class="message-avatar">⚠️</div>
        <div class="message-content">
            <div class="message-bubble" style="background: rgba(239, 68, 68, 0.1); border-color: var(--accent-error);">
                <p style="color: var(--accent-error);"><strong>Error:</strong> ${escapeHtml(errorText)}</p>
                <p style="font-size: 0.875rem; margin-top: var(--space-xs);">Silakan coba lagi atau hubungi administrator jika masalah berlanjut.</p>
            </div>
            <div class="message-meta">
                <span class="message-time">${timeStr}</span>
                <span class="message-badge" style="border-color: var(--accent-error); color: var(--accent-error);">Error</span>
            </div>
        </div>
    `;

    messagesArea.appendChild(messageEl);
    window.animationUtils.animateMessageEntry(messageEl);
    window.animationUtils.scrollToBottom(messagesArea);
}

// Create message element
function createMessageElement(role, text, sources = null, metadata = null) {
    const messageEl = document.createElement('div');
    messageEl.className = `message ${role}`;

    const now = new Date();
    const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;

    const avatar = role === 'user' ? '👤' : '🤖';
    const bubbleContent = formatMessageContent(text);

    let sourcesHTML = '';
    if (sources && sources.length > 0) {
        sourcesHTML = `
            <div class="sources-container">
                <div class="sources-header">
                    📚 Sumber (${sources.length} dokumen)
                </div>
                ${sources.map((source, idx) => `
                    <div class="source-card">
                        <div class="source-title">${idx + 1}. ${escapeHtml(source.title || 'Dokumen ' + (idx + 1))}</div>
                        <div class="source-preview">${escapeHtml(truncate(source.content || source.text || '', 120))}</div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    // Add metadata badges
    let metaBadges = '';
    if (metadata) {
        if (metadata.query_type) {
            metaBadges += `<span class="message-badge">${metadata.query_type}</span>`;
        }
        if (metadata.confidence) {
            const confidence = Math.round(metadata.confidence * 100);
            metaBadges += `<span class="message-badge">Confidence: ${confidence}%</span>`;
        }
    }

    messageEl.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">
            <div class="message-bubble">
                ${bubbleContent}
            </div>
            ${sourcesHTML}
            <div class="message-meta">
                <span class="message-time">${timeStr}</span>
                ${metaBadges}
            </div>
        </div>
    `;

    return messageEl;
}

// Format message content (support markdown-like formatting)
function formatMessageContent(text) {
    if (!text) return '';

    // Escape HTML first
    let formatted = escapeHtml(text);

    // Convert **bold**
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Convert *italic*
    formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');

    // Convert line breaks
    formatted = formatted.replace(/\n/g, '<br>');

    // Convert numbered lists (1., 2., etc.)
    formatted = formatted.replace(/^(\d+)\.\s/gm, '<br>$1. ');

    // Convert bullet lists (-, *, •)
    formatted = formatted.replace(/^[\-\*\•]\s/gm, '<br>• ');

    return `<p>${formatted}</p>`;
}

// Helper functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function truncate(text, length) {
    if (text.length <= length) return text;
    return text.slice(0, length) + '...';
}

function updateTime() {
    const now = new Date();
    const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
    const timeEl = document.getElementById('welcomeTime');
    if (timeEl) timeEl.textContent = timeStr;
}

// Update send button state
function updateSendButton(loading) {
    sendButton.disabled = loading;
    sendButton.innerHTML = loading ? '<span class="pulse">⏳</span>' : '<span>📤</span>';
}

// Handle keyboard shortcuts
function handleKeyDown(e) {
    // Enter to send (Shift+Enter for new line)
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        chatForm.dispatchEvent(new Event('submit'));
    }
}

// Auto-resize textarea
function setupInputAutoResize() {
    messageInput.addEventListener('input', resizeTextarea);
}

function resizeTextarea() {
    messageInput.style.height = 'auto';
    messageInput.style.height = messageInput.scrollHeight + 'px';
}

// Theme toggle
function setupThemeToggle() {
    themeToggle.addEventListener('click', toggleTheme);
}

function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);

    // Update icon
    themeIcon.textContent = newTheme === 'dark' ? '🌙' : '☀️';

    // Animate theme change
    document.body.style.transition = 'background-color 0.3s ease';
}

function loadTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    themeIcon.textContent = savedTheme === 'dark' ? '🌙' : '☀️';
}

// Export for debugging
window.indogovrag = {
    messageHistory,
    queryAPI,
    addUserMessage,
    addAssistantMessage
};
