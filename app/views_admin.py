from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from app.models import UserAdmin, UserPengguna
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
