/**
 * EXAMORA Shared Client-Side Authentication, API Layer, Avatar System, & Notification Center
 * Server-authoritative session support with automatic credential inclusion.
 */

const API_BASE = 'http://127.0.0.1:5000';

/**
 * Standard fetch wrapper that automatically includes HTTP credentials
 * and handles base URL resolution.
 */
async function fetchApi(endpoint, options = {}) {
    const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;
    
    const defaultHeaders = {
        'Accept': 'application/json'
    };

    if (options.body && typeof options.body === 'string') {
        defaultHeaders['Content-Type'] = 'application/json';
    }

    const config = {
        ...options,
        credentials: 'include', // Ensures Flask session cookie is sent with cross-port requests
        headers: {
            ...defaultHeaders,
            ...(options.headers || {})
        }
    };

    return fetch(url, config);
}

/**
 * Modern, non-blocking EXAMORA Toast Notification System.
 * Replaces intrusive native browser alert() popups.
 */
function showToast(message, type = 'info', duration = 4000) {
    let container = document.getElementById('examora-toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'examora-toast-container';
        container.className = 'fixed top-5 right-5 z-[9999] flex flex-col gap-2.5 pointer-events-none max-w-sm w-full px-4';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = 'pointer-events-auto flex items-start gap-3 p-4 rounded-xl shadow-xl text-xs font-semibold backdrop-blur-md transition-all duration-300 transform translate-y-[-10px] opacity-0';

    let icon = 'info';
    let bgStyle = 'bg-surface-container-lowest text-on-surface border border-outline-variant/40';
    let iconColor = 'text-primary';

    if (type === 'success') {
        icon = 'check_circle';
        bgStyle = 'bg-success-container/95 text-on-success-container border border-success/30';
        iconColor = 'text-success';
    } else if (type === 'error') {
        icon = 'error';
        bgStyle = 'bg-error-container/95 text-on-error-container border border-error/30';
        iconColor = 'text-error';
    } else if (type === 'warning') {
        icon = 'warning';
        bgStyle = 'bg-warning-container/95 text-on-warning-container border border-warning/30';
        iconColor = 'text-warning';
    } else if (type === 'info') {
        icon = 'info';
        bgStyle = 'bg-secondary-container/95 text-on-secondary-container border border-primary/20';
        iconColor = 'text-primary';
    }

    toast.className += ` ${bgStyle}`;
    toast.innerHTML = `
        <span class="material-symbols-outlined text-lg ${iconColor} flex-shrink-0 mt-0.5">${icon}</span>
        <div class="flex-1 leading-snug">${message}</div>
        <button class="text-on-surface-variant/60 hover:text-on-surface ml-2 flex-shrink-0 cursor-pointer" onclick="this.parentElement.remove()">
            <span class="material-symbols-outlined text-sm">close</span>
        </button>
    `;

    container.appendChild(toast);

    // Animate In
    setTimeout(() => {
        toast.classList.remove('translate-y-[-10px]', 'opacity-0');
        toast.classList.add('translate-y-0', 'opacity-100');
    }, 10);

    // Auto Dismiss
    setTimeout(() => {
        toast.classList.add('opacity-0', 'translate-y-[-10px]');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

/**
 * Generates and returns a consistent, clean default profile picture placeholder (Instagram-style "no profile photo" state).
 * Background: Plain white with light neutral border.
 * Center: Generic user silhouette in neutral gray.
 * Supports future uploaded photo: If photoUrl is provided, renders the uploaded image; otherwise renders the default placeholder.
 */
function getStudentAvatarHtml(photoUrl = null, size = 36) {
    if (photoUrl && typeof photoUrl === 'string' && photoUrl.trim().length > 0) {
        let fullUrl = photoUrl;
        if (photoUrl.startsWith('/api')) {
            fullUrl = `${API_BASE}${photoUrl}`;
        }
        return `
            <div class="w-[${size}px] h-[${size}px] min-w-[${size}px] min-h-[${size}px] rounded-full bg-white border border-slate-200 shadow-sm overflow-hidden flex-shrink-0">
                <img src="${fullUrl}" alt="Profile" class="w-full h-full object-cover" onerror="this.parentElement.outerHTML = getStudentAvatarHtml(null, ${size});"/>
            </div>
        `;
    }

    // Default "No profile photo uploaded" state: Clean white circular background with subtle neutral border and gray generic user silhouette
    return `
        <div class="w-[${size}px] h-[${size}px] min-w-[${size}px] min-h-[${size}px] rounded-full bg-white text-slate-400 border border-slate-200/90 shadow-sm flex items-center justify-center overflow-hidden flex-shrink-0 select-none" title="No profile photo uploaded">
            <svg class="w-[62%] h-[62%]" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
            </svg>
        </div>
    `;
}

/**
 * Hydrates DOM elements across the page with authenticated student data and default profile placeholder.
 */

function applyBranding(user) {
    if (!user) return;
    
    // Update institution name text
    document.querySelectorAll('.institution-name-display').forEach(el => {
        el.textContent = user.institution_name || 'EXAMORA';
    });
    
    // Update CSS variables for white-label colors
    const root = document.documentElement;
    if (user.primary_color) {
        // Convert hex to rgb format for tailwind opacity support
        const hex = user.primary_color.replace('#', '');
        if (hex.length === 6) {
            const r = parseInt(hex.substring(0, 2), 16);
            const g = parseInt(hex.substring(2, 4), 16);
            const b = parseInt(hex.substring(4, 6), 16);
            root.style.setProperty('--color-primary', `${r} ${g} ${b}`);
        }
    }
    if (user.secondary_color) {
        const hex = user.secondary_color.replace('#', '');
        if (hex.length === 6) {
            const r = parseInt(hex.substring(0, 2), 16);
            const g = parseInt(hex.substring(2, 4), 16);
            const b = parseInt(hex.substring(4, 6), 16);
            root.style.setProperty('--color-secondary', `${r} ${g} ${b}`);
        }
    }
}

function updateStudentUI(student) {
    applyBranding(student);
    if (!student) return;

    const name = student.student_name || student.username || 'Student';
    const id = student.student_id || student.id || '--';
    const photoUrl = student.profile_picture || student.avatar_url || null;

    document.querySelectorAll('.student-name-display').forEach(el => {
        el.textContent = name;
    });

    const greetingHeader = document.getElementById('greetingHeader');
    if (greetingHeader) {
        const hour = new Date().getHours();
        const timeOfDay = hour < 12 ? 'Good morning' : (hour < 17 ? 'Good afternoon' : 'Good evening');
        greetingHeader.textContent = `${timeOfDay}, ${name}`;
    }

    document.querySelectorAll('.student-id-display').forEach(el => {
        el.textContent = `ID: #${id}`;
    });

    // Default profile picture placeholder injection
    document.querySelectorAll('.student-avatar-display').forEach(el => {
        const sizeAttr = el.getAttribute('data-size');
        const size = sizeAttr ? parseInt(sizeAttr) : 36;
        el.innerHTML = getStudentAvatarHtml(photoUrl, size);
    });

    // Remove every reference to legacy profile headshot images across the DOM
    document.querySelectorAll('img[alt="Profile"], img[alt="Student"], img[alt="Student Avatar"]').forEach(img => {
        const parent = img.parentElement;
        if (parent) {
            const avatarWrap = document.createElement('div');
            avatarWrap.className = 'student-avatar-display flex items-center justify-center';
            avatarWrap.innerHTML = getStudentAvatarHtml(photoUrl, 36);
            parent.replaceChild(avatarWrap, img);
        }
    });
}

/**
 * Verifies that the current user has an active, authenticated student session.
 */
async function requireStudentAuth(options = { redirectOnFail: true, updateUI: true }) {
    if (options.updateUI) {
        const cached = localStorage.getItem('student_user');
        if (cached) {
            try {
                updateStudentUI(JSON.parse(cached));
            } catch (e) {}
        }
    }

    try {
        const response = await fetchApi('/api/profile');

        if (!response.ok) {
            if (response.status === 401 || response.status === 403) {
                if (options.redirectOnFail) {
                    sessionStorage.clear();
                    localStorage.removeItem('student_user');
                    window.location.href = '../student_login/code.html';
                }
                return null;
            }
        }

        const data = await response.json();
        if (data && data.success && data.student) {
            const student = data.student;
            localStorage.setItem('student_user', JSON.stringify(student));
            
            if (options.updateUI) {
                updateStudentUI(student);
                initNotificationCenter();
            }
            return student;
        }

        if (options.redirectOnFail) {
            window.location.href = '../student_login/code.html';
        }
        return null;

    } catch (err) {
        console.warn('Student authentication check failed (offline or server error):', err);
        const cached = localStorage.getItem('student_user');
        if (cached) {
            try {
                const parsed = JSON.parse(cached);
                if (options.updateUI) updateStudentUI(parsed);
                return parsed;
            } catch (e) { }
        }
        if (options.redirectOnFail) {
            window.location.href = '../student_login/code.html';
        }
        return null;
    }
}

/**
 * Verifies administrator authentication.
 */
async function requireAdminAuth(options = { redirectOnFail: true, updateUI: true }) {
    try {
        const response = await fetchApi('/api/admin/session');

        if (!response.ok) {
            if (options.redirectOnFail) {
                sessionStorage.clear();
                localStorage.removeItem('admin_user');
                window.location.href = '../admin_login/code.html';
            }
            return null;
        }

        const data = await response.json();
        if (data && data.success && data.admin) {
            const admin = data.admin;
            localStorage.setItem('admin_user', JSON.stringify(admin));
            
            if (options.updateUI) {
                document.querySelectorAll('.admin-name-display').forEach(el => {
                    el.textContent = admin.full_name || admin.username || 'Administrator';
                });
            }
            return admin;
        }

        if (options.redirectOnFail) {
            window.location.href = '../admin_login/code.html';
        }
        return null;

    } catch (err) {
        console.warn('Admin authentication check failed:', err);
        if (options.redirectOnFail) {
            window.location.href = '../admin_login/code.html';
        }
        return null;
    }
}

/**
 * Student Logout.
 */
async function performStudentLogout() {
    try {
        await fetchApi('/api/logout', { method: 'POST' });
    } catch (e) { }
    finally {
        sessionStorage.clear();
        localStorage.removeItem('student_user');
        localStorage.removeItem('exam_answers');
        localStorage.removeItem('exam_answers_dirty');
        localStorage.removeItem('exam_marked');
        localStorage.removeItem('last_result');
        window.location.href = '../student_login/code.html';
    }
}

/**
 * Admin Logout.
 */
async function performAdminLogout() {
    try {
        await fetchApi('/api/admin/logout', { method: 'POST' });
    } catch (e) { }
    finally {
        sessionStorage.clear();
        localStorage.removeItem('admin_user');
        window.location.href = '../admin_login/code.html';
    }
}

// ----------------------------------------------------
// NOTIFICATION CENTER UI CONTROLLER
// ----------------------------------------------------

async function initNotificationCenter() {
    // Find all bell icons / notification triggers
    const bellTriggers = document.querySelectorAll('.bell-icon, [data-action="notifications"]');
    if (bellTriggers.length === 0) return;

    // Fetch notifications
    let unreadCount = 0;
    try {
        const res = await fetchApi('/api/notifications');
        if (res.ok) {
            const data = await res.json();
            if (data && data.success) {
                unreadCount = data.unread_count || 0;
                updateNotificationBadge(unreadCount);
            }
        }
    } catch (e) { }

    bellTriggers.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            toggleNotificationModal();
        });
    });
}

