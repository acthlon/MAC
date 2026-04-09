from django.db import models
import uuid
from django.utils.text import slugify
from accounts.models import CustomUser
from core.models import CatalogBaseModel
from core.constants import CATEGORY_CHOICES 
from django.contrib.contenttypes.fields import GenericRelation
from review.models import Reviews

class Materials(CatalogBaseModel):

   user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
   id = models.UUIDField(primary_key=True, default=uuid.uuid4,editable=False) 
   category = models.CharField(max_length=30,choices= CATEGORY_CHOICES)
   color = models.CharField(max_length=200)
   stock = models.PositiveIntegerField()
   is_active = models.BooleanField(default=True)
   reviews = GenericRelation(Reviews,content_type_field='content_type',object_id_field='object_id')

# created_at
# updated_at
# id

# create a base mdel fr the above fields


   def get_similar_material(self):

      similar_materials = Materials.objects.filter(category=self.category).exclude(pk=self.id)
      return similar_materials

   def save(self,*args,**kwargs):

      if self.stock <= 0:
         self.is_active = False
         
      elif self.stock > 0:
         self.stock = True
         
      if not self.slug:
         self.slug = slugify(self.name)

      elif self.slug:
         self.slug = slugify(self.name)   
      super().save(*args,**kwargs)


   class Meta:
      verbose_name_plural = 'Materials'    
      ordering = ['-created_at']         


   def __str__(self):
      return  f'{self.name}'