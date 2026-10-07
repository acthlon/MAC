import uuid
from decimal import Decimal

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils.text import slugify

from accounts.models import CustomUser
from core.choices import BOOLEAN_CHOICES, Color, ProductSize, Status
from core.models import (
    CatalogBaseModel,
    Category,
    GeneratedImagePath,
    GeneratedVideoPath,
    InventoryBaseModel,
    SpecificationBaseModel,
    TimeStampModel,
)
from review.models import Reviews

image_path = GeneratedImagePath()
video_path = GeneratedVideoPath()


class Products(CatalogBaseModel):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="products"
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    reviews = GenericRelation(
        Reviews, content_type_field="content_type", object_id_field="object_id"
    )

    categories = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        limit_choices_to={"target_model__model": "products"},
        related_name="products",
    )

    @property
    def get_similar_products(self):

        from utils.products.product import ProductUtils  # isort: skip

        return ProductUtils.get_similar_products(self)

    @property
    def calculate_total_stock(self):

        from utils.products.product import ProductUtils  # isort: skip

        return ProductUtils.calculate_total_stock(self)

    def save(self, *args, **kwargs):

        if not self.slug or self.slug != slugify(self.name):
            orig_slug = slugify(self.name) or "product"
            slug = orig_slug
            counter = 1

            while Products.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{orig_slug}-{counter}"
                counter += 1
            self.slug = slug

        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Products"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class ProductVariant(TimeStampModel):
    product = models.ForeignKey(
        Products, on_delete=models.CASCADE, related_name="variants"
    )
    color = models.CharField(
        max_length=100, choices=Color.choices, blank=True, null=True
    )
    status = models.CharField(choices=Status.choices, default=Status.ACTIVE)

    @property
    def get_variant_pry_image(self):
        if not hasattr(self, "images"):
            return None
        image_obj = (
            self.images.filter(is_primary=True).first() or self.images.first()
            if self
            else None
        )
        image = image_obj.image if image_obj and image_obj.image else None
        return image

    class Meta:
        unique_together = ("product", "color")

    def __str__(self):
        return f"{self.product.name} - {self.get_color_display()}"


class ProductVariantSize(InventoryBaseModel):
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE, related_name="sizes"
    )
    size = models.CharField(
        max_length=100, blank=True, null=True, choices=ProductSize.choices
    )

    @property
    def calculate_variant_actual_unit_price(self):

        variant = getattr(self, "variant", None)
        catalog_item = variant.product
        if not variant and catalog_item:
            return Decimal("0.00")
        price = catalog_item.price + self.price_adjustment
        return price.quantize(Decimal("0.00"))

    @property
    def calculate_variant_discount(self):

        variant = getattr(self, "variant", None)
        catalog_item = variant.product

        if not catalog_item:
            return Decimal("0.00")
        return catalog_item.discount.quantize(Decimal("0.00"))

    @property
    def calculate_variant_discounted_price(self):
        price = (
            self.calculate_variant_actual_unit_price - self.calculate_variant_discount
        )
        return price.quantize(Decimal("0.00"))

    @property
    def calculate_variant_percent_discount(self):

        discount = self.calculate_variant_discount
        price = self.calculate_variant_actual_unit_price
        if discount > 0 and price > 0:
            return ((discount / price) * 100).quantize(Decimal("0.00"))
        return Decimal("0.00")

    @property
    def get_stock_status(self):

        from utils.products.product import VariantSizeUtils  # isort: skip

        return VariantSizeUtils.get_stock_status(self)

    @property
    def calculate_sku_value(self):

        from utils.products.product import VariantSizeUtils  # isort: skip

        return VariantSizeUtils.calculate_sku_value(self)

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)

        if self.id:
            self.sku = self.calculate_sku_value

            super().save(update_fields=["sku"])

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["variant", "size"], name="unique_variant_size"
            )
        ]


class ProductSpecification(SpecificationBaseModel):
    product = models.OneToOneField(
        Products, on_delete=models.CASCADE, related_name="specification"
    )

    product_line = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"Specs for {self.product.name}"


class ProductImages(models.Model):
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to=image_path, null=True, blank=True)
    display_order = models.PositiveIntegerField(null=True, blank=True)
    is_primary = models.BooleanField(choices=BOOLEAN_CHOICES, default=False)

    class Meta:
        ordering = ["display_order"]

    def __str__(self):
        return f"Image for {self.variant.product.name}"


class ProductVideo(models.Model):
    product = models.ForeignKey(
        Products, on_delete=models.CASCADE, related_name="videos"
    )
    video = models.FileField(upload_to=video_path, null=True, blank=True)
    thumbnail = models.ImageField(upload_to=video_path, null=True, blank=True)
    display_order = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["display_order"]

    def __str__(self):
        return f"Video for {self.product.name}"
