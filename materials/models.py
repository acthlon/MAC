import uuid
from decimal import Decimal

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils.text import slugify

from accounts.models import CustomUser
from core.choices import BOOLEAN_CHOICES, Color, Pattern, Status
from core.models import (
    CatalogBaseModel,
    Category,
    GeneratedImagePath,
    GeneratedVideoPath,
    InventoryBaseModel,
    SpecificationBaseModel,
)
from review.models import Reviews

image_path = GeneratedImagePath()

video_path = GeneratedVideoPath()


class Materials(CatalogBaseModel):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="materials"
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
        limit_choices_to={"target_model__model": "materials"},
        related_name="materials",
    )

    @property
    def get_similar_materials(self):

        from utils.materials.material import MaterialUtils  # isort: skip

        return MaterialUtils.get_similar_materials(self)

    @property
    def calculate_total_stock(self):

        from utils.materials.material import MaterialUtils  # isort: skip

        return MaterialUtils.calculate_total_stock(self)

    def save(self, *args, **kwargs):

        if not self.slug or self.slug != slugify(self.name):
            original_slug = slugify(self.name) or "product"
            slug = original_slug
            counter = 1

            # Loop until a unique slug is found
            while Materials.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{original_slug}-{counter}"
                counter += 1
            self.slug = slug

        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Materials"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name}"


class MaterialVariant(InventoryBaseModel):
    material = models.ForeignKey(
        Materials, on_delete=models.CASCADE, related_name="variants"
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

    @property
    def calculate_variant_actual_unit_price(self):

        catalog_item = getattr(self, "material", None)
        if not catalog_item:
            return Decimal("0.00")
        price = catalog_item.price + self.price_adjustment
        return price.quantize(Decimal("0.00"))

    @property
    def calculate_variant_discount(self):
        catalog_item = getattr(self, "material", None)
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
    def calculate_sku_value(self):
        from utils.materials.material import VariantUtils  # isort: skip

        return VariantUtils.calculate_sku_value(self)

    @property
    def get_stock_status(self):

        from utils.materials.material import VariantUtils  # isort: skip

        return VariantUtils.get_stock_status(self)

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)

        if self.id:
            self.sku = self.calculate_sku_value
            super().save(update_fields=["sku"])

    def __str__(self):
        return f"{self.material.name} - {self.get_color_display()}"

    class Meta:
        unique_together = ("material", "color")


class MaterialSpecification(SpecificationBaseModel):
    material = models.OneToOneField(
        Materials, on_delete=models.CASCADE, related_name="specifications"
    )

    width = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    thread_count = models.IntegerField(blank=True, null=True)
    pattern = models.CharField(
        max_length=100, blank=True, null=True, choices=Pattern.choices
    )

    def __str__(self):
        return f"Specs for {self.material.name}"


class MaterialImages(models.Model):
    variant = models.ForeignKey(
        MaterialVariant, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to=image_path, null=True, blank=True)
    display_order = models.PositiveIntegerField(null=True, blank=True)
    is_primary = models.BooleanField(choices=BOOLEAN_CHOICES, default=False)

    class Meta:
        ordering = ["display_order"]

    def __str__(self):
        return f"Image for {self.variant.material.name} - ({self.variant.color})"


class MaterialVideo(models.Model):
    material = models.ForeignKey(
        Materials, on_delete=models.CASCADE, related_name="videos"
    )
    video = models.FileField(upload_to=video_path, null=True, blank=True)
    thumbnail = models.ImageField(upload_to=video_path, null=True, blank=True)
    display_order = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["display_order"]

    def __str__(self):
        return f"Video for {self.material.name}"
