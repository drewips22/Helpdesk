import os
import logging
from flask import Flask
from config import Config
from .extensions import db, login_manager, csrf, migrate, socketio


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Setup logging
    logging.basicConfig(
        level=app.config.get('LOG_LEVEL', logging.INFO),
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    app.logger.setLevel(app.config.get('LOG_LEVEL', logging.INFO))

    # Config init check
    if hasattr(config_class, 'init_app'):
        config_class.init_app(app)

    # Ensure directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.instance_path), exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app, cors_allowed_origins="*")

    # Register blueprints
    from .routes.auth import auth_bp
    from .routes.tickets import tickets_bp
    from .routes.dashboard import dashboard_bp
    from .routes.statistics import stats_bp
    from .routes.notifications import notif_bp
    from .routes.master import master_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(tickets_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(stats_bp)
    app.register_blueprint(notif_bp)
    app.register_blueprint(master_bp)

    # Import SocketIO event handlers
    from . import events  # noqa: F401

    # Context processors
    @app.context_processor
    def inject_globals():
        from datetime import datetime
        from .utils import get_lokasi_options, get_bagian_options, get_perangkat_options, get_masalah_options
        return {
            'now': datetime.now(),
            'app_name': 'SI-TIK',
            'app_full_name': 'Sistem Informasi Tiket IT Polres',
            'all_lokasi': get_lokasi_options(),
            'all_bagian': get_bagian_options(),
            'all_perangkat': get_perangkat_options(),
            'all_masalah': get_masalah_options()
        }

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden(e):
        from flask import render_template
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def internal_error(e):
        from flask import render_template
        db.session.rollback()
        app.logger.error(f'Internal server error: {e}')
        return render_template('errors/500.html'), 500

    # Create tables
    with app.app_context():
        from . import models
        db.create_all()

    app.logger.info('SI-TIK application started successfully.')
    return app
