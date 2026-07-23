import uuid
from decimal import Decimal

from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.text import slugify

from accounts.models import CustomUser
from core.constants import PRODUCT_SIZE_CHOICES
from core.models import (CatalogBaseModel, Category, SpecificationBaseModel,
                         VariantBaseModel, generated_image_path,
                         generated_video_path)
from review.models import Reviews

image_path = generated_image_path()

video_path = generated_video_path()



class Products(CatalogBaseModel):

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE,related_name='user_product')
    id = models.UUIDField(primary_key=True, default=uuid.uuid4,editable=False) 
    status = models.BooleanField(default=True)
    reviews = GenericRelation(Reviews, content_type_field='content_type', object_id_field='object_id')
    
    categories = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        limit_choices_to={'target_model__model': 'products'},
        related_name='product_categories'
    )
    
    
    @property
    def get_similar_products(self):    
        
        similar_products = Products.objects.filter(categories=self.categories).exclude(pk=self.id)[:10]
        return similar_products
    
  

    def save(self,*args,**kwargs):
            
        if not self.slug or self.slug != slugify(self.name):
            orig_slug = slugify(self.name) or "product"
            slug = orig_slug
            counter = 1
            
            # Loop until a unique slug is found
            while Products.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{orig_slug}-{counter}"
                counter += 1
            self.slug = slug

        super().save(*args,**kwargs)


    class Meta:
        verbose_name_plural = 'Products'    
        ordering = ['-created_at']  

    def __str__(self):
        return self.name




class ProductVariant(VariantBaseModel):

    product = models.ForeignKey(Products, on_delete=models.CASCADE, related_name='variant')
    size = models.CharField(max_length=100, blank=True, null=True,choices=PRODUCT_SIZE_CHOICES)


    @property
    def final_price(self):
        
        price = self.product.price + self.price_adjustment
        total_price = price - self.product.discount

        return total_price.quantize(Decimal('0.00'))

    @property
    def sku_value(self):
        
        sku_id = 10000

        category_code = self.product.categories
        
        if self.id:
            sku_id += self.id
            
            color_code = str(self.color).upper().replace(" ", "")
            size_code = str(self.size).upper().replace(" ", "")
            
            value = f"MAC-PDT-{category_code}-{sku_id}-{color_code}-{size_code}"
            return value
    
    
    def save(self,*args,**kwargs):
       
        super().save(*args,**kwargs)
        
        if self.id:
            self.sku = self.sku_value 
           
            super().save(update_fields=['sku'])



    class Meta:
        unique_together = ('product','size','color') # A product can only have one 'M' variant

    def __str__(self):
        return f"{self.product.name} - {self.get_size_display()} ({self.get_color_display()})"



class ProductSpecification(SpecificationBaseModel):
    
    product = models.OneToOneField(
        Products, 
        on_delete=models.CASCADE,
        related_name='product_spec'
    )
    
    product_line = models.CharField(max_length=200, blank=True, null=True)


    def __str__(self):
        return f"Specs for {self.product.name}"



class ProductImages(models.Model):
    
    variant = models.ForeignKey(
        ProductVariant, 
        on_delete=models.CASCADE, 
        related_name='images'
    )
    image = models.ImageField(upload_to=image_path)
    display_order = models.PositiveIntegerField(default=0)
    is_primary = models.BooleanField(default=False)

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return f"Image for {self.variant.product.name}"


class ProductVideo(models.Model):
    product = models.ForeignKey(
        Products, 
        on_delete=models.CASCADE, 
        related_name='videos'
    )
    video = models.FileField(upload_to=video_path)
    thumbnail = models.ImageField(upload_to=video_path, null=True, blank=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return f"Video for {self.product.name}"