from django.db import models
from django.contrib.auth.models import User
import uuid
from django.utils import timezone
import os
from django.conf import settings

User.add_to_class("__str__", lambda self: f"{self.username} - {self.first_name}")

class Provinsi(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nama_provinsi = models.CharField(max_length=100, unique=True, verbose_name='Nama Provinsi')
    aktif = models.BooleanField(default=True, verbose_name='Aktif')

    class Meta:
        verbose_name = 'Provinsi'
        verbose_name_plural = 'Provinsi'
        ordering = ['nama_provinsi']

    def __str__(self):
        return f"{self.nama_provinsi}"

def rename_photo_anggota(instance, filename):
    ext = filename.split('.')[-1]
    username = instance.user.username
    timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
    new_filename = f"{username}_{timestamp}.{ext}"
    return os.path.join('img_profile/anggota/', new_filename)

class UserPengguna(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)    
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name="anggota")
    telp = models.CharField(max_length=15)
    gender = models.CharField(max_length=15, null=True, blank=True, choices=[
        ('Laki-laki', 'Laki-laki'),
        ('Perempuan', 'Perempuan'),
    ]) 
    alamat = models.CharField(max_length=50, null=True, blank=True)
    photo = models.ImageField(upload_to=rename_photo_anggota, null=True, blank=True)
    provinsi_anggota = models.ForeignKey(Provinsi, on_delete=models.SET_NULL, null=True, blank=True)
    jafung = models.CharField(max_length=100, null=True, blank=True)
    nuptk = models.CharField(max_length=20, null=True, blank=True, verbose_name='NUPTK')
    bidang_keahlian = models.CharField(max_length=100, null=True, blank=True)
    link_sinta = models.URLField(max_length=200, verbose_name='Link Sinta')
    link_scopus = models.URLField(max_length=200, null=True, blank=True, verbose_name='Link Scopus')
    link_google_scholar = models.URLField(max_length=200, null=True, blank=True, verbose_name='Link Google Scholar')
    link_orcid = models.URLField(max_length=200, null=True, blank=True, verbose_name='Link ORCID')


    class Meta:
        verbose_name = 'Anggota'
        verbose_name_plural = 'Anggota'

    def save(self, *args, **kwargs):
        try:
            old_instance = UserPengguna.objects.get(pk=self.pk)
            if old_instance.photo and old_instance.photo != self.photo:
                old_photo_path = os.path.join(
                    settings.MEDIA_ROOT,
                    old_instance.photo.name
                )
                if os.path.isfile(old_photo_path):
                    os.remove(old_photo_path)
        except UserPengguna.DoesNotExist:
            pass
        super().save(*args, **kwargs)

def rename_photo_admin(instance, filename):
    ext = filename.split('.')[-1]
    username = instance.username
    timestamp = timezone.now().strftime('%Y%m%d%H%M%S') 
    new_filename = f"{username}_{timestamp}.{ext}"
    return os.path.join('img_profile/admin/', new_filename)  


class UserAdmin(models.Model):
    username = models.OneToOneField(User, on_delete=models.CASCADE, to_field="username", primary_key=True)
    telp = models.CharField(max_length=15)
    gender = models.CharField(max_length=15, choices=[
        ('Laki-laki', 'Laki-laki'),
        ('Perempuan', 'Perempuan'),
    ])
    photo = models.ImageField(upload_to=rename_photo_admin)

    def save(self, *args, **kwargs):
        try:
            old_instance = UserAdmin.objects.get(pk=self.pk)
            if old_instance.photo and old_instance.photo != self.photo:
                old_photo_path = os.path.join(settings.MEDIA_ROOT, old_instance.photo.name)
                if os.path.isfile(old_photo_path):
                    os.remove(old_photo_path)
        except UserAdmin.DoesNotExist:
            pass  

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username}"


