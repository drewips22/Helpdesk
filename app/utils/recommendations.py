from app.models import Recommendation


def get_recommendation(jenis_perangkat, jenis_masalah):
    """Get recommendation for a specific device and issue type."""
    rec = Recommendation.query.filter_by(
        jenis_perangkat=jenis_perangkat,
        jenis_masalah=jenis_masalah
    ).first()

    if rec:
        return {
            'alat': rec.alat_yang_dibawa.split('\n') if rec.alat_yang_dibawa else [],
            'penyebab': rec.kemungkinan_penyebab.split('\n') if rec.kemungkinan_penyebab else [],
            'langkah': rec.langkah_awal.split('\n') if rec.langkah_awal else []
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
    }

    issue_causes = {
        'Tidak Menyala / Mati Total': ['Power supply rusak', 'Kabel power putus', 'Fuse mati', 'Motherboard rusak'],
        'Lambat / Hang': ['RAM penuh', 'HDD hampir penuh', 'Virus/malware', 'Terlalu banyak startup program'],
        'Blue Screen / Error': ['Driver tidak kompatibel', 'RAM rusak', 'HDD bad sector', 'Overheating'],
        'Tidak Bisa Print': ['Driver printer', 'Kabel USB longgar', 'Antrian print stuck', 'Tinta/toner habis'],
        'Tidak Bisa Konek Internet': ['Kabel LAN putus', 'IP conflict', 'DNS bermasalah', 'Router/switch down'],
        'Virus / Malware': ['Antivirus tidak update', 'Download dari sumber tidak aman', 'USB terinfeksi'],
        'Software Error / Crash': ['Software corrupt', 'File system rusak', 'Versi tidak kompatibel'],
        'Instalasi Software': ['Spesifikasi tidak memenuhi', 'Lisensi tidak valid', 'Dependency kurang'],
        'Lupa Password': ['User lupa', 'Password expired', 'Akun terkunci'],
        'Kerusakan Fisik': ['Jatuh/terbentur', 'Terkena air', 'Aus/usang'],
    }

    tools = base_tools + device_tools.get(jenis_perangkat, [])
    causes = issue_causes.get(jenis_masalah, ['Perlu investigasi lebih lanjut'])

    return {
        'alat': tools,
        'penyebab': causes,
        'langkah': [
            'Cek kondisi fisik perangkat',
            'Cek kabel dan koneksi',
            'Restart perangkat',
            'Cek log error',
            'Dokumentasikan temuan'
        ]
    }
