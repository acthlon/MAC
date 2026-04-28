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