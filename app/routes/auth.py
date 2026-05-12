from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app.extensions import db

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_teknisi():
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('tickets.my_tickets'))
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)

        user = User.query.filter_by(username=username).first()

        if user is None or not user.check_password(password):
            flash('Username atau password salah.', 'danger')
            return render_template('auth/login.html')

        if not user.is_active_user:
            flash('Akun Anda telah dinonaktifkan. Hubungi admin.', 'danger')
            return render_template('auth/login.html')

        login_user(user, remember=remember)
        flash(f'Selamat datang, {user.nama}!', 'success')

        # Security: validate next_page to prevent open redirect
        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)

        if user.is_teknisi():
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('tickets.my_tickets'))

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Anda telah keluar dari sistem.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        nama = request.form.get('nama', '').strip()
        email = request.form.get('email', '').strip()
        telepon = request.form.get('telepon', '').strip()
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')

        if nama:
            current_user.nama = nama
        if email:
            current_user.email = email
        if telepon:
            current_user.telepon = telepon

        # Handle password change - only one flash message
        if new_password:
            if not current_user.check_password(current_password):
                flash('Password lama salah.', 'danger')
                return render_template('auth/profile.html')
            current_user.set_password(new_password)
            db.session.commit()
            flash('Profil dan password berhasil diperbarui.', 'success')
        else:
            db.session.commit()
            flash('Profil berhasil diperbarui.', 'success')

        return redirect(url_for('auth.profile'))

    return render_template('auth/profile.html')
