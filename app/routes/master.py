"""Master data management routes for Lokasi (rooms) and Bagian (departments)."""
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required
from app.models import Lokasi, Bagian, JenisPerangkat, JenisMasalah
from app.extensions import db
from app.utils.decorators import admin_required

master_bp = Blueprint('master', __name__, url_prefix='/dashboard/master')


# ==================== LOKASI (RUANGAN) ====================

@master_bp.route('/lokasi')
@login_required
@admin_required
def manage_lokasi():
    search = request.args.get('search', '').strip()
    query = Lokasi.query

    if search:
        query = query.filter(Lokasi.nama.ilike(f'%{search}%'))

    lokasi_list = query.order_by(Lokasi.nama.asc()).all()

    return render_template('dashboard/manage_lokasi.html',
                           lokasi_list=lokasi_list,
                           search=search)


@master_bp.route('/lokasi/create', methods=['POST'])
@login_required
@admin_required
def create_lokasi():
    nama = request.form.get('nama', '').strip()

    if not nama:
        flash('Nama ruangan wajib diisi.', 'danger')
        return redirect(url_for('master.manage_lokasi'))

    if Lokasi.query.filter_by(nama=nama).first():
        flash(f'Ruangan "{nama}" sudah ada.', 'danger')
        return redirect(url_for('master.manage_lokasi'))

    lokasi = Lokasi(nama=nama)
    db.session.add(lokasi)
    db.session.commit()

    current_app.logger.info(f'Lokasi created: {nama}')
    flash(f'Ruangan "{nama}" berhasil ditambahkan.', 'success')
    return redirect(url_for('master.manage_lokasi'))


