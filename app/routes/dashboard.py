from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from app.models import Ticket, User, TicketLog
from app.extensions import db
import json
from app.utils import format_datetime, time_ago, STATUS_OPTIONS, get_bagian_options
from app.utils.decorators import teknisi_required, admin_required

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


@dashboard_bp.route('/')
@login_required
@teknisi_required
def index():
    # Filters
    status_filter = request.args.get('status', '')
    urgency_filter = request.args.get('urgency', '')
    bagian_filter = request.args.get('bagian', '')
    search = request.args.get('search', '').strip()
    sort_by = request.args.get('sort', 'newest')
    page = request.args.get('page', 1, type=int)
    date_filter = request.args.get('date', 'all')

    # Fix N+1 query: eagerly load pelapor relationship
    query = Ticket.query.options(joinedload(Ticket.pelapor))

    if status_filter:
        query = query.filter_by(status=status_filter)
    if urgency_filter:
        query = query.filter_by(urgency=urgency_filter)
    if bagian_filter:
        query = query.filter_by(bagian=bagian_filter)
    if search:
        query = query.filter(
            db.or_(
                Ticket.ticket_code.ilike(f'%{search}%'),
                Ticket.deskripsi.ilike(f'%{search}%'),
                Ticket.lokasi.ilike(f'%{search}%')
            )
        )
    # Date filtering
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if date_filter == 'today':
        query = query.filter(Ticket.created_at >= today_start)
    elif date_filter == 'this_week':
        start_of_week = today_start - timedelta(days=now.weekday())
        query = query.filter(Ticket.created_at >= start_of_week)
    elif date_filter == 'this_month':
        start_of_month = today_start.replace(day=1)
        query = query.filter(Ticket.created_at >= start_of_month)

    # Sorting
    if sort_by == 'oldest':
        query = query.order_by(Ticket.created_at.asc())
    elif sort_by == 'urgency':
        # Custom urgency ordering
        urgency_order = db.case(
            {'kritis': 1, 'tinggi': 2, 'sedang': 3, 'rendah': 4},
            value=Ticket.urgency
        )
        query = query.order_by(urgency_order, Ticket.created_at.desc())
    elif sort_by == 'sla':
        query = query.order_by(Ticket.sla_deadline.asc())
    else:  # newest
        query = query.order_by(Ticket.created_at.desc())

    tickets = query.paginate(page=page, per_page=15)

    # Stats
    total_tickets = Ticket.query.count()
    open_tickets = Ticket.query.filter_by(status='OPEN').count()
    assigned_tickets = Ticket.query.filter_by(status='ASSIGNED').count()
    progress_tickets = Ticket.query.filter(Ticket.status.in_(['ASSIGNED', 'ON_PROGRESS'])).count()
    done_tickets = Ticket.query.filter_by(status='DONE').count()
    closed_tickets = Ticket.query.filter_by(status='CLOSED').count()
    on_progress_tickets = Ticket.query.filter_by(status='ON_PROGRESS').count()

    # SLA breached count
    sla_breached = Ticket.query.filter(
        Ticket.status.notin_(['DONE', 'CLOSED']),
        Ticket.sla_deadline < datetime.now()
    ).count()

    # --- Chart Data ---
    # Daily trend: last 7 days
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    daily_labels = []
    daily_data = []
    for i in range(6, -1, -1):
        day = today_start - timedelta(days=i)
        day_end = day + timedelta(days=1)
        count = Ticket.query.filter(
            Ticket.created_at >= day,
            Ticket.created_at < day_end
        ).count()
        daily_labels.append(day.strftime('%d/%m'))
        daily_data.append(count)

    # Urgency distribution
    urgency_data = [
        Ticket.query.filter_by(urgency='rendah').count(),
        Ticket.query.filter_by(urgency='sedang').count(),
        Ticket.query.filter_by(urgency='tinggi').count(),
        Ticket.query.filter_by(urgency='kritis').count(),
    ]

    chart_data = {
        'status': [open_tickets, assigned_tickets, on_progress_tickets, done_tickets, closed_tickets],
        'daily_labels': daily_labels,
        'daily_data': daily_data,
        'urgency': urgency_data,
    }

    return render_template('dashboard/index.html',
                           tickets=tickets,
                           total_tickets=total_tickets,
                           open_tickets=open_tickets,
                           progress_tickets=progress_tickets,
                           done_tickets=done_tickets,
                           sla_breached=sla_breached,
                           status_filter=status_filter,
                           urgency_filter=urgency_filter,
                           bagian_filter=bagian_filter,
                           date_filter=date_filter,
                           search=search,
                           sort_by=sort_by,
                           status_options=STATUS_OPTIONS,
                           bagian_options=get_bagian_options(),
                           format_datetime=format_datetime,
                           time_ago=time_ago,
                           chart_data=json.dumps(chart_data))


@dashboard_bp.route('/users')
@login_required
@admin_required
def manage_users():
    page = request.args.get('page', 1, type=int)
    role_filter = request.args.get('role', '')
    search = request.args.get('search', '').strip()

    query = User.query

    if role_filter:
        query = query.filter_by(role=role_filter)
    if search:
        query = query.filter(
            db.or_(
                User.nama.ilike(f'%{search}%'),
                User.username.ilike(f'%{search}%')
            )
        )

    users = query.order_by(User.created_at.desc()).paginate(page=page, per_page=15)

    return render_template('dashboard/manage_users.html',
                           users=users,
                           role_filter=role_filter,
                           search=search,
                           bagian_options=get_bagian_options())


@dashboard_bp.route('/users/create', methods=['POST'])
@login_required
@admin_required
def create_user():
    nama = request.form.get('nama', '').strip()
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    role = request.form.get('role', 'pelapor')
    bagian = request.form.get('bagian', '').strip()
    email = request.form.get('email', '').strip()
    telepon = request.form.get('telepon', '').strip()

    if not all([nama, username, password]):
        flash('Nama, username, dan password wajib diisi.', 'danger')
        return redirect(url_for('dashboard.manage_users'))

    if User.query.filter_by(username=username).first():
        flash('Username sudah digunakan.', 'danger')
        return redirect(url_for('dashboard.manage_users'))

    user = User(
        nama=nama,
        username=username,
        role=role,
        bagian=bagian,
        email=email if email else None,
        telepon=telepon if telepon else None
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    flash(f'User {nama} berhasil ditambahkan.', 'success')
    return redirect(url_for('dashboard.manage_users'))


@dashboard_bp.route('/users/<int:user_id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)

    user.nama = request.form.get('nama', user.nama).strip()
    user.role = request.form.get('role', user.role)
    user.bagian = request.form.get('bagian', user.bagian).strip()
    user.email = request.form.get('email', '').strip() or None
    user.telepon = request.form.get('telepon', '').strip() or None

    new_password = request.form.get('new_password', '').strip()
    if new_password:
        user.set_password(new_password)

    db.session.commit()
    flash(f'User {user.nama} berhasil diperbarui.', 'success')
    return redirect(url_for('dashboard.manage_users'))


@dashboard_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash('Anda tidak bisa menonaktifkan akun sendiri.', 'danger')
        return redirect(url_for('dashboard.manage_users'))

    user.is_active_user = not user.is_active_user
    db.session.commit()

    status = 'diaktifkan' if user.is_active_user else 'dinonaktifkan'
    flash(f'User {user.nama} berhasil {status}.', 'success')
    return redirect(url_for('dashboard.manage_users'))
