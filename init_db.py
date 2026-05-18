from app import create_app
from app.extensions import db
from app.models import User
import seed_data
import time

app = create_app()

with app.app_context():
    # Beri jeda sedikit agar koneksi database siap
    time.sleep(2)
    
    # Buat tabel jika belum ada
    db.create_all()
    
    # Cek apakah database masih kosong (belum ada user sama sekali)
    if not User.query.first():
        print(">>> Database masih kosong! Menjalankan proses Seed Data otomatis...")
        try:
            seed_data.seed()
            print(">>> Seed Data Selesai!")
        except Exception as e:
            print(">>> Gagal menjalankan seed data:", e)
    else:
        print(">>> Database sudah terisi data. Melewati proses Seed Data.")
