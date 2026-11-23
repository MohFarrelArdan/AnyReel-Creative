from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from app.models import UserAdmin, UserPengguna, Pesanan, Layanan, Artikel, WebSetting, AnggotaTim
from .form_admin import formProfile
from app.decorators_admin import admin_required


@admin_required
def profile_admin(request):
    try:
        useradmin = UserAdmin.objects.get(username=request.user)
    except UserAdmin.DoesNotExist:
        useradmin = UserAdmin(username=request.user)

    if request.method == 'POST':
        form = formProfile(request.POST, request.FILES, instance=useradmin)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil Anda berhasil diperbarui!')
            return redirect('app:profile_admin')
        else:
            messages.error(request, 'Gagal memperbarui profil. Periksa isian form.')
    else:
        form = formProfile(instance=useradmin)

    context = {
        'title': 'Profile Admin',
        'heading': 'Edit Profile Admin',
        'useradmin': useradmin,
        'photo': useradmin.photo if getattr(useradmin, 'photo', None) else None,
        'form': form,
    }
    return render(request, 'admin_super/profile_admin.html', context)


@admin_required
def user_list(request):
    search = request.GET.get('search', '').strip()
    users = User.objects.filter(last_name='Pengguna').order_by('date_joined')
    if search:
        users = users.filter(first_name__icontains=search) | users.filter(email__icontains=search)

    user_data = []
    for u in users:
        pengguna = UserPengguna.objects.filter(user=u).first()
        user_data.append({
            'user': u,
            'pengguna': pengguna,
        })

    context = {
        'title': 'Manajemen User',
        'heading': 'Manajemen User',
        'user_data': user_data,
        'search': search,
        'total': users.count(),
    }
    return render(request, 'admin_super/user_list.html', context)


@admin_required
def user_edit(request, user_id):
    user = get_object_or_404(User, pk=user_id, last_name='Pengguna')
    pengguna = UserPengguna.objects.filter(user=user).first()

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        is_active = request.POST.get('is_active') == 'on'
        new_password = request.POST.get('new_password', '').strip()

        if email and email != user.email:
            if User.objects.filter(email=email).exclude(pk=user_id).exists():
                messages.error(request, 'Email sudah digunakan oleh user lain.')
                return redirect('app:user_edit', user_id=user_id)
            user.username = email
            user.email = email

        user.first_name = first_name
        user.is_active = is_active
        if new_password:
            user.set_password(new_password)
        user.save()
        messages.success(request, f'Data user {user.first_name} berhasil diperbarui!')
        return redirect('app:user_list')

    context = {
        'title': 'Edit User',
        'heading': 'Edit Data User',
        'edit_user': user,
        'pengguna': pengguna,
    }
    return render(request, 'admin_super/user_edit.html', context)


@admin_required
def user_delete(request, user_id):
    user = get_object_or_404(User, pk=user_id, last_name='Pengguna')
    if request.method == 'POST':
        name = user.first_name
        user.delete()
        messages.success(request, f'User {name} berhasil dihapus.')
    return redirect('app:user_list')


@admin_required
def user_toggle_active(request, user_id):
    user = get_object_or_404(User, pk=user_id, last_name='Pengguna')
    user.is_active = not user.is_active
    user.save()
    status = 'diaktifkan' if user.is_active else 'dinonaktifkan'
    messages.success(request, f'User {user.first_name} berhasil {status}.')
    return redirect('app:user_list')


# ==========================================
# LAYANAN (SERVICES) CRUD
# ==========================================
@admin_required
def service_list(request):
    search = request.GET.get('search', '').strip()
    kategori = request.GET.get('kategori', '').strip()
    services = Layanan.objects.all().order_by('urutan', 'id')
    if search:
        services = services.filter(nama__icontains=search) | services.filter(deskripsi__icontains=search)
    if kategori:
        services = services.filter(kategori=kategori)

    context = {
        'title': 'Manajemen Layanan',
        'heading': 'Manajemen Layanan Studio',
        'services': services,
        'search': search,
        'kategori': kategori,
        'total': services.count(),
    }
    return render(request, 'admin_super/service_list.html', context)


