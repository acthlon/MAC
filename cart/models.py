from secrets import token_hex

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from accounts.models import CustomUser
from core.models import TimeStampModel


class Cart(TimeStampModel):
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="cart"
    )
    cart_code = models.CharField(max_length=255, unique=True, blank=True)

    @property
    def cart_total_actual_price(self):
        from utils.cart.cart import CartUtils  # isort: skip

        return CartUtils.cart_total_actual_price(self)

    @property
    def cart_total_discount(self):
        from utils.cart.cart import CartUtils  # isort: skip

        return CartUtils.cart_total_discount(self)

    @property
    def calculate_cart_total_item_count(self):
        from utils.cart.cart import CartUtils  # isort: skip

        return CartUtils.calculate_cart_total_item_count(self)

    @property
    def cart_total_discounted_price(self):
        from utils.cart.cart import CartUtils  # isort: skip

        return CartUtils.cart_total_discounted_price(self)

    def save(self, *args, **kwargs):
        if not self.cart_code:  # NOTE: perorm while loop over here.
            self.cart_code = token_hex(3)  # NOTE: use token hex here instead of uuid
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Carts"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username}'s Cart with cartcode:{self.cart_code}"


class CartItem(TimeStampModel):
    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    quantity = models.PositiveIntegerField(default=1)

    def get_item_name(self):
        from utils.core.core import CatalogUtils

        catalog_item = CatalogUtils.get_catalog_item(self)
        return getattr(catalog_item, "name", None)

    def get_item_image(self):

        image = (
            self.content_object.get_variant_pry_image
            if self.content_object
            and getattr(self.content_object, "get_variant_pry_image", None)
            else None
        )
        return image

    def save(self, *args, **kwargs):

        # self.sub_total = self.calculate_item_total

        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "CartItems"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Cartitem in {self.cart.user.username}'s cart"
