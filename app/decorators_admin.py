from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect
from .models import UserAdmin


def is_admin_user(user):
    if not user or not user.is_authenticated:
        return False
    if getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False):
        return True
    if getattr(user, 'last_name', '') in ['Super Admin', 'Admin']:
        return True
    try:
        return UserAdmin.objects.filter(username=user).exists()
    except Exception:
        return False


def check_useradmin(function):

  def wrapper(request, *args, **kwargs):
    useradmin = UserAdmin.objects.filter(username=request.user).first()
    request.useradmin = useradmin
    if not useradmin or useradmin.photo == None:
      messages.error(request, 'Lengkapi data anda terlebih dahulu!')
      return redirect('app:profile_admin')
    return function(request, *args, **kwargs)

  return wrapper


def admin_required(view_func):

  @wraps(view_func)
  def _wrapped_view(request, *args, **kwargs):
    if not request.user.is_authenticated:
      return redirect(f"/login/?next={request.path}")
    if is_admin_user(request.user):
      return view_func(request, *args, **kwargs)
    else:
      messages.warning(request, 'Akses terbatas untuk Administrator.')
      return redirect('app:dashboard')

  return _wrapped_view
