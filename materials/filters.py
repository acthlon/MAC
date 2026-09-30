import django_filters
from django.db.models import Avg

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
    category = django_filters.ChoiceFilter(
        choices=MaterialCategory.choices,
        field_name="categories__name",
        lookup_expr="iexact",
        label="All Categories",
    )

    ratings = django_filters.ChoiceFilter(
        choices=Rating.choices,
        label="Material Rating",
        method="filter_by_average_rating",
    )

    def filter_by_average_rating(self, queryset, name, value):
        if value:
            val = int(value)
            return queryset.annotate(avg_rating=Avg("reviews__rating")).filter(
                avg_rating__gte=val, avg_rating__lt=val + 1
            )
        return queryset

    class Meta:
        model = Materials
        fields = ()
