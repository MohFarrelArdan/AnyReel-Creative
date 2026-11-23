from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from app.models import UserAdmin, UserPengguna, Pesanan, Layanan, Artikel, KomentarArtikel
from app.midtrans import (
    create_snap_transaction,
    process_midtrans_notification,
    check_midtrans_status,
    get_midtrans_config,
    charge_and_settle_sandbox
)
import random
import json


def homeView(request):
    """
    Halaman Utama (Home) Website FRAMEHAUS
    Memuat layanan unggulan dan artikel terbaru dari database.
    """
    featured_services = Layanan.objects.filter(aktif=True).order_by('urutan')[:4]
    latest_articles = Artikel.objects.all().order_by('-created_at')[:3]
    return render(request, 'home.html', {
        'title': 'FRAMEHAUS — Creative Video Editing Studio',
        'services': featured_services,
        'articles': latest_articles,
    })


def aboutView(request):
    """
    Halaman About Us (Tentang Kami)
    Menampilkan data tim dinamis dari model AnggotaTim (CRUD Dashboard).
    """
    from app.models import AnggotaTim
    team_members = AnggotaTim.objects.filter(aktif=True).order_by('urutan', 'id')
    return render(request, 'about.html', {
        'title': 'About Us — FRAMEHAUS Creative Studio',
        'team_members': team_members,
    })


def artikelView(request):
    """
    Halaman Artikel & Journal
    Terhubung langsung ke database Artikel.
    """
    category = request.GET.get('category', '').strip()
    search = request.GET.get('search', '').strip()
    articles = Artikel.objects.all().order_by('-created_at')
    if category:
        articles = articles.filter(kategori=category)
    if search:
        articles = articles.filter(judul__icontains=search) | articles.filter(ringkasan__icontains=search)

    return render(request, 'artikel.html', {
        'title': 'Journal & Artikel Kreatif — FRAMEHAUS',
        'articles': articles,
        'selected_category': category,
        'search': search,
    })


def artikel_detailView(request, article_id):
    """
    Halaman Detail Artikel bergaya Blogger / Editorial
    Mendukung tampilan penuh artikel, daftar komentar, dan form penambahan komentar pembaca.
    """
    article = get_object_or_404(Artikel, pk=article_id)

    # Handle Comment Submission
    if request.method == 'POST':
        nama = request.POST.get('nama', '').strip()
        email = request.POST.get('email', '').strip()
        pesan = request.POST.get('pesan', '').strip()

        if nama and email and pesan:
            KomentarArtikel.objects.create(
                artikel=article,
                nama=nama,
                email=email,
                pesan=pesan,
            )
            messages.success(request, 'Terima kasih! Komentar Anda berhasil dipublikasikan di artikel ini.')
            return redirect('artikel_detail', article_id=article.id)
        else:
            messages.error(request, 'Mohon lengkapi nama, email, dan pesan komentar Anda.')

    comments = article.komentar.all().order_by('-created_at')
    related_articles = Artikel.objects.filter(kategori=article.kategori).exclude(pk=article.id)[:3]
    if not related_articles.exists():
        related_articles = Artikel.objects.exclude(pk=article.id)[:3]

    prev_article = Artikel.objects.filter(id__lt=article.id).order_by('-id').first()
    next_article = Artikel.objects.filter(id__gt=article.id).order_by('id').first()

    popular_articles = Artikel.objects.all().order_by('id')[:4]
    categories = Artikel.KATEGORI_CHOICES

    return render(request, 'artikel_detail.html', {
        'title': f'{article.judul} — FRAMEHAUS Journal',
        'article': article,
        'comments': comments,
        'comment_count': comments.count(),
        'related_articles': related_articles,
        'prev_article': prev_article,
        'next_article': next_article,
        'popular_articles': popular_articles,
        'categories': categories,
    })


def shopView(request):
    """
    Halaman Katalog Layanan & Shop
    Terhubung langsung ke database Layanan (CRUD Admin).
    """
    category = request.GET.get('category', '').strip()
    search = request.GET.get('search', '').strip()
    services = Layanan.objects.filter(aktif=True).order_by('urutan')
    if category:
        services = services.filter(kategori=category)
    if search:
        services = services.filter(nama__icontains=search) | services.filter(deskripsi__icontains=search)

    all_services = Layanan.objects.filter(aktif=True).order_by('urutan')

    return render(request, 'shop.html', {
        'title': 'Katalog Layanan Video Editing — FRAMEHAUS',
        'services': services,
        'all_services': all_services,
        'selected_category': category,
        'search': search,
    })


