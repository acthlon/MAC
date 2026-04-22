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

        return path


image_path = generated_image_path()


import uuid
# BaseModel
class TimeStampModel(models.Model):
    # NOTE: YOU MAY RENAME THIS TO `BaseModel`, and make all your other models inherit it
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add = True)
    updatred_at = models.DateTimeField(auto_now = True)

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