from app.models import Layanan, Artikel

def seed_initial_data():
    """
    Seeds initial default services and articles into database if table is empty.
    """
    if Layanan.objects.count() == 0:
        layanan_list = [
            {
                'nama': 'Short-form Reels / TikTok / Shorts',
                'kategori': 'social',
                'tag': 'Populer',
                'deskripsi': 'Editing vertikal 9:16 dengan fast pacing, hook 3 detik pertama, animated subtitles, sound effect beat sync, dan trending audio treatment.',
                'harga': 350000,
                'durasi': '1–2 Hari',
                'gambar': 'https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?auto=format&fit=crop&w=600&q=80',
                'urutan': 1,
                'aktif': True
            },
            {
                'nama': 'YouTube Video & Long-form Editing',
                'kategori': 'youtube',
                'tag': 'Best Value',
                'deskripsi': 'Editing sinematik 10–20 menit dengan dynamic b-roll, motion title pop-ups, sound design imersif, dan optimasi retensi penonton.',
                'harga': 650000,
                'durasi': '2–3 Hari',
                'gambar': 'https://images.unsplash.com/photo-1574717024653-61fd2cf4d44d?auto=format&fit=crop&w=600&q=80',
                'urutan': 2,
                'aktif': True
            },
            {
                'nama': 'Commercial & Brand Advertisement',
                'kategori': 'brand',
                'tag': 'Signature',
                'deskripsi': 'Produksi video iklan TVC / digital ads premium dengan color grading profesional (Rec.709/Log), lisensi musik komersial, dan voiceover mastering.',
                'harga': 1500000,
                'durasi': '3–5 Hari',
                'gambar': 'https://images.unsplash.com/photo-1492691527719-9d1e07e534b4?auto=format&fit=crop&w=600&q=80',
                'urutan': 3,
                'aktif': True
            },
            {
                'nama': 'Wedding & Event Highlight Film',
                'kategori': 'event',
                'tag': 'Cinematic',
                'deskripsi': 'Highlight dokumenter emosional berdurasi 3–5 menit dengan storytelling naratif, LUT custom cinematic tone, dan transisi mulus.',
                'harga': 1200000,
                'durasi': '3–5 Hari',
                'gambar': 'https://images.unsplash.com/photo-1519741497674-611481863552?auto=format&fit=crop&w=600&q=80',
                'urutan': 4,
                'aktif': True
            },
            {
                'nama': 'Color Grading & Film Look Mastering',
                'kategori': 'other',
                'tag': 'Technical',
                'deskripsi': 'Koreksi warna profesional dan grading shot-matching di DaVinci Studio dari RAW/ProRes/Log ke standar broadcast dan streaming film.',
                'harga': 500000,
                'durasi': '1–2 Hari',
                'gambar': 'https://images.unsplash.com/photo-1574717024653-61fd2cf4d44d?auto=format&fit=crop&w=800&q=80',
                'urutan': 5,
                'aktif': True
            },
            {
                'nama': 'Motion Graphics & Animated Titles Pack',
                'kategori': 'other',
                'tag': 'Creative',
                'deskripsi': 'Desain animasi lower-thirds, intro, outro, logo bumper, dan infografis 2D yang elegan dan sesuai identitas visual brand Anda.',
                'harga': 450000,
                'durasi': '2 Hari',
                'gambar': 'https://images.unsplash.com/photo-1550745165-9bc0b252726f?auto=format&fit=crop&w=600&q=80',
                'urutan': 6,
                'aktif': True
            },
        ]
        for data in layanan_list:
            Layanan.objects.create(**data)

    if Artikel.objects.count() == 0:
        artikel_list = [
            {
                'judul': 'Pacing dalam Short-form: Cara Menahan Retensi Penonton di 3 Detik Pertama',
                'kategori': 'creative',
                'ringkasan': 'Analisis mendalam teknik audio-visual pacing dan visual hook yang membuat audiens berhenti scrolling di Reels dan TikTok.',
                'konten': 'Di era konten serba cepat, 3 detik pertama adalah penentu apakah audiens akan menonton hingga akhir atau melakukan swipe away. Pacing bukan sekadar memotong video dengan cepat, melainkan menciptakan ritme visual yang sinkron dengan micro-cues emosional penonton. Menggunakan sound effect whoosh yang pas, zoom in dinamis pada punchline, serta teks animasi dengan palet warna berani adalah kunci menaikkan watch-time hingga 80% ke atas.',
                'penulis': 'Dimas Prasetyo (Lead Editor)',
                'estimasi_baca': '3 min read',
                'gambar': 'https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?auto=format&fit=crop&w=600&q=80',
            },
            {
                'judul': 'Color Grading: Memahami Transformasi dari LOG ke Rec.709',
                'kategori': 'technical',
                'ringkasan': 'Panduan esensial bagi editor video untuk mempertahankan dynamic range sensor dan akurasi warna kulit (skin tone).',
                'konten': 'Banyak videografer pemula bingung mengapa video LOG mereka terlihat pudar dan flat. Color science modern memisahkan color correction dari creative grading. Langkah pertama selalu normalisasi color space menggunakan CST (Color Space Transform) di DaVinci Resolve atau LUT vendor resmi seperti Sony S-Log3 ke Rec.709. Pastikan skin tone indicator berada di sepanjang garis vector 11:00 sebelum menerapkan stylized look film split-toning.',
                'penulis': 'FRAMEHAUS Lab',
                'estimasi_baca': '5 min read',
                'gambar': 'https://images.unsplash.com/photo-1574717024653-61fd2cf4d44d?auto=format&fit=crop&w=800&q=80',
            },
            {
                'judul': 'Workflow Editing Cepat: Shortcut & Template yang Menghemat 10+ Jam Per Minggu',
                'kategori': 'production',
                'ringkasan': 'Eksplorasi teknik organisasi project, hotkey mapping, dan proxy rendering yang biasa dipakai studio post-production.',
                'konten': 'Kecepatan editing tidak ditentukan oleh seberapa cepat jari menekan keyboard, tetapi oleh seberapa rapi sistem penamaan aset, struktur timeline, dan otomasi tugas berulang. Dengan memisahkan bin footage, music, sound effects, dan adjustment layers secara konsisten serta menggunakan Q & W ripple edit trimming, editor dapat memangkas 40% durasi rough cut.',
                'penulis': 'Aditya Nugroho',
                'estimasi_baca': '4 min read',
                'gambar': 'https://images.unsplash.com/photo-1492691527719-9d1e07e534b4?auto=format&fit=crop&w=600&q=80',
            },
            {
                'judul': 'Sound Design: 50% dari Jiwa Video Anda',
                'kategori': 'creative',
                'ringkasan': 'Mengapa mixing audio, ambient textures, dan foley mikro menentukan kualitas video kelas industri.',
                'konten': 'George Lucas pernah berucap bahwa suara adalah separuh dari pengalaman menonton film. Dalam video editing modern, sound design bukan sekadar latar belakang musik. Risers, sub-booms, swooshes, dan room ambience memberikan bobot fisikal pada transisi visual yang tampak biasa saja.',
                'penulis': 'FRAMEHAUS Sound Team',
                'estimasi_baca': '4 min read',
                'gambar': 'https://images.unsplash.com/photo-1598488035139-bdbb2231ce04?auto=format&fit=crop&w=600&q=80',
            },
        ]
        for data in artikel_list:
            Artikel.objects.create(**data)

    seed_team_and_settings()
    seed_demo_accounts()


