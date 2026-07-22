import django_filters

from core.constants import (MATERIAL_CATEGORY_CHOICES, QUALITY_CHOICES,
                            RATING_CHOICES)
from materials.models import Materials


class MaterialsFilter(django_filters.FilterSet):
  
    name_search = django_filters.CharFilter(field_name='name',lookup_expr='icontains')
    description_search = django_filters.CharFilter(field_name = 'description',lookup_expr='icontains')

    min_price = django_filters.NumberFilter(field_name='price',lookup_expr='gte', label='Min Prices')
    max_price = django_filters.NumberFilter(field_name='price',lookup_expr='lte',label='Max Prices')

    quality_category = django_filters.ChoiceFilter(choices=QUALITY_CHOICES,lookup_expr='icontains',label='All Qualities')
    categories = django_filters.ChoiceFilter(choices=MATERIAL_CATEGORY_CHOICES,field_name='categories__name',lookup_expr='iexact',label='All Categories')

    review = django_filters.ChoiceFilter(choices = RATING_CHOICES,label= 'Material Rating')


    class Meta:
        model = Materials
        fields = ()
