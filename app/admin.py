from django.contrib import admin
from .models import Provinsi, UserAdmin, UserPengguna

admin.site.register(Provinsi)
admin.site.register(UserPengguna)
admin.site.register(UserAdmin)    