def seed_team_and_settings():
    """
    Initializes default WebSetting and initial AnggotaTim members if none exist.
    """
    from app.models import WebSetting, AnggotaTim
    WebSetting.get_solo()

    if AnggotaTim.objects.count() == 0:
        team_list = [
            {
                'nama': 'Moh Farrel Ardan',
                'role': 'Lead Editor & Creative Director',
                'role_badge': 'FOUNDER & DIRECTOR',
                'foto_url': 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=700&q=80',
                'bio': 'Berpengalaman 8+ tahun memimpin produksi visual naratif komersial, brand storytelling, dan video kampanye berskala nasional.',
                'keahlian': 'Premiere Pro, Directing, Pacing & Cut',
                'social_instagram': 'https://instagram.com',
                'social_linkedin': 'https://linkedin.com',
                'social_behance': 'https://behance.net',
                'email': 'farrel@framehaus.studio',
                'urutan': 1,
                'aktif': True
            },
            {
                'nama': 'Nadia Rahman',
                'role': 'Audio Designer & Foley Specialist',
                'role_badge': 'HEAD OF SOUND',
                'foto_url': 'https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=700&q=80',
                'bio': 'Spesialis mixing audio broadcast, perancangan ambient foley, dialog remastering, dan audio spatial immersive yang menghidupkan setiap scene.',
                'keahlian': 'Pro Tools, Dolby Atmos, iZotope RX',
                'social_instagram': 'https://instagram.com',
                'social_linkedin': 'https://linkedin.com',
                'social_behance': 'https://spotify.com',
                'email': 'nadia@framehaus.studio',
                'urutan': 2,
                'aktif': True
            },
            {
                'nama': 'Rizky Pratama',
                'role': 'Color Grading & Finishing Artist',
                'role_badge': 'LEAD COLORIST',
                'foto_url': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=700&q=80',
                'bio': 'Ahli transformasi ruang warna LOG ke Rec.709, ACES color management, look development sinematik, dan mastering HDR / Dolby Vision.',
                'keahlian': 'DaVinci Resolve, ACEScc, Colorist',
                'social_instagram': 'https://instagram.com',
                'social_linkedin': 'https://linkedin.com',
                'social_behance': 'https://vimeo.com',
                'email': 'rizky@framehaus.studio',
                'urutan': 3,
                'aktif': True
            },
            {
                'nama': 'Dimas Prasetyo',
                'role': 'Motion Designer & 3D Typography',
                'role_badge': 'MOTION & VFX LEAD',
                'foto_url': 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=700&q=80',
                'bio': 'Menciptakan motion graphics modern, kinetik tipografi dinamis, efek visual compositing, dan animasi logo 3D untuk brand global.',
                'keahlian': 'After Effects, Blender 3D, Cinema 4D',
                'social_instagram': 'https://instagram.com',
                'social_linkedin': 'https://linkedin.com',
                'social_behance': 'https://dribbble.com',
                'email': 'dimas@framehaus.studio',
                'urutan': 4,
                'aktif': True
            },
            {
                'nama': 'Maya Anggraini',
                'role': 'Producer & Client Relations',
                'role_badge': 'POST PRODUCER',
                'foto_url': 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=700&q=80',
                'bio': 'Menjamin setiap timeline proyek selesai tepat waktu, alur revisi terstruktur rapi, komunikasi transparan, dan delivery master 4K terverifikasi.',
                'keahlian': 'Pipeline QC, Frame.io, Client Success',
                'social_instagram': 'https://instagram.com',
                'social_linkedin': 'https://linkedin.com',
                'social_behance': 'https://behance.net',
                'email': 'maya@framehaus.studio',
                'urutan': 5,
                'aktif': True
            },
        ]
        for t in team_list:
            AnggotaTim.objects.create(**t)



