from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from app.models import UserAdmin, UserPengguna


def loginView(request):
    if request.user.is_authenticated:
        return redirect('app:dashboard')

    if request.method == 'POST':
        identifier = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        # Support login by email OR username (case-insensitive)
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
            return redirect('app:dashboard')

        messages.warning(request, 'Email/Username atau password salah.')
        return redirect('login')

    return render(request, 'login.html', {
        'title': 'Login',
        'heading': 'Login',
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
            # Create associated UserPengguna profile
            UserPengguna.objects.get_or_create(
                user=new_user,
                defaults={'telp': '', 'alamat': ''}
            )
            messages.success(request, 'Registrasi berhasil, silakan login.')
            return redirect('login')

    return render(request, 'register.html', {
        'title': 'Daftar Akun',
        'heading': 'Pendaftaran Akun',
    })


@login_required
def logoutView(request):
    logout(request)
    messages.success(request, 'Anda telah berhasil logout!')
    return redirect('login')