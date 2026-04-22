from django.db.models import TextChoices


class PaymentCurrencyChoices(TextChoices):
    NGN = 'NGN', 'Nigerian Naira'
    USD = 'USD', 'US Dollar'
    EUR = 'EUR', 'Euro'
    GBP = 'GBP', 'British Pound'


class PaymentStatusChoices(TextChoices):
    PENDING = 'pending', 'Pending'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'
    REFUNDED = 'refunded', 'Refunded'