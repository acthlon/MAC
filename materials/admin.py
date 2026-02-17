from django.contrib import admin
from materials.models import Materials


class MaterialAdmin(admin.ModelAdmin):

    list_display = ('name','description','price','image','category','color','slug','discount','is_active')
    search_fields = ('name','category')

admin.site.register(Materials,MaterialAdmin)