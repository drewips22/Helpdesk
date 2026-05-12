/**
 * SI-TIK Real-Time Module
 * Handles SocketIO connections, notifications, chat, and live updates
 */

// Global socket instance
let socket = null;
let currentTicketId = null;
let typingTimeout = null;

// Initialize SocketIO connection
function initRealtime() {
    if (typeof io === 'undefined') {
        console.warn('Socket.IO not loaded');
        return;
    }

    socket = io({
        transports: ['websocket', 'polling'],
        reconnection: true,
        reconnectionDelay: 1000,
        reconnectionAttempts: 10
    });

    socket.on('connect', () => {
        console.log('🔌 Connected to real-time server');
        // Re-join ticket room if on detail page
        if (currentTicketId) {
            socket.emit('join_ticket', { ticket_id: currentTicketId });
        }
    });

    socket.on('disconnect', () => {
        console.log('❌ Disconnected from real-time server');
    });

    // --- Notification events ---
    socket.on('notification', (data) => {
        showToastNotification(data);
        updateNotificationBadge();
        playNotificationSound();
    });

    // --- Dashboard events ---
    socket.on('dashboard_update', () => {
        refreshDashboardStats();
    });

    socket.on('new_ticket', (data) => {
        showToastNotification({
            type: 'new_ticket',
            icon: 'bi-plus-circle-fill',
            color: 'danger',
            title: `Tiket Baru: ${data.ticket_code}`,
            message: `${data.jenis_perangkat} - ${data.jenis_masalah}`,
            url: `/tickets/${data.id}`
        });
        refreshDashboardStats();
        addNewTicketRow(data);
        updateNotificationBadge();
        playNotificationSound();
    });

    // --- Chat events ---
    socket.on('new_message', (data) => {
        appendChatMessage(data);
    });

    // --- Ticket update events ---
    socket.on('ticket_updated', (data) => {
        handleTicketUpdate(data);
    });

    // --- Typing indicator ---
    socket.on('user_typing', (data) => {
        showTypingIndicator(data.user_nama);
    });

    socket.on('user_stop_typing', () => {
        hideTypingIndicator();
    });
}

// --- Toast Notification System ---

function showToastNotification(data) {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toastId = 'toast-' + Date.now();
    const toastHtml = `
        <div id="${toastId}" class="rt-toast animate-slide-in" onclick="window.location='${data.url || '#'}'">
            <div class="rt-toast-icon">
                <i class="bi ${data.icon || 'bi-bell-fill'} text-${data.color || 'primary'}"></i>
            </div>
            <div class="rt-toast-body">
                <strong class="rt-toast-title">${data.title || 'Notifikasi'}</strong>
                <small class="rt-toast-msg">${data.message || ''}</small>
            </div>
            <button class="rt-toast-close" onclick="event.stopPropagation(); this.parentElement.remove();">&times;</button>
        </div>
    `;
    container.insertAdjacentHTML('beforeend', toastHtml);

    // Auto-remove after 6 seconds
    setTimeout(() => {
        const el = document.getElementById(toastId);
        if (el) {
            el.classList.add('animate-slide-out');
            setTimeout(() => el.remove(), 300);
        }
    }, 6000);
}

function playNotificationSound() {
    const audio = document.getElementById('notifSound');
    if (audio) {
        audio.currentTime = 0;
        audio.play().catch((e) => {
            console.warn('Browser memblokir suara notifikasi (Autoplay Policy). Klik di mana saja pada halaman untuk mengizinkan suara.', e);
        });
    }
}

// --- Dashboard Live Updates ---

function refreshDashboardStats() {
    const statsUrl = '/api/notifications/stats';
    fetch(statsUrl)
        .then(r => r.json())
        .then(data => {
            const els = {
                'statTotal': data.total,
                'statOpen': data.open,
                'statProgress': data.progress,
                'statDone': data.done
            };
            for (const [id, val] of Object.entries(els)) {
                const el = document.getElementById(id);
                if (el && el.textContent != val) {
                    el.textContent = val;
                    el.closest('.stat-card')?.classList.add('stat-pulse');
                    setTimeout(() => el.closest('.stat-card')?.classList.remove('stat-pulse'), 600);
                }
            }
        })
        .catch(() => {});
}

