from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from app.models import Ticket, TicketPhoto, TicketLog, TicketComment
from app.extensions import db
from app.utils import (
    save_upload, get_lokasi_options, get_bagian_options,
    get_perangkat_options, get_masalah_options, URGENCY_OPTIONS,
    format_datetime, time_ago
)
from app.utils.recommendations import get_recommendation

tickets_bp = Blueprint('tickets', __name__, url_prefix='/tickets')


@tickets_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        lokasi = request.form.get('lokasi', '').strip()
        bagian = request.form.get('bagian', '').strip()
        jenis_perangkat = request.form.get('jenis_perangkat', '').strip()
        jenis_masalah = request.form.get('jenis_masalah', '').strip()
        deskripsi = request.form.get('deskripsi', '').strip()
        urgency = request.form.get('urgency', 'sedang')

        if not all([lokasi, bagian, jenis_perangkat, jenis_masalah, deskripsi]):
            flash('Semua field wajib diisi.', 'danger')
            return render_template('tickets/create.html',
                                   lokasi_options=get_lokasi_options(),
                                   bagian_options=get_bagian_options(),
                                   perangkat_options=get_perangkat_options(),
                                   masalah_options=get_masalah_options(),
                                   urgency_options=URGENCY_OPTIONS)

        ticket = Ticket(
            ticket_code=Ticket.generate_ticket_code(),
            user_id=current_user.id,
            lokasi=lokasi,
            bagian=bagian,
            jenis_perangkat=jenis_perangkat,
            jenis_masalah=jenis_masalah,
            deskripsi=deskripsi,
            urgency=urgency,
            status='OPEN',
            created_at=datetime.now()
        )
        ticket.calculate_sla_deadline()
        db.session.add(ticket)
        db.session.flush()

        # Handle file uploads
        files = request.files.getlist('photos')
        for file in files:
            if file and file.filename:
                filename, filepath = save_upload(file)
                if filename:
                    photo = TicketPhoto(
                        ticket_id=ticket.id,
                        filename=filename,
                        filepath=filepath
                    )
                    db.session.add(photo)

        # Add creation log
        log = TicketLog(
            ticket_id=ticket.id,
            user_id=current_user.id,
            action='created',
            new_value='OPEN',
            note=f'Tiket dibuat oleh {current_user.nama}'
        )
        db.session.add(log)
        db.session.commit()

        # Real-time: notify all teknisi about new ticket
        try:
            from app.events import emit_new_ticket_alert, emit_dashboard_update
            emit_new_ticket_alert({
                'id': ticket.id,
                'ticket_code': ticket.ticket_code,
                'pelapor': current_user.nama,
                'jenis_perangkat': ticket.jenis_perangkat,
                'jenis_masalah': ticket.jenis_masalah,
                'lokasi': ticket.lokasi,
                'urgency': ticket.urgency,
                'time': 'Baru saja'
            })
            emit_dashboard_update()
        except Exception as e:
            current_app.logger.warning(f'SocketIO emit failed: {e}')

        current_app.logger.info(f'Ticket created: {ticket.ticket_code} by {current_user.username}')
        flash(f'Tiket berhasil dibuat! Kode tiket: {ticket.ticket_code}', 'success')
        return redirect(url_for('tickets.detail', ticket_id=ticket.id))

    return render_template('tickets/create.html',
                           lokasi_options=get_lokasi_options(),
                           bagian_options=get_bagian_options(),
                           perangkat_options=get_perangkat_options(),
                           masalah_options=get_masalah_options(),
                           urgency_options=URGENCY_OPTIONS)