def parse_rupiah_amount(raw_val, default=0):
    """Membersihkan format rupiah seperti 'Rp 350.000', '350.000', '350,000' menjadi int bersih."""
    if raw_val is None:
        return default
    clean = str(raw_val).replace('Rp', '').replace('rp', '').replace('RP', '').replace('.', '').replace(',', '').replace(' ', '').strip()
    try:
        val = int(clean)
        return max(0, val)
    except (ValueError, TypeError):
        return default


@admin_required
def service_create(request):
    if request.method == 'POST':
        nama = request.POST.get('nama', '').strip()
        kategori = request.POST.get('kategori', 'social')
        tag = request.POST.get('tag', 'Populer').strip()
        harga = parse_rupiah_amount(request.POST.get('harga'))
        durasi = request.POST.get('durasi', '1–2 Hari').strip()
        deskripsi = request.POST.get('deskripsi', '').strip()
        gambar = request.POST.get('gambar', '').strip()
        urutan = int(request.POST.get('urutan', 0) or 0)
        aktif = request.POST.get('aktif') == 'on'

        if not nama or harga < 0:
            messages.error(request, 'Nama layanan dan nominal harga valid (minimal 0) wajib diisi!')
            return render(request, 'admin_super/service_form.html', {
                'title': 'Tambah Layanan',
                'action': 'create',
                'categories': Layanan.KATEGORI_CHOICES,
            })

        try:
            Layanan.objects.create(
                nama=nama,
                kategori=kategori,
                tag=tag,
                harga=harga,
                durasi=durasi,
                deskripsi=deskripsi,
                gambar=gambar,
                foto=request.FILES.get('foto'),
                urutan=urutan,
                aktif=aktif,
            )
            messages.success(request, f'Layanan "{nama}" berhasil ditambahkan ke database & katalog!')
            return redirect('app:service_list')
        except Exception as e:
            messages.error(request, f'Gagal menambahkan layanan: {e}')
            return render(request, 'admin_super/service_form.html', {
                'title': 'Tambah Layanan',
                'action': 'create',
                'categories': Layanan.KATEGORI_CHOICES,
            })

    return render(request, 'admin_super/service_form.html', {
        'title': 'Tambah Layanan',
        'action': 'create',
        'categories': Layanan.KATEGORI_CHOICES,
    })


@admin_required
def service_edit(request, service_id):
    service = get_object_or_404(Layanan, pk=service_id)
    if request.method == 'POST':
        service.nama = request.POST.get('nama', '').strip()
        service.kategori = request.POST.get('kategori', 'social')
        service.tag = request.POST.get('tag', 'Populer').strip()
        service.harga = parse_rupiah_amount(request.POST.get('harga'))
        service.durasi = request.POST.get('durasi', '1–2 Hari').strip()
        service.deskripsi = request.POST.get('deskripsi', '').strip()
        service.gambar = request.POST.get('gambar', '').strip()
        service.urutan = int(request.POST.get('urutan', 0) or 0)
        service.aktif = request.POST.get('aktif') == 'on'

        if 'foto' in request.FILES:
            service.foto = request.FILES['foto']

        if not service.nama or service.harga < 0:
            messages.error(request, 'Nama layanan dan nominal harga valid (minimal 0) wajib diisi!')
            return render(request, 'admin_super/service_form.html', {
                'title': 'Edit Layanan',
                'action': 'edit',
                'service': service,
                'categories': Layanan.KATEGORI_CHOICES,
            })

        try:
            service.save()
            messages.success(request, f'Layanan "{service.nama}" berhasil diperbarui!')
            return redirect('app:service_list')
        except Exception as e:
            messages.error(request, f'Gagal memperbarui layanan: {e}')
            return render(request, 'admin_super/service_form.html', {
                'title': 'Edit Layanan',
                'action': 'edit',
                'service': service,
                'categories': Layanan.KATEGORI_CHOICES,
            })

    return render(request, 'admin_super/service_form.html', {
        'title': 'Edit Layanan',
        'action': 'edit',
        'service': service,
        'categories': Layanan.KATEGORI_CHOICES,
    })


