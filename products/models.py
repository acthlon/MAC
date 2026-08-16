import uuid

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils.text import slugify

from accounts.models import CustomUser
from core.choices import IS_PRIMARY_CHOICES, ProductSize
from core.models import (
    CatalogBaseModel,
    Category,
    GeneratedImagePath,
    GeneratedVideoPath,
    SpecificationBaseModel,
    VariantBaseModel,
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


class ProductVariant(VariantBaseModel):
    product = models.ForeignKey(
        Products, on_delete=models.CASCADE, related_name="variants"
    )
    size = models.CharField(
        max_length=100, blank=True, null=True, choices=ProductSize.choices
    )

    @property
    def calculate_product_variant_final_price(self):

        from utils.products.product import VariantUtils  # isort: skip

        return VariantUtils.calculate_product_variant_final_price(self)

    @property
    def calculate_sku_value(self):

        from utils.products.product import VariantUtils  # isort: skip

        return VariantUtils.calculate_sku_value(self)

    @property
    def get_stock_status(self):

        from utils.products.product import VariantUtils  # isort: skip

        return VariantUtils.get_stock_status(self)

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)

        if self.id:
            self.sku = self.calculate_sku_value

            super().save(update_fields=["sku"])

    class Meta:
        unique_together = (
            "product",
            "size",
            "color",
        )  # A product can only have one 'M' variant

    def __str__(self):
        return f"{self.product.name} - {self.get_size_display()} ({self.get_color_display()})"


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
    is_primary = models.BooleanField(choices=IS_PRIMARY_CHOICES, default=False)

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
