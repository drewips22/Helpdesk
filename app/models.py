from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from .extensions import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='pelapor')  # pelapor, teknisi
    bagian = db.Column(db.String(100), nullable=True)
    telepon = db.Column(db.String(20), nullable=True)
    is_active_user = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    # Relationships
    tickets_created = db.relationship('Ticket', foreign_keys='Ticket.user_id', backref='pelapor', lazy='dynamic')
    tickets_assigned = db.relationship('Ticket', foreign_keys='Ticket.assigned_to', backref='teknisi', lazy='dynamic')
    logs = db.relationship('TicketLog', backref='user', lazy='dynamic')
    comments = db.relationship('TicketComment', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_teknisi(self):
        return self.role == 'teknisi'

    def is_admin(self):
        return self.role == 'teknisi'

    def unread_notification_count(self):
        """Count unread notifications for this user."""
        if self.is_teknisi():
            # Teknisi: count new OPEN tickets + SLA breached
            open_count = Ticket.query.filter_by(status='OPEN').count()
            sla_count = Ticket.query.filter(
                Ticket.status.notin_(['DONE', 'CLOSED']),
                Ticket.sla_deadline < datetime.now()
            ).count()
            return open_count + sla_count
        else:
            # Pelapor: count tickets with recent status changes
            return Ticket.query.filter(
                Ticket.user_id == self.id,
                Ticket.status.in_(['DONE', 'ASSIGNED', 'ON_PROGRESS']),
                Ticket.updated_at >= datetime.now() - timedelta(hours=24)
            ).count()

    def __repr__(self):
        return f'<User {self.username}>'


@login_manager.user_loader
def load_user(id):
    return db.session.get(User, int(id))


class Ticket(db.Model):
    __tablename__ = 'tickets'

    id = db.Column(db.Integer, primary_key=True)
    ticket_code = db.Column(db.String(20), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    lokasi = db.Column(db.String(100), nullable=False)
    bagian = db.Column(db.String(100), nullable=False)
    jenis_perangkat = db.Column(db.String(50), nullable=False)
    jenis_masalah = db.Column(db.String(50), nullable=False)
    deskripsi = db.Column(db.Text, nullable=False)
    urgency = db.Column(db.String(20), nullable=False, default='sedang')
    status = db.Column(db.String(20), nullable=False, default='OPEN')
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    catatan_teknisi = db.Column(db.Text, nullable=True)
    sla_deadline = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    resolved_at = db.Column(db.DateTime, nullable=True)

    # Rating fields
    rating = db.Column(db.Integer, nullable=True)  # 1-5 stars
    rating_comment = db.Column(db.Text, nullable=True)
    rated_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    photos = db.relationship('TicketPhoto', backref='ticket', lazy='dynamic', cascade='all, delete-orphan')
    logs = db.relationship('TicketLog', backref='ticket', lazy='dynamic', cascade='all, delete-orphan',
                           order_by='TicketLog.created_at.desc()')
    comments = db.relationship('TicketComment', backref='ticket', lazy='dynamic', cascade='all, delete-orphan',
                               order_by='TicketComment.created_at.asc()')

    @staticmethod
    def generate_ticket_code():
        today = datetime.now().strftime('%Y%m%d')
        last_ticket = Ticket.query.filter(
            Ticket.ticket_code.like(f'TIK-{today}-%')
        ).order_by(Ticket.id.desc()).first()

        if last_ticket:
            last_num = int(last_ticket.ticket_code.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        return f'TIK-{today}-{new_num:03d}'

    def calculate_sla_deadline(self):
        from flask import current_app
        sla_hours = current_app.config.get('SLA_HOURS', {})
        hours = sla_hours.get(self.urgency, 24)
        self.sla_deadline = self.created_at + timedelta(hours=hours)

    @property
    def is_sla_breached(self):
        if self.sla_deadline and self.status not in ('DONE', 'CLOSED'):
            return datetime.now() > self.sla_deadline
        return False

    @property
    def sla_remaining(self):
        if self.sla_deadline and self.status not in ('DONE', 'CLOSED'):
            remaining = self.sla_deadline - datetime.now()
            if remaining.total_seconds() > 0:
                hours = int(remaining.total_seconds() // 3600)
                minutes = int((remaining.total_seconds() % 3600) // 60)
                return f'{hours}j {minutes}m'
            else:
                overdue = datetime.now() - self.sla_deadline
                hours = int(overdue.total_seconds() // 3600)
                minutes = int((overdue.total_seconds() % 3600) // 60)
                return f'-{hours}j {minutes}m'
        return '-'

    @property
    def sla_deadline_iso(self):
        """Return SLA deadline as ISO string for JS countdown."""
        if self.sla_deadline:
            return self.sla_deadline.isoformat()
        return ''

    @property
    def status_badge_class(self):
        classes = {
            'OPEN': 'bg-danger',
            'ASSIGNED': 'bg-warning text-dark',
            'ON_PROGRESS': 'bg-info',
            'DONE': 'bg-success',
            'CLOSED': 'bg-secondary'
        }
        return classes.get(self.status, 'bg-secondary')

    @property
    def status_label(self):
        labels = {
            'OPEN': 'Baru',
            'ASSIGNED': 'Ditugaskan',
            'ON_PROGRESS': 'Dikerjakan',
            'DONE': 'Selesai',
            'CLOSED': 'Ditutup'
        }
        return labels.get(self.status, self.status)

    @property
    def urgency_badge_class(self):
        classes = {
            'rendah': 'bg-success',
            'sedang': 'bg-info',
            'tinggi': 'bg-warning text-dark',
            'kritis': 'bg-danger'
        }
        return classes.get(self.urgency, 'bg-secondary')

    def __repr__(self):
        return f'<Ticket {self.ticket_code}>'


class TicketPhoto(db.Model):
    __tablename__ = 'ticket_photos'

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.now)


class TicketLog(db.Model):
    __tablename__ = 'ticket_logs'

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    old_value = db.Column(db.String(100), nullable=True)
    new_value = db.Column(db.String(100), nullable=True)
    note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    @property
    def action_label(self):
        labels = {
            'created': 'Tiket dibuat',
            'status_change': 'Status diubah',
            'assigned': 'Teknisi ditugaskan',
            'note_added': 'Catatan ditambahkan',
            'photo_added': 'Foto ditambahkan',
            'urgency_change': 'Urgency diubah',
            'rated': 'Rating diberikan',
            'closed_by_pelapor': 'Ditutup oleh pelapor'
        }
        return labels.get(self.action, self.action)

    @property
    def action_icon(self):
        icons = {
            'created': 'bi-plus-circle-fill',
            'status_change': 'bi-arrow-repeat',
            'assigned': 'bi-person-fill-check',
            'note_added': 'bi-chat-left-text-fill',
            'photo_added': 'bi-camera-fill',
            'urgency_change': 'bi-exclamation-triangle-fill',
            'rated': 'bi-star-fill',
            'closed_by_pelapor': 'bi-check-circle-fill'
        }
        return icons.get(self.action, 'bi-circle-fill')


class TicketComment(db.Model):
    __tablename__ = 'ticket_comments'

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)


class Lokasi(db.Model):
    __tablename__ = 'lokasi'

    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<Lokasi {self.nama}>'


class Bagian(db.Model):
    __tablename__ = 'bagian'

    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<Bagian {self.nama}>'


class JenisPerangkat(db.Model):
    __tablename__ = 'jenis_perangkat'

    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<JenisPerangkat {self.nama}>'


class JenisMasalah(db.Model):
    __tablename__ = 'jenis_masalah'

    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<JenisMasalah {self.nama}>'


class Recommendation(db.Model):
    __tablename__ = 'recommendations'

    id = db.Column(db.Integer, primary_key=True)
    jenis_perangkat = db.Column(db.String(50), nullable=False)
    jenis_masalah = db.Column(db.String(50), nullable=False)
    alat_yang_dibawa = db.Column(db.Text, nullable=False)
    kemungkinan_penyebab = db.Column(db.Text, nullable=False)
    langkah_awal = db.Column(db.Text, nullable=True)