@tickets_bp.route('/<int:ticket_id>')
@login_required
def detail(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)

    # Pelapor can only see their own tickets
    if not current_user.is_teknisi() and ticket.user_id != current_user.id:
        flash('Anda tidak memiliki akses ke tiket ini.', 'danger')
        return redirect(url_for('tickets.my_tickets'))

    # Get recommendation
    rec = get_recommendation(ticket.jenis_perangkat, ticket.jenis_masalah)

    logs = ticket.logs.order_by(TicketLog.created_at.desc()).all()
    photos = ticket.photos.all()
    comments = ticket.comments.order_by(TicketComment.created_at.asc()).all()

    from app.models import User
    # Fixed: removed stale 'admin' role from query
    teknisi_list = User.query.filter_by(role='teknisi', is_active_user=True).all()

    return render_template('tickets/detail.html',
                           ticket=ticket,
                           logs=logs,
                           photos=photos,
                           comments=comments,
                           recommendation=rec,
                           teknisi_list=teknisi_list,
                           format_datetime=format_datetime,
                           time_ago=time_ago)


@tickets_bp.route('/<int:ticket_id>/update', methods=['POST'])
@login_required
def update(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)

    action = request.form.get('action')

    # Allow pelapor to close their own DONE tickets or add comments
    if not current_user.is_teknisi():
        if action == 'close' and ticket.user_id == current_user.id and ticket.status == 'DONE':
            ticket.status = 'CLOSED'
            ticket.updated_at = datetime.now()
            log = TicketLog(
                ticket_id=ticket.id,
                user_id=current_user.id,
                action='closed_by_pelapor',
                old_value='DONE',
                new_value='CLOSED',
                note=f'Tiket ditutup oleh pelapor {current_user.nama}'
            )
            db.session.add(log)
            db.session.commit()

            # Real-time: notify teknisi
            _emit_status_update(ticket, 'DONE', 'CLOSED')

            flash('Tiket berhasil ditutup. Terima kasih!', 'success')
            return redirect(url_for('tickets.detail', ticket_id=ticket_id))
        elif action == 'rate' and ticket.user_id == current_user.id and ticket.status in ('DONE', 'CLOSED'):
            rating = request.form.get('rating', type=int)
            rating_comment = request.form.get('rating_comment', '').strip()
            if rating and 1 <= rating <= 5:
                ticket.rating = rating
                ticket.rating_comment = rating_comment
                ticket.rated_at = datetime.now()
                log = TicketLog(
                    ticket_id=ticket.id,
                    user_id=current_user.id,
                    action='rated',
                    new_value=f'{rating} bintang',
                    note=rating_comment or f'Rating {rating}/5'
                )
                db.session.add(log)
                db.session.commit()
                flash('Terima kasih atas feedback Anda!', 'success')
            return redirect(url_for('tickets.detail', ticket_id=ticket_id))
        elif action == 'comment' and ticket.user_id == current_user.id:
            message = request.form.get('message', '').strip()
            if message:
                comment = TicketComment(
                    ticket_id=ticket.id,
                    user_id=current_user.id,
                    message=message
                )
                db.session.add(comment)
                ticket.updated_at = datetime.now()
                db.session.commit()

                # Real-time: broadcast message
                _emit_new_comment(ticket, comment)

                flash('Komentar berhasil dikirim.', 'success')
            return redirect(url_for('tickets.detail', ticket_id=ticket_id))
        else:
            flash('Anda tidak memiliki akses.', 'danger')
            return redirect(url_for('tickets.detail', ticket_id=ticket_id))

    # Teknisi actions below
    if action == 'assign':
        from app.models import User
        teknisi_id = request.form.get('teknisi_id')
        if teknisi_id:
            teknisi = User.query.get(int(teknisi_id))
            if teknisi:
                old_status = ticket.status
                ticket.assigned_to = teknisi.id
                if ticket.status == 'OPEN':
                    ticket.status = 'ASSIGNED'

                log = TicketLog(
                    ticket_id=ticket.id,
                    user_id=current_user.id,
                    action='assigned',
                    new_value=teknisi.nama,
                    note=f'Ditugaskan kepada {teknisi.nama}'
                )
                db.session.add(log)

                if old_status != ticket.status:
                    log2 = TicketLog(
                        ticket_id=ticket.id,
                        user_id=current_user.id,
                        action='status_change',
                        old_value=old_status,
                        new_value=ticket.status,
                        note=f'Status diubah dari {old_status} ke {ticket.status}'
                    )
                    db.session.add(log2)

                flash(f'Tiket ditugaskan kepada {teknisi.nama}.', 'success')

    elif action == 'status':
        new_status = request.form.get('status')
        if new_status and new_status in ['OPEN', 'ASSIGNED', 'ON_PROGRESS', 'DONE', 'CLOSED']:
            old_status = ticket.status
            ticket.status = new_status

            if new_status == 'DONE':
                ticket.resolved_at = datetime.now()

            log = TicketLog(
                ticket_id=ticket.id,
                user_id=current_user.id,
                action='status_change',
                old_value=old_status,
                new_value=new_status,
                note=f'Status diubah dari {old_status} ke {new_status}'
            )
            db.session.add(log)
            flash(f'Status tiket diubah menjadi {new_status}.', 'success')

    elif action == 'note':
        note_text = request.form.get('note', '').strip()
        if note_text:
            ticket.catatan_teknisi = note_text
            log = TicketLog(
                ticket_id=ticket.id,
                user_id=current_user.id,
                action='note_added',
                note=note_text
            )
            db.session.add(log)
            flash('Catatan berhasil ditambahkan.', 'success')

    elif action == 'urgency':
        new_urgency = request.form.get('urgency')
        if new_urgency:
            old_urgency = ticket.urgency
            ticket.urgency = new_urgency
            ticket.calculate_sla_deadline()
            log = TicketLog(
                ticket_id=ticket.id,
                user_id=current_user.id,
                action='urgency_change',
                old_value=old_urgency,
                new_value=new_urgency,
                note=f'Urgency diubah dari {old_urgency} ke {new_urgency}'
            )
            db.session.add(log)
            flash('Urgency tiket berhasil diubah.', 'success')

    elif action == 'add_photo':
        files = request.files.getlist('photos')
        for file in files:
            if file and file.filename:
                filename, filepath = save_upload(file)
                if filename:
                    photo = TicketPhoto(
                        ticket_id=ticket.id,
                        filename=filename,
                        filepath=filepath
                    )
                    db.session.add(photo)
                    log = TicketLog(
                        ticket_id=ticket.id,
                        user_id=current_user.id,
                        action='photo_added',
                        note='Foto baru ditambahkan'
                    )
                    db.session.add(log)
        flash('Foto berhasil ditambahkan.', 'success')

    elif action == 'comment':
        message = request.form.get('message', '').strip()
        if message:
            comment = TicketComment(
                ticket_id=ticket.id,
                user_id=current_user.id,
                message=message
            )
            db.session.add(comment)
            flash('Komentar berhasil dikirim.', 'success')

    old_status_before = ticket.status
    ticket.updated_at = datetime.now()
    db.session.commit()

    # Real-time: emit updates
    try:
        from app.events import emit_ticket_update, emit_ticket_notification, emit_dashboard_update

        # Notify ticket viewers about changes
        emit_ticket_update(ticket.id, {
            'ticket_id': ticket.id,
            'status': ticket.status,
            'status_label': ticket.status_label,
            'status_badge_class': ticket.status_badge_class,
            'action': action
        })

        # Notify pelapor if teknisi changed something
        if current_user.is_teknisi() and ticket.user_id != current_user.id:
            emit_ticket_notification(ticket.user_id, {
                'type': 'ticket_update',
                'icon': 'bi-arrow-repeat',
                'color': 'info',
                'title': f'Update: {ticket.ticket_code}',
                'message': f'Status: {ticket.status_label}',
                'url': f'/tickets/{ticket.id}'
            })

        # Notify teknisi if pelapor did something
        if not current_user.is_teknisi() and ticket.assigned_to:
            emit_ticket_notification(ticket.assigned_to, {
                'type': 'ticket_update',
                'icon': 'bi-chat-left-text-fill',
                'color': 'primary',
                'title': f'Update: {ticket.ticket_code}',
                'message': f'Pelapor mengirim komentar',
                'url': f'/tickets/{ticket.id}'
            })

        emit_dashboard_update()
    except Exception as e:
        current_app.logger.warning(f'SocketIO emit failed: {e}')

    return redirect(url_for('tickets.detail', ticket_id=ticket_id))


