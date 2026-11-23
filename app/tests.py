from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from app.models import Provinsi, UserAdmin, UserPengguna, Pesanan, Layanan, Artikel
from app.seed_data import seed_initial_data
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
import io


class FrontEndIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        seed_initial_data()

        # Create or get Provinsi
        self.provinsi, _ = Provinsi.objects.get_or_create(nama_provinsi="Sulawesi Selatan", defaults={'aktif': True})

        # Create dummy image for testing
        image = Image.new('RGB', (100, 100), color='green')
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG')
        buffer.seek(0)
        self.uploaded_photo = SimpleUploadedFile("test.jpg", buffer.read(), content_type="image/jpeg")

        # Create Super Admin
        self.admin_user = User.objects.create_superuser(
            username="admin@framehaus.com",
            email="admin@framehaus.com",
            password="adminpassword123",
            first_name="Admin Framehaus",
            last_name="Super Admin"
        )
        self.user_admin_profile = UserAdmin.objects.create(
            username=self.admin_user,
            telp="08123456789",
            gender="Laki-laki",
            photo=self.uploaded_photo
        )

        # Create Pengguna (Member)
        self.member_user = User.objects.create_user(
            username="member@framehaus.com",
            email="member@framehaus.com",
            password="memberpassword123",
            first_name="Farrel Ardan",
            last_name="Pengguna"
        )
        buffer.seek(0)
        photo2 = SimpleUploadedFile("test2.jpg", buffer.read(), content_type="image/jpeg")
        self.user_pengguna_profile = UserPengguna.objects.create(
            user=self.member_user,
            telp="08987654321",
            gender="Laki-laki",
            alamat="Jl. Perintis Kemerdekaan",
            provinsi_anggota=self.provinsi,
            photo=photo2,
            jafung="Asisten Ahli",
            nuptk="1234567890123456",
            bidang_keahlian="Multimedia & Web",
            link_sinta="https://sinta.kemdikbud.go.id/authors/detail?id=123",
            link_scopus="https://www.scopus.com/authid/detail.uri?authorId=123",
            link_google_scholar="https://scholar.google.com/citations?user=123",
            link_orcid="https://orcid.org/0000-0001-2345-6789"
        )

    def test_homepage_renders(self):
        """Halaman Home terbuka langsung di /"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "FRAMEHAUS")
        self.assertContains(response, "Good stories")
        self.assertContains(response, "Jelajahi Layanan")

    def test_about_page_renders(self):
        """Halaman About terbuka di /about/"""
        response = self.client.get(reverse('about'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A LITTLE ABOUT US")
        self.assertContains(response, "We make ideas")
        self.assertContains(response, "Small details.")

    def test_artikel_page_renders(self):
        """Halaman Artikel terbuka di /artikel/"""
        response = self.client.get(reverse('artikel'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "THE FRAMEHAUS JOURNAL")
        self.assertContains(response, "Pacing dalam Short-form")

    def test_shop_page_renders(self):
        """Halaman Shop terbuka di /shop/ dengan katalog dan kalkulator"""
        response = self.client.get(reverse('shop'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "THE SERVICE MENU")
        self.assertContains(response, "YouTube Video")
        self.assertContains(response, "CUSTOM PACKAGE")

    def test_kontak_page_renders_and_submits(self):
        """Halaman Kontak terbuka di /kontak/ dan dapat mengirim pesan"""
        response = self.client.get(reverse('kontak'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "LET'S TALK")
        self.assertContains(response, "hello@framehaus.studio")

        # Submit contact form
        post_response = self.client.post(reverse('kontak'), {
            'nama': 'Calon Klien',
            'email': 'klien@gmail.com',
            'telepon': '081234567890',
            'layanan': 'Social Media / Reels Editing',
            'pesan': 'Halo, saya ingin memesan 5 video reels.'
        }, follow=True)
        self.assertEqual(post_response.status_code, 200)
        self.assertContains(post_response, "Pesan Anda telah diterima")

    def test_order_without_login_redirects_to_login(self):
        """Pengunjung belum login yang ingin memesan diarahkan ke halaman login"""
        response = self.client.post(reverse('pesan'), {
            'layanan_nama': 'Social Reels Starter',
            'total_harga': '350000'
        }, follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))

    def test_order_with_authenticated_user_creates_database_record(self):
        """User yang sudah login dapat memesan dan pesanan tersimpan ke database"""
        self.client.login(username="member@framehaus.com", password="memberpassword123")
        response = self.client.post(reverse('pesan'), {
            'layanan_nama': 'Social Reels Premium',
            'total_harga': '550000',
            'kategori': 'social',
            'durasi': '3–5 hari',
            'catatan': 'Tolong berikan subtitle dinamis warna kuning.'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Verify Pesanan created in database
        pesanan = Pesanan.objects.filter(user=self.member_user, layanan_nama='Social Reels Premium').first()
        self.assertIsNotNone(pesanan)
        self.assertEqual(pesanan.total_harga, 550000)
        self.assertEqual(pesanan.status, 'In progress')

    def test_admin_dashboard_renders_full_width(self):
        """Dashboard Admin terbuka dengan layout full-width responsif"""
        self.client.login(username="admin@framehaus.com", password="adminpassword123")
        response = self.client.get(reverse('app:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Admin Overview")
        self.assertContains(response, "Total Pengguna")
        self.assertContains(response, "Daftar Pesanan Masuk")

    def test_pengguna_dashboard_renders(self):
        """Dashboard Pengguna menampilkan profil dan daftar pesanan"""
        self.client.login(username="member@framehaus.com", password="memberpassword123")
        response = self.client.get(reverse('app:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dashboard Pengguna")
        self.assertContains(response, "Farrel Ardan")
        self.assertContains(response, "Riwayat Pesanan Layanan Saya")

    def test_admin_user_list_renders(self):
        self.client.login(username="admin@framehaus.com", password="adminpassword123")
        response = self.client.get(reverse('app:user_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Direktori Anggota")
        self.assertContains(response, "Farrel Ardan")

    def test_service_crud_lifecycle_and_frontend_sync(self):
        """Tes lengkap CRUD Layanan: Tambah, Tampil di Frontend Shop, Edit, Toggle, Hapus"""
        from app.models import Layanan
        self.client.login(username="admin@framehaus.com", password="adminpassword123")

        # 1. CREATE
        response = self.client.post(reverse('app:service_create'), {
            'nama': 'Video Podcast Multicam 4K',
            'kategori': 'youtube',
            'tag': 'New 2026',
            'harga': '850000',
            'durasi': '2–4 Hari',
            'deskripsi': 'Editing multicam 3 angle dengan auto audio switching dan noise reduction.',
            'gambar': 'https://images.unsplash.com/photo-1590602847861-f357a9332bbc',
            'urutan': '1',
            'aktif': 'on',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        service = Layanan.objects.filter(nama='Video Podcast Multicam 4K').first()
        self.assertIsNotNone(service)
        self.assertEqual(service.harga, 850000)

        # 2. READ (Frontend Shop should reflect the new service)
        shop_response = self.client.get(reverse('shop'))
        self.assertEqual(shop_response.status_code, 200)
        self.assertContains(shop_response, "Video Podcast Multicam 4K")
        self.assertContains(shop_response, "850000")

        # 3. UPDATE
        edit_response = self.client.post(reverse('app:service_edit', args=[service.id]), {
            'nama': 'Video Podcast Multicam 4K Studio Edit',
            'kategori': 'youtube',
            'tag': 'Super Saver',
            'harga': '900000',
            'durasi': '2 Hari',
            'deskripsi': 'Editing multicam 3 angle versi studio.',
            'gambar': 'https://images.unsplash.com/photo-1590602847861-f357a9332bbc',
            'urutan': '1',
            'aktif': 'on',
        }, follow=True)
        self.assertEqual(edit_response.status_code, 200)
        service.refresh_from_db()
        self.assertEqual(service.nama, 'Video Podcast Multicam 4K Studio Edit')
        self.assertEqual(service.harga, 900000)

        # 4. TOGGLE
        toggle_response = self.client.get(reverse('app:service_toggle_active', args=[service.id]), follow=True)
        self.assertEqual(toggle_response.status_code, 200)
        service.refresh_from_db()
        self.assertFalse(service.aktif)

        # 5. DELETE
        delete_response = self.client.post(reverse('app:service_delete', args=[service.id]), follow=True)
        self.assertEqual(delete_response.status_code, 200)
        self.assertFalse(Layanan.objects.filter(id=service.id).exists())

    def test_article_crud_lifecycle_and_frontend_sync(self):
        """Tes lengkap CRUD Artikel: Buat, Tampil di Frontend Journal, Edit, Hapus"""
        from app.models import Artikel
        self.client.login(username="admin@framehaus.com", password="adminpassword123")

        # 1. CREATE
        response = self.client.post(reverse('app:article_create'), {
            'judul': 'Tutorial Dynamic Masking di DaVinci Resolve',
            'kategori': 'technical',
            'penulis': 'Master Editor',
            'estimasi_baca': '6 min read',
            'ringkasan': 'Teknik isolasi objek bergerak dengan Magic Mask AI.',
            'konten': 'Langkah pertama dalam isolasi subjek adalah memilih frame referensi yang paling jelas...',
            'gambar': 'https://images.unsplash.com/photo-1536240478700-b869070f9279',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        article = Artikel.objects.filter(judul='Tutorial Dynamic Masking di DaVinci Resolve').first()
        self.assertIsNotNone(article)

        # 2. READ (Frontend Artikel Journal should reflect this article)
        journal_response = self.client.get(reverse('artikel'))
        self.assertEqual(journal_response.status_code, 200)
        self.assertContains(journal_response, "Tutorial Dynamic Masking di DaVinci Resolve")

        # 3. UPDATE
        edit_response = self.client.post(reverse('app:article_edit', args=[article.id]), {
            'judul': 'Tutorial Dynamic Masking di DaVinci Resolve Studio 19',
            'kategori': 'technical',
            'penulis': 'Master Editor Lead',
            'estimasi_baca': '7 min read',
            'ringkasan': 'Teknik isolasi objek bergerak dengan Magic Mask AI versi 19.',
            'konten': 'Langkah pertama dalam isolasi subjek versi terbaru...',
            'gambar': 'https://images.unsplash.com/photo-1536240478700-b869070f9279',
        }, follow=True)
        self.assertEqual(edit_response.status_code, 200)
        article.refresh_from_db()
        self.assertEqual(article.judul, 'Tutorial Dynamic Masking di DaVinci Resolve Studio 19')

        # 4. DELETE
        delete_response = self.client.post(reverse('app:article_delete', args=[article.id]), follow=True)
        self.assertEqual(delete_response.status_code, 200)
        self.assertFalse(Artikel.objects.filter(id=article.id).exists())

    def test_artikel_detail_page_and_comment(self):
        """Halaman detail artikel Blogger-style terbuka dan menerima komentar pembaca"""
        article = Artikel.objects.first()
        self.assertIsNotNone(article)

        # GET detail page
        response = self.client.get(reverse('artikel_detail', args=[article.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, article.judul)
        self.assertContains(response, "Journal & Insights")
        self.assertContains(response, "Bagikan:")
        self.assertContains(response, "Diskusi & Komentar")
        self.assertContains(response, "Artikel Populer")

        # POST comment
        comment_res = self.client.post(reverse('artikel_detail', args=[article.id]), {
            'nama': 'Ahmad Fauzi',
            'email': 'ahmad@example.com',
            'pesan': 'Penjelasan color grading sangat mendalam dan mudah dipahami!'
        }, follow=True)
        self.assertEqual(comment_res.status_code, 200)
        self.assertContains(comment_res, "Ahmad Fauzi")
        self.assertContains(comment_res, "Penjelasan color grading sangat mendalam")

    def test_web_settings_crud_and_frontend_sync(self):
        """Tes lengkap Pengaturan Web: Update via Dashboard Admin dan sinkron ke Beranda, About, & Footer"""
        from app.models import WebSetting
        self.client.login(username="admin@framehaus.com", password="adminpassword123")

        # 1. GET Settings page
        response = self.client.get(reverse('app:web_settings'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pengaturan Website & Branding")
        self.assertContains(response, "Brand & Logo")
        self.assertContains(response, "Video Hero & Headline")

        # 2. POST updates
        update_data = {
            'site_name': 'FRAMEHAUS PRO STUDIO',
            'site_tagline': 'Premium Video Finishing & Audio Studio',
            'logo_text': 'FRAMEHAUS PRO',
            'logo_badge': '★',
            'hero_eyebrow': 'AWARD WINNING STUDIO',
            'hero_title_line1': 'Cinematic Stories',
            'hero_title_line2': 'built with surgical precision.',
            'hero_subtitle': 'Kami menghadirkan editing video kelas bioskop untuk kampanye global.',
            'hero_video_url': 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',
            'hero_poster_image': 'https://images.unsplash.com/photo-1574717024653-61fd2cf4d44d?w=1000',
            'hero_badge_text': 'OFFICIAL 2026 EDITION',
            'hero_card_title': 'Feature Film Edit',
            'hero_card_desc': '8K Cinema Finishing',
            'hero_stat_1_num': '500+',
            'hero_stat_1_label': 'Karya Selesai',
            'hero_stat_2_num': '5.0/5',
            'hero_stat_2_label': 'Kepuasan Brand',
            'hero_stat_3_num': '24 jam',
            'hero_stat_3_label': 'First Draft Delivery',
            'work_1_title': 'Master Brand Commercial 2026',
            'work_1_meta': 'GLOBAL SPOT',
            'work_1_image': 'https://images.unsplash.com/photo-1518173946687-a4c8892bbd9f?w=1000',
            'work_2_title': 'High Pacing Reel',
            'work_2_meta': 'TIKTOK VIRAL',
            'work_2_image': 'https://images.unsplash.com/photo-1492619375914-88005aa9e8fb?w=1000',
            'work_3_title': 'Documentary of Makassar',
            'work_3_meta': 'DOCUSERIES',
            'work_3_image': 'https://images.unsplash.com/photo-1485846234645-a62644f84728?w=1000',
            'about_hero_title': 'Crafting Cinematic Moments That Last',
            'about_hero_desc': 'Cerita yang dikurasi dengan presisi seni gambar bergerak.',
            'about_story_heading': 'Filmmaking is about soul, rhythm, and passion.',
            'about_story_text1': 'Setiap frame diperlakukan sebagai kanvas hidup.',
            'about_story_text2': 'Kami bekerja bersama kreator dan produser terbaik.',
            'about_story_image': 'https://images.unsplash.com/photo-1574717024653-61fd2cf4d44d?w=1100',
            'footer_desc': 'Studio editing independen dengan komitmen tanpa kompromi.',
            'studio_status_text': 'CAPACITY: 3 SPOTS OPEN THIS MONTH',
            'address': 'Jl. Sudirman Kav. 1, Jakarta Pusat 10220',
            'operational_hours': 'Senin – Minggu, 24 Jam Online Support',
            'email': 'contact@framehauspro.com',
            'phone_wa': '+6281199887766',
            'social_instagram': 'https://instagram.com/framehauspro',
            'social_youtube': 'https://youtube.com/@framehauspro',
            'social_tiktok': 'https://tiktok.com/@framehauspro',
            'social_linkedin': 'https://linkedin.com/company/framehauspro',
            'social_behance': 'https://behance.net/framehauspro',
            'footer_copyright': '© 2026 FRAMEHAUS PRO STUDIO. ALL RIGHTS RESERVED.',
        }
        post_res = self.client.post(reverse('app:web_settings'), update_data, follow=True)
        self.assertEqual(post_res.status_code, 200)

        # 3. Verify Database
        setting = WebSetting.get_solo()
        self.assertEqual(setting.site_name, 'FRAMEHAUS PRO STUDIO')
        self.assertEqual(setting.hero_title_line1, 'Cinematic Stories')
        self.assertEqual(setting.address, 'Jl. Sudirman Kav. 1, Jakarta Pusat 10220')

        # 4. Verify Frontend Home Page
        home_res = self.client.get(reverse('home'))
        self.assertEqual(home_res.status_code, 200)
        self.assertContains(home_res, 'Cinematic Stories')
        self.assertContains(home_res, 'Master Brand Commercial 2026')
        self.assertContains(home_res, 'FRAMEHAUS PRO STUDIO')
        self.assertContains(home_res, 'Jl. Sudirman Kav. 1, Jakarta Pusat 10220')

        # 5. Verify Frontend About Page
        about_res = self.client.get(reverse('about'))
        self.assertEqual(about_res.status_code, 200)
        self.assertContains(about_res, 'Crafting Cinematic Moments That Last')
        self.assertContains(about_res, 'Filmmaking is about soul')

    def test_team_crud_lifecycle_and_about_sync(self):
        """Tes lengkap CRUD Manajemen Tim: Tambah personil, tampil di About, edit, toggle aktif, hapus"""
        from app.models import AnggotaTim
        self.client.login(username="admin@framehaus.com", password="adminpassword123")

        # 1. GET Team list
        list_res = self.client.get(reverse('app:team_list'))
        self.assertEqual(list_res.status_code, 200)
        self.assertContains(list_res, "Manajemen Tim Studio")

        # 2. CREATE team member
        create_res = self.client.post(reverse('app:team_create'), {
            'nama': 'Budi Santoso',
            'role': 'Senior VFX Compositor',
            'role_badge': 'VFX LEAD',
            'foto_url': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400',
            'bio': 'Spesialis CGI 3D photorealistic dan plate restoration.',
            'keahlian': 'Nuke, Blender, After Effects',
            'social_instagram': 'https://instagram.com/budivfx',
            'social_linkedin': 'https://linkedin.com/in/budivfx',
            'social_behance': 'https://behance.net/budivfx',
            'email': 'budi@framehaus.studio',
            'urutan': '10',
            'aktif': 'on',
        }, follow=True)
        self.assertEqual(create_res.status_code, 200)

        member = AnggotaTim.objects.filter(nama='Budi Santoso').first()
        self.assertIsNotNone(member)
        self.assertEqual(member.role, 'Senior VFX Compositor')

        # 3. VERIFY visible in About page
        about_res = self.client.get(reverse('about'))
        self.assertEqual(about_res.status_code, 200)
        self.assertContains(about_res, 'Budi Santoso')
        self.assertContains(about_res, 'Senior VFX Compositor')
        self.assertContains(about_res, 'VFX LEAD')
        self.assertContains(about_res, 'Nuke')

        # 4. UPDATE team member
        edit_res = self.client.post(reverse('app:team_edit', args=[member.id]), {
            'nama': 'Budi Santoso, M.Sn',
            'role': 'Director of VFX and CGI',
            'role_badge': 'EXECUTIVE VFX',
            'foto_url': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400',
            'bio': 'Spesialis CGI 3D photorealistic dan plate restoration.',
            'keahlian': 'Nuke, Blender, Houdini',
            'social_instagram': 'https://instagram.com/budivfx',
            'social_linkedin': 'https://linkedin.com/in/budivfx',
            'social_behance': 'https://behance.net/budivfx',
            'email': 'budi@framehaus.studio',
            'urutan': '1',
            'aktif': 'on',
        }, follow=True)
        self.assertEqual(edit_res.status_code, 200)
        member.refresh_from_db()
        self.assertEqual(member.nama, 'Budi Santoso, M.Sn')
        self.assertEqual(member.role, 'Director of VFX and CGI')

        # Verify edited in About page
        about_res2 = self.client.get(reverse('about'))
        self.assertContains(about_res2, 'Budi Santoso, M.Sn')
        self.assertContains(about_res2, 'Director of VFX and CGI')

        # 5. TOGGLE active status (Deactivate)
        toggle_res = self.client.get(reverse('app:team_toggle_active', args=[member.id]), follow=True)
        self.assertEqual(toggle_res.status_code, 200)
        member.refresh_from_db()
        self.assertFalse(member.aktif)

        # Inactive member should NOT appear on public About page
        about_res3 = self.client.get(reverse('about'))
        self.assertNotContains(about_res3, 'Budi Santoso, M.Sn')

        # 6. DELETE team member
        del_res = self.client.post(reverse('app:team_delete', args=[member.id]), follow=True)
        self.assertEqual(del_res.status_code, 200)
        self.assertFalse(AnggotaTim.objects.filter(id=member.id).exists())

    def test_service_detail_page_renders_and_actions(self):
        """Halaman detail produk/layanan terbuka di /shop/<id>/ dan /layanan/<id>/ dengan informasi lengkap"""
        service = Layanan.objects.filter(aktif=True).first()
        self.assertIsNotNone(service)

        # 1. GET via /shop/<id>/
        res = self.client.get(reverse('service_detail', args=[service.id]))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, service.nama)
        self.assertContains(res, service.durasi)
        self.assertContains(res, "Tambah ke Keranjang")
        self.assertContains(res, "Chat WhatsApp")
        self.assertContains(res, "Pesan Layanan Ini Sekarang")
        self.assertContains(res, "Alur Pengerjaan Editing di FRAMEHAUS")

        # 2. GET via /layanan/<id>/ alias
        res_alias = self.client.get(reverse('layanan_detail', args=[service.id]))
        self.assertEqual(res_alias.status_code, 200)
        self.assertContains(res_alias, service.nama)

        # 3. Non-existent service returns 404
        res_404 = self.client.get(reverse('service_detail', args=[999999]))
        self.assertEqual(res_404.status_code, 404)

    def test_midtrans_payment_page_and_checkout_flow(self):
        """Uji flow pemesanan layanan yang langsung mengarahkan ke halaman pembayaran Midtrans"""
        self.client.login(username="member@framehaus.com", password="memberpassword123")

        # 1. Pesan layanan
        res = self.client.post(reverse('pesan'), {
            'layanan_nama': 'Brand Commercial Editing',
            'total_harga': '5500000',
            'kategori': 'Commercial & Brand Ads',
            'durasi': '3–5 Hari',
            'catatan': 'Color grade filmic teal and orange'
        })
        self.assertEqual(res.status_code, 302)

        # Cari pesanan yang baru dibuat
        pesanan = Pesanan.objects.filter(user=self.member_user, layanan_nama='Brand Commercial Editing').first()
        self.assertIsNotNone(pesanan)
        self.assertEqual(pesanan.total_harga, 5500000)

        # Redirect target harus ke halaman pembayaran
        expected_url = reverse('payment_page', args=[pesanan.clean_order_id])
        self.assertIn(pesanan.clean_order_id, res.url)

        # 2. Buka halaman pembayaran
        pay_res = self.client.get(expected_url)
        self.assertEqual(pay_res.status_code, 200)
        self.assertContains(pay_res, pesanan.order_id)
        self.assertContains(pay_res, "Detail Pesanan Layanan")
        self.assertContains(pay_res, "Midtrans Sandbox Payment Gateway")
        self.assertContains(pay_res, "TOTAL TAGIHAN")
        self.assertContains(pay_res, "5500000")

    def test_midtrans_webhook_notification_settlement(self):
        """Uji notifikasi webhook dari Midtrans dengan signature SHA-512"""
        from app.midtrans import get_midtrans_config
        import hashlib
        import json

        pesanan = Pesanan.objects.create(
            order_id="#FH-9876",
            user=self.member_user,
            layanan_nama="Color Grading Feature",
            total_harga=2500000,
            payment_status="pending"
        )

        cfg = get_midtrans_config()
        server_key = cfg['server_key']
        clean_id = pesanan.clean_order_id
        gross_amount = "2500000.00"
        status_code = "200"

        # Hitung SHA512 signature
        sig_str = f"{clean_id}{status_code}{gross_amount}{server_key}"
        signature_key = hashlib.sha512(sig_str.encode('utf-8')).hexdigest()

        payload = {
            "order_id": clean_id,
            "status_code": status_code,
            "gross_amount": gross_amount,
            "signature_key": signature_key,
            "transaction_status": "settlement",
            "fraud_status": "accept",
            "payment_type": "bank_transfer",
            "transaction_id": "midtrans-txn-12345"
        }

        webhook_res = self.client.post(
            reverse('payment_notification'),
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(webhook_res.status_code, 200)

        pesanan.refresh_from_db()
        self.assertEqual(pesanan.payment_status, "settlement")
        self.assertEqual(pesanan.payment_type, "bank_transfer")
        self.assertEqual(pesanan.midtrans_transaction_id, "midtrans-txn-12345")
        self.assertTrue(pesanan.is_paid)

    def test_payment_finish_page_renders(self):
        """Halaman konfirmasi pembayaran /payment/finish/ menampilkan ringkasan nota"""
        pesanan = Pesanan.objects.create(
            order_id="#FH-4321",
            user=self.member_user,
            layanan_nama="Sound Design Mix",
            total_harga=750000,
            payment_status="settlement"
        )
        res = self.client.get(f"{reverse('payment_finish')}?order_id={pesanan.clean_order_id}&status_code=200&transaction_status=settlement")
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Pembayaran Berhasil!")
        self.assertContains(res, pesanan.order_id)
        self.assertContains(res, "Sound Design Mix")
        self.assertContains(res, "750000")

    def test_payment_sandbox_simulation(self):
        """Uji fitur simulasi pembayaran sandbox instan"""
        self.client.login(username="member@framehaus.com", password="memberpassword123")
        pesanan = Pesanan.objects.create(
            order_id="#FH-5555",
            user=self.member_user,
            layanan_nama="Color Grading Demo",
            total_harga=1200000,
            payment_status="pending"
        )
        res = self.client.post(reverse('payment_simulate_sandbox', args=[pesanan.clean_order_id]), {
            'method': 'BCA Virtual Account (Sandbox)'
        }, follow=True)
        self.assertEqual(res.status_code, 200)
        pesanan.refresh_from_db()
        self.assertEqual(pesanan.payment_status, "settlement")
        self.assertTrue(pesanan.is_paid)

    def test_pesan_with_google_drive_footage(self):
        """Pemesanan layanan dengan bahan footage tautan Google Drive"""
        self.client.login(username="member@framehaus.com", password="memberpassword123")
        post_data = {
            'layanan_nama': 'YouTube Video Editing',
            'total_harga': 450000,
            'kategori': 'Long-form Video',
            'durasi': '3-5 Hari',
            'catatan': 'Tolong potong bagian hening di awal',
            'upload_method': 'drive',
            'video_link': 'https://drive.google.com/drive/folders/sample-client-footage-123'
        }
        res = self.client.post(reverse('pesan'), post_data, follow=True)
        self.assertEqual(res.status_code, 200)

        pesanan = Pesanan.objects.filter(video_link='https://drive.google.com/drive/folders/sample-client-footage-123').first()
        self.assertIsNotNone(pesanan)
        self.assertEqual(pesanan.upload_method, 'drive')
        self.assertTrue(pesanan.has_footage)

        # Cek apakah halaman pembayaran menampilkan tautan Drive
        pay_res = self.client.get(reverse('payment_page', args=[pesanan.clean_order_id]))
        self.assertEqual(pay_res.status_code, 200)
        self.assertContains(pay_res, 'Tautan Google Drive / Cloud')
        self.assertContains(pay_res, 'https://drive.google.com/drive/folders/sample-client-footage-123')

    def test_pesan_with_direct_video_file(self):
        """Pemesanan layanan dengan upload file video mentahan langsung"""
        self.client.login(username="member@framehaus.com", password="memberpassword123")
        dummy_video = SimpleUploadedFile("client_clip.mp4", b"dummy_video_stream_binary", content_type="video/mp4")
        post_data = {
            'layanan_nama': 'Reels TikTok Dynamic',
            'total_harga': 250000,
            'kategori': 'Social Media',
            'durasi': '1-2 Hari',
            'catatan': 'Tambahkan subtitle otomatis',
            'upload_method': 'file',
            'video_file': dummy_video
        }
        res = self.client.post(reverse('pesan'), post_data, follow=True)
        self.assertEqual(res.status_code, 200)

        pesanan = Pesanan.objects.filter(layanan_nama='Reels TikTok Dynamic').first()
        self.assertIsNotNone(pesanan)
        self.assertEqual(pesanan.upload_method, 'file')
        self.assertTrue(pesanan.has_footage)
        self.assertIn('client_clip', pesanan.footage_filename)

        # Cek apakah halaman pembayaran menampilkan file video terunggah
        pay_res = self.client.get(reverse('payment_page', args=[pesanan.clean_order_id]))
        self.assertEqual(pay_res.status_code, 200)
        self.assertContains(pay_res, 'File Video Terunggah')
        self.assertContains(pay_res, 'client_clip')

    def test_pesan_upload_footage_update_endpoint(self):
        """Pelanggan mengunggah atau memperbarui footage setelah pesanan dibuat"""
        self.client.login(username="member@framehaus.com", password="memberpassword123")
        pesanan = Pesanan.objects.create(
            order_id="#FH-7788",
            user=self.member_user,
            layanan_nama="Short Film Edit",
            total_harga=1500000,
            upload_method='drive'
        )
        self.assertFalse(pesanan.has_footage)

        update_data = {
            'upload_method': 'drive',
            'video_link': 'https://drive.google.com/drive/folders/updated-raw-footage-456'
        }
        res = self.client.post(reverse('pesan_upload_footage', args=[pesanan.clean_order_id]), update_data, follow=True)
        self.assertEqual(res.status_code, 200)

        pesanan.refresh_from_db()
        self.assertEqual(pesanan.video_link, 'https://drive.google.com/drive/folders/updated-raw-footage-456')
        self.assertTrue(pesanan.has_footage)

    def test_dashboards_render_footage_columns(self):
        """Dashboard Pengguna dan Admin menampilkan kolom footage dengan tepat"""
        pesanan = Pesanan.objects.create(
            order_id="#FH-9900",
            user=self.member_user,
            layanan_nama="Documentary Cut",
            total_harga=3000000,
            upload_method='drive',
            video_link='https://drive.google.com/drive/folders/documentary-files'
        )

        # Pengguna Dashboard
        self.client.login(username="member@framehaus.com", password="memberpassword123")
        user_dash_res = self.client.get(reverse('app:dashboard'))
        self.assertEqual(user_dash_res.status_code, 200)
        self.assertContains(user_dash_res, "Bahan Video (Footage)")
        self.assertContains(user_dash_res, "Link Drive ↗")

        # Admin Dashboard
        self.client.login(username="admin@framehaus.com", password="adminpassword123")
        admin_dash_res = self.client.get(reverse('app:dashboard'))
        self.assertEqual(admin_dash_res.status_code, 200)
        self.assertContains(admin_dash_res, "Footage Klien")
        self.assertContains(admin_dash_res, "Buka Drive ↗")

    def test_service_detail_buttons_and_whatsapp_link(self):
        """Memverifikasi bahwa tombol Tambah ke Keranjang, Chat WhatsApp, dan Pesan Sekarang berfungsi di service_detail"""
        service = Layanan.objects.create(
            nama="Short-form Reels / TikTok / Shorts",
            kategori="social",
            harga=10000,
            durasi="1-2 Hari",
            deskripsi="Jasa editing video vertikal profesional untuk TikTok dan Reels.",
            aktif=True
        )

        res = self.client.get(reverse('service_detail', args=[service.id]))
        self.assertEqual(res.status_code, 200)
        # Tombol Tambah ke Keranjang
        self.assertContains(res, 'btn-add-cart')
        self.assertContains(res, 'Tambah ke Keranjang')
        self.assertContains(res, 'addToCart')

        # Tombol Chat WhatsApp
        self.assertContains(res, 'btn-wa-chat')
        self.assertContains(res, 'Chat WhatsApp')
        self.assertContains(res, 'handleWhatsAppChat')
        self.assertContains(res, 'api.whatsapp.com')

        # Tombol Pesan Layanan Ini Sekarang
        self.assertContains(res, 'btn-direct-order')
        self.assertContains(res, 'Pesan Layanan Ini Sekarang')
        self.assertContains(res, 'directOrderNow')

    def test_web_setting_clean_wa_number(self):
        """Memverifikasi pembersihan nomor WhatsApp otomatis ke format internasional 628..."""
        from app.models import WebSetting
        ws = WebSetting.objects.first() or WebSetting.objects.create()

        ws.phone_wa = "+62 812-3456-7890"
        self.assertEqual(ws.clean_wa_number, "6281234567890")

        ws.phone_wa = "0852-9988-7766"
        self.assertEqual(ws.clean_wa_number, "6285299887766")

        ws.phone_wa = "8123456789"
        self.assertEqual(ws.clean_wa_number, "628123456789")






