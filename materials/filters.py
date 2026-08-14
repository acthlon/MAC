import django_filters

from core.choices import MaterialCategory, Quality, Rating
from materials.models import Materials


class MaterialsFilter(django_filters.FilterSet):
    name_search = django_filters.CharFilter(field_name="name", lookup_expr="icontains")
    description_search = django_filters.CharFilter(
        field_name="description", lookup_expr="icontains"
    )

    min_price = django_filters.NumberFilter(
        field_name="price", lookup_expr="gte", label="Min Prices"
    )
    max_price = django_filters.NumberFilter(
        field_name="price", lookup_expr="lte", label="Max Prices"
    )

    quality_category = django_filters.ChoiceFilter(
        choices=Quality.choices, lookup_expr="iexact", label="All Qualities"
    )
    categories = django_filters.ChoiceFilter(
        choices=MaterialCategory.choices,
        field_name="categories__name",
        lookup_expr="iexact",
        label="All Categories",
    )

    reviews = django_filters.ChoiceFilter(
        choices=Rating.choices,
        label="Material Rating",
        field_name="review__rating",
        lookup_expr="iexact",
    )

    class Meta:
        model = Materials
        fields = ()
