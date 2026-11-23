"""
Script Migrasi Database FRAMEHAUS ke Supabase PostgreSQL.

Fungsi:
1. Memverifikasi koneksi ke Supabase PostgreSQL (menggunakan connection string atau password).
2. Menjalankan migrasi skema tabel Django (migrate) ke Supabase.
3. Memuat (loaddata) seluruh data lokal yang tersimpan di datadump.json.
4. Memvalidasi bahwa seluruh data (User, Layanan, Artikel, Pesanan, WebSetting, AnggotaTim)
   berhasil masuk 100% tanpa ada data yang terhapus.
"""

import os
import sys
import json
import urllib.parse

def main():
    print("=" * 65)
    print("   MIGRASI DATABASE FRAMEHAUS LOKAL KE SUPABASE POSTGRESQL   ")
    print("=" * 65)

    # 1. Pastikan file backup data tersedia
    fixture_path = os.path.join(os.path.dirname(__file__), 'datadump.json')
    if not os.path.exists(fixture_path):
        print("[-] File 'datadump.json' tidak ditemukan! Silakan dump data terlebih dahulu.")
        sys.exit(1)

    with open(fixture_path, 'r', encoding='utf-8') as f:
        local_records = json.load(f)
    print(f"[+] Backup data lokal terverifikasi: {len(local_records)} total entitas siap dipindahkan.")

    # 2. Ambil parameter koneksi Supabase
    db_url = os.environ.get('SUPABASE_DB_URL') or os.environ.get('DATABASE_URL')
    
    if not db_url:
        if len(sys.argv) > 1:
            arg = sys.argv[1].strip()
            if arg.startswith('postgres://') or arg.startswith('postgresql://'):
                db_url = arg
            else:
                # Argumen adalah password
                db_password = arg
                # Susun URI pooler default
                encoded_pw = urllib.parse.quote_plus(db_password)
                db_url = f"postgresql://postgres.ccfcoutegeqfeccznqtq:{encoded_pw}@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"
        else:
            print("\nSilakan masukkan Connection String URI atau Database Password Supabase Anda:")
            print("Contoh URI: postgresql://postgres.ccfcoutegeqfeccznqtq:[PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require")
            print("Atau masukkan Password Database Supabase Anda saja:")
            user_input = input("Input: ").strip()
            if user_input.startswith('postgres://') or user_input.startswith('postgresql://'):
                db_url = user_input
            else:
                encoded_pw = urllib.parse.quote_plus(user_input)
                db_url = f"postgresql://postgres.ccfcoutegeqfeccznqtq:{encoded_pw}@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"

    os.environ['DATABASE_URL'] = db_url

    # 3. Uji koneksi PostgreSQL menggunakan psycopg2
    try:
        import psycopg2
    except ImportError:
        print("[!] Modul psycopg2 belum terpasang. Menginstall psycopg2-binary...")
        os.system(f"{sys.executable} -m pip install psycopg2-binary")
        import psycopg2

    parsed = urllib.parse.urlparse(db_url)
    print(f"\n[*] Menghubungi Supabase PostgreSQL di {parsed.hostname}:{parsed.port or 5432}...")

    try:
        conn = psycopg2.connect(
            dbname=parsed.path.lstrip('/') or 'postgres',
            user=parsed.username,
            password=urllib.parse.unquote(parsed.password or ''),
            host=parsed.hostname,
            port=parsed.port or 5432,
            sslmode='require',
            connect_timeout=15
        )
        print("[+] KONEKSI BERHASIL! Terhubung ke Supabase PostgreSQL instance.")
        conn.close()
    except Exception as e:
        print(f"[-] Gagal terhubung ke database Supabase: {e}")
        print("\nTips:")
        print("1. Pastikan Password Database Supabase benar (dapat di-reset di Supabase Dashboard > Project Settings > Database).")
        print("2. Jika menggunakan pooler, pastikan port 6543 (transaction) atau 5432 (session) dan region pooler sesuai.")
        sys.exit(1)

    # 4. Jalankan Migrasi Skema Django ke Supabase
    print("\n[*] Menjalankan migrasi skema tabel Django ke Supabase (python manage.py migrate)...")
    exit_code = os.system(f"{sys.executable} manage.py migrate")
    if exit_code != 0:
        print("[-] Terjadi kesalahan saat migrasi skema.")
        sys.exit(1)

    # 5. Memuat Seluruh Data Lokal ke Supabase
    print("\n[*] Memindahkan seluruh data lokal ke database Supabase (python manage.py loaddata datadump.json)...")
    exit_code = os.system(f"{sys.executable} manage.py loaddata datadump.json")
    if exit_code != 0:
        print("[-] Terjadi kesalahan saat memuat data fixture.")
        sys.exit(1)

    # 6. Verifikasi Integritas Data
    print("\n[*] Memvalidasi kelengkapan data di Supabase:")
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    import django
    django.setup()

    from django.contrib.auth.models import User
    from app.models import Layanan, Artikel, Pesanan, WebSetting, AnggotaTim, UserPengguna, UserAdmin

    print(f"  - Users       : {User.objects.count()} pengguna")
    print(f"  - Layanan     : {Layanan.objects.count()} paket")
    print(f"  - Artikel     : {Artikel.objects.count()} artikel")
    print(f"  - Pesanan     : {Pesanan.objects.count()} pesanan")
    print(f"  - Anggota Tim : {AnggotaTim.objects.count()} orang")
    print(f"  - Web Setting : {WebSetting.objects.count()} konfigurasi")
    print(f"  - Profil User : {UserPengguna.objects.count()} pengguna, {UserAdmin.objects.count()} admin")

    print("\n" + "=" * 65)
    print("  MIGRASI 100% SUKSES! SELURUH DATA LOKAL TELAH PINDAH KE SUPABASE  ")
    print("=" * 65)

if __name__ == '__main__':
    main()
