from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.homeView, name='home'),
    path('about/', views.aboutView, name='about'),
    path('artikel/', views.artikelView, name='artikel'),
    path('artikel/<int:article_id>/', views.artikel_detailView, name='artikel_detail'),
    path('shop/', views.shopView, name='shop'),
    path('shop/<int:service_id>/', views.service_detailView, name='service_detail'),
    path('layanan/<int:service_id>/', views.service_detailView, name='layanan_detail'),
    path('kontak/', views.kontakView, name='kontak'),
    path('app/', include(('app.urls', 'app'), namespace='app')),
    path('login/', views.loginView, name='login'),
    path('register/', views.registerView, name='register'),
    path('logout/', views.logoutView, name='logout'),
    path('pesan/', views.pesanView, name='pesan'),
    path('pesanan/<str:order_id>/bayar/', views.payment_pageView, name='payment_page'),
    path('payment/notification/', views.payment_notificationView, name='payment_notification'),
    path('payment/finish/', views.payment_finishView, name='payment_finish'),
    path('payment/check/<str:order_id>/', views.payment_check_statusView, name='payment_check_status'),
    path('pesanan/<str:order_id>/simulasi/', views.payment_simulate_sandboxView, name='payment_simulate_sandbox'),
    path('pesanan/<str:order_id>/upload-footage/', views.pesan_upload_footageView, name='pesan_upload_footage'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
