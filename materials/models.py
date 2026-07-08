from django.db import models
import uuid
from django.utils.text import slugify
from accounts.models import CustomUser
from core.models import CatalogBaseModel,SpecificationBaseModel,generated_image_path,generated_video_path
from core.constants import PATTERN_CHOICES 
from django.contrib.contenttypes.fields import GenericRelation
from review.models import Reviews
from core.models import Category,VariantBaseModel
from django.db.models import Sum
from decimal import Decimal
from django.contrib.contenttypes.models import ContentType


image_path = generated_image_path()

video_path = generated_video_path()



class Materials(CatalogBaseModel):

   user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='user_material')
   id = models.UUIDField(primary_key=True, default=uuid.uuid4,editable=False)
   is_active = models.BooleanField(default=True)
   reviews = GenericRelation(Reviews,content_type_field='content_type',object_id_field='object_id')
   categories = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        limit_choices_to={'target_model__model': 'materials'},
        related_name='material_categories'
    )



   @property
   def get_similar_material(self):

      similar_materials = Materials.objects.filter(categories=self.categories).exclude(pk=self.id)
      return similar_materials
   
   @property
   def total_stock(self):
      
      total = self.variants.aggregate(Sum('stock'))['stock__sum']
      return total if total else 0

   def save(self,*args,**kwargs):
         
      if not self.slug or self.slug != slugify(self.name):
         orig_slug = slugify(self.name) or "product"
         slug = orig_slug
         counter = 1
         
         # Loop until a unique slug is found
         while Materials.objects.filter(slug=slug).exclude(pk=self.pk).exists():
               slug = f"{orig_slug}-{counter}"
               counter += 1
         self.slug = slug   
      
      # if not self.slug:
      #    self.slug = slugify(self.name)

      # elif self.slug:
      #    self.slug = slugify(self.name)   
      super().save(*args,**kwargs)


   class Meta:
      verbose_name_plural = 'Materials'    
      ordering = ['-created_at']         


   def __str__(self):
      return  f'{self.name}'
   
   
class MaterialVariant(VariantBaseModel):
   
   material = models.ForeignKey(Materials, on_delete=models.CASCADE,related_name='variant')
   
   @property
   def final_price(self):
        
      price = self.material.price + self.price_adjustment
      total_price = price - self.material.discount
      # return total_price
      return total_price.quantize(Decimal('0.00'))
   
   @property
   def sku_value(self):
      
      sku_id = 10000
      category_code = self.material.categories
      
      if self.id:
         sku_id += self.id
         
         color_code = str(self.color).upper().replace(" ", "")
        
         value = f"MAC-MTL-{category_code}-{sku_id}-{color_code}"
         return value
   
   def save(self,*args,**kwargs):

      super().save(*args,**kwargs) 
      
      if self.id:
         self.sku = self.sku_value 
         # print(self.sku_value)
         super().save(update_fields=['sku'])
         
        
         
   
   def __str__(self):
      return f'{self.material.name} - {self.get_color_display()}'
   
   class Meta:
      unique_together = ('material', 'color')





class MaterialSpecification(SpecificationBaseModel):
   
   material = models.OneToOneField(
      Materials, 
      on_delete=models.CASCADE, 
      related_name='material_spec'
   )

   width = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)  #standard siz 45 or 60
   thread_count = models.IntegerField(blank=True, null=True)
   pattern = models.CharField(max_length=100, blank=True, null=True,choices=PATTERN_CHOICES)


   def __str__(self):
      return f"Specs for {self.material.name}"



image_path = generated_image_path()



class MaterialImages(models.Model):
   
   variant = models.ForeignKey(
      MaterialVariant, 
      on_delete=models.CASCADE, 
      related_name='images'
   )
   image = models.ImageField(upload_to=image_path)
   display_order = models.PositiveIntegerField(default=0)
   is_primary = models.BooleanField(default=False)

   class Meta:
      ordering = ['display_order']

   def __str__(self):
      return f"Image for {self.variant.material.name} - ({self.variant.color})"





class MaterialVideo(models.Model):
   
   
    material = models.ForeignKey(
        Materials, 
        on_delete=models.CASCADE, 
        related_name='videos'
    )
    video = models.FileField(upload_to=video_path)
    thumbnail = models.ImageField(upload_to=video_path, null=True, blank=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return f"Video for {self.material.name}"
     
     
     
     
     
# @property
# def sku_value(self):
#     # Initialize a default value to prevent "UnboundLocalError"
#     value = ""
    
#     if self.id:
#         sku_id = 10000 + self.id
        
#         # Clean up category, color, and size (make them uppercase, no spaces)
#         category_code = str(self.material.categories).upper()[:3]
#         color_code = str(self.color).upper().replace(" ", "")
#         size_code = str(self.size).upper().replace(" ", "")
        
#         value = f"MAC-{category_code}-{sku_id}-{color_code}-{size_code}"
        
#     return value

# def save(self, *args, **kwargs):
#     # Check if this is a brand new object being created
#     is_new = self.id is None
    
#     # 1. Save first to generate the database ID (self.id)
#     super().save(*args, **kwargs)
    
#     # 2. If it is new and has no SKU, generate the SKU and save it
#     if is_new and not self.sku:
#         self.sku = self.sku_value
#         # Save again, updating ONLY the sku field to keep it fast
#         super().save(update_fields=['sku'])