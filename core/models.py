from django.db import models
from django.utils.deconstruct import deconstructible


@deconstructible
class generated_image_path():

    def __init__(self):
        pass

    def __call__(self,instance,filename):

        extension = filename.split('.')[-1]
        image_name = f'{instance.slug}'
        path = f'images/{image_name}.{extension}'
        # NOTE: Do 
        """
        path = f'images/{instance.id}/{image_name}'
        """
        return path


image_path = generated_image_path()


class TimeStampModel(models.Model):

    created_at = models.DateTimeField(auto_now_add = True)
    updatred_at = models.DateTimeField(auto_now = True)
    # `updatred_at`
    class Meta:
        abstract = True


class CatalogBaseModel(TimeStampModel):

    name = models.CharField(max_length=255)
    description = models.TextField(max_length = 500)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2,default=0.00)
    image = models.ImageField(upload_to=image_path,null=True,blank=True)
    slug = models.SlugField(unique=True, blank=True)


    class Meta:
        abstract = True 