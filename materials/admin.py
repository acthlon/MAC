from django.contrib import admin
from materials.models import Materials


class MaterialAdmin(admin.ModelAdmin):

    list_display = ('name','description','price','image','category','color','slug')
    search_fields = ('name','category')

admin.site.register(Materials,MaterialAdmin)