from django.db import models
from accounts.models import CustomUser
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey 
from django.db.models import Avg
from core.constants import RATING_CHOICES 




class Reviews(models.Model):


    user = models.ForeignKey(CustomUser, on_delete=models.PROTECT, related_name='user_reviews')
    comment = models.TextField(max_length=500, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    rating = models.IntegerField(choices=RATING_CHOICES)
    verified_purchase = models.BooleanField(default=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT, related_name='reviews' )  
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type','object_id')




    @property
    def get_item_name(self):
        if self.content_object:
            return self.content_object.name    

    @property
    def item_average_rating(self):

            average_rating_for_item = Reviews.objects.filter(object_id = self.object_id, content_type=self.content_type).aggregate(Avg('rating'))
            item_avg_rating = round(average_rating_for_item.get('rating__avg',0),2)

            return item_avg_rating

    # @property
    # def get_review_count(self):    
    #      total_count = Reviews.objects.count()
    #      return total_count
    
    class Meta:
        verbose_name_plural = 'Reviews'    
        ordering = ['-created_at']  

    def __str__(self):
        return f'Review for {self.content_object.name} by {self.user.username}'
    
    
    # GLOBAL Methods
    
    @classmethod
    def get_total_customers(cls):
        profile_numbers = CustomUser.objects.count() 
        return profile_numbers
    
                     
    @classmethod
    def get_total_average_rating(self):
         
        average_rating = Reviews.objects.all().aggregate(Avg('rating'))
        total_avg_rating = round(average_rating.get('rating__avg',0),2)
        return total_avg_rating
    
    @classmethod
    def satisfacton_rate(cls):
        
        total_review_counts = Reviews.objects.count()
        filtered_reviews = Reviews.objects.filter(rating__gte=4).count()
        happy_reviews = ((filtered_reviews / total_review_counts) * 100) if total_review_counts > 0 else 0
        return happy_reviews

