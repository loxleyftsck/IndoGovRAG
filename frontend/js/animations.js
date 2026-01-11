/* =====================================================
   ✨ Micro-Animations - IndoGovRAG
   Smooth, delightful interactions
   ===================================================== */

// Initialize animations on page load
document.addEventListener('DOMContentLoaded', () => {
    initAnimations();
    setupScrollAnimations();
    setupHoverAnimations();
});

// Initialize all animations
function initAnimations() {
    // Animate header on load
    const header = document.getElementById('header');
    if (header) {
        header.style.opacity = '0';
        header.style.transform = 'translateY(-20px)';
        setTimeout(() => {
            header.style.transition = 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
            header.style.opacity = '1';
            header.style.transform = 'translateY(0)';
        }, 100);
    }

    // Animate welcome message timestamp
    updateWelcomeTime();
}

// Update welcome message timestamp
function updateWelcomeTime() {
    const timeElement = document.getElementById('welcomeTime');
    if (timeElement) {
        const now = new Date();
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        timeElement.textContent = `${hours}:${minutes}`;
    }
}

// Setup scroll-based animations
function setupScrollAnimations() {
    const messagesArea = document.getElementById('messagesArea');
    if (!messagesArea) return;

    // Smooth scroll to bottom when new message added
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.addedNodes.length) {
                scrollToBottom(messagesArea);
            }
        });
    });

    observer.observe(messagesArea, { childList: true });
}

// Smooth scroll to bottom
function scrollToBottom(element, smooth = true) {
    if (!element) return;

    const scrollOptions = {
        top: element.scrollHeight,
        behavior: smooth ? 'smooth' : 'auto'
    };

    element.scrollTo(scrollOptions);
}

// Setup hover animations
function setupHoverAnimations() {
    // Add ripple effect to buttons
    const buttons = document.querySelectorAll('.btn-send, .theme-toggle');
    buttons.forEach(button => {
        button.addEventListener('click', createRipple);
    });
}

// Create ripple effect
function createRipple(event) {
    const button = event.currentTarget;
    const ripple = document.createElement('span');

    // Calculate ripple position
    const rect = button.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = event.clientX - rect.left - size / 2;
    const y = event.clientY - rect.top - size / 2;

    // Style ripple
    ripple.style.width = ripple.style.height = `${size}px`;
    ripple.style.left = `${x}px`;
    ripple.style.top = `${y}px`;
    ripple.style.position = 'absolute';
    ripple.style.borderRadius = '50%';
    ripple.style.background = 'rgba(255, 255, 255, 0.5)';
    ripple.style.pointerEvents = 'none';
    ripple.style.animation = 'ripple 0.6s ease-out';

    // Add ripple animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes ripple {
            to {
                transform: scale(2);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);

    // Add and remove ripple
    button.style.position = 'relative';
    button.style.overflow = 'hidden';
    button.appendChild(ripple);

    setTimeout(() => ripple.remove(), 600);
}

// Animate message entry
function animateMessageEntry(messageElement) {
    messageElement.style.opacity = '0';
    messageElement.style.transform = 'translateY(20px)';

    // Force reflow
    messageElement.offsetHeight;

    // Animate in
    messageElement.style.transition = 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
    messageElement.style.opacity = '1';
    messageElement.style.transform = 'translateY(0)';
}

// Typing indicator animation
function createTypingIndicator() {
    const indicator = document.createElement('div');
    indicator.className = 'message assistant';
    indicator.id = 'typingIndicator';

    indicator.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-content">
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>
    `;

    return indicator;
}

// Remove typing indicator
function removeTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
        indicator.style.transition = 'opacity 0.3s ease';
        indicator.style.opacity = '0';
        setTimeout(() => indicator.remove(), 300);
    }
}

// Pulse animation for send button
function pulseButton(button) {
    button.style.animation = 'pulse 0.5s cubic-bezier(0.4, 0, 0.6, 1)';
    setTimeout(() => {
        button.style.animation = '';
    }, 500);
}

// Shimmer effect for loading
function addShimmerEffect(element) {
    element.classList.add('loading');
    setTimeout(() => element.classList.remove('loading'), 2000);
}

// Export functions for use in main.js
window.animationUtils = {
    animateMessageEntry,
    createTypingIndicator,
    removeTypingIndicator,
    pulseButton,
    addShimmerEffect,
    scrollToBottom
};
