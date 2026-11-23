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
    path('admin/orders/<str:order_id>/status', views_admin.order_status_update, name='order_status_update'),
    path('admin/orders/<str:order_id>/delete', views_admin.order_delete, name='order_delete'),

    # Services CRUD
    path('admin/services', views_admin.service_list, name='service_list'),
    path('admin/services/new', views_admin.service_create, name='service_create'),
    path('admin/services/<int:service_id>/edit', views_admin.service_edit, name='service_edit'),
    path('admin/services/<int:service_id>/delete', views_admin.service_delete, name='service_delete'),
    path('admin/services/<int:service_id>/toggle', views_admin.service_toggle_active, name='service_toggle_active'),

    # Articles CRUD
    path('admin/articles', views_admin.article_list, name='article_list'),
    path('admin/articles/new', views_admin.article_create, name='article_create'),
    path('admin/articles/<int:article_id>/edit', views_admin.article_edit, name='article_edit'),
    path('admin/articles/<int:article_id>/delete', views_admin.article_delete, name='article_delete'),

    # Website Settings (CMS)
    path('admin/settings', views_admin.web_settings, name='web_settings'),

    # Team CRUD
    path('admin/team', views_admin.team_list, name='team_list'),
    path('admin/team/new', views_admin.team_create, name='team_create'),
    path('admin/team/<int:team_id>/edit', views_admin.team_edit, name='team_edit'),
    path('admin/team/<int:team_id>/delete', views_admin.team_delete, name='team_delete'),
    path('admin/team/<int:team_id>/toggle', views_admin.team_toggle_active, name='team_toggle_active'),

    ###### PENGGUNA ######
    path('profile/pengguna', views_pengguna.profile_pengguna, name='profile_pengguna'),

    ###### UMUM ######
    path('dashboard', views.index, name='dashboard'),
    path('', views.index, name='index'),
]