@admin_required
def service_delete(request, service_id):
    service = get_object_or_404(Layanan, pk=service_id)
    if request.method == 'POST':
        nama = service.nama
        service.delete()
        messages.success(request, f'Layanan "{nama}" berhasil dihapus dari database.')
    return redirect('app:service_list')


@admin_required
def service_toggle_active(request, service_id):
    service = get_object_or_404(Layanan, pk=service_id)
    service.aktif = not service.aktif
    service.save()
    status = 'diaktifkan' if service.aktif else 'dinonaktifkan'
    messages.success(request, f'Layanan "{service.nama}" berhasil {status}.')
    return redirect('app:service_list')


# ==========================================
# ARTIKEL (ARTICLES) CRUD
# ==========================================
@admin_required
def article_list(request):
    search = request.GET.get('search', '').strip()
    kategori = request.GET.get('kategori', '').strip()
    articles = Artikel.objects.all().order_by('-created_at')
    if search:
        articles = articles.filter(judul__icontains=search) | articles.filter(ringkasan__icontains=search)
    if kategori:
        articles = articles.filter(kategori=kategori)

    context = {
        'title': 'Manajemen Artikel & Journal',
        'heading': 'Manajemen Artikel & Journal',
        'articles': articles,
        'search': search,
        'kategori': kategori,
        'total': articles.count(),
    }
    return render(request, 'admin_super/article_list.html', context)


@admin_required
def article_create(request):
    if request.method == 'POST':
        judul = request.POST.get('judul', '').strip()
        kategori = request.POST.get('kategori', 'creative')
        ringkasan = request.POST.get('ringkasan', '').strip()
        konten = request.POST.get('konten', '').strip()
        penulis = request.POST.get('penulis', 'FRAMEHAUS Editorial').strip()
        estimasi_baca = request.POST.get('estimasi_baca', '4 min read').strip()
        gambar = request.POST.get('gambar', '').strip()

        if not judul or not ringkasan or not konten:
            messages.error(request, 'Judul, ringkasan, dan konten wajib diisi!')
            return render(request, 'admin_super/article_form.html', {
                'title': 'Tulis Artikel Baru',
                'action': 'create',
                'categories': Artikel.KATEGORI_CHOICES,
            })

        Artikel.objects.create(
            judul=judul,
            kategori=kategori,
            ringkasan=ringkasan,
            konten=konten,
            penulis=penulis,
            estimasi_baca=estimasi_baca,
            gambar=gambar,
        )
        messages.success(request, f'Artikel "{judul}" berhasil dipublikasikan ke website!')
        return redirect('app:article_list')

    return render(request, 'admin_super/article_form.html', {
        'title': 'Tulis Artikel Baru',
        'action': 'create',
        'categories': Artikel.KATEGORI_CHOICES,
    })


@admin_required
def article_edit(request, article_id):
    article = get_object_or_404(Artikel, pk=article_id)
    if request.method == 'POST':
        article.judul = request.POST.get('judul', '').strip()
        article.kategori = request.POST.get('kategori', 'creative')
        article.ringkasan = request.POST.get('ringkasan', '').strip()
        article.konten = request.POST.get('konten', '').strip()
        article.penulis = request.POST.get('penulis', 'FRAMEHAUS Editorial').strip()
        article.estimasi_baca = request.POST.get('estimasi_baca', '4 min read').strip()
        article.gambar = request.POST.get('gambar', '').strip()
        article.save()

        messages.success(request, f'Artikel "{article.judul}" berhasil diperbarui!')
        return redirect('app:article_list')

    return render(request, 'admin_super/article_form.html', {
        'title': 'Edit Artikel',
        'action': 'edit',
        'article': article,
        'categories': Artikel.KATEGORI_CHOICES,
    })