@master_bp.route('/lokasi/<int:lokasi_id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_lokasi(lokasi_id):
    lokasi = Lokasi.query.get_or_404(lokasi_id)
    nama = request.form.get('nama', '').strip()

    if not nama:
        flash('Nama ruangan wajib diisi.', 'danger')
        return redirect(url_for('master.manage_lokasi'))

    # Check duplicate
    existing = Lokasi.query.filter(Lokasi.nama == nama, Lokasi.id != lokasi_id).first()
    if existing:
        flash(f'Ruangan "{nama}" sudah ada.', 'danger')
        return redirect(url_for('master.manage_lokasi'))

    lokasi.nama = nama
    db.session.commit()

    flash(f'Ruangan berhasil diperbarui.', 'success')
    return redirect(url_for('master.manage_lokasi'))


@master_bp.route('/lokasi/<int:lokasi_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_lokasi(lokasi_id):
    lokasi = Lokasi.query.get_or_404(lokasi_id)
    lokasi.is_active = not lokasi.is_active
    db.session.commit()

    status = 'diaktifkan' if lokasi.is_active else 'dinonaktifkan'
    flash(f'Ruangan "{lokasi.nama}" berhasil {status}.', 'success')
    return redirect(url_for('master.manage_lokasi'))


# ==================== BAGIAN (DEPARTMENTS) ====================

@master_bp.route('/bagian')
@login_required
@admin_required
def manage_bagian():
    search = request.args.get('search', '').strip()
    query = Bagian.query

    if search:
        query = query.filter(Bagian.nama.ilike(f'%{search}%'))

    bagian_list = query.order_by(Bagian.nama.asc()).all()

    return render_template('dashboard/manage_bagian.html',
                           bagian_list=bagian_list,
                           search=search)


@master_bp.route('/bagian/create', methods=['POST'])
@login_required
@admin_required
def create_bagian():
    nama = request.form.get('nama', '').strip()

    if not nama:
        flash('Nama bagian wajib diisi.', 'danger')
        return redirect(url_for('master.manage_bagian'))

    if Bagian.query.filter_by(nama=nama).first():
        flash(f'Bagian "{nama}" sudah ada.', 'danger')
        return redirect(url_for('master.manage_bagian'))

    bagian = Bagian(nama=nama)
    db.session.add(bagian)
    db.session.commit()

    current_app.logger.info(f'Bagian created: {nama}')
    flash(f'Bagian "{nama}" berhasil ditambahkan.', 'success')
    return redirect(url_for('master.manage_bagian'))


@master_bp.route('/bagian/<int:bagian_id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_bagian(bagian_id):
    bagian = Bagian.query.get_or_404(bagian_id)
    nama = request.form.get('nama', '').strip()

    if not nama:
        flash('Nama bagian wajib diisi.', 'danger')
        return redirect(url_for('master.manage_bagian'))

    existing = Bagian.query.filter(Bagian.nama == nama, Bagian.id != bagian_id).first()
    if existing:
        flash(f'Bagian "{nama}" sudah ada.', 'danger')
        return redirect(url_for('master.manage_bagian'))

    bagian.nama = nama
    db.session.commit()

    flash(f'Bagian berhasil diperbarui.', 'success')
    return redirect(url_for('master.manage_bagian'))


@master_bp.route('/bagian/<int:bagian_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_bagian(bagian_id):
    bagian = Bagian.query.get_or_404(bagian_id)
    bagian.is_active = not bagian.is_active
    db.session.commit()

    status = 'diaktifkan' if bagian.is_active else 'dinonaktifkan'
    flash(f'Bagian "{bagian.nama}" berhasil {status}.', 'success')
    return redirect(url_for('master.manage_bagian'))


# ==================== JENIS PERANGKAT ====================

@master_bp.route('/perangkat')
@login_required
@admin_required
def manage_perangkat():
    search = request.args.get('search', '').strip()
    query = JenisPerangkat.query

    if search:
        query = query.filter(JenisPerangkat.nama.ilike(f'%{search}%'))

    perangkat_list = query.order_by(JenisPerangkat.nama.asc()).all()

    return render_template('dashboard/manage_perangkat.html',
                           perangkat_list=perangkat_list,
                           search=search)


@master_bp.route('/perangkat/create', methods=['POST'])
@login_required
@admin_required
def create_perangkat():
    nama = request.form.get('nama', '').strip()

    if not nama:
        flash('Nama perangkat wajib diisi.', 'danger')
        return redirect(url_for('master.manage_perangkat'))

    if JenisPerangkat.query.filter_by(nama=nama).first():
        flash(f'Perangkat "{nama}" sudah ada.', 'danger')
        return redirect(url_for('master.manage_perangkat'))

    perangkat = JenisPerangkat(nama=nama)
    db.session.add(perangkat)
    db.session.commit()

    current_app.logger.info(f'JenisPerangkat created: {nama}')
    flash(f'Perangkat "{nama}" berhasil ditambahkan.', 'success')
    return redirect(url_for('master.manage_perangkat'))


@master_bp.route('/perangkat/<int:perangkat_id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_perangkat(perangkat_id):
    perangkat = JenisPerangkat.query.get_or_404(perangkat_id)
    nama = request.form.get('nama', '').strip()

    if not nama:
        flash('Nama perangkat wajib diisi.', 'danger')
        return redirect(url_for('master.manage_perangkat'))

    existing = JenisPerangkat.query.filter(JenisPerangkat.nama == nama, JenisPerangkat.id != perangkat_id).first()
    if existing:
        flash(f'Perangkat "{nama}" sudah ada.', 'danger')
        return redirect(url_for('master.manage_perangkat'))

    perangkat.nama = nama
    db.session.commit()

    flash(f'Perangkat berhasil diperbarui.', 'success')
    return redirect(url_for('master.manage_perangkat'))


@master_bp.route('/perangkat/<int:perangkat_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_perangkat(perangkat_id):
    perangkat = JenisPerangkat.query.get_or_404(perangkat_id)
    perangkat.is_active = not perangkat.is_active
    db.session.commit()

    status = 'diaktifkan' if perangkat.is_active else 'dinonaktifkan'
    flash(f'Perangkat "{perangkat.nama}" berhasil {status}.', 'success')
    return redirect(url_for('master.manage_perangkat'))


# ==================== JENIS MASALAH ====================

@master_bp.route('/masalah')
@login_required
@admin_required
def manage_masalah():
    search = request.args.get('search', '').strip()
    query = JenisMasalah.query

    if search:
        query = query.filter(JenisMasalah.nama.ilike(f'%{search}%'))

    masalah_list = query.order_by(JenisMasalah.nama.asc()).all()

    return render_template('dashboard/manage_masalah.html',
                           masalah_list=masalah_list,
                           search=search)


@master_bp.route('/masalah/create', methods=['POST'])
@login_required
@admin_required
def create_masalah():
    nama = request.form.get('nama', '').strip()

    if not nama:
        flash('Nama jenis masalah wajib diisi.', 'danger')
        return redirect(url_for('master.manage_masalah'))

    if JenisMasalah.query.filter_by(nama=nama).first():
        flash(f'Jenis masalah "{nama}" sudah ada.', 'danger')
        return redirect(url_for('master.manage_masalah'))

    masalah = JenisMasalah(nama=nama)
    db.session.add(masalah)
    db.session.commit()

    current_app.logger.info(f'JenisMasalah created: {nama}')
    flash(f'Jenis masalah "{nama}" berhasil ditambahkan.', 'success')
    return redirect(url_for('master.manage_masalah'))


@master_bp.route('/masalah/<int:masalah_id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_masalah(masalah_id):
    masalah = JenisMasalah.query.get_or_404(masalah_id)
    nama = request.form.get('nama', '').strip()

    if not nama:
        flash('Nama jenis masalah wajib diisi.', 'danger')
        return redirect(url_for('master.manage_masalah'))

    existing = JenisMasalah.query.filter(JenisMasalah.nama == nama, JenisMasalah.id != masalah_id).first()
    if existing:
        flash(f'Jenis masalah "{nama}" sudah ada.', 'danger')
        return redirect(url_for('master.manage_masalah'))

    masalah.nama = nama
    db.session.commit()

    flash(f'Jenis masalah berhasil diperbarui.', 'success')
    return redirect(url_for('master.manage_masalah'))


@master_bp.route('/masalah/<int:masalah_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_masalah(masalah_id):
    masalah = JenisMasalah.query.get_or_404(masalah_id)
    masalah.is_active = not masalah.is_active
    db.session.commit()

    status = 'diaktifkan' if masalah.is_active else 'dinonaktifkan'
    flash(f'Jenis masalah "{masalah.nama}" berhasil {status}.', 'success')
    return redirect(url_for('master.manage_masalah'))
