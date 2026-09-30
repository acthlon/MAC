import django_filters
from django.db.models import Avg

from core.choices import ProductCategory, ProductSize, Quality, Rating
from products.models import Products


class ProductFilter(django_filters.FilterSet):
    name_search = django_filters.CharFilter(field_name="name", lookup_expr="icontains")
    description_search = django_filters.CharFilter(
        field_name="description", lookup_expr="icontains"
    )

    max_price = django_filters.NumberFilter(
        field_name="price", lookup_expr="lte", label="All Prices"
    )

    min_prices = django_filters.NumberFilter(
        field_name="price", lookup_expr="gte", label="All Prices"
    )

    quality_category = django_filters.ChoiceFilter(
        choices=Quality.choices, lookup_expr="iexact", label="All Quality Category"
    )
    category = django_filters.ChoiceFilter(
        choices=ProductCategory.choices,
        lookup_expr="iexact",
        field_name="categories__name",
        label="All Category",
    )

    ratings = django_filters.ChoiceFilter(
        choices=Rating.choices,
        label="Product Rating",
        method="filter_by_average_rating",
    )

    sizes = django_filters.ChoiceFilter(
        choices=ProductSize.choices,
        lookup_expr="iexact",
        field_name="variant__size",
        label="Size",
    )

    def filter_by_average_rating(self, queryset, name, value):
        if value:
            val = int(value)
            return queryset.annotate(avg_rating=Avg("reviews__rating")).filter(
                avg_rating__gte=val, avg_rating__lt=val + 1
            )
        return queryset

    # anywhere you see field_name, it means that attribute is not direct attribute of the model (Product in hte is case) so you acess it through the related model (e.g sizes as a case study)

    class Meta:
        model = Products
        fields = ()
