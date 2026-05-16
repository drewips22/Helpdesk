from app.models import Recommendation


def get_recommendation(jenis_perangkat, jenis_masalah):
    """Get recommendation for a specific device and issue type."""
    # Cari rekomendasi spesifik untuk perangkat dan masalah tersebut
    rec = Recommendation.query.filter_by(
        jenis_perangkat=jenis_perangkat,
        jenis_masalah=jenis_masalah
    ).first()

    # Jika tidak ada, fallback ke rekomendasi umum untuk masalah tersebut (Semua Perangkat)
    if not rec:
        rec = Recommendation.query.filter_by(
            jenis_perangkat='Semua Perangkat',
            jenis_masalah=jenis_masalah
        ).first()

    if rec:
        def parse_lines(text):
            if not text:
                return []
            return [line.strip() for line in text.replace('\r\n', '\n').split('\n') if line.strip()]

        return {
            'alat': parse_lines(rec.alat_yang_dibawa),
            'penyebab': parse_lines(rec.kemungkinan_penyebab),
            'langkah': parse_lines(rec.langkah_awal)
        }

    # Default recommendations based on device type
    defaults = get_default_recommendations(jenis_perangkat, jenis_masalah)
    return defaults


def get_default_recommendations(jenis_perangkat, jenis_masalah):
    """Provide default recommendations when no specific data exists."""

    # Base tools always needed
    base_tools = ['Obeng set (+/-)', 'Multimeter', 'Kabel LAN cadangan', 'Flashdisk tools']

    device_tools = {
        'Komputer / PC': ['Thermal paste', 'Compressed air', 'Kabel power cadangan', 'RAM cadangan'],
        'Laptop': ['Charger universal', 'Compressed air', 'Thermal paste', 'SSD/HDD cadangan'],
        'Printer': ['Tinta/Toner cadangan', 'Kabel USB', 'Roller cleaning kit', 'Driver CD/USB'],
        'Scanner': ['Kabel USB', 'Cleaning kit', 'Driver CD/USB'],
        'Monitor': ['Kabel VGA/HDMI cadangan', 'Kabel power cadangan'],
        'Router / Switch': ['Kabel LAN cadangan', 'Kabel console', 'Laptop konfigurasi'],
        'Access Point / WiFi': ['Kabel LAN cadangan', 'PoE injector', 'Laptop konfigurasi'],
        'CCTV': ['Kabel BNC/LAN', 'Power adapter', 'Monitor portabel'],
        'Server': ['RAM cadangan', 'HDD/SSD cadangan', 'Kabel SATA/SAS'],
        'UPS': ['Multimeter', 'Baterai cadangan'],
        'Keyboard / Mouse': ['Baterai cadangan (wireless)', 'Dongle USB tester', 'Cleaning kit'],
        'Telepon / Intercom': ['Kabel RJ11', 'Line tester', 'Handset cadangan'],
        'Proyektor': ['Kabel HDMI/VGA', 'Remote proyektor', 'Compressed air'],
    }

    issue_causes = {
        'Tidak Menyala / Mati Total': ['Power supply rusak', 'Kabel power putus', 'Fuse mati', 'Motherboard/Mainboard rusak'],
        'Lambat / Hang': ['RAM penuh atau bottleneck', 'Storage (HDD/SSD) hampir penuh', 'Infeksi virus/malware', 'Overheating / Throttling'],
        'Blue Screen / Error': ['Driver tidak kompatibel', 'Modul RAM rusak/kotor', 'System files corrupt', 'Suhu komponen terlalu tinggi'],
        'Tidak Bisa Print': ['Driver printer bermasalah', 'Koneksi kabel USB/Jaringan terputus', 'Antrian print (Spooler) stuck', 'Tinta/toner habis atau tersumbat'],
        'Tidak Bisa Konek Internet': ['Kabel LAN putus/longgar', 'Konfigurasi IP/DNS salah', 'Gangguan pada Switch/Router utama', 'Koneksi ISP down'],
        'Virus / Malware': ['Database antivirus usang', 'Menjalankan file dari sumber tidak dikenal', 'Flashdisk/USB eksternal terinfeksi'],
        'Software Error / Crash': ['File instalasi corrupt', 'Konflik dengan aplikasi lain', 'Kebutuhan library/dependensi tidak terpenuhi'],
        'Instalasi Software': ['Spesifikasi hardware tidak mencukupi', 'Lisensi software kedaluwarsa', 'Akses hak administrator (UAC) dibatasi'],
        'Lupa Password': ['Pengguna lupa kredensial', 'Masa berlaku password habis (expired)', 'Akun terkunci karena salah input berturut-turut'],
        'Email Bermasalah': ['Server mail tujuan down', 'Pengaturan port SMTP/IMAP/POP3 tidak sesuai', 'Kapasitas penyimpanan email penuh', 'Koneksi jaringan terblokir firewall'],
        'Kerusakan Fisik': ['Terjatuh atau terbentur benda keras', 'Terkena tumpahan cairan', 'Komponen aus karena faktor usia'],
        'Kabel Putus / Rusak': ['Kabel terjepit perabot/meja', 'Digigit hewan pengerat (tikus)', 'Konektor RJ45/USB patah', 'Kabel tertekuk ekstrem'],
        'Suara Berisik / Overheat': ['Penumpukan debu tebal pada sirip heatsink', 'Kipas/fan pendingin macet atau rusak', 'Sirkulasi udara ruangan/casing terhalang', 'Thermal paste prosesor mengering'],
        'Permintaan Baru': ['Kebutuhan operasional pengguna baru', 'Peningkatan kapasitas (upgrade) sistem', 'Pemasangan jalur koneksi baru'],
        'Lainnya': ['Masalah spesifik/custom yang jarang terjadi', 'Kombinasi beberapa kendala sekaligus', 'Membutuhkan penelusuran lebih mendalam']
    }

    issue_steps = {
        'Tidak Menyala / Mati Total': [
            'Periksa sambungan kabel power ke stopkontak',
            'Coba gunakan kabel power lain yang berfungsi',
            'Periksa indikator lampu LED pada perangkat',
            'Lakukan hard reset (cabut power, tekan tombol power 30 detik)',
            'Gunakan multimeter untuk mengukur tegangan output adaptor'
        ],
        'Lambat / Hang': [
            'Buka Task Manager/Resource Monitor untuk cek penggunaan CPU/RAM',
            'Tutup aplikasi latar belakang yang memakan banyak memori',
            'Periksa sisa kapasitas harddisk (pastikan sisa > 15%)',
            'Lakukan pembersihan file sementara (temp files/cache)',
            'Jadwalkan pemindaian penuh dengan antivirus terupdate'
        ],
        'Blue Screen / Error': [
            'Catat kode error (Stop Code) yang muncul di layar',
            'Boot ke Safe Mode untuk memastikan kestabilan OS',
            'Periksa log event di Windows Event Viewer',
            'Bersihkan pin konektor RAM menggunakan penghapus karet',
            'Lakukan System File Checker (sfc /scannow) di Command Prompt'
        ],
        'Tidak Bisa Print': [
            'Pastikan printer dalam kondisi On dan siap (Ready)',
            'Periksa status koneksi kabel USB atau sambungan Wi-Fi printer',
            'Hapus antrian cetak yang tersendat (Restart Print Spooler)',
            'Cetak halaman pengujian (Test Print) langsung dari printer',
            'Instal ulang driver printer dengan versi terbaru'
        ],
        'Tidak Bisa Konek Internet': [
            'Periksa kedipan lampu indikator LAN pada port NIC',
            'Jalankan perintah ping ke gateway/router lokal',
            'Gunakan fitur Windows Network Troubleshooter',
            'Lakukan pelepasan dan pembaruan IP (ipconfig /release & /renew)',
            'Restart Switch atau Access Point terdekat'
        ],
        'Virus / Malware': [
            'Putuskan koneksi perangkat dari jaringan lokal (isolasi)',
            'Jalankan pembaruan definisi virus secara manual/offline',
            'Lakukan Full Scan menggunakan Windows Defender / Antivirus',
            'Hapus program mencurigakan dari Control Panel',
            'Amankan data penting ke media penyimpanan terpisah'
        ],
        'Software Error / Crash': [
            'Jalankan aplikasi dengan opsi Run as Administrator',
            'Periksa kompatibilitas OS pada Properties aplikasi',
            'Hapus cache spesifik aplikasi di folder AppData',
            'Lakukan perbaikan (Repair) instalasi software',
            'Cek ketersediaan patch atau update dari pengembang'
        ],
        'Instalasi Software': [
            'Verifikasi kecukupan ruang penyimpanan dan RAM',
            'Nonaktifkan sementara antivirus selama proses instalasi',
            'Pastikan installer diunduh utuh (tidak corrupt)',
            'Instal dependensi pendukung (seperti .NET Framework / VCRedist)',
            'Gunakan akun dengan hak akses Administrator penuh'
        ],
        'Lupa Password': [
            'Verifikasi identitas pelapor untuk keamanan data',
            'Gunakan tool reset password administrator lokal jika diizinkan',
            'Arahkan pengguna ke portal self-service reset jika ada',
            'Buka blokir akun (Unlock) melalui Active Directory / Server',
            'Bantu pengguna mengatur ulang password baru yang aman'
        ],
        'Email Bermasalah': [
            'Uji akses webmail melalui browser untuk memastikan server aktif',
            'Verifikasi pengaturan nama server, port, dan SSL/TLS',
            'Pastikan tidak ada salah ketik pada alamat email dan password',
            'Arsipkan email lama untuk melonggarkan kapasitas kuota',
            'Nonaktifkan sementara add-in pihak ketiga di aplikasi klien email'
        ],
        'Kerusakan Fisik': [
            'Amankan perangkat agar tidak membahayakan pengguna',
            'Dokumentasikan area kerusakan dengan foto secara detail',
            'Matikan dan cabut semua sumber daya listrik dari perangkat',
            'Lakukan pembongkaran casing untuk memeriksa internal',
            'Siapkan formulir pengajuan penggantian suku cadang'
        ],
        'Kabel Putus / Rusak': [
            'Telusuri sepanjang jalur kabel untuk menemukan titik kerusakan',
            'Ganti kabel patch cord dengan unit cadangan baru',
            'Gunakan crimping tool untuk memasang ulang konektor RJ45 jika longgar',
            'Gunakan cable tester untuk memverifikasi urutan pin koneksi',
            'Rapikan jalur kabel menggunakan pelindung (cable duct)'
        ],
        'Suara Berisik / Overheat': [
            'Periksa apakah ada kabel internal yang menyentuh baling-baling kipas',
            'Gunakan compressed air untuk meniup debu keluar dari ventilasi',
            'Periksa putaran RPM kipas melalui BIOS atau software monitor',
            'Bongkar heatsink dan ganti thermal paste lama dengan yang baru',
            'Posisikan perangkat di area dengan sirkulasi udara terbuka'
        ],
        'Permintaan Baru': [
            'Lakukan analisis kebutuhan spesifik bersama pelapor',
            'Periksa ketersediaan perangkat atau sumber daya di gudang',
            'Siapkan jalur instalasi dan titik kelistrikan/jaringan yang dibutuhkan',
            'Lakukan konfigurasi dasar dan pengujian fungsionalitas',
            'Berikan orientasi singkat penggunaan kepada pelapor'
        ],
        'Lainnya': [
            'Lakukan wawancara mendalam dengan pelapor mengenai kronologi awal',
            'Periksa seluruh indikator fisik dan log sistem secara menyeluruh',
            'Lakukan riset silang pada basis pengetahuan eksternal',
            'Konsultasikan kendala dengan tim teknisi senior atau vendor',
            'Catat setiap langkah eksperimental yang dilakukan secara rinci'
        ]
    }

    tools = base_tools + device_tools.get(jenis_perangkat, [])
    causes = issue_causes.get(jenis_masalah, [
        'Terjadi kendala pada subsistem internal',
        'Faktor ketidakstabilan pasokan daya atau koneksi',
        'Konfigurasi sistem tidak selaras dengan lingkungan operasional'
    ])

    default_steps = [
        'Lakukan observasi dan identifikasi gejala awal',
        'Periksa integritas sambungan fisik dan suplai daya',
        'Restart sistem untuk menyegarkan memori perangkat',
        'Analisis log sistem untuk melacak sumber masalah',
        'Konsultasikan panduan manual perangkat terkait'
    ]
    steps = issue_steps.get(jenis_masalah, default_steps)

    return {
        'alat': tools,
        'penyebab': causes,
        'langkah': steps
    }

