from django.db import models
from accounts.models import UserProfile  
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey 
from django.db.models import Avg
from core.constants import RATING_CHOICES 



class Reviews(models.Model):

    profile = models.ForeignKey(UserProfile, on_delete=models.PROTECT, related_name='reviews')
    comment = models.TextField(max_length=500, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    rating = models.IntegerField(choices=RATING_CHOICES)
    verified_purchase = models.BooleanField(default=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT, related_name='reviews' )  
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type','object_id')


    def get_item_name(self):
        if self.content_object:
            return self.content_object.name    

    def get_total_customers(self):
        profile_numbers = UserProfile.objects.count() 
        return profile_numbers
    
    def get_item_average_rating(self):

            average_rating_for_item = Reviews.objects.filter(object_id = self.object_id, content_type=self.content_type).aggregate(Avg('rating'))
            item_avg_rating = round(average_rating_for_item.get('rating__avg',0),2)

            return item_avg_rating
                     
    def get_total_average_rating(self):
         
        average_rating = Reviews.objects.all().aggregate(Avg('rating'))
        total_avg_rating = round(average_rating.get('rating__avg',0),2)
        return total_avg_rating

    def get_review_count(self):    
         total_count = Reviews.objects.count()
         return total_count
    
    class Meta:
        verbose_name_plural = 'Reviews'    
        ordering = ['-created_at']  

    def __str__(self):
        return f'Review for {self.content_object.name} by {self.profile.user.username}'

    

