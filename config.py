import os
import logging

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sitik-secret-key-polres-2026'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'sitik.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Upload config
    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # SLA deadlines in hours
    SLA_HOURS = {
        'rendah': 48,
        'sedang': 24,
        'tinggi': 8,
        'kritis': 2
    }

    # Logging
    LOG_LEVEL = logging.INFO

    @staticmethod
    def init_app(app):
        """Check for insecure configuration at startup."""
        if app.config['SECRET_KEY'] == 'sitik-secret-key-polres-2026':
            app.logger.warning(
                '⚠️  PERINGATAN: Menggunakan SECRET_KEY default! '
                'Set SECRET_KEY di environment variable atau file .env untuk production.'
            )