function updateNotificationBadge(unreadCount) {
    document.querySelectorAll('.bell-icon').forEach(bell => {
        let badge = bell.querySelector('.notification-badge');
        let staticDot = bell.querySelector('span.rounded-full:not(.notification-badge)');
        
        if (unreadCount > 0) {
            if (staticDot) staticDot.style.display = 'none';
            if (!badge) {
                badge = document.createElement('span');
                badge.className = 'notification-badge absolute -top-1 -right-1 px-1.5 py-0.2 bg-error text-white text-[9px] font-bold rounded-full border-2 border-surface';
                bell.appendChild(badge);
            }
            badge.textContent = unreadCount > 9 ? '9+' : unreadCount;
            badge.style.display = 'block';
        } else {
            if (staticDot) staticDot.style.display = 'none';
            if (badge) badge.style.display = 'none';
        }
    });
}

async function toggleNotificationModal() {
    let modal = document.getElementById('examora-notifications-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'examora-notifications-modal';
        modal.className = 'fixed inset-0 z-50 flex items-center justify-center bg-on-surface/40 backdrop-blur-sm p-4';
        modal.innerHTML = `
            <div class="bg-surface-container-lowest w-full max-w-lg rounded-2xl shadow-2xl border border-outline-variant/30 max-h-[85vh] flex flex-col overflow-hidden">
                <div class="p-5 border-b border-outline-variant/20 flex items-center justify-between bg-surface-container-low/50">
                    <div class="flex items-center gap-2">
                        <span class="material-symbols-outlined text-primary text-xl">notifications</span>
                        <h3 class="text-base font-bold text-on-surface">Notification Center</h3>
                    </div>
                    <div class="flex items-center gap-2">
                        <button onclick="markAllNotificationsRead()" class="px-2.5 py-1 text-primary hover:bg-primary/10 rounded-lg text-xs font-semibold cursor-pointer">Mark all as read</button>
                        <button onclick="closeNotificationModal()" class="p-1 rounded-lg text-on-surface-variant hover:bg-surface-container cursor-pointer">
                            <span class="material-symbols-outlined text-lg">close</span>
                        </button>
                    </div>
                </div>
                <div id="notificationsListContainer" class="flex-1 overflow-y-auto p-4 space-y-3">
                    <p class="text-xs text-on-surface-variant text-center py-8">Loading notifications...</p>
                </div>
            </div>
        `;
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeNotificationModal();
        });
        document.body.appendChild(modal);
    } else {
        modal.classList.remove('hidden');
    }

    await loadNotificationsList();
}

