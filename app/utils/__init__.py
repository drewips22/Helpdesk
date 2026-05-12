import os
import uuid
import logging
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app

logger = logging.getLogger(__name__)


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def save_upload(file):
    """Save uploaded file with compression and return (filename, filepath)."""
    if file and allowed_file(file.filename):
        try:
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{uuid.uuid4().hex}.{ext}"
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

            # Compress image using Pillow
            try:
                from PIL import Image
                img = Image.open(file)

                # Convert RGBA to RGB for JPEG
                if img.mode in ('RGBA', 'P') and ext in ('jpg', 'jpeg'):
                    img = img.convert('RGB')

                # Resize if too large (max 1920x1080)
                img.thumbnail((1920, 1080), Image.LANCZOS)

                # Save with optimization
                if ext in ('jpg', 'jpeg'):
                    img.save(filepath, 'JPEG', quality=85, optimize=True)
                elif ext == 'webp':
                    img.save(filepath, 'WEBP', quality=85, optimize=True)
                elif ext == 'png':
                    img.save(filepath, 'PNG', optimize=True)
                else:
                    img.save(filepath)

                logger.info(f'Image saved and compressed: {filename}')
            except ImportError:
                # Fallback: save without compression if Pillow not available
                file.seek(0)
                file.save(filepath)
                logger.warning('Pillow not available, saved without compression')

            return filename, f"uploads/{filename}"
        except Exception as e:
            logger.error(f'Error saving upload: {e}')
            return None, None
    return None, None


def format_datetime(dt):
    """Format datetime to Indonesian format."""
    if not dt:
        return '-'
    months = [
        '', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
        'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
    ]
    return f"{dt.day} {months[dt.month]} {dt.year}, {dt.strftime('%H:%M')}"


def time_ago(dt):
    """Return human-readable time ago string in Indonesian."""
    if not dt:
        return '-'
    diff = datetime.now() - dt
    seconds = diff.total_seconds()

    if seconds < 60:
        return 'Baru saja'
    elif seconds < 3600:
        minutes = int(seconds // 60)
        return f'{minutes} menit lalu'
    elif seconds < 86400:
        hours = int(seconds // 3600)
        return f'{hours} jam lalu'
    elif seconds < 604800:
        days = int(seconds // 86400)
        return f'{days} hari lalu'
    else:
        return format_datetime(dt)


# --- Database-backed dropdown options ---

def get_lokasi_options():
    """Get active lokasi (room) options from database."""
    try:
        from app.models import Lokasi
        lokasi_list = Lokasi.query.filter_by(is_active=True).order_by(Lokasi.nama).all()
        if lokasi_list:
            return [l.nama for l in lokasi_list]
    except Exception:
        pass
    # Fallback to hardcoded if DB not available
    return LOKASI_OPTIONS_DEFAULT


def get_bagian_options():
    """Get active bagian (department) options from database."""
    try:
        from app.models import Bagian
        bagian_list = Bagian.query.filter_by(is_active=True).order_by(Bagian.nama).all()
        if bagian_list:
            return [b.nama for b in bagian_list]
    except Exception:
        pass
    # Fallback to hardcoded if DB not available
    return BAGIAN_OPTIONS_DEFAULT


def get_perangkat_options():
    """Get active jenis perangkat (device type) options from database."""
    try:
        from app.models import JenisPerangkat
        perangkat_list = JenisPerangkat.query.filter_by(is_active=True).order_by(JenisPerangkat.nama).all()
        if perangkat_list:
            return [p.nama for p in perangkat_list]
    except Exception:
        pass
    return JENIS_PERANGKAT_OPTIONS_DEFAULT


def get_masalah_options():
    """Get active jenis masalah (issue type) options from database."""
    try:
        from app.models import JenisMasalah
        masalah_list = JenisMasalah.query.filter_by(is_active=True).order_by(JenisMasalah.nama).all()
        if masalah_list:
            return [m.nama for m in masalah_list]
    except Exception:
        pass
    return JENIS_MASALAH_OPTIONS_DEFAULT


# Default options (used as fallback and for initial seed)
LOKASI_OPTIONS_DEFAULT = [
    'Ruang Kapolres',
    'Ruang Wakapolres',
    'Ruang Bag Ops',
    'Ruang Bag Ren',
    'Ruang Bag Sumda',
    'Ruang Bag Log',
    'Ruang SPKT',
    'Ruang Sat Reskrim',
    'Ruang Sat Resnarkoba',
    'Ruang Sat Intelkam',
    'Ruang Sat Sabhara',
    'Ruang Sat Lantas',
    'Ruang Sat Binmas',
    'Ruang Sat Tahti',
    'Ruang Sipropam',
    'Ruang SIUM',
    'Ruang TI / Komlek',
    'Lainnya'
]

BAGIAN_OPTIONS_DEFAULT = [
    'Bag Ops',
    'Bag Ren',
    'Bag Sumda',
    'Bag Log',
    'SPKT',
    'Sat Reskrim',
    'Sat Resnarkoba',
    'Sat Intelkam',
    'Sat Sabhara',
    'Sat Lantas',
    'Sat Binmas',
    'Sat Tahti',
    'Sipropam',
    'SIUM',
    'TI / Komlek',
    'Lainnya'
]

# Keep backward-compatible names for existing code
LOKASI_OPTIONS = LOKASI_OPTIONS_DEFAULT
BAGIAN_OPTIONS = BAGIAN_OPTIONS_DEFAULT

JENIS_PERANGKAT_OPTIONS_DEFAULT = [
    'Komputer / PC',
    'Laptop',
    'Printer',
    'Scanner',
    'Monitor',
    'Keyboard / Mouse',
    'Router / Switch',
    'Access Point / WiFi',
    'CCTV',
    'Server',
    'UPS',
    'Telepon / Intercom',
    'Proyektor',
    'Lainnya'
]

JENIS_MASALAH_OPTIONS_DEFAULT = [
    'Tidak Menyala / Mati Total',
    'Lambat / Hang',
    'Blue Screen / Error',
    'Tidak Bisa Print',
    'Tidak Bisa Konek Internet',
    'Virus / Malware',
    'Software Error / Crash',
    'Instalasi Software',
    'Lupa Password',
    'Email Bermasalah',
    'Kerusakan Fisik',
    'Kabel Putus / Rusak',
    'Suara Berisik / Overheat',
    'Permintaan Baru',
    'Lainnya'
]

# Backward-compat
JENIS_PERANGKAT_OPTIONS = JENIS_PERANGKAT_OPTIONS_DEFAULT
JENIS_MASALAH_OPTIONS = JENIS_MASALAH_OPTIONS_DEFAULT

URGENCY_OPTIONS = [
    ('rendah', 'Rendah', 'Tidak mengganggu pekerjaan'),
    ('sedang', 'Sedang', 'Mengganggu tapi masih bisa kerja'),
    ('tinggi', 'Tinggi', 'Sangat mengganggu pekerjaan'),
    ('kritis', 'Kritis', 'Pekerjaan berhenti total')
]

STATUS_OPTIONS = [
    'OPEN', 'ASSIGNED', 'ON_PROGRESS', 'DONE', 'CLOSED'
]

