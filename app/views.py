from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.utils import timezone
from .models import UserAdmin, UserPengguna, Provinsi, Pesanan, Layanan, Artikel
from .decorators_admin import is_admin_user


@login_required
def index(request):
    today = timezone.localdate()

    if is_admin_user(request.user):
        userC = UserAdmin.objects.filter(username=request.user).first()
        total_pengguna = UserPengguna.objects.count()
        total_provinsi = Provinsi.objects.count()
        total_layanan = Layanan.objects.count()
        total_artikel = Artikel.objects.count()

        pesanan_qs = Pesanan.objects.all().order_by('-created_at')
        total_pesanan = pesanan_qs.count()
        pending_pesanan = pesanan_qs.filter(status='Pending').count()
        inprogress_pesanan = pesanan_qs.filter(status='In progress').count()
        completed_pesanan = pesanan_qs.filter(status='Completed').count()
        total_revenue = sum(p.total_harga for p in pesanan_qs.filter(status__in=['In progress', 'Completed']))

        context = {
            'title': 'Dashboard',
            'heading': 'Dashboard Administrator',
            'photo': userC.photo if userC and userC.photo else None,
            'userdetail': userC if userC else None,
            'total_pengguna': total_pengguna,
            'total_provinsi': total_provinsi,
            'total_layanan': total_layanan,
            'total_artikel': total_artikel,
            'pesanan_list': pesanan_qs[:10],
            'total_pesanan': total_pesanan,
            'pending_pesanan': pending_pesanan,
            'inprogress_pesanan': inprogress_pesanan,
            'completed_pesanan': completed_pesanan,
            'total_revenue': total_revenue,
        }
        return render(request, 'admin_super/index.html', context)

    else:
        userC = UserPengguna.objects.filter(user=request.user).first()
        if not userC:
            userC = UserPengguna.objects.create(user=request.user, telp='', alamat='')

        user_pesanan = Pesanan.objects.filter(user=request.user).order_by('-created_at')
        total_pesanan = user_pesanan.count()
        inprogress_pesanan = user_pesanan.filter(status='In progress').count()
        completed_pesanan = user_pesanan.filter(status='Completed').count()

        context = {
            'title': 'Dashboard',
            'heading': 'Dashboard Pengguna',
            'photo': userC.photo if userC and userC.photo else None,
            'userdetail': userC,
            'today': today,
            'user_pesanan': user_pesanan,
            'total_pesanan': total_pesanan,
            'inprogress_pesanan': inprogress_pesanan,
            'completed_pesanan': completed_pesanan,
        }
        return render(request, 'pengguna/index.html', context)