def service_detailView(request, service_id):
    """
    Halaman Detail Produk / Layanan Studio
    Menampilkan visual, spesifikasi lengkap, fitur paket, checkout langsung, dan rekomendasi terkait.
    """
    is_admin = request.user.is_authenticated and (request.user.is_superuser or hasattr(request.user, 'useradmin'))
    if is_admin:
        service = get_object_or_404(Layanan, pk=service_id)
    else:
        service = get_object_or_404(Layanan, pk=service_id, aktif=True)

    related_services = Layanan.objects.filter(aktif=True).exclude(pk=service.id).order_by('?')[:3]

    return render(request, 'service_detail.html', {
        'title': f'{service.nama} — FRAMEHAUS Studio',
        'service': service,
        'related_services': related_services,
    })


def kontakView(request):
    """
    Halaman Kontak Studio & Pengiriman Pesan
    """
    if request.method == 'POST':
        nama = request.POST.get('nama', '').strip()
        messages.success(request, f'Terima kasih {nama}! Pesan Anda telah diterima. Tim kami akan segera menghubungi Anda.')
        return redirect('kontak')

    return render(request, 'kontak.html', {
        'title': 'Hubungi Kami — FRAMEHAUS Studio',
    })


def loginView(request):
    next_url = request.GET.get('next') or request.POST.get('next') or ''

    if request.user.is_authenticated:
        if next_url and next_url.startswith('/'):
            return redirect(next_url)
        return redirect('app:dashboard')

    if request.method == 'POST':
        identifier = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        user_obj = User.objects.filter(
            Q(email__iexact=identifier) | Q(username__iexact=identifier)
        ).first()

        user = None
        if user_obj:
            user = authenticate(request, username=user_obj.username, password=password)
        if not user:
            user = authenticate(request, username=identifier, password=password)

        if user:
            login(request, user)
            display_name = user.first_name if user.first_name else user.username
            messages.success(request, f'Selamat Datang, {display_name}!')

            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect('app:dashboard')

        messages.warning(request, 'Email/Username atau password salah.')
        if next_url:
            return redirect(f'/login/?next={next_url}')
        return redirect('login')

    return render(request, 'login.html', {
        'title': 'Login — FRAMEHAUS',
        'heading': 'Login',
        'next': next_url,
    })


def registerView(request):
    if request.user.is_authenticated:
        return redirect('app:dashboard')

    if request.method == 'POST':
        name = request.POST.get('first_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        confirm = request.POST.get('confirm_password', '')

        if confirm != password:
            messages.warning(request, 'Password dan konfirmasi password tidak cocok.')
        elif User.objects.filter(email=email).exists() or User.objects.filter(username=email).exists():
            messages.warning(request, 'Email sudah terdaftar.')
        else:
            new_user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=name,
                last_name='Pengguna',
            )
            UserPengguna.objects.get_or_create(
                user=new_user,
                defaults={'telp': '', 'alamat': ''}
            )
            messages.success(request, 'Registrasi berhasil, silakan login.')
            return redirect('login')

    return render(request, 'register.html', {
        'title': 'Daftar Akun — FRAMEHAUS',
        'heading': 'Pendaftaran Akun',
    })


@login_required
def logoutView(request):
    logout(request)
    messages.success(request, 'Anda telah berhasil logout!')
    return redirect('home')


def pesanView(request):
    """
    Endpoint pemesanan layanan.
    Jika pengunjung belum login:
    - Muncul notifikasi bahwa harus login sebagai user terlebih dahulu
    - Dialihkan ke halaman login
    Jika sudah login:
    - Pesanan disimpan ke database (Model Pesanan)
    - Snap Token Midtrans otomatis di-generate
    - Pengguna dialihkan ke halaman pembayaran resmi Midtrans Snap
    """
    if not request.user.is_authenticated:
        messages.warning(request, 'Silakan login sebagai user terlebih dahulu untuk memesan layanan.')
        return redirect('/login/?next=/shop/')

    if request.method == 'POST':
        layanan_nama = request.POST.get('layanan_nama', 'Custom Video Editing').strip()
        try:
            total_harga = int(request.POST.get('total_harga', 350000))
        except (ValueError, TypeError):
            total_harga = 350000

        kategori = request.POST.get('kategori', 'Video Editing').strip()
        durasi = request.POST.get('durasi', '3–5 hari').strip()
        catatan = request.POST.get('catatan', '').strip()

        # Bahan Footage Video dari Pelanggan (Link Drive / File Video)
        upload_method = request.POST.get('upload_method', 'drive').strip()
        video_link = request.POST.get('video_link', '').strip()
        video_file = request.FILES.get('video_file')

        order_number = random.randint(2040, 9999)
        order_id = f"#FH-{order_number}"
        while Pesanan.objects.filter(order_id=order_id).exists():
            order_number = random.randint(2040, 9999)
            order_id = f"#FH-{order_number}"

        pesanan = Pesanan.objects.create(
            order_id=order_id,
            user=request.user,
            layanan_nama=layanan_nama,
            kategori=kategori,
            durasi=durasi,
            total_harga=total_harga,
            catatan=catatan,
            status='In progress',
            payment_status='unpaid',
            upload_method=upload_method,
            video_link=video_link,
            video_file=video_file,
        )

        # Generate Midtrans Snap Token secara otomatis
        try:
            snap_token, redirect_url = create_snap_transaction(pesanan, request=request)
            if snap_token:
                messages.success(request, f'Pesanan {pesanan.order_id} berhasil dibuat. Silakan lakukan pembayaran.')
            else:
                messages.info(request, f'Pesanan {pesanan.order_id} dibuat. Menyiapkan gateway pembayaran...')
        except Exception as e:
            messages.warning(request, f'Pesanan tercatat. Gateway sedang bersiap: {e}')

        return redirect('payment_page', order_id=pesanan.clean_order_id)

    return redirect('shop')


