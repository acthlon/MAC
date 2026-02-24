from django.contrib import admin
from accounts.models import CustomUser,UserProfile



class CustomUserAdmin(admin.ModelAdmin):
    list_display=('username','first_name','last_name','email','phone','gender','is_active','is_staff','is_superuser')

admin.site.register(CustomUser,CustomUserAdmin)



class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('country','state','city','address','profile_image')

admin.site.register(UserProfile,UserProfileAdmin)