function closeNotificationModal() {
    const modal = document.getElementById('examora-notifications-modal');
    if (modal) modal.classList.add('hidden');
}

async function loadNotificationsList() {
    const container = document.getElementById('notificationsListContainer');
    if (!container) return;

    try {
        const res = await fetchApi('/api/notifications');
        if (res.ok) {
            const data = await res.json();
            if (data && data.success && Array.isArray(data.notifications)) {
                updateNotificationBadge(data.unread_count || 0);

                if (data.notifications.length === 0) {
                    container.innerHTML = `
                        <div class="py-12 text-center text-on-surface-variant space-y-2">
                            <span class="material-symbols-outlined text-4xl text-outline-variant">notifications_off</span>
                            <p class="text-xs font-semibold">No notifications right now.</p>
                            <p class="text-[11px] text-outline">You are all caught up!</p>
                        </div>
                    `;
                    return;
                }

                container.innerHTML = '';
                data.notifications.forEach(n => {
                    const isUnread = !n.is_read;
                    const item = document.createElement('div');
                    item.className = `p-3.5 rounded-xl border transition-all ${isUnread ? 'bg-secondary-container/40 border-primary/30 shadow-sm' : 'bg-surface-container-low/60 border-outline-variant/20'}`;

                    let iconName = 'notifications';
                    if (n.type === 'account') iconName = 'manage_accounts';
                    else if (n.type === 'exam') iconName = 'quiz';
                    else if (n.type === 'result') iconName = 'verified';

                    item.innerHTML = `
                        <div class="flex items-start justify-between gap-3">
                            <div class="flex items-start gap-3 flex-1">
                                <span class="material-symbols-outlined text-base ${isUnread ? 'text-primary' : 'text-on-surface-variant'} mt-0.5">${iconName}</span>
                                <div>
                                    <h4 class="text-xs font-bold text-on-surface flex items-center gap-2">
                                        ${n.title}
                                        ${isUnread ? '<span class="w-2 h-2 rounded-full bg-primary inline-block"></span>' : ''}
                                    </h4>
                                    <p class="text-xs text-on-surface-variant mt-0.5 leading-relaxed">${n.message}</p>
                                    <span class="text-[10px] text-outline mt-1 block">${n.created_at || 'Just now'}</span>
                                </div>
                            </div>
                            ${isUnread ? `
                                <button onclick="markNotificationSingle(${n.id})" class="text-[10px] text-primary hover:underline font-bold flex-shrink-0 cursor-pointer">
                                    Mark read
                                </button>
                            ` : ''}
                        </div>
                    `;
                    container.appendChild(item);
                });
            }
        }
    } catch (e) {
        container.innerHTML = `<p class="text-xs text-error text-center py-6">Failed to load notifications.</p>`;
    }
}

async function markNotificationSingle(nid) {
    try {
        await fetchApi(`/api/notifications/${nid}/read`, { method: 'PUT' });
        await loadNotificationsList();
    } catch (e) { }
}

async function markAllNotificationsRead() {
    try {
        await fetchApi('/api/notifications/read-all', { method: 'PUT' });
        await loadNotificationsList();
        showToast('All notifications marked as read', 'success');
    } catch (e) { }
}

// Global hooks on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-action="logout"]').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            performStudentLogout();
        });
    });

    document.querySelectorAll('[data-action="admin-logout"]').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            performAdminLogout();
        });
    });
});