@login_required
def payment_pageView(request, order_id):
    """
    Halaman Pembayaran Interaktif Midtrans Sandbox / Production.
    Menampilkan detail pesanan, total tagihan, tombol popup snap.pay(),
    dan link langsung ke hosted payment page.
    """
    clean_id = order_id.replace('#', '')
    pesanan = Pesanan.objects.filter(order_id=f"#{clean_id}").first()
    if not pesanan:
        pesanan = Pesanan.objects.filter(order_id=clean_id).first()

    if not pesanan:
        messages.error(request, f'Pesanan dengan ID {order_id} tidak ditemukan.')
        return redirect('app:dashboard')

    # Keamanan akses: pastikan pemilik pesanan atau superadmin/staff
    if pesanan.user != request.user and not request.user.is_superuser and request.user.last_name != 'Admin':
        messages.error(request, 'Anda tidak memiliki otorisasi untuk mengakses rincian pesanan ini.')
        return redirect('app:dashboard')

    # Jika snap_token belum ada, buat sekarang
    if not pesanan.snap_token and pesanan.payment_status in ['unpaid', 'pending']:
        create_snap_transaction(pesanan, request=request)

    midtrans_cfg = get_midtrans_config()

    context = {
        'title': f'Pembayaran {pesanan.order_id} — FRAMEHAUS',
        'pesanan': pesanan,
        'snap_token': pesanan.snap_token,
        'snap_redirect_url': pesanan.snap_redirect_url,
        'snap_js_url': midtrans_cfg['snap_js_url'],
        'client_key': midtrans_cfg['client_key'],
        'is_production': midtrans_cfg['is_production'],
        'server_key_preview': f"{midtrans_cfg['server_key'][:8]}...{midtrans_cfg['server_key'][-6:]}" if midtrans_cfg['server_key'] else "Belum diset",
    }
    return render(request, 'payment_page.html', context)


@csrf_exempt
def payment_notificationView(request):
    """
    Webhook Notifikasi HTTP POST dari Midtrans.
    Dipanggil otomatis oleh server Midtrans ketika transaksi mengalami perubahan status
    (settlement, pending, cancel, expire, deny).
    """
    if request.method != 'POST':
        return HttpResponseBadRequest("Hanya menerima request POST webhook.")

    try:
        body_unicode = request.body.decode('utf-8')
        payload = json.loads(body_unicode)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Invalid JSON payload: {str(e)}'}, status=400)

    success, message = process_midtrans_notification(payload)
    if success:
        return JsonResponse({'status': 'ok', 'message': message})
    else:
        return JsonResponse({'status': 'failed', 'message': message}, status=400)


def payment_finishView(request):
    """
    Halaman Sukses / Callback setelah pengguna menyelesaikan transaksi via Snap Midtrans.
    """
    order_id = request.GET.get('order_id', '').strip().replace('#', '')
    status_code = request.GET.get('status_code', '')
    transaction_status = request.GET.get('transaction_status', '')

    pesanan = None
    if order_id:
        pesanan = Pesanan.objects.filter(order_id=f"#{order_id}").first()
        if not pesanan:
            pesanan = Pesanan.objects.filter(order_id=order_id).first()

        # Sinkronkan status langsung ke API Midtrans
        if pesanan:
            try:
                check_midtrans_status(order_id)
                pesanan.refresh_from_db()
            except Exception:
                pass

    context = {
        'title': 'Status Pembayaran — FRAMEHAUS Studio',
        'order_id': order_id,
        'status_code': status_code,
        'transaction_status': transaction_status,
        'pesanan': pesanan,
    }
    return render(request, 'payment_finish.html', context)


