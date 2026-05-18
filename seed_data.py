"""Seed data for SI-TIK application."""
from datetime import datetime, timedelta
import random
from app import create_app
from app.extensions import db
from app.models import User, Ticket, TicketLog, TicketComment, Recommendation, Lokasi, Bagian, JenisPerangkat, JenisMasalah

app = create_app()

def seed():
    with app.app_context():
        db.create_all()
        
        # Check if already seeded
        if User.query.first():
            print("Database already seeded. Skipping seed.")
            return

        print("Database is empty. Running seed...")

        # ==================== SEED LOKASI (RUANGAN) ====================
        lokasi_names = [
            'Ruang Kapolres', 'Ruang Wakapolres', 'Ruang Bag Ops',
            'Ruang Bag Ren', 'Ruang Bag Sumda', 'Ruang Bag Log',
            'Ruang SPKT', 'Ruang Sat Reskrim', 'Ruang Sat Resnarkoba',
            'Ruang Sat Intelkam', 'Ruang Sat Sabhara', 'Ruang Sat Lantas',
            'Ruang Sat Binmas', 'Ruang Sat Tahti', 'Ruang Sipropam',
            'Ruang SIUM', 'Ruang TI / Komlek', 'Lainnya'
        ]
        for nama in lokasi_names:
            db.session.add(Lokasi(nama=nama))
        print("[OK] Lokasi (ruangan) berhasil di-seed.")

        # ==================== SEED BAGIAN ====================
        bagian_names = [
            'Bag Ops', 'Bag Ren', 'Bag Sumda', 'Bag Log',
            'SPKT', 'Sat Reskrim', 'Sat Resnarkoba', 'Sat Intelkam',
            'Sat Sabhara', 'Sat Lantas', 'Sat Binmas', 'Sat Tahti',
            'Sipropam', 'SIUM', 'TI / Komlek', 'Lainnya'
        ]
        for nama in bagian_names:
            db.session.add(Bagian(nama=nama))
        print("[OK] Bagian berhasil di-seed.")

        # ==================== SEED JENIS PERANGKAT ====================
        perangkat_names = [
            'Komputer / PC', 'Laptop', 'Printer', 'Scanner', 'Monitor',
            'Keyboard / Mouse', 'Router / Switch', 'Access Point / WiFi',
            'CCTV', 'Server', 'UPS', 'Telepon / Intercom', 'Proyektor', 'Lainnya'
        ]
        for nama in perangkat_names:
            db.session.add(JenisPerangkat(nama=nama))
        print("[OK] Jenis Perangkat berhasil di-seed.")

        # ==================== SEED JENIS MASALAH ====================
        masalah_names = [
            'Tidak Menyala / Mati Total', 'Lambat / Hang', 'Blue Screen / Error',
            'Tidak Bisa Print', 'Tidak Bisa Konek Internet', 'Virus / Malware',
            'Software Error / Crash', 'Instalasi Software', 'Lupa Password',
            'Email Bermasalah', 'Kerusakan Fisik', 'Kabel Putus / Rusak',
            'Suara Berisik / Overheat', 'Permintaan Baru', 'Lainnya'
        ]
        for nama in masalah_names:
            db.session.add(JenisMasalah(nama=nama))
        print("[OK] Jenis Masalah berhasil di-seed.")

        db.session.flush()

        # ==================== SEED USERS ====================
        admin = User(nama='Admin IT', username='admin', role='teknisi', bagian='TI / Komlek', email='admin@polres.go.id')
        admin.set_password('admin123')
        teknisi1 = User(nama='Budi Teknisi', username='teknisi1', role='teknisi', bagian='TI / Komlek')
        teknisi1.set_password('teknisi123')
        teknisi2 = User(nama='Andi Teknisi', username='teknisi2', role='teknisi', bagian='TI / Komlek')
        teknisi2.set_password('teknisi123')
        pelapor1 = User(nama='Siti Rahayu', username='siti', role='pelapor', bagian='Sat Reskrim')
        pelapor1.set_password('user123')
        pelapor2 = User(nama='Ahmad Fauzi', username='ahmad', role='pelapor', bagian='Bag Ops')
        pelapor2.set_password('user123')
        pelapor3 = User(nama='Dewi Lestari', username='dewi', role='pelapor', bagian='SPKT')
        pelapor3.set_password('user123')

        db.session.add_all([admin, teknisi1, teknisi2, pelapor1, pelapor2, pelapor3])
        db.session.flush()

        # ==================== SEED TICKETS ====================
        samples = [
            {'lokasi':'Ruang Sat Reskrim','bagian':'Sat Reskrim','perangkat':'Komputer / PC','masalah':'Tidak Menyala / Mati Total','urgency':'tinggi','deskripsi':'Komputer di meja penyidik tidak bisa menyala sejak pagi. Sudah coba ganti colokan tetap tidak bisa.','user':pelapor1,'status':'OPEN'},
            {'lokasi':'Ruang Bag Ops','bagian':'Bag Ops','perangkat':'Printer','masalah':'Tidak Bisa Print','urgency':'sedang','deskripsi':'Printer HP LaserJet tidak merespon perintah print dari semua komputer.','user':pelapor2,'status':'ASSIGNED','teknisi':teknisi1},
            {'lokasi':'Ruang SPKT','bagian':'SPKT','perangkat':'Access Point / WiFi','masalah':'Tidak Bisa Konek Internet','urgency':'kritis','deskripsi':'WiFi di ruang SPKT mati total. Tidak bisa akses sistem pelaporan online.','user':pelapor3,'status':'ON_PROGRESS','teknisi':teknisi2},
            {'lokasi':'Ruang Sat Lantas','bagian':'Sat Lantas','perangkat':'Laptop','masalah':'Lambat / Hang','urgency':'rendah','deskripsi':'Laptop sering hang saat buka aplikasi SKCK online.','user':pelapor1,'status':'DONE','teknisi':teknisi1},
            {'lokasi':'Ruang Bag Sumda','bagian':'Bag Sumda','perangkat':'Komputer / PC','masalah':'Virus / Malware','urgency':'tinggi','deskripsi':'Komputer terinfeksi virus ransomware. File-file terenkripsi.','user':pelapor2,'status':'ON_PROGRESS','teknisi':teknisi2},
        ]

        for i, s in enumerate(samples):
            days_ago = len(samples) - i
            created = datetime.now() - timedelta(days=days_ago, hours=random.randint(1,8))
            ticket = Ticket(
                ticket_code=f"TIK-{created.strftime('%Y%m%d')}-{i+1:03d}",
                user_id=s['user'].id, lokasi=s['lokasi'], bagian=s['bagian'],
                jenis_perangkat=s['perangkat'], jenis_masalah=s['masalah'],
                deskripsi=s['deskripsi'], urgency=s['urgency'],
                status=s['status'], created_at=created, updated_at=created
            )
            if s.get('teknisi'):
                ticket.assigned_to = s['teknisi'].id
            if s['status'] == 'DONE':
                ticket.resolved_at = created + timedelta(hours=random.randint(2,12))
                ticket.rating = random.choice([4, 5])
                ticket.rating_comment = random.choice(['Mantap, cepat ditangani!', 'Terima kasih, masalah teratasi.', ''])
                ticket.rated_at = ticket.resolved_at + timedelta(hours=1)
            ticket.calculate_sla_deadline()
            db.session.add(ticket)
            db.session.flush()

            log = TicketLog(ticket_id=ticket.id, user_id=s['user'].id, action='created', new_value='OPEN', note='Tiket dibuat', created_at=created)
            db.session.add(log)

            # Add sample comments for tickets with teknisi
            if s.get('teknisi'):
                c1 = TicketComment(ticket_id=ticket.id, user_id=s['user'].id,
                    message='Tolong segera ditangani ya, terima kasih.',
                    created_at=created + timedelta(hours=1))
                c2 = TicketComment(ticket_id=ticket.id, user_id=s['teknisi'].id,
                    message='Baik, saya akan segera ke lokasi.',
                    created_at=created + timedelta(hours=2))
                db.session.add_all([c1, c2])

        # ==================== SEED RECOMMENDATIONS ====================
        recs = [
            Recommendation(jenis_perangkat='Komputer / PC', jenis_masalah='Tidak Menyala / Mati Total',
                alat_yang_dibawa='Obeng set\nMultimeter\nKabel power cadangan\nPSU cadangan',
                kemungkinan_penyebab='PSU rusak\nKabel power putus\nMotherboard short circuit',
                langkah_awal='Cek kabel power\nTest dengan PSU lain\nCek lampu indikator motherboard'),
            Recommendation(jenis_perangkat='Printer', jenis_masalah='Tidak Bisa Print',
                alat_yang_dibawa='Kabel USB cadangan\nTinta/Toner cadangan\nDriver USB',
                kemungkinan_penyebab='Driver rusak\nAntrian print stuck\nKabel USB longgar\nTinta habis',
                langkah_awal='Restart printer\nClear print queue\nReinstall driver'),
        ]
        db.session.add_all(recs)
        db.session.commit()
        print("[OK] Seed data berhasil ditambahkan!")
        print("   Admin: admin / admin123")
        print("   Teknisi: teknisi1 / teknisi123")
        print("   Pelapor: siti / user123")

if __name__ == '__main__':
    seed()
