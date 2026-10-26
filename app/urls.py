from django.urls import path
from . import views, views_admin, views_pengguna

app_name = "app"

urlpatterns = [
    ###### ADMIN ######
    path('profile/admin', views_admin.profile_admin, name='profile_admin'),
    path('admin/users', views_admin.user_list, name='user_list'),
    path('admin/users/<int:user_id>/edit', views_admin.user_edit, name='user_edit'),
    path('admin/users/<int:user_id>/delete', views_admin.user_delete, name='user_delete'),
    path('admin/users/<int:user_id>/toggle', views_admin.user_toggle_active, name='user_toggle_active'),

    ###### PENGGUNA ######
    path('profile/pengguna', views_pengguna.profile_pengguna, name='profile_pengguna'),

    ###### UMUM ######
    path('dashboard', views.index, name='dashboard'),
    path('', views.index, name='index'),
]