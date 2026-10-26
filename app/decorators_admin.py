from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect
from .models import UserAdmin


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
      return redirect('login')
    if request.user.last_name == 'Super Admin' or request.user.is_superuser:
      return view_func(request, *args, **kwargs)
    else:
      return redirect('app:dashboard')

  return _wrapped_view