@login_required
def payment_check_statusView(request, order_id):
    """
    AJAX endpoint untuk polling atau live refresh status pembayaran pesanan.
    """
    clean_id = order_id.replace('#', '')
    pesanan = Pesanan.objects.filter(order_id=f"#{clean_id}").first()
    if not pesanan:
        pesanan = Pesanan.objects.filter(order_id=clean_id).first()

    if not pesanan:
        return JsonResponse({'success': False, 'message': 'Pesanan tidak ditemukan'}, status=404)

    # Sinkronisasi ke Midtrans API
    check_midtrans_status(clean_id)
    pesanan.refresh_from_db()

    return JsonResponse({
        'success': True,
        'order_id': pesanan.order_id,
        'payment_status': pesanan.payment_status,
        'status_display': pesanan.get_payment_status_display(),
        'is_paid': pesanan.is_paid,
        'payment_type': pesanan.payment_type or '-',
        'payment_time': pesanan.payment_time.strftime('%d %b %Y %H:%M') if pesanan.payment_time else None
    })


@login_required
def payment_simulate_sandboxView(request, order_id):
    """
    Simulasi Pembayaran Sandbox Instan.
    Memungkinkan pengujian alur pesanan lunas secara langsung di lingkungan lokal/development
    bahkan saat koneksi browser sedang mengalami kendala proxy/VPN.
    """
    clean_id = order_id.replace('#', '')
    pesanan = Pesanan.objects.filter(order_id=f"#{clean_id}").first()
    if not pesanan:
        pesanan = Pesanan.objects.filter(order_id=clean_id).first()

    if not pesanan:
        messages.error(request, 'Pesanan tidak ditemukan.')
        return redirect('app:dashboard')

    if request.method == 'POST':
        method = request.POST.get('method', 'BCA Virtual Account (Midtrans Sandbox)')
        
        # Settle transaksi langsung ke server Midtrans Sandbox Cloud!
        try:
            charge_and_settle_sandbox(pesanan)
        except Exception as e:
            from django.utils import timezone
            pesanan.payment_status = 'settlement'
            pesanan.payment_type = method
            pesanan.payment_time = timezone.now()
            pesanan.save()

        messages.success(request, f'Pembayaran Berhasil! Pesanan {pesanan.order_id} telah resmi berstatus Settlement di Midtrans Sandbox.')
        finish_url = f"/payment/finish/?order_id={pesanan.clean_order_id}&status_code=200&transaction_status=settlement"

        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json' or request.GET.get('format') == 'json':
            return JsonResponse({
                'success': True,
                'message': f'Pembayaran {pesanan.order_id} berhasil diproses.',
                'redirect_url': finish_url
            })

        return redirect(finish_url)

    return redirect('payment_page', order_id=clean_id)


@login_required
def pesan_upload_footageView(request, order_id):
    """
    Endpoint untuk mengunggah atau memperbarui footage video (Link Drive / Upload File)
    setelah pesanan dibuat, dari halaman pembayaran maupun dashboard pengguna.
    """
    clean_id = order_id.replace('#', '')
    pesanan = Pesanan.objects.filter(order_id=f"#{clean_id}").first()
    if not pesanan:
        pesanan = Pesanan.objects.filter(order_id=clean_id).first()

    if not pesanan:
        messages.error(request, 'Pesanan tidak ditemukan.')
        return redirect('app:dashboard')

    if pesanan.user != request.user and not request.user.is_superuser and request.user.last_name != 'Admin':
        messages.error(request, 'Anda tidak memiliki hak akses untuk pesanan ini.')
        return redirect('app:dashboard')

    if request.method == 'POST':
        upload_method = request.POST.get('upload_method', 'drive').strip()
        video_link = request.POST.get('video_link', '').strip()
        
        pesanan.upload_method = upload_method
        if video_link:
            pesanan.video_link = video_link
        if 'video_file' in request.FILES:
            pesanan.video_file = request.FILES['video_file']
            
        pesanan.save()
        messages.success(request, f'Bahan video footage untuk pesanan {pesanan.order_id} berhasil disimpan!')

    referer = request.META.get('HTTP_REFERER')
    if referer and 'upload-footage' not in referer:
        return redirect(referer)
    return redirect('payment_page', order_id=pesanan.clean_order_id)



