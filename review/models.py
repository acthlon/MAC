from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from accounts.models import CustomUser
from core.choices import Rating
from core.models import TimeStampModel


# NOTE: Should inherit from timestamped mopdel
class Reviews(TimeStampModel):
    user = models.ForeignKey(
        CustomUser, on_delete=models.PROTECT, related_name="reviews"
    )
    comment = models.TextField(max_length=500, blank=False)
    rating = models.IntegerField(choices=Rating.choices)
    purchase_verified = models.BooleanField(
        default=True
    )  # Should be purchased_verified

    content_type = models.ForeignKey(
        ContentType, on_delete=models.PROTECT, related_name="reviews"
    )
    object_id = models.UUIDField()
    content_object = GenericForeignKey("content_type", "object_id")

    @property
    def get_item_name(self):
        from utils.reviews.review import ReviewUtils

        return ReviewUtils.get_item_name(self)
        if self.content_object:
            return self.content_object.name

    @property
    def calculate_item_average_rating(self):

        from utils.reviews.review import ReviewUtils

        return ReviewUtils.calculate_item_average_rating(self)

    @property
    def get_review_count(self):
        from utils.reviews.review import ReviewUtils

        return ReviewUtils.calculate_review_count(self)

    class Meta:
        verbose_name_plural = "Reviews"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Review for {self.content_object.name} by {self.user.username}"
