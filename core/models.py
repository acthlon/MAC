from django.db import models
from django.utils.deconstruct import deconstructible
from django.utils.text import slugify
from core.constants import COLOR_CHOICES,MATERIAL_CATEGORY_CHOICES,QUALITY_CHOICES
from django.contrib.contenttypes.models import ContentType
import uuid
from decimal import Decimal




# @deconstructible
# class generated_image_path():

#     def __init__(self):
#         pass

#     def __call__(self,instance,filename):

#         extension = filename.split('.')[-1]
#         image_name = f'{instance.slug}'
#         path = f'images/{image_name}.{extension}'

#         return path

@deconstructible
class generated_image_path():

    def __init__(self):
        pass

    def __call__(self,instance,filename):

        extension = filename.split(".")[-1]
        random_name = uuid.uuid4().hex[:6]
        
        
        if hasattr(instance, 'variant'):
            if hasattr(instance.variant, 'product') and hasattr(instance.variant.product, 'slug'):
                slug = instance.variant.product.slug
                path = f'products/images/{slug}/{instance.variant.get_color_display()}/{random_name}.{extension}'
                return path

            elif hasattr(instance.variant, 'material') and hasattr(instance.variant.material, 'slug'):
                slug = instance.variant.material.slug
                path = f'materials/images/{slug}/{instance.variant.get_color_display()}/{random_name}.{extension}'
                return path
                    
        
        return path

@deconstructible
class generated_video_path():
    
    def __init__(self):
        pass
    
    def __call__(self,instance,filename):
        
        extension = filename.split(".")[-1]
        random_name = uuid.uuid4().hex[:6]
        
        if hasattr(instance, 'product') and hasattr(instance.product,'slug'):
            
            slug = instance.product.slug
            path = f'products/videos/{slug}/{random_name}.{extension}'
            return path
            
            
        elif hasattr(instance,'material') and hasattr(instance.material,'slug'):
            slug = instance.material.slug
            path = f'materials/videos/{slug}/{random_name}.{extension}'
            
            return path



# image_path = generated_image_path()



class TimeStampModel(models.Model):

    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    class Meta:
        abstract = True


class CatalogBaseModel(TimeStampModel):

    name = models.CharField(max_length=255)
    description = models.TextField(max_length = 500)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2,default=0.00)
    slug = models.SlugField(unique=True, blank=True)
    quality_category = models.CharField(max_length=30,choices= QUALITY_CHOICES,null=True,blank=True)

        
    class Meta:
        abstract = True 

    @property
    def model_name(self):
        
        return self._meta.model_name


    @property
    def total_stock(self):
        from django.db.models import Sum
        total = self.variant.aggregate(Sum('stock'))['stock__sum']
        return total if total else 0


    @property
    def pry_image(self):
        
        primary = self.images.filter(is_primary = True).first()
        if primary :
            return primary.image

    @property
    def average_rating(self):
        from django.db.models import Avg
        avg = self.reviews.aggregate(Avg('rating'))['rating__avg']
        return round(avg, 2) if avg is not None else 0.0

    @property
    def review_count(self):
        return self.reviews.count()

    @property
    def get_percent_disount(self):
        if self.price > 0 and self.discount > 0:
            return round((self.discount / self.price) * 100, 2)
        return 0.0
    
    @property
    def discounted_price(self):
        price = self.price - self.discount
        # return round(price,2)
        return price.quantize(Decimal('0.00'))




class Banner(models.Model):
    
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True, null=True)
    discription = models.TextField(max_length=500, blank=True, null=True)
    image = models.ImageField(upload_to='banners/images', null=True,blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return self.title



# class HomepageContent(models.Model):
    
#     section = models.CharField(max_length=100, unique=True)
#     title = models.CharField(max_length=200)
#     subtitle = models.TextField(blank=True, null=True)
#     is_active = models.BooleanField(default=True)

#     class Meta:
#         verbose_name_plural = "Homepage Content"
        

class Category(models.Model):
    
    
    # NEW: This determines whether this category belongs to Products or Materials    
    target_model = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to={'model__in': ['products', 'materials']},
        null=True,
        blank=True
    )
    
    name = models.CharField(max_length=200)
    icon = models.ImageField(upload_to="category/icon/",blank=True, null=True)
    image = models.ImageField(upload_to="category/images/",blank=True, null=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True, null=True)
    slug = models.SlugField(unique=True, blank=True, null=True)

    
    def save(self,*args,**kwargs):
        if not self.slug or self.slug != slugify(self.name):
            orig_slug = slugify(self.name) or "category"
            slug = orig_slug
            counter = 1
            # Loop until a unique slug is found
            while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{orig_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args,**kwargs)
    

    
    class Meta:
        ordering = ['display_order','name']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name
    
    

class SpecificationBaseModel(TimeStampModel):

    weight = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    material_type = models.CharField(max_length=100, blank=True, null=True,choices=MATERIAL_CATEGORY_CHOICES)
    key_features = models.TextField(max_length=500, blank=True, null=True)
    
    
    class Meta:
        abstract = True
        
        


class VariantBaseModel(TimeStampModel): 
    
    stock = models.PositiveIntegerField(default=0)
    sku = models.CharField(max_length=100, unique=True, blank=True,null=True)
    color = models.CharField(max_length=100,choices=COLOR_CHOICES, blank=True, null=True)
    price_adjustment = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default = False)


    def save(self,*args,**kwargs):
        
        if self.stock <= 0:
            self.is_active = False 
        elif self.stock > 0:
            self.is_active = True 

        super().save(*args,**kwargs)

    class Meta:
        abstract = True