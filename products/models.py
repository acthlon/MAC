from django.db import models
from core.models import CatalogBaseModel
from accounts.models import CustomUser 
import uuid
from core.constants import CATEGORY_CHOICES
from django.contrib.contenttypes.fields import GenericRelation
from review.models import Reviews 
from django.utils.text import slugify



class Products(CatalogBaseModel):

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4,editable=False) 
    category = models.CharField(max_length=30,choices= CATEGORY_CHOICES)
    stock = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    reviews = GenericRelation(Reviews, content_type_field='content_type', object_id_field='object_id')

    def get_similar_products(self):
        similar_products = Products.objects.filter(category=self.category).exclude(pk=self.id)
        return similar_products

    def save(self,*args,**kwargs):

        if self.stock <= 0:
            self.is_active = False 
        if not self.slug:
            self.slug = slugify(self.name)
        elif self.slug:
            self.slug = slugify(self.name)  
                       
        super().save(*args,**kwargs)


    class Meta:
        verbose_name_plural = 'Products'    
        ordering = ['-created_at']  

    def __str__(self):
        return self.name