def seed_demo_accounts():
    """
    Sets up default Admin Demo and User Demo accounts if they do not exist,
    or resets their credentials so they are always guaranteed to work.
    """
    from django.contrib.auth.models import User
    from app.models import UserAdmin, UserPengguna, Provinsi, Pesanan

    # Ensure at least 1 Provinsi exists for profile FK
    provinsi, _ = Provinsi.objects.get_or_create(
        nama_provinsi="Sulawesi Selatan",
        defaults={'aktif': True}
    )

    # 1. Admin Demo Account
    # Username: admin / Email: admin@framehaus.studio / Pass: admin123
    admin_user, _ = User.objects.get_or_create(username="admin")
    admin_user.email = "admin@framehaus.studio"
    admin_user.first_name = "Farrel Ardan"
    admin_user.last_name = "Super Admin"
    admin_user.is_superuser = True
    admin_user.is_staff = True
    admin_user.is_active = True
    admin_user.set_password("admin123")
    admin_user.save()

    UserAdmin.objects.get_or_create(
        username=admin_user,
        defaults={
            'telp': '081234567890',
            'gender': 'Laki-laki',
        }
    )

    # Also update muhfarelardan if exists to share password admin123
    mf_user = User.objects.filter(username="muhfarelardan").first()
    if mf_user:
        mf_user.set_password("admin123")
        mf_user.last_name = "Super Admin"
        mf_user.is_superuser = True
        mf_user.is_staff = True
        mf_user.save()
        UserAdmin.objects.get_or_create(
            username=mf_user,
            defaults={'telp': '081234567890', 'gender': 'Laki-laki'}
        )

    # 2. User Demo Account
    # Username: user / Email: user@framehaus.studio / Pass: user123
    demo_user, _ = User.objects.get_or_create(username="user")
    demo_user.email = "user@framehaus.studio"
    demo_user.first_name = "Nara Rahman"
    demo_user.last_name = "Pengguna"
    demo_user.is_superuser = False
    demo_user.is_staff = False
    demo_user.is_active = True
    demo_user.set_password("user123")
    demo_user.save()

    UserPengguna.objects.get_or_create(
        user=demo_user,
        defaults={
            'telp': '089876543210',
            'gender': 'Perempuan',
            'alamat': 'Jl. Boulevard Panakkukang No. 12, Kota Makassar',
            'provinsi_anggota': provinsi,
            'jafung': 'Creative Producer',
            'nuptk': '20261019882901',
            'bidang_keahlian': 'Brand Video & Digital Media',
            'link_sinta': 'https://sinta.kemdikbud.go.id',
            'link_google_scholar': 'https://scholar.google.com',
        }
    )

    # 3. Create sample orders for demo_user so the dashboard shows real activity
    if Pesanan.objects.filter(user=demo_user).count() == 0:
        Pesanan.objects.create(
            order_id='#FH-2026',
            user=demo_user,
            layanan_nama='Short-form Reels / TikTok / Shorts (x2)',
            total_harga=700000,
            status='In progress',
            kategori='social',
            durasi='1–2 Hari',
            catatan='Video konten fashion campaign musim panas, warna pastel.'
        )
        Pesanan.objects.create(
            order_id='#FH-2027',
            user=demo_user,
            layanan_nama='Commercial & Brand Advertisement',
            total_harga=1500000,
            status='Completed',
            kategori='brand',
            durasi='3–5 Hari',
            catatan='TVC launching produk kopi lokal Makassar, grading Rec.709.'
        )

