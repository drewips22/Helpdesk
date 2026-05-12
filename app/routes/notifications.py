from datetime import datetime, timedelta
from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from app.models import Ticket, TicketLog
from app.extensions import db

notif_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')


@notif_bp.route('/')
@login_required
def get_notifications():
    """Get recent notifications for the current user."""
    notifications = []

    if current_user.is_teknisi():
        # 1. New OPEN tickets
        open_tickets = Ticket.query.filter_by(status='OPEN')\
            .order_by(Ticket.created_at.desc()).limit(5).all()
        for t in open_tickets:
            notifications.append({
                'type': 'new_ticket',
                'icon': 'bi-plus-circle-fill',
                'color': 'danger',
                'title': f'Tiket Baru: {t.ticket_code}',
                'message': f'{t.jenis_perangkat} - {t.jenis_masalah}',
                'time': _time_ago(t.created_at),
                'url': f'/tickets/{t.id}'
            })

        # 2. SLA breached tickets
        sla_breached = Ticket.query.filter(
            Ticket.status.notin_(['DONE', 'CLOSED']),
            Ticket.sla_deadline < datetime.now()
        ).order_by(Ticket.sla_deadline.asc()).limit(5).all()
        for t in sla_breached:
            notifications.append({
                'type': 'sla_breach',
                'icon': 'bi-exclamation-triangle-fill',
                'color': 'warning',
                'title': f'SLA Breach: {t.ticket_code}',
                'message': f'Deadline terlewat! {t.sla_remaining}',
                'time': _time_ago(t.sla_deadline),
                'url': f'/tickets/{t.id}'
            })

    else:
        # Pelapor notifications
        recent_updates = Ticket.query.filter(
            Ticket.user_id == current_user.id,
            Ticket.updated_at >= datetime.now() - timedelta(days=7)
        ).order_by(Ticket.updated_at.desc()).limit(10).all()

        for t in recent_updates:
            if t.status == 'DONE':
                notifications.append({
                    'type': 'ticket_done',
                    'icon': 'bi-check-circle-fill',
                    'color': 'success',
                    'title': f'Tiket Selesai: {t.ticket_code}',
                    'message': f'{t.jenis_perangkat} - {t.jenis_masalah}',
                    'time': _time_ago(t.updated_at),
                    'url': f'/tickets/{t.id}'
                })
            elif t.status == 'ASSIGNED':
                notifications.append({
                    'type': 'ticket_assigned',
                    'icon': 'bi-person-check-fill',
                    'color': 'info',
                    'title': f'Teknisi Ditugaskan: {t.ticket_code}',
                    'message': f'Teknisi: {t.teknisi.nama if t.teknisi else "-"}',
                    'time': _time_ago(t.updated_at),
                    'url': f'/tickets/{t.id}'
                })
            elif t.status == 'ON_PROGRESS':
                notifications.append({
                    'type': 'ticket_progress',
                    'icon': 'bi-gear-fill',
                    'color': 'primary',
                    'title': f'Dikerjakan: {t.ticket_code}',
                    'message': f'{t.jenis_perangkat} - {t.jenis_masalah}',
                    'time': _time_ago(t.updated_at),
                    'url': f'/tickets/{t.id}'
                })

    # Sort by most recent
    count = len(notifications)

    return jsonify({
        'count': count,
        'notifications': notifications[:10]
    })


def _time_ago(dt):
    """Helper: time ago string."""
    if not dt:
        return ''
    diff = datetime.now() - dt
    seconds = diff.total_seconds()
    if seconds < 0:
        return 'Sekarang'
    if seconds < 60:
        return 'Baru saja'
    elif seconds < 3600:
        return f'{int(seconds // 60)}m lalu'
    elif seconds < 86400:
        return f'{int(seconds // 3600)}j lalu'
    else:
        return f'{int(seconds // 86400)}h lalu'


@notif_bp.route('/stats')
@login_required
def get_stats():
    """Lightweight endpoint for real-time dashboard stat updates."""
    total = Ticket.query.count()
    open_count = Ticket.query.filter_by(status='OPEN').count()
    progress = Ticket.query.filter(Ticket.status.in_(['ASSIGNED', 'ON_PROGRESS'])).count()
    done = Ticket.query.filter_by(status='DONE').count()

    return jsonify({
        'total': total,
        'open': open_count,
        'progress': progress,
        'done': done
    })