@tickets_bp.route('/my')
@login_required
def my_tickets():
    from datetime import datetime, timedelta
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    date_filter = request.args.get('date', 'all')

    query = Ticket.query.filter_by(user_id=current_user.id)



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

    if status_filter:
        query = query.filter_by(status=status_filter)

    tickets = query.order_by(Ticket.created_at.desc()).paginate(page=page, per_page=10)

    # Summary stats for pelapor dashboard
    total = Ticket.query.filter_by(user_id=current_user.id).count()
    open_count = Ticket.query.filter_by(user_id=current_user.id, status='OPEN').count()
    progress_count = Ticket.query.filter(
        Ticket.user_id == current_user.id,
        Ticket.status.in_(['ASSIGNED', 'ON_PROGRESS'])
    ).count()
    done_count = Ticket.query.filter_by(user_id=current_user.id, status='DONE').count()

    return render_template('tickets/list.html',
                           tickets=tickets,
                           status_filter=status_filter,
                           date_filter=date_filter,
                           total=total,
                           open_count=open_count,
                           progress_count=progress_count,
                           done_count=done_count,
                           format_datetime=format_datetime,
                           time_ago=time_ago)


@tickets_bp.route('/track', methods=['GET', 'POST'])
def track():
    ticket = None
    if request.method == 'POST' or request.args.get('code'):
        code = request.form.get('ticket_code', '') or request.args.get('code', '')
        code = code.strip().upper()
        if code:
            ticket = Ticket.query.filter_by(ticket_code=code).first()
            if not ticket:
                flash('Tiket tidak ditemukan. Periksa kembali kode tiket Anda.', 'warning')

    return render_template('tickets/track.html',
                           ticket=ticket,
                           format_datetime=format_datetime,
                           time_ago=time_ago)