class Pesanan(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In progress', 'In progress'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('unpaid', 'Belum Bayar'),
        ('pending', 'Menunggu Pembayaran'),
        ('settlement', 'Lunas / Berhasil'),
        ('cancel', 'Dibatalkan'),
        ('expire', 'Kedaluwarsa'),
    ]

    order_id = models.CharField(max_length=30, unique=True, verbose_name="Order ID")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="pesanan")
    layanan_nama = models.CharField(max_length=255, verbose_name="Nama Layanan")
    kategori = models.CharField(max_length=100, blank=True, null=True, verbose_name="Kategori")
    durasi = models.CharField(max_length=100, blank=True, null=True, verbose_name="Estimasi Durasi")
    total_harga = models.BigIntegerField(default=0, verbose_name="Total Harga")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='In progress')
    catatan = models.TextField(blank=True, null=True, verbose_name="Catatan Pesanan")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Tanggal Pesan")

    # Midtrans Payment Fields
    payment_status = models.CharField(max_length=50, choices=PAYMENT_STATUS_CHOICES, default='unpaid', verbose_name="Status Pembayaran")
    payment_type = models.CharField(max_length=50, blank=True, null=True, verbose_name="Metode Pembayaran")
    payment_time = models.DateTimeField(blank=True, null=True, verbose_name="Waktu Pembayaran")
    snap_token = models.CharField(max_length=255, blank=True, null=True, verbose_name="Midtrans Snap Token")
    snap_redirect_url = models.CharField(max_length=500, blank=True, null=True, verbose_name="Midtrans Redirect URL")
    midtrans_transaction_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="ID Transaksi Midtrans")
    midtrans_response = models.TextField(blank=True, null=True, verbose_name="Raw Midtrans Response")

    # Customer Video Footage Fields (Google Drive Link atau Upload File Langsung)
    UPLOAD_METHOD_CHOICES = [
        ('drive', 'Link Google Drive / Cloud'),
        ('file', 'Upload File Video Langsung'),
    ]
    upload_method = models.CharField(max_length=20, default='drive', choices=UPLOAD_METHOD_CHOICES, verbose_name="Metode Kirim Footage")
    video_link = models.URLField(max_length=500, blank=True, null=True, verbose_name="Link Google Drive / Cloud Footage")
    video_file = models.FileField(upload_to='pesanan/footage/', blank=True, null=True, verbose_name="File Video Footage Upload")

    class Meta:
        verbose_name = "Pesanan"
        verbose_name_plural = "Pesanan"
        ordering = ['-created_at']

    @property
    def has_footage(self):
        return bool(self.video_link or self.video_file)

    @property
    def footage_filename(self):
        if self.video_file:
            return os.path.basename(self.video_file.name)
        return ""

    @property
    def clean_order_id(self):
        return self.order_id.replace('#', '')

    @property
    def is_paid(self):
        return self.payment_status in ['settlement', 'capture', 'paid']

    def save(self, *args, **kwargs):
        if not self.order_id:
            import random
            order_number = random.randint(1000, 9999)
            gen_id = f"#FH-{order_number}"
            while Pesanan.objects.filter(order_id=gen_id).exists():
                order_number = random.randint(1000, 9999)
                gen_id = f"#FH-{order_number}"
            self.order_id = gen_id
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order_id} - {self.layanan_nama} ({self.user.first_name or self.user.username})"


class Layanan(models.Model):
    KATEGORI_CHOICES = [
        ('social', 'Social Media / Reels'),
        ('youtube', 'YouTube & Podcasts'),
        ('brand', 'Commercial & Brand Ads'),
        ('event', 'Wedding & Event Film'),
        ('other', 'Creative & Color Grading'),
    ]

    nama = models.CharField(max_length=150, verbose_name="Nama Layanan")
    kategori = models.CharField(max_length=50, choices=KATEGORI_CHOICES, default='social', verbose_name="Kategori")
    tag = models.CharField(max_length=50, default='Populer', verbose_name="Tag / Badge")
    deskripsi = models.TextField(verbose_name="Deskripsi Layanan")
    harga = models.BigIntegerField(default=0, verbose_name="Harga (IDR)")
    durasi = models.CharField(max_length=50, default="1–2 Hari", verbose_name="Estimasi Pengerjaan")
    gambar = models.CharField(max_length=500, blank=True, null=True, verbose_name="URL Gambar / Path")
    foto = models.ImageField(upload_to='layanan/', blank=True, null=True, verbose_name="Upload Gambar")
    urutan = models.IntegerField(default=0, verbose_name="Urutan Tampil")
    aktif = models.BooleanField(default=True, verbose_name="Status Aktif")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Layanan"
        verbose_name_plural = "Layanan"
        ordering = ['urutan', 'id']

    def __str__(self):
        return f"{self.nama} - Rp {self.harga:,}"

    def get_image_url(self):
        if self.foto:
            return self.foto.url
        if self.gambar:
            return self.gambar
        return "https://images.unsplash.com/photo-1574717024653-61fd2cf4d44d?auto=format&fit=crop&w=600&q=80"


