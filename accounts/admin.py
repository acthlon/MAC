from django.contrib import admin
from accounts.models import CustomUser

class CustomUserAdmin(admin.ModelAdmin):
    list_display=('country','state','city','address','email','phone')

admin.site.register(CustomUser,CustomUserAdmin)