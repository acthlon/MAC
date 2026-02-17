import django_filters
from materials.models import Materials
from core.constants import CATEGORY_CHOICES,RATING_CHOICES



class MaterialsFilter(django_filters.FilterSet):
  
    name_search = django_filters.CharFilter(field_name='name',lookup_expr='icontains')
    description_search = django_filters.CharFilter(field_name = 'description',lookup_expr='icontains')

    min_price = django_filters.NumberFilter(field_name='price',lookup_expr='gte', label='Min Prices')
    max_price = django_filters.NumberFilter(field_name='price',lookup_expr='lte',label='Max Prices')

    category = django_filters.ChoiceFilter(choices=CATEGORY_CHOICES,label='All Qualities')

    review = django_filters.ChoiceFilter(choices = RATING_CHOICES,label= 'Product Rating')


    class Meta:
        model = Materials
        fields = ()