@tickets_bp.route('/api/recommendation')
@login_required
def api_recommendation():
    jenis_perangkat = request.args.get('perangkat', '')
    jenis_masalah = request.args.get('masalah', '')
    rec = get_recommendation(jenis_perangkat, jenis_masalah)
    return jsonify(rec)


# --- Helper functions for real-time emit ---

def _emit_status_update(ticket, old_status, new_status):
    """Emit status update events."""
    try:
        from app.events import emit_ticket_update, emit_ticket_notification, emit_dashboard_update
        emit_ticket_update(ticket.id, {
            'ticket_id': ticket.id,
            'status': new_status,
            'status_label': ticket.status_label,
            'status_badge_class': ticket.status_badge_class,
            'action': 'status'
        })
        emit_dashboard_update()
    except Exception:
        pass


def _emit_new_comment(ticket, comment):
    """Emit new comment event."""
    try:
        from app.events import emit_ticket_update
        emit_ticket_update(ticket.id, {
            'ticket_id': ticket.id,
            'action': 'comment',
            'comment': {
                'id': comment.id,
                'user_id': comment.user_id,
                'user_nama': current_user.nama,
                'user_initial': current_user.nama[0].upper(),
                'message': comment.message,
                'time': 'Baru saja'
            }
        })
    except Exception:
        pass


@tickets_bp.route('/<int:ticket_id>/berita-acara')
@login_required
def berita_acara(ticket_id):
    """Render print-friendly Berita Acara Perbaikan for a resolved/closed ticket."""
    from app.utils.decorators import teknisi_required
    ticket = Ticket.query.get_or_404(ticket_id)

    # Only teknisi or the ticket owner can access
    if not current_user.is_teknisi() and ticket.user_id != current_user.id:
        flash('Anda tidak memiliki akses ke tiket ini.', 'danger')
        return redirect(url_for('tickets.my_tickets'))

    logs = ticket.logs.order_by(TicketLog.created_at.asc()).all()

    return render_template(
        'tickets/berita_acara.html',
        ticket=ticket,
        logs=logs,
        format_datetime=format_datetime,
        now=datetime.now()
    )
