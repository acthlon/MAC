from django.db import models
import uuid
from django.utils.text import slugify
import os
from django.utils.deconstruct import deconstructible 


CATEGORIES = [('regular','Regular'),
            ('premium','Premium',
            'luxury','Luxury')]

image_path = generated_image_path()

@deconstructible
class generated_image_path:
   
   def __init__(self):
      pass
   
   def __call__(self, instance,filename):
      extension = filename.split('.')[-1]
      path = f'media/images/{instance.slug}.{extension}' 
      return path



class Materials(models.Model):


    id = models.UUIDField(primary_key=True, default=uuid.uuid4,editable=False) 
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_length=10, decimal_place=2)
    image = models.ImageField(upload_to=image_path)
    category = models.CharField(max_length=30,choices=CATEGORIES)
    color = models.CharField(max_length=200)
    slug = models.SlugField(unique=True,blank=True)
    stock = models.IntegerField()



    def save(self,*args,**kwargs):
       
       if not self.slug:
          self.slug = slugify(self.name)

          super.save(self,*args,**kwargs)
          
       
    def __str__(self):
      return  f'{self.name}'