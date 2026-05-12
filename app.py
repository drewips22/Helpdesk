from app import create_app
from app.extensions import socketio

app = create_app()

import socket

def get_local_ip():
    """Mendeteksi IP address lokal PC yang terhubung ke WiFi/LAN."""
    try:
        # Buka koneksi socket kosong hanya untuk memancing IP lokal keluar
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

if __name__ == '__main__':
    local_ip = get_local_ip()
    print("\n" + "="*50)
    print(">>> SI-TIK Server Berhasil Dijalankan! <<<")
    print(f"Akses dari PC ini  : http://127.0.0.1:5000")
    print(f"Akses dari HP/Lain : http://{local_ip}:5000")
    print("="*50 + "\n")
    
    # host='0.0.0.0' artinya server akan terbuka untuk diakses dari IP manapun di jaringan lokal
    socketio.run(app, host='0.0.0.0', debug=True, port=5000, allow_unsafe_werkzeug=True)