function addNewTicketRow(data) {
    const tbody = document.querySelector('.ticket-table tbody');
    if (!tbody) return;

    // Remove "no data" row if exists
    const emptyRow = tbody.querySelector('td[colspan]');
    if (emptyRow) emptyRow.closest('tr').remove();

    const urgencyClasses = {
        'rendah': 'bg-success', 'sedang': 'bg-info',
        'tinggi': 'bg-warning text-dark', 'kritis': 'bg-danger'
    };

    const row = document.createElement('tr');
    row.className = 'new-ticket-highlight';
    row.innerHTML = `
        <td><a href="/tickets/${data.id}" class="ticket-code-link">${data.ticket_code}</a></td>
        <td>
            <div class="d-flex align-items-center gap-2">
                <div class="user-avatar-xs">${data.pelapor ? data.pelapor[0].toUpperCase() : '?'}</div>
                <span>${data.pelapor || '-'}</span>
            </div>
        </td>
        <td>
            <div class="ticket-issue">
                <span class="text-muted small">${data.jenis_perangkat}</span><br>
                <span>${data.jenis_masalah}</span>
            </div>
        </td>
        <td><small>${data.lokasi || '-'}</small></td>
        <td><span class="badge ${urgencyClasses[data.urgency] || 'bg-info'}">${data.urgency ? data.urgency.charAt(0).toUpperCase() + data.urgency.slice(1) : '-'}</span></td>
        <td><span class="badge bg-danger">Baru</span></td>
        <td><span class="text-muted">-</span></td>
        <td><small class="text-muted">Baru saja</small></td>
        <td><a href="/tickets/${data.id}" class="btn btn-sm btn-outline-primary"><i class="bi bi-eye"></i></a></td>
    `;
    tbody.insertBefore(row, tbody.firstChild);

    // Remove highlight after animation
    setTimeout(() => row.classList.remove('new-ticket-highlight'), 3000);
}

// --- Chat Real-Time ---

function joinTicketRoom(ticketId) {
    currentTicketId = ticketId;
    if (socket && socket.connected) {
        socket.emit('join_ticket', { ticket_id: ticketId });
    }
}

function sendChatMessage(ticketId, message) {
    if (socket && socket.connected) {
        socket.emit('send_message', {
            ticket_id: ticketId,
            message: message
        });
    }
}

function appendChatMessage(data) {
    const chatList = document.getElementById('chatMessages');
    if (!chatList) return;

    // Check if this user's own message
    const currentUserId = parseInt(document.body.dataset.userId || '0');
    const isOwn = data.user_id === currentUserId;

    const msgHtml = `
        <div class="comment-item ${isOwn ? 'own' : ''} animate-msg-in">
            <div class="user-avatar-xs">${data.user_initial}</div>
            <div>
                <div class="comment-bubble">${escapeHtml(data.message)}</div>
                <div class="comment-meta">${data.user_nama} &bull; ${data.time}</div>
            </div>
        </div>
    `;
    chatList.insertAdjacentHTML('beforeend', msgHtml);

    // Scroll to bottom
    chatList.scrollTop = chatList.scrollHeight;

    // Remove empty state
    const emptyState = chatList.querySelector('.text-muted.text-center');
    if (emptyState) emptyState.remove();
}

function emitTyping(ticketId) {
    if (!socket || !socket.connected) return;

    socket.emit('typing', { ticket_id: ticketId });

    clearTimeout(typingTimeout);
    typingTimeout = setTimeout(() => {
        socket.emit('stop_typing', { ticket_id: ticketId });
    }, 2000);
}

function showTypingIndicator(userName) {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
        indicator.innerHTML = `<span class="typing-dots"><span></span><span></span><span></span></span> <em>${userName} sedang mengetik...</em>`;
        indicator.style.display = 'block';
    }
}

function hideTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
        indicator.style.display = 'none';
    }
}

// --- Ticket Status Update ---

function handleTicketUpdate(data) {
    // Update status badge on detail page
    const statusBadge = document.getElementById('ticketStatusBadge');
    if (statusBadge && data.status_label) {
        statusBadge.textContent = data.status_label;
        statusBadge.className = `badge ${data.status_badge_class} fs-6`;
    }

    // If a new comment came via ticket_updated event (from form POST fallback)
    if (data.action === 'comment' && data.comment) {
        appendChatMessage(data.comment);
    }
}

// --- Update Notification Badge ---

function updateNotificationBadge() {
    fetchNotifications();
}

// --- Utility ---

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    initRealtime();
});
