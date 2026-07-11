#NOTE: these aren't constants per say, they are choices
# you can have a file called choices.py or types.py, then do this 

"""
choices.py or types.py
from django.db import models

class CategoryChoices(models.TextChoices):
    REGULAR = "regular",  "Regular"
    PREMIUM = "premium", "Premium"
    LUXURY = "luxury", "Luxury"

then

category = models.CharField(choices=CategoryChoices)

"""



CATEGORY_CHOICES = [('regular','Regular'),
                    ('premium','Premium'),
                     ('luxury','Luxury')]


EXCELLENT = 5
VERY_GOOD = 4
GOOD = 3
FAIR = 2
POOR = 1 


RATING_CHOICES = [
    (EXCELLENT,'Excellent'),
    (VERY_GOOD,'Very Good'),
    (GOOD,'Good'),
    (FAIR,'Fair'),
    (POOR,'Poor'),
]


PAYMENT_STATUS_CHOICES = [
    ('PENDING','Pending'),
    ('SUCCESSFUL','Successful'),
    ('FAILED','Failed')
]


REFUND_STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('UNDER_REVIEW','Under Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('COMPLETED', 'Refund Completed'),
    ]


ACTION_CHOICES = [
    ('APPROVED','Approved'),
    ('REJECTED','Rejected'),
]