class Artikel(models.Model):
    KATEGORI_CHOICES = [
        ('creative', 'Editorial & Creative'),
        ('production', 'Production & Workflow'),
        ('trends', 'Industry & Trends'),
        ('technical', 'Color & Technical'),
    ]

    judul = models.CharField(max_length=200, verbose_name="Judul Artikel")
    kategori = models.CharField(max_length=50, choices=KATEGORI_CHOICES, default='creative', verbose_name="Kategori")
    ringkasan = models.TextField(verbose_name="Ringkasan Singkat")
    konten = models.TextField(verbose_name="Konten Lengkap")
    penulis = models.CharField(max_length=100, default="FRAMEHAUS Editorial", verbose_name="Penulis")
    estimasi_baca = models.CharField(max_length=50, default="4 min read", verbose_name="Estimasi Baca")
    gambar = models.CharField(max_length=500, blank=True, null=True, verbose_name="URL Gambar / Path")
    foto = models.ImageField(upload_to='artikel/', blank=True, null=True, verbose_name="Upload Gambar")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Artikel"
        verbose_name_plural = "Artikel"
        ordering = ['-created_at']

    def __str__(self):
        return self.judul

    def get_image_url(self):
        if self.foto:
            return self.foto.url
        if self.gambar:
            return self.gambar
        return "https://images.unsplash.com/photo-1574717024653-61fd2cf4d44d?auto=format&fit=crop&w=800&q=80"


class KomentarArtikel(models.Model):
    artikel = models.ForeignKey(Artikel, on_delete=models.CASCADE, related_name='komentar')
    nama = models.CharField(max_length=100, verbose_name="Nama Komentator")
    email = models.EmailField(verbose_name="Email Komentator")
    pesan = models.TextField(verbose_name="Isi Komentar")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Komentar Artikel"
        verbose_name_plural = "Komentar Artikel"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.nama} on {self.artikel.judul}"


def rename_web_logo(instance, filename):
    ext = filename.split('.')[-1]
    return f"site/logo_{timezone.now().strftime('%Y%m%d%H%M%S')}.{ext}"


def rename_team_photo(instance, filename):
    ext = filename.split('.')[-1]
    safe_name = instance.nama.lower().replace(' ', '_') if instance.nama else 'member'
    return f"team/{safe_name}_{timezone.now().strftime('%Y%m%d%H%M%S')}.{ext}"