@admin_required
def article_delete(request, article_id):
    article = get_object_or_404(Artikel, pk=article_id)
    if request.method == 'POST':
        judul = article.judul
        article.delete()
        messages.success(request, f'Artikel "{judul}" berhasil dihapus dari database.')
    return redirect('app:article_list')


# ==========================================
# ORDERS (PESANAN) MANAGEMENT
# ==========================================
@admin_required
def order_status_update(request, order_id):
    order = get_object_or_404(Pesanan, order_id=order_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['Pending', 'In progress', 'Completed', 'Cancelled']:
            order.status = new_status
            order.save()
            messages.success(request, f"Status pesanan {order.order_id} berhasil diubah menjadi {new_status}.")
    return redirect('app:dashboard')


@admin_required
def order_delete(request, order_id):
    order = get_object_or_404(Pesanan, order_id=order_id)
    if request.method == 'POST':
        oid = order.order_id
        order.delete()
        messages.success(request, f'Pesanan {oid} berhasil dihapus.')
    return redirect('app:dashboard')


# ==========================================
# WEBSITE SETTINGS (CMS)
# ==========================================
@admin_required
def web_settings(request):
    setting = WebSetting.get_solo()

    if request.method == 'POST':
        # 1. Identity & Branding
        setting.site_name = request.POST.get('site_name', setting.site_name).strip()
        setting.site_tagline = request.POST.get('site_tagline', setting.site_tagline).strip()
        setting.logo_text = request.POST.get('logo_text', setting.logo_text).strip()
        setting.logo_badge = request.POST.get('logo_badge', setting.logo_badge).strip()
        if 'logo_image' in request.FILES:
            setting.logo_image = request.FILES['logo_image']

        # 2. Hero Section
        setting.hero_eyebrow = request.POST.get('hero_eyebrow', setting.hero_eyebrow).strip()
        setting.hero_title_line1 = request.POST.get('hero_title_line1', setting.hero_title_line1).strip()
        setting.hero_title_line2 = request.POST.get('hero_title_line2', setting.hero_title_line2).strip()
        setting.hero_subtitle = request.POST.get('hero_subtitle', setting.hero_subtitle).strip()
        setting.hero_video_url = request.POST.get('hero_video_url', setting.hero_video_url).strip()
        if 'hero_video_file' in request.FILES:
            setting.hero_video_file = request.FILES['hero_video_file']
        setting.hero_poster_image = request.POST.get('hero_poster_image', setting.hero_poster_image).strip()
        if 'hero_poster_file' in request.FILES:
            setting.hero_poster_file = request.FILES['hero_poster_file']
        setting.hero_badge_text = request.POST.get('hero_badge_text', setting.hero_badge_text).strip()
        setting.hero_card_title = request.POST.get('hero_card_title', setting.hero_card_title).strip()
        setting.hero_card_desc = request.POST.get('hero_card_desc', setting.hero_card_desc).strip()
        setting.hero_stat_1_num = request.POST.get('hero_stat_1_num', setting.hero_stat_1_num).strip()
        setting.hero_stat_1_label = request.POST.get('hero_stat_1_label', setting.hero_stat_1_label).strip()
        setting.hero_stat_2_num = request.POST.get('hero_stat_2_num', setting.hero_stat_2_num).strip()
        setting.hero_stat_2_label = request.POST.get('hero_stat_2_label', setting.hero_stat_2_label).strip()
        setting.hero_stat_3_num = request.POST.get('hero_stat_3_num', setting.hero_stat_3_num).strip()
        setting.hero_stat_3_label = request.POST.get('hero_stat_3_label', setting.hero_stat_3_label).strip()

        # 3. Selected Work Section
        setting.work_1_title = request.POST.get('work_1_title', setting.work_1_title).strip()
        setting.work_1_meta = request.POST.get('work_1_meta', setting.work_1_meta).strip()
        setting.work_1_image = request.POST.get('work_1_image', setting.work_1_image).strip()
        if 'work_1_file' in request.FILES:
            setting.work_1_file = request.FILES['work_1_file']

        setting.work_2_title = request.POST.get('work_2_title', setting.work_2_title).strip()
        setting.work_2_meta = request.POST.get('work_2_meta', setting.work_2_meta).strip()
        setting.work_2_image = request.POST.get('work_2_image', setting.work_2_image).strip()
        if 'work_2_file' in request.FILES:
            setting.work_2_file = request.FILES['work_2_file']

        setting.work_3_title = request.POST.get('work_3_title', setting.work_3_title).strip()
        setting.work_3_meta = request.POST.get('work_3_meta', setting.work_3_meta).strip()
        setting.work_3_image = request.POST.get('work_3_image', setting.work_3_image).strip()
        if 'work_3_file' in request.FILES:
            setting.work_3_file = request.FILES['work_3_file']

        # 4. About Story
        setting.about_hero_title = request.POST.get('about_hero_title', setting.about_hero_title).strip()
        setting.about_hero_desc = request.POST.get('about_hero_desc', setting.about_hero_desc).strip()
        setting.about_story_heading = request.POST.get('about_story_heading', setting.about_story_heading).strip()
        setting.about_story_text1 = request.POST.get('about_story_text1', setting.about_story_text1).strip()
        setting.about_story_text2 = request.POST.get('about_story_text2', setting.about_story_text2).strip()
        setting.about_story_image = request.POST.get('about_story_image', setting.about_story_image).strip()
        if 'about_story_file' in request.FILES:
            setting.about_story_file = request.FILES['about_story_file']

        # 5. Footer & Contacts
        setting.footer_desc = request.POST.get('footer_desc', setting.footer_desc).strip()
        setting.studio_status_text = request.POST.get('studio_status_text', setting.studio_status_text).strip()
        setting.address = request.POST.get('address', setting.address).strip()
        setting.operational_hours = request.POST.get('operational_hours', setting.operational_hours).strip()
        setting.email = request.POST.get('email', setting.email).strip()
        setting.phone_wa = request.POST.get('phone_wa', setting.phone_wa).strip()
        setting.social_instagram = request.POST.get('social_instagram', setting.social_instagram).strip()
        setting.social_youtube = request.POST.get('social_youtube', setting.social_youtube).strip()
        setting.social_tiktok = request.POST.get('social_tiktok', setting.social_tiktok).strip()
        setting.social_linkedin = request.POST.get('social_linkedin', setting.social_linkedin).strip()
        setting.social_behance = request.POST.get('social_behance', setting.social_behance).strip()
        setting.footer_copyright = request.POST.get('footer_copyright', setting.footer_copyright).strip()

        # 6. Midtrans Payment Gateway
        if 'midtrans_server_key' in request.POST:
            setting.midtrans_server_key = request.POST.get('midtrans_server_key', '').strip() or 'SB-Mid-server-J.j-PoUUXZKyfZ8dZKsSxkB'
        if 'midtrans_client_key' in request.POST:
            setting.midtrans_client_key = request.POST.get('midtrans_client_key', '').strip()
        if 'midtrans_is_production' in request.POST:
            setting.midtrans_is_production = request.POST.get('midtrans_is_production') == 'on'
        else:
            if 'midtrans_server_key' in request.POST:
                setting.midtrans_is_production = False

        setting.save()
        messages.success(request, 'Pengaturan Website berhasil disimpan dan langsung diterapkan ke seluruh halaman!')
        return redirect('app:web_settings')

    team_members = AnggotaTim.objects.all().order_by('urutan', 'id')
    return render(request, 'admin_super/web_settings.html', {
        'title': 'Pengaturan Web',
        'heading': 'Pengaturan Website & Branding',
        'setting': setting,
        'team_members': team_members,
    })


# ==========================================
# TEAM MANAGEMENT (CRUD)
# ==========================================
@admin_required
def team_list(request):
    members = AnggotaTim.objects.all().order_by('urutan', 'id')
    return render(request, 'admin_super/team_list.html', {
        'title': 'Manajemen Tim',
        'heading': 'Kelola Anggota Tim Studio',
        'members': members,
        'total': members.count(),
    })


@admin_required
def team_create(request):
    if request.method == 'POST':
        nama = request.POST.get('nama', '').strip()
        role = request.POST.get('role', '').strip()
        role_badge = request.POST.get('role_badge', 'CREATIVE TEAM').strip()
        foto_url = request.POST.get('foto_url', '').strip()
        bio = request.POST.get('bio', '').strip()
        keahlian = request.POST.get('keahlian', '').strip()
        social_instagram = request.POST.get('social_instagram', '').strip()
        social_linkedin = request.POST.get('social_linkedin', '').strip()
        social_behance = request.POST.get('social_behance', '').strip()
        email = request.POST.get('email', '').strip()
        urutan = int(request.POST.get('urutan') or 1)
        aktif = request.POST.get('aktif') == 'on'

        member = AnggotaTim(
            nama=nama,
            role=role,
            role_badge=role_badge,
            foto_url=foto_url,
            bio=bio,
            keahlian=keahlian,
            social_instagram=social_instagram,
            social_linkedin=social_linkedin,
            social_behance=social_behance,
            email=email,
            urutan=urutan,
            aktif=aktif,
        )
        if 'foto' in request.FILES:
            member.foto = request.FILES['foto']
        member.save()

        messages.success(request, f'Anggota tim "{member.nama}" berhasil ditambahkan!')
        return redirect('app:team_list')

    return render(request, 'admin_super/team_form.html', {
        'title': 'Tambah Anggota Tim',
        'action': 'create',
    })


@admin_required
def team_edit(request, team_id):
    member = get_object_or_404(AnggotaTim, pk=team_id)

    if request.method == 'POST':
        member.nama = request.POST.get('nama', '').strip()
        member.role = request.POST.get('role', '').strip()
        member.role_badge = request.POST.get('role_badge', 'CREATIVE TEAM').strip()
        member.foto_url = request.POST.get('foto_url', '').strip()
        member.bio = request.POST.get('bio', '').strip()
        member.keahlian = request.POST.get('keahlian', '').strip()
        member.social_instagram = request.POST.get('social_instagram', '').strip()
        member.social_linkedin = request.POST.get('social_linkedin', '').strip()
        member.social_behance = request.POST.get('social_behance', '').strip()
        member.email = request.POST.get('email', '').strip()
        member.urutan = int(request.POST.get('urutan') or 1)
        member.aktif = request.POST.get('aktif') == 'on'

        if 'foto' in request.FILES:
            member.foto = request.FILES['foto']
        member.save()

        messages.success(request, f'Data anggota tim "{member.nama}" berhasil diperbarui!')
        return redirect('app:team_list')

    return render(request, 'admin_super/team_form.html', {
        'title': 'Edit Anggota Tim',
        'action': 'edit',
        'member': member,
    })


@admin_required
def team_delete(request, team_id):
    member = get_object_or_404(AnggotaTim, pk=team_id)
    if request.method == 'POST':
        nama = member.nama
        member.delete()
        messages.success(request, f'Anggota tim "{nama}" berhasil dihapus.')
    return redirect('app:team_list')


@admin_required
def team_toggle_active(request, team_id):
    member = get_object_or_404(AnggotaTim, pk=team_id)
    member.aktif = not member.aktif
    member.save()
    status_str = 'diaktifkan' if member.aktif else 'dinonaktifkan'
    messages.success(request, f'Status {member.nama} berhasil {status_str}.')
    return redirect('app:team_list')

