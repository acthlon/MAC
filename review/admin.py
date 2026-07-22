from django.contrib import admin
from django.contrib.contenttypes.models import ContentType

from materials.models import Materials
from products.models import Products
from review.models import Reviews


# @admin.register(Reviews)
class ReviewAdmin(admin.ModelAdmin):

    list_display = ('profiles','comment','rating','verified_purchase','content_object','content_type')
    list_filter = ['rating', 'created_at', 'content_type']
    search_fields = ('name','category')

    def content_object(self, obj):
            return obj.content_object
    
    content_object.short_description = "Reviewed item"

    def content_type(self,obj):
         return obj.content_type
    
    content_type.short_description = 'Item Type'

    def profiles(self,obj):
          return obj.user.username
    
    profiles.short_description = "profiles"


    def formfield_for_foreignkey(self, db_field, request, **kwargs):
          
        if db_field.name == 'content_type':
            allowed_models = ContentType.objects.get_for_models(Products,Materials)
            kwargs["queryset"] = ContentType.objects.filter(pk__in = [ct.id for ct in allowed_models.values()])
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(Reviews,ReviewAdmin)