class WebSetting(models.Model):
    # 1. Identity & Branding
    site_name = models.CharField(max_length=100, default="FRAMEHAUS", verbose_name="Nama Website")
    site_tagline = models.CharField(max_length=200, default="Creative Video Editing & Color Studio", verbose_name="Tagline Website")
    logo_text = models.CharField(max_length=50, default="FRAMEHAUS", verbose_name="Teks Logo")
    logo_badge = models.CharField(max_length=10, default="®", verbose_name="Simbol / Badge Logo")
    logo_image = models.ImageField(upload_to=rename_web_logo, null=True, blank=True, verbose_name="Upload Logo (Opsional)")

    # 2. Hero Section (Home)
    hero_eyebrow = models.CharField(max_length=100, default="THE CREATIVE EDITING HOUSE", verbose_name="Eyebrow Hero")
    hero_title_line1 = models.CharField(max_length=150, default="Good stories", verbose_name="Judul Hero Baris 1")
    hero_title_line2 = models.CharField(max_length=150, default="deserve a great cut.", verbose_name="Judul Hero Baris 2")
    hero_subtitle = models.TextField(
        default="Kami mengubah footage mentah menjadi video yang punya cerita, karakter, dan alasan untuk ditonton sampai akhir. Untuk kreator, brand, dan bisnis yang ingin tampil beda.",
        verbose_name="Deskripsi Hero"
    )
    hero_video_url = models.CharField(
        max_length=500,
        default="https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
        verbose_name="URL Video Hero (MP4)"
    )
    hero_video_file = models.FileField(upload_to='site/video/', null=True, blank=True, verbose_name="Upload File Video Hero (.mp4)")
    hero_poster_image = models.CharField(
        max_length=500,
        default="https://images.unsplash.com/photo-1492619375914-88005aa9e8fb?auto=format&fit=crop&w=1200&q=85",
        verbose_name="URL Gambar Poster Hero"
    )
    hero_poster_file = models.ImageField(upload_to='site/poster/', null=True, blank=True, verbose_name="Upload File Poster Hero")
    hero_badge_text = models.CharField(max_length=100, default="CREATIVE IN EVERY FRAME", verbose_name="Teks Badge Hero")
    hero_card_label = models.CharField(max_length=100, default="CURRENTLY EDITING", verbose_name="Label Kartu Hero")
    hero_card_title = models.CharField(max_length=100, default="Brand Film 01", verbose_name="Judul Kartu Hero")
    hero_card_desc = models.CharField(max_length=150, default="Color grading · Sound design", verbose_name="Deskripsi Kartu Hero")
    hero_stat_1_num = models.CharField(max_length=50, default="350+", verbose_name="Statistik 1 Angka")
    hero_stat_1_label = models.CharField(max_length=100, default="Video selesai", verbose_name="Statistik 1 Label")
    hero_stat_2_num = models.CharField(max_length=50, default="4.9/5", verbose_name="Statistik 2 Angka")
    hero_stat_2_label = models.CharField(max_length=100, default="Rating klien", verbose_name="Statistik 2 Label")
    hero_stat_3_num = models.CharField(max_length=50, default="48 jam", verbose_name="Statistik 3 Angka")
    hero_stat_3_label = models.CharField(max_length=100, default="Mulai proses", verbose_name="Statistik 3 Label")

    # 3. Selected Work Section Images & Titles (Home)
    work_1_title = models.CharField(max_length=150, default="Beyond the ordinary.", verbose_name="Karya 1 Judul")
    work_1_meta = models.CharField(max_length=100, default="BRAND FILM · 2026", verbose_name="Karya 1 Meta")
    work_1_image = models.CharField(max_length=500, default="https://images.unsplash.com/photo-1518173946687-a4c8892bbd9f?auto=format&fit=crop&w=1200&q=85", verbose_name="Karya 1 URL Gambar")
    work_1_file = models.ImageField(upload_to='site/work/', null=True, blank=True, verbose_name="Upload Gambar Karya 1")
    
    work_2_title = models.CharField(max_length=150, default="Made to be remembered.", verbose_name="Karya 2 Judul")
    work_2_meta = models.CharField(max_length=100, default="SOCIAL CAMPAIGN", verbose_name="Karya 2 Meta")
    work_2_image = models.CharField(max_length=500, default="https://images.unsplash.com/photo-1492619375914-88005aa9e8fb?auto=format&fit=crop&w=900&q=85", verbose_name="Karya 2 URL Gambar")
    work_2_file = models.ImageField(upload_to='site/work/', null=True, blank=True, verbose_name="Upload Gambar Karya 2")

    work_3_title = models.CharField(max_length=150, default="Moments that matter.", verbose_name="Karya 3 Judul")
    work_3_meta = models.CharField(max_length=100, default="DOCUMENTARY", verbose_name="Karya 3 Meta")
    work_3_image = models.CharField(max_length=500, default="https://images.unsplash.com/photo-1485846234645-a62644f84728?auto=format&fit=crop&w=900&q=85", verbose_name="Karya 3 URL Gambar")
    work_3_file = models.ImageField(upload_to='site/work/', null=True, blank=True, verbose_name="Upload Gambar Karya 3")

    # 4. About Page Story
    about_hero_title = models.CharField(max_length=150, default="We make ideas move people.", verbose_name="Judul Hero About")
    about_hero_desc = models.TextField(
        default="FRAMEHAUS adalah creative video editing studio independen yang percaya bahwa setiap detik rekaman punya potensi untuk menjadi cerita visual yang kuat dan berkesan.",
        verbose_name="Deskripsi Hero About"
    )
    about_story_heading = models.CharField(max_length=200, default="It's not just about cutting clips. It's about creating a feeling.", verbose_name="Judul Cerita Studio")
    about_story_text1 = models.TextField(
        default="Kami menggabungkan storytelling, ritme visual, sound design, dan detail yang presisi untuk menghasilkan video yang bukan hanya terlihat bagus, tetapi juga terasa tepat di mata dan hati penonton.",
        verbose_name="Paragraf Cerita 1"
    )
    about_story_text2 = models.TextField(
        default="Mulai dari kreator independen hingga brand yang sedang berkembang pesat, kami hadir sebagai partner kreatif yang membuat proses produksi post-editing lebih mudah, transparan, dan menyenangkan.",
        verbose_name="Paragraf Cerita 2"
    )
    about_story_image = models.CharField(
        max_length=500,
        default="https://images.unsplash.com/photo-1574717024653-61fd2cf4d44d?auto=format&fit=crop&w=1100&q=85",
        verbose_name="URL Gambar Studio About"
    )
    about_story_file = models.ImageField(upload_to='site/about/', null=True, blank=True, verbose_name="Upload Gambar Studio About")

    # 5. Footer & Contacts
    footer_desc = models.TextField(
        default="Creative video editing & color grading studio. Kami menyunting footage mentah menjadi karya visual berkarakter kuat untuk brand, kreator, dan filmmaker independen.",
        verbose_name="Deskripsi Footer"
    )
    studio_status_text = models.CharField(max_length=150, default="STUDIO STATUS: READY FOR NEW PROJECTS", verbose_name="Teks Status Studio")
    address = models.CharField(max_length=255, default="Jl. A.P. Pettarani No. 88, Panakkukang, Kota Makassar, Sulawesi Selatan 90222", verbose_name="Alamat Studio")
    operational_hours = models.CharField(max_length=150, default="Senin – Sabtu, 09.00 – 20.00 WITA (Fast Response)", verbose_name="Jam Operasional")
    email = models.CharField(max_length=100, default="hello@framehaus.studio", verbose_name="Email Studio")
    phone_wa = models.CharField(max_length=50, default="+6281234567890", verbose_name="Nomor WhatsApp Studio")
    social_instagram = models.CharField(max_length=200, default="https://instagram.com", verbose_name="URL Instagram")
    social_youtube = models.CharField(max_length=200, default="https://youtube.com", verbose_name="URL YouTube")
    social_tiktok = models.CharField(max_length=200, default="https://tiktok.com", verbose_name="URL TikTok")
    social_linkedin = models.CharField(max_length=200, default="https://linkedin.com", verbose_name="URL LinkedIn")
    social_behance = models.CharField(max_length=200, default="https://behance.net", verbose_name="URL Behance")
    footer_copyright = models.CharField(max_length=200, default="© 2026 FRAMEHAUS STUDIO. SELURUH HAK CIPTA DILINDUNGI.", verbose_name="Teks Copyright Footer")

    # 6. Midtrans Payment Gateway
    midtrans_server_key = models.CharField(
        max_length=255,
        default="SB-Mid-server-huy54.WVwscvTpLWU_BUjJf4",
        verbose_name="Midtrans Server Key"
    )
    midtrans_client_key = models.CharField(
        max_length=255,
        default="",
        blank=True,
        verbose_name="Midtrans Client Key (Opsional)"
    )
    midtrans_is_production = models.BooleanField(
        default=False,
        verbose_name="Mode Produksi Midtrans"
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pengaturan Web"
        verbose_name_plural = "Pengaturan Web"

    def __str__(self):
        return f"{self.site_name} Settings (Updated {self.updated_at.strftime('%Y-%m-%d %H:%M') if self.updated_at else ''})"

    def get_logo_url(self):
        if self.logo_image:
            return self.logo_image.url
        return None

    def get_hero_video_url(self):
        if self.hero_video_file:
            return self.hero_video_file.url
        return self.hero_video_url or "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4"

    def get_hero_poster_url(self):
        if self.hero_poster_file:
            return self.hero_poster_file.url
        return self.hero_poster_image or "https://images.unsplash.com/photo-1492619375914-88005aa9e8fb?auto=format&fit=crop&w=1200&q=85"

    def get_work_1_img(self):
        if self.work_1_file:
            return self.work_1_file.url
        return self.work_1_image or "https://images.unsplash.com/photo-1518173946687-a4c8892bbd9f?auto=format&fit=crop&w=1200&q=85"

    def get_work_2_img(self):
        if self.work_2_file:
            return self.work_2_file.url
        return self.work_2_image or "https://images.unsplash.com/photo-1492619375914-88005aa9e8fb?auto=format&fit=crop&w=900&q=85"

    def get_work_3_img(self):
        if self.work_3_file:
            return self.work_3_file.url
        return self.work_3_image or "https://images.unsplash.com/photo-1485846234645-a62644f84728?auto=format&fit=crop&w=900&q=85"

    def get_about_story_img(self):
        if self.about_story_file:
            return self.about_story_file.url
        return self.about_story_image or "https://images.unsplash.com/photo-1574717024653-61fd2cf4d44d?auto=format&fit=crop&w=1100&q=85"

    @classmethod
    def get_solo(cls):
        obj, created = cls.objects.get_or_create(id=1)
        return obj

    @property
    def clean_wa_number(self):
        """Mengembalikan nomor WA bersih hanya angka untuk wa.me / api.whatsapp.com (misal 6281234567890)."""
        raw = str(self.phone_wa or '6281234567890')
        digits = ''.join(c for c in raw if c.isdigit())
        if digits.startswith('08'):
            digits = '628' + digits[2:]
        elif digits.startswith('8'):
            digits = '628' + digits[1:]
        return digits or '6281234567890'


class AnggotaTim(models.Model):
    nama = models.CharField(max_length=100, verbose_name="Nama Anggota")
    role = models.CharField(max_length=100, verbose_name="Role / Jabatan")
    role_badge = models.CharField(max_length=50, default="CREATIVE TEAM", verbose_name="Lencana Badge")
    foto = models.ImageField(upload_to=rename_team_photo, null=True, blank=True, verbose_name="Upload Foto")
    foto_url = models.CharField(max_length=500, blank=True, default="", verbose_name="URL Foto (jika tidak upload)")
    bio = models.TextField(verbose_name="Bio Singkat")
    keahlian = models.CharField(max_length=255, default="", verbose_name="Keahlian / Software (pisahkan koma)")
    social_instagram = models.CharField(max_length=200, blank=True, default="", verbose_name="Instagram URL")
    social_linkedin = models.CharField(max_length=200, blank=True, default="", verbose_name="LinkedIn URL")
    social_behance = models.CharField(max_length=200, blank=True, default="", verbose_name="Behance / Vimeo URL")
    email = models.CharField(max_length=100, blank=True, default="", verbose_name="Email")
    urutan = models.IntegerField(default=1, verbose_name="Urutan Tampil")
    aktif = models.BooleanField(default=True, verbose_name="Aktif Ditampilkan")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Anggota Tim"
        verbose_name_plural = "Anggota Tim"
        ordering = ['urutan', 'id']

    def __str__(self):
        return f"{self.nama} ({self.role})"

    def get_photo_url(self):
        if self.foto:
            return self.foto.url
        if self.foto_url:
            return self.foto_url
        return "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=700&q=80"

    def get_keahlian_list(self):
        if not self.keahlian:
            return []
        return [k.strip() for k in self.keahlian.split(',') if k.strip()]




