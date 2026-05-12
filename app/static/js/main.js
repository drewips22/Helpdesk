// SI-TIK Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Sidebar toggle
    const sidebar = document.getElementById('sidebar');
    const toggle = document.getElementById('sidebarToggle');
    const close = document.getElementById('sidebarClose');
    const overlay = document.getElementById('sidebarOverlay');

    if (toggle) toggle.addEventListener('click', () => { sidebar.classList.add('open'); overlay.classList.add('show'); });
    if (close) close.addEventListener('click', () => { sidebar.classList.remove('open'); overlay.classList.remove('show'); });
    if (overlay) overlay.addEventListener('click', () => { sidebar.classList.remove('open'); overlay.classList.remove('show'); });

    // Dark mode
    const darkBtn = document.getElementById('darkModeToggle') || document.getElementById('darkModeTogglePelapor');
    if (darkBtn) {
        const saved = localStorage.getItem('theme');
        if (saved === 'dark') document.documentElement.setAttribute('data-bs-theme', 'dark');
        darkBtn.addEventListener('click', () => {
            const current = document.documentElement.getAttribute('data-bs-theme');
            const next = current === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-bs-theme', next);
            localStorage.setItem('theme', next);
            const icon = darkBtn.querySelector('i');
            icon.className = next === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-fill';
            
            // Notify charts to update colors
            window.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme: next } }));
        });
        if (saved === 'dark') {
            const icon = darkBtn.querySelector('i');
            if (icon) icon.className = 'bi bi-sun-fill';
        }
    }

    // Toast notifications instead of alerts
    document.querySelectorAll('.alert-dismissible').forEach(el => {
        setTimeout(() => { const alert = bootstrap.Alert.getOrCreateInstance(el); alert.close(); }, 5000);
    });

    // Loading state on form submit
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function() {
            const btn = form.querySelector('button[type="submit"]');
            if (btn && !btn.dataset.noloading) {
                btn.disabled = true;
                const origHTML = btn.innerHTML;
                btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Memproses...';
                setTimeout(() => { btn.disabled = false; btn.innerHTML = origHTML; }, 8000);
            }
        });
    });

    // Initial notification load (one-time, then SocketIO handles updates)
    fetchNotifications();

    // SLA live countdown
    initSLACountdowns();
});

// Notifications
function fetchNotifications() {
    const badge = document.getElementById('notifBadge');
    const list = document.getElementById('notifList');
    if (!badge || !list) return;

    fetch('/api/notifications/')
        .then(r => r.json())
        .then(data => {
            if (data.count > 0) {
                const notifStateHash = JSON.stringify(data.notifications);
                const lastSeenState = localStorage.getItem('lastSeenNotifState');
                
                if (notifStateHash !== lastSeenState) {
                    badge.style.display = 'block';
                    badge.textContent = data.count > 9 ? '9+' : data.count;
                } else {
                    badge.style.display = 'none';
                }

                let html = '';
                data.notifications.forEach(n => {
                    html += `<a href="${n.url}" class="dropdown-item notif-item">
                        <div class="d-flex gap-2 align-items-start">
                            <i class="bi ${n.icon} text-${n.color} mt-1"></i>
                            <div>
                                <strong class="d-block" style="font-size:13px">${n.title}</strong>
                                <small class="text-muted">${n.message}</small>
                                <small class="text-muted d-block">${n.time}</small>
                            </div>
                        </div>
                    </a>`;
                });
                list.innerHTML = html;

                // Handle clear on click
                const dropdownBtn = badge.closest('button');
                if (dropdownBtn && !dropdownBtn.dataset.hasNotifListener) {
                    dropdownBtn.addEventListener('click', () => {
                        badge.style.display = 'none';
                        localStorage.setItem('lastSeenNotifState', notifStateHash);
                    });
                    dropdownBtn.dataset.hasNotifListener = 'true';
                }
            } else {
                badge.style.display = 'none';
                list.innerHTML = '<div class="dropdown-item text-muted text-center py-3"><small>Tidak ada notifikasi baru</small></div>';
            }
        }).catch(() => {});
}

// SLA Live Countdown
function initSLACountdowns() {
    document.querySelectorAll('[data-sla-deadline]').forEach(el => {
        const deadline = new Date(el.dataset.slaDeadline);
        if (isNaN(deadline.getTime())) return;
        updateSLAElement(el, deadline);
        setInterval(() => updateSLAElement(el, deadline), 60000);
    });
}

function updateSLAElement(el, deadline) {
    const now = new Date();
    const diff = deadline - now;
    const abs = Math.abs(diff);
    const h = Math.floor(abs / 3600000);
    const m = Math.floor((abs % 3600000) / 60000);
    if (diff > 0) {
        el.textContent = h + 'j ' + m + 'm';
        el.classList.remove('sla-breached');
        el.classList.add('sla-ok');
    } else {
        el.textContent = '-' + h + 'j ' + m + 'm';
        el.classList.remove('sla-ok');
        el.classList.add('sla-breached');
    }
}
