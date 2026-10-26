from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.utils import timezone
from .models import UserAdmin, UserPengguna, Provinsi


@login_required
def index(request):
    today = timezone.localdate()

    if request.user.last_name == 'Super Admin' or request.user.is_superuser:
        userC = UserAdmin.objects.filter(username=request.user).first()
        total_pengguna = UserPengguna.objects.count()
        total_provinsi = Provinsi.objects.count()

        context = {
            'title': 'Dashboard',
            'heading': 'Dashboard Administrator',
            'photo': userC.photo if userC and userC.photo else None,
            'userdetail': userC if userC else None,
            'total_pengguna': total_pengguna,
            'total_provinsi': total_provinsi,
        }
        return render(request, 'admin_super/index.html', context)

    else:
        userC = UserPengguna.objects.filter(user=request.user).first()
        if not userC:
            userC = UserPengguna.objects.create(user=request.user, telp='', alamat='')

        context = {
            'title': 'Dashboard',
            'heading': 'Dashboard Pengguna',
            'photo': userC.photo if userC and userC.photo else None,
            'userdetail': userC,
            'today': today,
        }
        return render(request, 'pengguna/index.html', context)